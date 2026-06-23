# -*- coding: utf-8 -*-
import os
from pathlib import Path

# 项目根目录（app/core/config.py -> 上两级）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = PROJECT_ROOT / "asset"
OUTPUT_DIR = PROJECT_ROOT / "output"
MODELS_DIR = PROJECT_ROOT / "models"

# GPU 设备，单卡 [0] 或多卡 [0, 1]
CUDA_DEVICES = [0, 1]

MODEL_PATH = os.getenv("TTS_MODEL_PATH", str(MODELS_DIR / "k2-fsa/OmniVoice"))
DEVICE_MAP = os.getenv("TTS_DEVICE", f"cuda:{CUDA_DEVICES[0]}")
SAMPLE_RATE = 24000

# API 服务配置
API_HOST = os.getenv("TTS_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("TTS_API_PORT", "8000"))
API_VERSION = "1.0.0"

_DEFAULT_API_KEYS = "dev-tts-api-key-change-me"
API_KEYS = {
    k.strip()
    for k in os.getenv("TTS_API_KEYS", _DEFAULT_API_KEYS).split(",")
    if k.strip()
}

RATE_LIMIT_QPS = int(os.getenv("TTS_RATE_LIMIT_QPS", "10"))
RATE_LIMIT_DAILY = int(os.getenv("TTS_RATE_LIMIT_DAILY", "100000"))
WS_MAX_CONNECTIONS_PER_KEY = int(os.getenv("TTS_WS_MAX_CONNECTIONS", "5"))
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("TTS_IDEMPOTENCY_TTL", str(24 * 3600)))

HTTP_TEXT_MAX_LEN = 5000
WS_TEXT_MAX_LEN = 20000
SEGMENT_MAX_LEN = 500
SEGMENT_FORCE_WINDOW = 200


def _voice(wav_file: str, **meta: str) -> dict:
    return {
        **meta,
        "prompt_wav": str(ASSET_DIR / wav_file),
    }


VOICE_CONFIG = {
    "Vivian": _voice(
        "Vivian.wav",
        description="明亮、略带锋芒的年轻女声",
        prompt_text="你好很高兴认识你，我叫Vivian，这是我的声音",
        gender="female",
        language="zh",
    ),
    "Serena": _voice(
        "Serena.wav",
        description="温暖、柔和的年轻女声",
        prompt_text="你好很高兴认识你，我叫Serena，这是我的声音",
        gender="female",
        language="zh",
    ),
    "Ryan": _voice(
        "Ryan.wav",
        description="节奏感强、富有动感的男声",
        prompt_text="你好很高兴认识你，我叫Ryan，这是我的声音",
        gender="male",
        language="zh",
    ),
    "Aiden": _voice(
        "Aiden.wav",
        description="阳光开朗、音色清晰的美式男声",
        prompt_text="你好很高兴认识你，我叫Aiden，这是我的声音",
        gender="male",
        language="en",
    ),
    "Sohee": _voice(
        "Sohee.wav",
        description="情感丰富、温暖的女声",
        prompt_text="你好很高兴认识你，我叫Sohee，这是我的声音",
        gender="female",
        language="zh",
    ),
}

VOICE_CONFIG["sohee"] = VOICE_CONFIG["Sohee"]
