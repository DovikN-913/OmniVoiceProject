# OmniVoiceProject

English | **[简体中文](./README.md)**

A multilingual zero-shot text-to-speech (TTS) inference project built on [OmniVoice](https://github.com/k2-fsa/OmniVoice), featuring voice cloning and built-in preset voice references.

OmniVoice is an ultra-large-scale zero-shot TTS model supporting **600+ languages**, built on a diffusion language model architecture with high-quality synthesis, fast inference, and voice cloning capabilities.

## Features

- **Zero-shot voice cloning**: synthesize any target voice with only a short reference audio and transcript
- **Multilingual support**: TTS for Chinese and 600+ other languages
- **Preset voices**: built-in references including Vivian, Serena, Ryan, Aiden, and Sohee
- **Speed control**: adjust synthesis speed via the `speed` parameter
- **Enterprise-grade API**: HTTP and WebSocket streaming synthesis — see [API docs](./docs/TTS%20API.md)
- **Docker deployment**: one-command GPU container startup — see [deployment guide](./docs/docker.md)
- **Local inference**: download models locally for offline GPU inference

## Project Structure

```
OmniVoiceProject/
├── app/                        # TTS API application
│   ├── main.py                 # FastAPI entry point
│   ├── api/                    # Routes and dependencies
│   │   ├── routes.py
│   │   └── dependencies.py
│   ├── core/                   # Config and error codes
│   │   ├── config.py
│   │   └── errors.py
│   ├── models/                 # Pydantic request/response schemas
│   │   └── schemas.py
│   ├── services/               # TTS engine, audio codec, rate limiting, etc.
│   └── utils/
├── scripts/                    # CLI scripts
│   ├── infer.py                # Local single-shot inference
│   └── download_model.py       # Model download
├── docs/                       # Documentation
│   ├── TTS API.md              # API specification
│   ├── docker.md               # Docker deployment guide
│   └── install.md              # PyTorch installation
├── requirements/               # Dependency groups
│   ├── base.txt                # Inference dependencies
│   └── api.txt                 # API service dependencies
├── asset/                      # Reference audio files
├── models/                     # Model weights (gitignored)
├── output/                     # Generated audio (gitignored)
├── server.py                   # Start API server
├── requirements.txt            # Full dependency entry point
├── .env.example
└── README.md
```

## Requirements

- Python 3.10+
- NVIDIA GPU (recommended, CUDA required)
- Disk space: ~3 GB+ for model weights

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/DovikN-913/OmniVoiceProject.git
cd OmniVoiceProject
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. Install PyTorch

Install PyTorch for your CUDA version — see [docs/install.md](./docs/install.md). This project recommends CUDA 12.8:

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

### 4. Install project dependencies

```bash
# Inference only
pip install -r requirements/base.txt

# Inference + API service (full)
pip install -r requirements.txt
```

## Download Model

```bash
python scripts/download_model.py
```

The model will be saved to `./models/k2-fsa/OmniVoice/`.

## Quick Start

### Local Inference

```bash
python scripts/infer.py
```

Output: `./output/out_1.0.wav` (24 kHz)

### Start API Server

```bash
# Optional: configure API Key
export TTS_API_KEYS="your-secret-key"   # Linux / macOS
# $env:TTS_API_KEYS="your-secret-key"   # Windows PowerShell

python server.py
```

- Service URL: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `GET /api/v1/tts/health`

Default API Key: `dev-tts-api-key-change-me` (local development only)

### API Examples

```bash
# List voices
curl "http://localhost:8000/api/v1/tts/voices" \
  -H "Authorization: Bearer dev-tts-api-key-change-me"

# Non-streaming synthesis
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Authorization: Bearer dev-tts-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, this is my voice.","voice_id":"Vivian","speed":1.0}'
```

Full API reference: [docs/TTS API.md](./docs/TTS%20API.md).

### Docker Deployment

```bash
python scripts/download_model.py   # Download model on host
cp .env.example .env               # Configure API Key
docker compose up -d --build
```

See [docs/docker.md](./docs/docker.md) for details.

## Preset Voices

Voice configuration is in `app/core/config.py`:

| Voice  | Description                              |
| ------ | ---------------------------------------- |
| Vivian | Bright, sharp young female voice         |
| Serena | Warm, soft young female voice            |
| Ryan   | Rhythmic, energetic male voice           |
| Aiden  | Sunny, clear American male voice         |
| Sohee  | Emotionally rich, warm female voice      |

## Configuration

Main settings in `app/core/config.py`, overridable via environment variables:

| Variable         | Description              | Default                          |
| ---------------- | ------------------------ | -------------------------------- |
| `TTS_API_KEYS`   | API keys (comma-separated) | `dev-tts-api-key-change-me`    |
| `TTS_DEVICE`     | Inference device         | `cuda:0`                         |
| `TTS_MODEL_PATH` | Model path               | `./models/k2-fsa/OmniVoice`      |
| `TTS_API_PORT`   | Service port             | `8000`                           |

See `.env.example` for the full list.

## Links

- **OmniVoice Repository**: [k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice)
- **Hugging Face Model**: [k2-fsa/OmniVoice](https://huggingface.co/k2-fsa/OmniVoice)
- **Online Demo**: [Hugging Face Space](https://huggingface.co/spaces/k2-fsa/OmniVoice)
- **Paper**: [OmniVoice: Towards Omnilingual Zero-Shot Text-to-Speech with Diffusion Language Models](https://huggingface.co/papers/2604.00688)

## License

This project code is for learning and inference purposes only. The OmniVoice model is licensed under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) — see the [official repository](https://github.com/k2-fsa/OmniVoice).
