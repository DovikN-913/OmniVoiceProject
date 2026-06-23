from app.core.errors import ErrorCode
from app.services.voice_registry import resolve_voice
from app.core.config import HTTP_TEXT_MAX_LEN, WS_TEXT_MAX_LEN


def validate_synthesis_params(
    text: str,
    voice_id: str,
    speed: float,
    volume: float,
    max_len: int,
) -> ErrorCode | None:
    if not text or not text.strip():
        return ErrorCode.TEXT_EMPTY
    if len(text) > max_len:
        return ErrorCode.TEXT_TOO_LONG
    if resolve_voice(voice_id) is None:
        return ErrorCode.VOICE_NOT_FOUND
    if not 0.5 <= speed <= 2.0:
        return ErrorCode.INVALID_PARAMS
    if not 0.0 <= volume <= 2.0:
        return ErrorCode.INVALID_PARAMS
    return None
