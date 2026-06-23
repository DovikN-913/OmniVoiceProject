from typing import Annotated

from fastapi import Header, HTTPException

from app.core.config import API_KEYS
from app.core.errors import ERROR_MESSAGES, ErrorCode
from app.models.schemas import ApiResponse
from app.services.rate_limiter import rate_limiter
from app.utils.ids import new_request_id, now_ms


def extract_bearer_token(authorization: str | None) -> str | None:
    """从 Authorization 头中提取 Bearer Token。

    Args:
        authorization: 请求头值，例如 "Bearer <token>"。

    Returns:
        解析成功返回 token 字符串，否则返回 None。
    """
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1].strip() or None


def verify_api_key(authorization: str | None) -> str:
    """校验 Authorization 头中的 API key，并返回 token。

    Args:
        authorization: Authorization 请求头值。

    Returns:
        校验通过的 API key token。

    Raises:
        HTTPException: token 缺失或不合法时抛出。
    """
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
    """基于可选的客户端请求 ID 生成内部 request_id。

    Args:
        x_request_id: 客户端提供的请求 ID（可为空）。

    Returns:
        用于链路追踪的 request_id 字符串。
    """
    return new_request_id(x_request_id)


def build_envelope(code: ErrorCode, request_id: str, data=None, message: str | None = None):
    """构造统一的 API 响应信封（envelope）。

    Args:
        code: 业务错误码。
        request_id: 请求 ID（用于追踪）。
        data: 响应数据体。
        message: 可选自定义消息；为空时使用 code 对应的默认消息。

    Returns:
        ApiResponse 模型实例。
    """
    return ApiResponse(
        code=int(code),
        message=message or ERROR_MESSAGES[code],
        request_id=request_id,
        timestamp=now_ms(),
        data=data,
    )


def check_rate_limit(api_key: str, request_id: str):
    """执行限流校验，超限则抛出 HTTPException。

    Args:
        api_key: 调用方 API key。
        request_id: 当前请求 ID。

    Returns:
        未超限时返回 RateLimitResult。

    Raises:
        HTTPException: 超限时抛出（包含限流响应头信息）。
    """
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
    """依赖注入：将 X-Request-Id 解析为内部 request_id。"""
    return get_request_id(x_request_id)


def require_api_key(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> str:
    """依赖注入：校验 Authorization 并返回 API key token。"""
    return verify_api_key(authorization)


def optional_idempotency_key(
    x_idempotency_key: Annotated[str | None, Header(alias="X-Idempotency-Key")] = None,
) -> str | None:
    """依赖注入：读取 X-Idempotency-Key。"""
    return x_idempotency_key
