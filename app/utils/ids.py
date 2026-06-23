import re
import time
import uuid
from datetime import datetime


def now_ms() -> int:
    """返回当前 Unix 时间戳（毫秒）。"""
    return int(time.time() * 1000)


def new_request_id(client_id: str | None = None) -> str:
    """生成用于链路追踪与幂等缓存的 request_id。

    Args:
        client_id: 可选的客户端请求 ID（例如 X-Request-Id）。若提供，将进行安全清洗并拼入生成的
            request_id 中。

    Returns:
        带时间戳前缀的 request_id 字符串。
    """
    suffix = uuid.uuid4().hex[:6]
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    if client_id:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "", client_id)[:32]
        return f"req_{ts}_{safe}"
    return f"req_{ts}_{suffix}"


def new_task_id() -> str:
    """生成用于一次合成任务的 task_id。

    Returns:
        带时间戳前缀的 task_id 字符串。
    """
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"tts_{ts}_{uuid.uuid4().hex[:6]}"
