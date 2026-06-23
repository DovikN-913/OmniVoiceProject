import re

from app.core.config import SEGMENT_FORCE_WINDOW, SEGMENT_MAX_LEN

_SPLIT_RE = re.compile(r"(?<=[。！？；，\n])")


def split_text(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []

    parts = _SPLIT_RE.split(text)
    segments: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) <= SEGMENT_MAX_LEN:
            segments.append(part)
            continue
        segments.extend(_force_split(part))
    return segments


def _force_split(text: str) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + SEGMENT_FORCE_WINDOW, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks
