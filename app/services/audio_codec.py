import base64
import io
from typing import Literal

import numpy as np
import soundfile as sf

from app.core.config import SAMPLE_RATE

AudioFormat = Literal["wav", "pcm", "mp3"]


def audio_duration_seconds(audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> float:
    if audio.size == 0:
        return 0.0
    return round(len(audio) / sample_rate, 3)


def apply_volume(audio: np.ndarray, volume: float) -> np.ndarray:
    if volume == 1.0:
        return audio
    scaled = audio.astype(np.float32) * volume
    return np.clip(scaled, -1.0, 1.0)


def encode_audio(
    audio: np.ndarray,
    audio_format: AudioFormat,
    sample_rate: int = SAMPLE_RATE,
) -> tuple[bytes, str]:
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
    return base64.b64encode(audio_bytes).decode("ascii")


def concat_audio(chunks: list[np.ndarray]) -> np.ndarray:
    if not chunks:
        return np.array([], dtype=np.float32)
    return np.concatenate([np.asarray(c, dtype=np.float32) for c in chunks])
