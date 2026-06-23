import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from app.core.config import DEVICE_MAP, MODEL_PATH, PINYIN_WITH_TONE, SAMPLE_RATE
from app.services.audio_codec import apply_volume, audio_duration_seconds
from app.services.voice_registry import resolve_voice

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def to_pinyin(text: str) -> str:
    """将中文文本转换为拼音（用于辅助输出/调试）。

    是否带音调由 PINYIN_WITH_TONE 配置控制。

    Args:
        text: 输入文本。

    Returns:
        以空格分隔的拼音字符串；若未安装 pypinyin，则返回空字符串。
    """
    try:
        from pypinyin import Style, lazy_pinyin
    except ImportError:
        return ""
    style = Style.TONE if PINYIN_WITH_TONE else Style.NORMAL
    return " ".join(lazy_pinyin(text, style=style))


@dataclass
class SegmentResult:
    text: str
    audio: np.ndarray
    duration: float
    pinyin: str


class TTSEngine:
    def __init__(self) -> None:
        """创建 TTS 引擎实例（模型按需加载）。"""
        self._model: Any = None
        self._lock = asyncio.Lock()
        self._load_error: str | None = None
        self._torch = None

    @property
    def is_loaded(self) -> bool:
        """模型是否已加载到内存中。"""
        return self._model is not None

    @property
    def load_error(self) -> str | None:
        """返回最近一次模型加载失败的错误信息（如有）。"""
        return self._load_error

    def _import_torch(self):
        """延迟导入 torch 并缓存模块引用。"""
        if self._torch is None:
            import torch

            self._torch = torch
        return self._torch

    def gpu_available(self) -> bool:
        """检查当前运行环境是否可用 CUDA。"""
        try:
            torch = self._import_torch()
            return torch.cuda.is_available()
        except ImportError:
            return False

    async def load(self) -> None:
        """加载 OmniVoice 模型（若尚未加载）。

        Raises:
            Exception: 模型加载失败时向上抛出，便于调用方决定是否快速失败。
        """
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
        """合成单个文本分段。

        Args:
            text: 待合成分段文本。
            voice_id: 使用的音色 ID。
            speed: 传给模型的语速倍率。
            volume: 生成后对音频应用的增益倍率。
            enable_pinyin: 是否为该分段计算拼音辅助信息。

        Returns:
            SegmentResult，包含音频波形与元信息。

        Raises:
            RuntimeError: 模型未加载时抛出。
            ValueError: voice_id 不存在/不合法时抛出。
        """
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
