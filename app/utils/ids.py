import re
import time
import uuid
from datetime import datetime


def now_ms() -> int:
    return int(time.time() * 1000)


def new_request_id(client_id: str | None = None) -> str:
    suffix = uuid.uuid4().hex[:6]
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    if client_id:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "", client_id)[:32]
        return f"req_{ts}_{safe}"
    return f"req_{ts}_{suffix}"


def new_task_id() -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"tts_{ts}_{uuid.uuid4().hex[:6]}"
