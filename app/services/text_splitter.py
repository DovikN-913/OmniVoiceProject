from app.core.config import SEGMENT_FORCE_WINDOW, SEGMENT_MAX_LEN


def split_text(text: str) -> list[str]:
    """将输入文本切分为适合流式合成的多个片段。

    切分规则：
    1) 先按句末标点断句；
    2) 合并过短片段，同时尽量控制每段不超过最大长度；
    3) 若仍有超长段，先尝试在次级标点二次切分；若仍无法保证长度，则按固定长度强制切割兜底。

    Args:
        text: 待切分文本。

    Returns:
        分段后的文本列表；若输入为空/全空白，返回空列表。
    """
    text = text.strip()
    if not text:
        return []

    max_chars = SEGMENT_MAX_LEN
    min_chars = SEGMENT_FORCE_WINDOW

    sentences: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        buf.append(ch)

        if ch in {"。", "！", "？", "!", "?"}:
            sentences.append("".join(buf).strip())
            buf = []
        elif ch == "…":
            while i + 1 < len(text) and text[i + 1] == "…":
                i += 1
                buf.append(text[i])
            sentences.append("".join(buf).strip())
            buf = []
        elif ch == "." and not (
            i > 0
            and i < len(text) - 1
            and text[i - 1].isdigit()
            and text[i + 1].isdigit()
        ):
            sentences.append("".join(buf).strip())
            buf = []
        i += 1

    if buf:
        tail = "".join(buf).strip()
        if tail:
            sentences.append(tail)

    merged: list[str] = []
    current = ""
    for sent in sentences:
        if not sent:
            continue
        if not current:
            current = sent
        elif len(current) < min_chars or len(current) + len(sent) <= max_chars:
            current += sent
        else:
            merged.extend(_split_oversized(current, max_chars))
            current = sent
    if current:
        merged.extend(_split_oversized(current, max_chars))

    return merged if merged else [text]


def _split_oversized(segment: str, max_chars: int) -> list[str]:
    """将单个超长片段切分为不超过 max_chars 的多个片段。

    优先在次级标点处分割；若无法产生有效分割（例如没有次级标点），则按固定长度强制切割兜底。
    对于二次合并后的结果，如仍出现超长段，也会再次强制切割以保证上限生效。

    Args:
        segment: 可能超过 max_chars 的单段文本。
        max_chars: 输出片段允许的最大字符数。

    Returns:
        切分后的片段列表，保证每段长度 <= max_chars。
    """
    if len(segment) <= max_chars:
        return [segment]

    secondary = {"，", "；", "、", ",", ";", "：", ":",}
    parts: list[str] = []
    buf: list[str] = []
    for ch in segment:
        buf.append(ch)
        if ch in secondary and len("".join(buf)) >= 10:
            parts.append("".join(buf).strip())
            buf = []
    if buf:
        parts.append("".join(buf).strip())

    if len(parts) <= 1:
        return _force_split(segment, max_chars)

    result: list[str] = []
    current = ""
    for part in parts:
        if not current:
            current = part
        elif len(current) + len(part) <= max_chars:
            current += part
        else:
            result.append(current)
            current = part
    if current:
        result.append(current)
    normalized: list[str] = []
    for item in result:
        if len(item) <= max_chars:
            normalized.append(item)
        else:
            normalized.extend(_force_split(item, max_chars))
    return normalized


def _force_split(text: str, window: int) -> list[str]:
    """按固定窗口长度强制切分文本。

    Args:
        text: 待切分文本。
        window: 每段窗口大小（字符数）。

    Returns:
        切分后的片段列表；每段长度不超过 window，并对首尾空白做 strip。
        若 strip 后会导致结果为空，则退化为返回原文本的单段列表。
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + window, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end
    return chunks if chunks else [text]
