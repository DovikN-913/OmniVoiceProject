import asyncio
import json
import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from app.api.dependencies import (
    build_envelope,
    check_rate_limit,
    extract_bearer_token,
    optional_idempotency_key,
    require_api_key,
    resolve_request_id,
)
from app.core.config import (
    API_KEYS,
    API_VERSION,
    HTTP_TEXT_MAX_LEN,
    SAMPLE_RATE,
    WS_MAX_CONNECTIONS_PER_KEY,
    WS_TEXT_MAX_LEN,
)
from app.core.errors import ERROR_MESSAGES, ErrorCode
from app.models.schemas import StreamClientMessage, SynthesizeData, SynthesizeRequest
from app.services.audio_codec import (
    audio_duration_seconds,
    concat_audio,
    encode_audio,
    encode_base64,
)
from app.services.idempotency import idempotency_store
from app.services.text_splitter import split_text
from app.services.tts_engine import engine
from app.services.validation import validate_synthesis_params
from app.services.voice_registry import list_voices, resolve_voice
from app.utils.ids import new_request_id, new_task_id, now_ms

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tts", tags=["tts"])

_ws_connections: dict[str, int] = defaultdict(int)


def _business_response(
    code: ErrorCode,
    request_id: str,
    data=None,
    message: str | None = None,
) -> JSONResponse:
    body = build_envelope(code, request_id, data=data, message=message)
    return JSONResponse(status_code=200, content=body.model_dump())


@router.get("/health")
async def health():
    model_loaded = engine.is_loaded
    gpu_ok = engine.gpu_available()
    status = "ok" if model_loaded else "degraded"
    payload = {
        "status": status,
        "version": API_VERSION,
        "model_loaded": model_loaded,
        "gpu_available": gpu_ok,
        "timestamp": now_ms(),
    }
    if engine.load_error:
        payload["load_error"] = engine.load_error
    status_code = 200 if status == "ok" else 503
    return JSONResponse(status_code=status_code, content=payload)


@router.get("/voices")
async def get_voices(
    api_key: str = Depends(require_api_key),
    request_id: str = Depends(resolve_request_id),
    language: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    check_rate_limit(api_key, request_id)

    voices = list_voices(language=language)
    total = len(voices)
    start = (page - 1) * page_size
    end = start + page_size
    data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": voices[start:end],
    }
    return _business_response(ErrorCode.SUCCESS, request_id, data=data)


@router.post("/synthesize")
async def synthesize(
    body: SynthesizeRequest,
    api_key: str = Depends(require_api_key),
    request_id: str = Depends(resolve_request_id),
    idempotency_key: str | None = Depends(optional_idempotency_key),
):
    check_rate_limit(api_key, request_id)

    if idempotency_key:
        cached = idempotency_store.get(f"{api_key}:{idempotency_key}")
        if cached is not None:
            return JSONResponse(status_code=200, content=cached)

    err = validate_synthesis_params(
        body.text,
        body.voice_id or "",
        body.speed,
        body.volume,
        HTTP_TEXT_MAX_LEN,
    )
    if err:
        response = build_envelope(err, request_id, data=None).model_dump()
        if idempotency_key:
            idempotency_store.set(f"{api_key}:{idempotency_key}", response)
        return JSONResponse(status_code=200, content=response)

    if not engine.is_loaded:
        response = build_envelope(ErrorCode.INTERNAL_ERROR, request_id, data=None).model_dump()
        return JSONResponse(status_code=200, content=response)

    canonical_voice, _ = resolve_voice(body.voice_id or "")
    task_id = new_task_id()

    try:
        segments = split_text(body.text)
        if not segments:
            return _business_response(ErrorCode.TEXT_EMPTY, request_id, data=None)

        audio_chunks = []
        pinyin_parts = []
        for segment in segments:
            result = await engine.synthesize_segment(
                text=segment,
                voice_id=canonical_voice or body.voice_id or "",
                speed=body.speed,
                volume=body.volume,
                enable_pinyin=body.enable_pinyin,
            )
            audio_chunks.append(result.audio)
            if body.enable_pinyin and result.pinyin:
                pinyin_parts.append(result.pinyin)

        merged = concat_audio(audio_chunks)
        audio_bytes, content_type = encode_audio(merged, body.audio_format)
        duration = audio_duration_seconds(merged, SAMPLE_RATE)

        if body.response_mode == "binary":
            headers = {
                "X-Task-Id": task_id,
                "X-Audio-Duration": str(duration),
                "X-Request-Id": request_id,
            }
            return Response(content=audio_bytes, media_type=content_type, headers=headers)

        data = SynthesizeData(
            task_id=task_id,
            audio_data=encode_base64(audio_bytes),
            audio_format=body.audio_format,
            sample_rate=SAMPLE_RATE,
            audio_duration=duration,
            audio_pinyin=" ".join(pinyin_parts) if body.enable_pinyin else None,
        )
        response = build_envelope(ErrorCode.SUCCESS, request_id, data=data.model_dump()).model_dump()
        if idempotency_key:
            idempotency_store.set(f"{api_key}:{idempotency_key}", response)
        return JSONResponse(status_code=200, content=response)

    except ValueError as exc:
        message = str(exc)
        code = ErrorCode.INVALID_PARAMS if "format" in message else ErrorCode.SYNTHESIS_FAILED
        return _business_response(code, request_id, data=None, message=message)
    except Exception:
        logger.exception("Synthesis failed request_id=%s", request_id)
        return _business_response(ErrorCode.SYNTHESIS_FAILED, request_id, data=None)


@router.websocket("/stream")
async def stream_tts(websocket: WebSocket):
    token = extract_bearer_token(websocket.headers.get("authorization"))
    if not token:
        token = websocket.query_params.get("api_key")

    if not token or token not in API_KEYS:
        await websocket.close(code=4401, reason="unauthorized")
        return

    current = _ws_connections[token]
    if current >= WS_MAX_CONNECTIONS_PER_KEY:
        await websocket.close(code=4429, reason="too many connections")
        return

    await websocket.accept()
    _ws_connections[token] += 1
    busy = False
    current_task_id: str | None = None
    cancel_event = asyncio.Event()
    heartbeat_stop = asyncio.Event()

    async def heartbeat_loop():
        while not heartbeat_stop.is_set():
            await asyncio.sleep(30)
            if heartbeat_stop.is_set():
                break
            try:
                await websocket.send_json({"event": "heartbeat", "timestamp": now_ms()})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = StreamClientMessage.model_validate(json.loads(raw))
            except (json.JSONDecodeError, ValidationError) as exc:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": int(ErrorCode.INVALID_PARAMS),
                        "message": str(exc),
                    }
                )
                continue

            if message.action == "pong":
                continue

            if message.action == "cancel":
                if message.task_id and message.task_id == current_task_id:
                    cancel_event.set()
                await websocket.send_json(
                    {
                        "event": "error",
                        "task_id": message.task_id,
                        "code": int(ErrorCode.TASK_CANCELLED),
                        "message": ERROR_MESSAGES[ErrorCode.TASK_CANCELLED],
                    }
                )
                continue

            if message.action != "synthesize" or not message.payload:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": int(ErrorCode.INVALID_PARAMS),
                        "message": "invalid action",
                    }
                )
                continue

            if busy:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": int(ErrorCode.INVALID_PARAMS),
                        "message": "connection is busy",
                    }
                )
                continue

            payload = message.payload
            request_id = message.request_id or new_request_id()
            err = validate_synthesis_params(
                payload.text,
                payload.voice_id or "",
                payload.speed,
                payload.volume,
                WS_TEXT_MAX_LEN,
            )
            if err:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": int(err),
                        "message": ERROR_MESSAGES[err],
                        "request_id": request_id,
                    }
                )
                continue

            if not engine.is_loaded:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": int(ErrorCode.INTERNAL_ERROR),
                        "message": ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR],
                        "request_id": request_id,
                    }
                )
                continue

            canonical_voice, _ = resolve_voice(payload.voice_id or "")
            segments = split_text(payload.text)
            if not segments:
                await websocket.send_json(
                    {
                        "event": "error",
                        "code": int(ErrorCode.TEXT_EMPTY),
                        "message": ERROR_MESSAGES[ErrorCode.TEXT_EMPTY],
                        "request_id": request_id,
                    }
                )
                continue

            busy = True
            cancel_event.clear()
            task_id = new_task_id()
            current_task_id = task_id
            total_segments = len(segments)
            total_duration = 0.0

            await websocket.send_json(
                {
                    "event": "begin",
                    "task_id": task_id,
                    "request_id": request_id,
                    "voice_id": canonical_voice,
                    "speed": payload.speed,
                    "total_segments": total_segments,
                }
            )

            try:
                for index, segment in enumerate(segments, start=1):
                    if cancel_event.is_set():
                        raise asyncio.CancelledError()

                    result = await engine.synthesize_segment(
                        text=segment,
                        voice_id=canonical_voice or payload.voice_id or "",
                        speed=payload.speed,
                        volume=payload.volume,
                        enable_pinyin=payload.enable_pinyin,
                    )
                    audio_bytes, _ = encode_audio(result.audio, payload.audio_format)
                    total_duration += result.duration

                    await websocket.send_json(
                        {
                            "event": "streaming",
                            "task_id": task_id,
                            "index": index,
                            "total_segments": total_segments,
                            "text": segment,
                            "audio_data": encode_base64(audio_bytes),
                            "audio_format": payload.audio_format,
                            "sample_rate": SAMPLE_RATE,
                            "audio_duration": result.duration,
                            "audio_pinyin": result.pinyin if payload.enable_pinyin else None,
                        }
                    )

                await websocket.send_json(
                    {
                        "event": "end",
                        "task_id": task_id,
                        "total_segments": total_segments,
                        "total_duration": round(total_duration, 3),
                    }
                )
            except asyncio.CancelledError:
                await websocket.send_json(
                    {
                        "event": "error",
                        "task_id": task_id,
                        "code": int(ErrorCode.TASK_CANCELLED),
                        "message": ERROR_MESSAGES[ErrorCode.TASK_CANCELLED],
                        "request_id": request_id,
                    }
                )
            except ValueError as exc:
                await websocket.send_json(
                    {
                        "event": "error",
                        "task_id": task_id,
                        "code": int(ErrorCode.SYNTHESIS_FAILED),
                        "message": str(exc),
                        "request_id": request_id,
                    }
                )
            except Exception:
                logger.exception("WebSocket synthesis failed task_id=%s", task_id)
                await websocket.send_json(
                    {
                        "event": "error",
                        "task_id": task_id,
                        "code": int(ErrorCode.SYNTHESIS_FAILED),
                        "message": ERROR_MESSAGES[ErrorCode.SYNTHESIS_FAILED],
                        "request_id": request_id,
                    }
                )
            finally:
                busy = False
                current_task_id = None
                cancel_event.clear()

    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_stop.set()
        heartbeat_task.cancel()
        _ws_connections[token] = max(0, _ws_connections[token] - 1)
