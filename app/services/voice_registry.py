from app.core.config import SAMPLE_RATE, VOICE_CONFIG


def _canonical_voice_id(voice_id: str) -> str | None:
    if voice_id in VOICE_CONFIG:
        return voice_id
    lower = voice_id.lower()
    for key in VOICE_CONFIG:
        if key.lower() == lower:
            return key
    return None


def resolve_voice(voice_id: str | None) -> tuple[str, dict] | None:
    if not voice_id:
        return None
    canonical = _canonical_voice_id(voice_id)
    if canonical is None:
        return None
    return canonical, VOICE_CONFIG[canonical]


def list_voices(language: str | None = None) -> list[dict]:
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
