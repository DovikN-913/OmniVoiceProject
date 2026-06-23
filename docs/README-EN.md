# OmniVoiceProject

English | **[简体中文](../README.md)**

`OmniVoiceProject` turns [OmniVoice](https://github.com/k2-fsa/OmniVoice) into a practical multilingual zero-shot TTS project that is ready for local experiments, service integration, and GPU deployment.

Instead of exposing only a model demo, this repository packages the model as a real project with local inference scripts, FastAPI endpoints, WebSocket streaming, preset voices, authentication, rate limiting, idempotency support, and Docker-based deployment.

## Highlights

- **Zero-shot voice cloning** with reference audio and transcript
- **Multilingual TTS** powered by an OmniVoice model that supports 600+ languages
- **Two integration modes**: HTTP batch synthesis and WebSocket streaming synthesis
- **Production-oriented API behavior**: API keys, rate limiting, idempotency, and unified response envelopes
- **Built-in preset voices**: Vivian, Serena, Ryan, Aiden, and Sohee
- **Two ways to run**: direct Python service or Docker Compose on GPU

## Documentation

- [Quick Start](#quick-start): get local inference and the API server running
- [Installation Guide](./docs/install.md): environment setup, PyTorch installation, and troubleshooting
- [TTS API Guide](./docs/TTS%20API.md): HTTP and WebSocket request/response details
- [Docker Deployment Guide](./docs/docker.md): GPU container deployment and operations
- [Chinese README](./README.md): Chinese project documentation

## What It Is For

- Exposing a TTS service for web apps, internal tools, or device-side applications
- Evaluating OmniVoice as a reusable backend service rather than a one-off notebook demo
- Serving as a starting point for custom voices, auth logic, quotas, and service extensions
- Running a GPU-backed TTS service on a single machine or inside a containerized environment

## Project Layout

```text
OmniVoiceProject/
├── app/
│   ├── api/                     # Routes, dependencies, auth helpers
│   ├── core/                    # Config, constants, and error codes
│   ├── models/                  # Pydantic request/response schemas
│   ├── services/                # TTS engine, text splitting, audio encoding, rate limit, etc.
│   ├── utils/                   # request_id / task_id helpers
│   └── main.py                  # FastAPI application entry
├── asset/                       # Preset reference audio files
├── docs/                        # Project documentation
├── scripts/
│   ├── download_model.py        # Download OmniVoice model weights
│   ├── infer.py                 # Local one-shot inference example
│   └── docker-entrypoint.sh     # Docker startup check
├── Dockerfile                   # GPU image definition
├── docker-compose.yaml          # Compose service definition
├── server.py                    # API server launcher
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── README.md
└── README-EN.md
```

## Requirements

- Python `3.10+`
- NVIDIA GPU with CUDA support is strongly recommended
- About `3 GB+` free disk space for model weights
- `ffmpeg` is required only if you want `mp3` output

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/DovikN-913/OmniVoiceProject.git
cd OmniVoiceProject
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install PyTorch

Install the PyTorch build that matches your CUDA version. `CUDA 12.8` is the recommended baseline for this project. See [docs/install.md](./docs/install.md) for a fuller setup guide.

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

### 4. Install project dependencies

```bash
pip install -r requirements.txt
```

### 5. Download the model

```bash
python scripts/download_model.py
```

The model is stored in `./models/k2-fsa/OmniVoice/` by default.

### 6. Run the local inference example

```bash
python scripts/infer.py
```

The script writes a 24 kHz audio file to `./output/out_1.0.wav`.

### 7. Start the API server

You can use the default local API key or define your own first:

```powershell
$env:TTS_API_KEYS="your-secret-key"
python server.py
```

```bash
export TTS_API_KEYS="your-secret-key"
python server.py
```

Once started, the service exposes:

- Root info: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/docs`
- Health endpoint: `http://localhost:8000/api/v1/tts/health`

Default local API key: `dev-tts-api-key-change-me`

### 8. Call the API

List available voices:

```bash
curl "http://localhost:8000/api/v1/tts/voices" \
  -H "Authorization: Bearer dev-tts-api-key-change-me"
```

Run non-streaming synthesis:

```bash
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Authorization: Bearer dev-tts-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is my voice.",
    "voice_id": "Vivian",
    "speed": 1.0
  }'
```

See [docs/TTS API.md](./docs/TTS%20API.md) for the full API surface.

## Preset Voices

Preset voices are defined in `app/core/config.py`:

| Voice | Language | Description |
| ----- | -------- | ----------- |
| Vivian | `zh` | Bright young female voice with a crisp tone |
| Serena | `zh` | Warm and soft young female voice |
| Ryan | `zh` | Rhythmic and energetic male voice |
| Aiden | `en` | Clear and sunny American male voice |
| Sohee | `zh` | Warm female voice with richer emotion |

> The API resolves `voice_id` case-insensitively, so values like `Sohee` and `sohee` are both accepted.

## Configuration

Common environment variables are listed below. The full list is in `.env.example`.

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `TTS_API_KEYS` | `dev-tts-api-key-change-me` | API keys, comma-separated |
| `TTS_API_HOST` | `0.0.0.0` | Listen host |
| `TTS_API_PORT` | `8000` | Service port |
| `TTS_DEVICE` | `cuda:0` | Inference device such as `cpu` or `cuda:0` |
| `TTS_MODEL_PATH` | `./models/k2-fsa/OmniVoice` | Model directory |
| `TTS_RATE_LIMIT_QPS` | `10` | Per-key requests per second |
| `TTS_RATE_LIMIT_DAILY` | `100000` | Per-key daily request cap |
| `TTS_WS_MAX_CONNECTIONS` | `5` | Per-key WebSocket connection limit |
| `TTS_PINYIN_WITH_TONE` | `true` | Whether returned pinyin includes tone marks |

## Docker Deployment

To run the service in a GPU container:

```bash
python scripts/download_model.py
cp .env.example .env
docker compose up -d --build
```

On Windows PowerShell, you can use:

```powershell
python scripts/download_model.py
Copy-Item .env.example .env
docker compose up -d --build
```

See [docs/docker.md](./docs/docker.md) for deployment and operations details.

## Notes For Developers

- The HTTP synthesis endpoint supports `wav`, `pcm`, and `mp3`
- `response_mode=binary` returns raw audio bytes instead of base64 JSON
- The WebSocket interface supports `synthesize`, `cancel`, and `pong`
- The service preloads the model on startup, so the health endpoint may briefly return `503` during warm-up

## Links

- [OmniVoice Repository](https://github.com/k2-fsa/OmniVoice)
- [Hugging Face Model](https://huggingface.co/k2-fsa/OmniVoice)
- [Online Demo](https://huggingface.co/spaces/k2-fsa/OmniVoice)
- [OmniVoice Paper](https://huggingface.co/papers/2604.00688)

## License

This repository is intended for learning, testing, and service packaging examples. For the OmniVoice model license and usage limits, follow the official repository and model card.
