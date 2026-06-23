from app.core.config import SAMPLE_RATE, VOICE_CONFIG


def _canonical_voice_id(voice_id: str) -> str | None:
    """将输入 voice_id 解析为 VOICE_CONFIG 中的规范 key。

    匹配规则为大小写不敏感；返回值一定是 VOICE_CONFIG 中真实存在的 key。

    Args:
        voice_id: 客户端传入的音色标识。

    Returns:
        命中时返回规范化后的 VOICE_CONFIG key，否则返回 None。
    """
    if voice_id in VOICE_CONFIG:
        return voice_id
    lower = voice_id.lower()
    for key in VOICE_CONFIG:
        if key.lower() == lower:
            return key
    return None


def resolve_voice(voice_id: str | None) -> tuple[str, dict] | None:
    """解析 voice_id 并返回 (规范 voice_id, 元数据)。

    Args:
        voice_id: 客户端传入的音色标识（可为空）。

    Returns:
        命中时返回 (canonical_voice_id, voice_metadata)，否则返回 None。
    """
    if not voice_id:
        return None
    canonical = _canonical_voice_id(voice_id)
    if canonical is None:
        return None
    return canonical, VOICE_CONFIG[canonical]


def list_voices(language: str | None = None) -> list[dict]:
    """列出可用音色列表（用于 API 响应）。

    Args:
        language: 可选语言过滤（ISO 639-1，例如 "zh"、"en"）。

    Returns:
        适合 JSON 序列化的音色元数据列表（按 voice_id 排序）。
    """
    seen: set[str] = set()
    items: list[dict] = []
    for voice_id, meta in VOICE_CONFIG.items():
        display = voice_id if voice_id[0].isupper() else voice_id.capitalize()
        if display in seen:
            continue
        seen.add(display)
        if language and meta.get("language") != language:
            continue
        items.append(
            {
                "voice_id": display,
                "display_name": display,
                "gender": meta["gender"],
                "language": meta["language"],
                "description": meta["description"].rstrip("。"),
                "sample_rate": SAMPLE_RATE,
            }
        )
    items.sort(key=lambda x: x["voice_id"])
    return items
