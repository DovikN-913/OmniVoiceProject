from enum import IntEnum


class ErrorCode(IntEnum):
    SUCCESS = 0
    VOICE_NOT_FOUND = 1001
    TEXT_EMPTY = 1002
    TEXT_TOO_LONG = 1003
    INVALID_PARAMS = 1004
    SYNTHESIS_FAILED = 1005
    INTERNAL_ERROR = 1006
    TASK_CANCELLED = 1007
    UNAUTHORIZED = 4010
    FORBIDDEN = 4030
    RATE_LIMITED = 4290


ERROR_MESSAGES = {
    ErrorCode.SUCCESS: "success",
    ErrorCode.VOICE_NOT_FOUND: "voice not found",
    ErrorCode.TEXT_EMPTY: "text is empty",
    ErrorCode.TEXT_TOO_LONG: "text length exceeded",
    ErrorCode.INVALID_PARAMS: "invalid parameter",
    ErrorCode.SYNTHESIS_FAILED: "synthesis failed",
    ErrorCode.INTERNAL_ERROR: "internal server error",
    ErrorCode.TASK_CANCELLED: "task cancelled",
    ErrorCode.UNAUTHORIZED: "unauthorized",
    ErrorCode.FORBIDDEN: "forbidden",
    ErrorCode.RATE_LIMITED: "rate limit exceeded",
}
