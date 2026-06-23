#!/bin/sh
set -e

MODEL_DIR="${TTS_MODEL_PATH:-./models/k2-fsa/OmniVoice}"

if [ ! -d "$MODEL_DIR" ]; then
    echo "[WARN] Model directory not found: $MODEL_DIR"
    echo "[WARN] Download on host first: python scripts/download_model.py"
    echo "[WARN] Then mount ./models into the container."
fi

exec "$@"
