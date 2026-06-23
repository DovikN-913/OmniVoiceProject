import base64
import io
from typing import Literal

import numpy as np
import soundfile as sf

from app.core.config import SAMPLE_RATE

AudioFormat = Literal["wav", "pcm", "mp3"]


def audio_duration_seconds(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> float:
    """计算音频时长（秒）。

    Args:
        audio: 一维音频采样数组。
        sample_rate: 采样率（Hz）。

    Returns:
        时长（秒），保留 3 位小数。
    """
    if audio.size == 0:
        return 0.0
    return round(len(audio) / sample_rate, 3)


def apply_volume(audio: np.ndarray, volume: float) -> np.ndarray:
    """对音频应用线性增益并进行裁剪。

    Args:
        audio: 音频采样（通常范围 [-1.0, 1.0]）。
        volume: 增益倍率；1.0 表示不变。

    Returns:
        增益后的音频，并裁剪到 [-1.0, 1.0]。
    """
    if volume == 1.0:
        return audio
    scaled = audio.astype(np.float32) * volume
    return np.clip(scaled, -1.0, 1.0)


def encode_audio(
    audio: np.ndarray,
    audio_format: AudioFormat,
    sample_rate: int = SAMPLE_RATE,
) -> tuple[bytes, str]:
    """将 float32 波形编码为指定输出格式。

    Args:
        audio: 一维音频采样数组（期望范围 [-1.0, 1.0]）。
        audio_format: 输出格式：wav / pcm / mp3。
        sample_rate: 输出音频采样率。

    Returns:
        (编码后的字节串, 对应的 Content-Type)。

    Raises:
        ValueError: 不支持的音频格式，或 mp3 缺少所需依赖。
    """
    audio = np.asarray(audio, dtype=np.float32)
    if audio_format == "pcm":
        pcm = np.clip(audio, -1.0, 1.0)
        pcm16 = (pcm * 32767).astype(np.int16)
        return pcm16.tobytes(), "audio/pcm"

    if audio_format == "wav":
        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
        return buffer.getvalue(), "audio/wav"

    if audio_format == "mp3":
        try:
            from pydub import AudioSegment
        except ImportError as exc:
            raise ValueError("mp3 format requires pydub package") from exc

        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format="WAV", subtype="PCM_16")
        buffer.seek(0)
        segment = AudioSegment.from_wav(buffer)
        out = io.BytesIO()
        segment.export(out, format="mp3")
        return out.getvalue(), "audio/mpeg"

    raise ValueError(f"unsupported audio format: {audio_format}")


def encode_base64(audio_bytes: bytes) -> str:
    """将音频字节进行 Base64 编码，便于 JSON 传输。

    Args:
        audio_bytes: 编码后的音频字节串。

    Returns:
        Base64 字符串（ASCII）。
    """
    return base64.b64encode(audio_bytes).decode("ascii")


def concat_audio(chunks: list[np.ndarray]) -> np.ndarray:
    """将多个音频片段拼接为一个连续波形。

    Args:
        chunks: 一维音频数组列表。

    Returns:
        拼接后的 float32 音频数组。
    """
    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate([np.asarray(c, dtype=np.float32) for c in chunks])
