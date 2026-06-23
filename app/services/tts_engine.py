import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from app.core.config import DEVICE_MAP, MODEL_PATH, SAMPLE_RATE
from app.services.audio_codec import apply_volume, audio_duration_seconds
from app.services.voice_registry import resolve_voice

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def to_pinyin(text: str) -> str:
    try:
        from pypinyin import lazy_pinyin
    except ImportError:
        return ""
    return " ".join(lazy_pinyin(text))


@dataclass
class SegmentResult:
    text: str
    audio: np.ndarray
    duration: float
    pinyin: str


class TTSEngine:
    def __init__(self) -> None:
        self._model: Any = None
        self._lock = asyncio.Lock()
        self._load_error: str | None = None
        self._torch = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def load_error(self) -> str | None:
        return self._load_error

    def _import_torch(self):
        if self._torch is None:
            import torch

            self._torch = torch
        return self._torch

    def gpu_available(self) -> bool:
        try:
            torch = self._import_torch()
            return torch.cuda.is_available()
        except ImportError:
            return False

    async def load(self) -> None:
        if self._model is not None:
            return

        loop = asyncio.get_running_loop()

        def _load():
            torch = self._import_torch()
            from omnivoice import OmniVoice

            logger.info("Loading OmniVoice model from %s on %s", MODEL_PATH, DEVICE_MAP)
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            device = DEVICE_MAP if torch.cuda.is_available() else "cpu"
            return OmniVoice.from_pretrained(MODEL_PATH, device_map=device, dtype=dtype)

        try:
            self._model = await loop.run_in_executor(None, _load)
            logger.info("OmniVoice model loaded")
        except Exception as exc:
            self._load_error = str(exc)
            logger.exception("Failed to load OmniVoice model")
            raise

    async def synthesize_segment(
        self,
        text: str,
        voice_id: str,
        speed: float,
        volume: float,
        enable_pinyin: bool,
    ) -> SegmentResult:
        if not self._model:
            raise RuntimeError("model not loaded")

        resolved = resolve_voice(voice_id)
        if resolved is None:
            raise ValueError("voice not found")

        _, voice_meta = resolved
        loop = asyncio.get_running_loop()

        def _generate() -> np.ndarray:
            outputs = self._model.generate(
                text=text,
                ref_audio=voice_meta["prompt_wav"],
                ref_text=voice_meta["prompt_text"],
                speed=speed,
            )
            audio = np.asarray(outputs[0], dtype=np.float32)
            return apply_volume(audio, volume)

        async with self._lock:
            audio = await loop.run_in_executor(None, _generate)

        pinyin = to_pinyin(text) if enable_pinyin else ""
        return SegmentResult(
            text=text,
            audio=audio,
            duration=audio_duration_seconds(audio, SAMPLE_RATE),
            pinyin=pinyin,
        )


engine = TTSEngine()
