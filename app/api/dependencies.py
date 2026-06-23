from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.core.config import API_KEYS
from app.core.errors import ERROR_MESSAGES, ErrorCode
from app.models.schemas import ApiResponse
from app.services.rate_limiter import rate_limiter
from app.utils.ids import new_request_id, now_ms


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def verify_api_key(authorization: str | None) -> str:
    token = extract_bearer_token(authorization)
    if not token or token not in API_KEYS:
        raise HTTPException(
            status_code=401,
            detail={
                "code": int(ErrorCode.UNAUTHORIZED),
                "message": ERROR_MESSAGES[ErrorCode.UNAUTHORIZED],
            },
        )
    return token


def get_request_id(x_request_id: str | None) -> str:
    return new_request_id(x_request_id)


def build_envelope(code: ErrorCode, request_id: str, data=None, message: str | None = None):
    return ApiResponse(
        code=int(code),
        message=message or ERROR_MESSAGES[code],
        request_id=request_id,
        timestamp=now_ms(),
        data=data,
    )


def check_rate_limit(api_key: str, request_id: str):
    result = rate_limiter.check(api_key)
    if result.allowed:
        return result
    raise HTTPException(
        status_code=429,
        detail={
            "code": int(ErrorCode.RATE_LIMITED),
            "message": ERROR_MESSAGES[ErrorCode.RATE_LIMITED],
            "request_id": request_id,
        },
        headers={
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(result.reset_at),
            "Retry-After": str(result.retry_after),
        },
    )


def resolve_request_id(
    x_request_id: Annotated[str | None, Header(alias="X-Request-Id")] = None,
) -> str:
    return get_request_id(x_request_id)


def require_api_key(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> str:
    return verify_api_key(authorization)


def optional_idempotency_key(
    x_idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
) -> str | None:
    return x_idempotency_key
