"""本地推理脚本：单次合成并保存 wav 文件。"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import soundfile as sf
import torch
from omnivoice import OmniVoice

from app.core.config import DEVICE_MAP, MODEL_PATH, OUTPUT_DIR, SAMPLE_RATE, VOICE_CONFIG


def main() -> None:
    """执行一次本地推理并保存输出 wav 文件。"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    voice = VOICE_CONFIG["Serena"]
    model = OmniVoice.from_pretrained(
        MODEL_PATH,
        device_map=DEVICE_MAP,
        dtype=torch.float16,
    )

    audio = model.generate(
        text=(
            "OmniVoice 是一个超大规模多语言零样本文本到语音（TTS）模型，支持超过 600 种语言。"
            "该模型基于一种新颖的扩散语言模型架构，能够生成高质量语音并具备卓越的推理速度，"
            "同时支持声音克隆和声音设计。"
        ),
        ref_audio=voice["prompt_wav"],
        ref_text=voice["prompt_text"],
        speed=1.0,
    )

    output_path = OUTPUT_DIR / "out_1.0.wav"
    sf.write(str(output_path), audio[0], SAMPLE_RATE)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
