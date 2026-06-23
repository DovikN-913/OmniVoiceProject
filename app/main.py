import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.dependencies import build_envelope, get_request_id
from app.api.routes import router
from app.core.config import API_VERSION
from app.core.errors import ErrorCode
from app.services.tts_engine import engine
from app.utils.ids import now_ms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await engine.load()
    except Exception:
        logger.warning("Model preload failed; service will report degraded health")
    yield


app = FastAPI(
    title="OmniVoice TTS API",
    version=API_VERSION,
    lifespan=lifespan,
)
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = get_request_id(request.headers.get("X-Request-Id"))
    message = "invalid request"
    for err in exc.errors():
        msg = err.get("msg", "")
        if "text is empty" in msg:
            body = build_envelope(ErrorCode.TEXT_EMPTY, request_id, data=None).model_dump()
            return JSONResponse(status_code=200, content=body)
        if "voice_id is required" in msg:
            body = build_envelope(ErrorCode.INVALID_PARAMS, request_id, data=None, message=msg).model_dump()
            return JSONResponse(status_code=200, content=body)
        message = msg
    body = build_envelope(ErrorCode.INVALID_PARAMS, request_id, data=None, message=message).model_dump()
    return JSONResponse(status_code=400, content=body)


@app.get("/")
async def root():
    return {
        "service": "OmniVoice TTS API",
        "version": API_VERSION,
        "docs": "/docs",
        "health": "/api/v1/tts/health",
        "timestamp": now_ms(),
    }
