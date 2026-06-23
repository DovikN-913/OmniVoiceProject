# OmniVoice TTS API — GPU 镜像（CUDA 12.8）
FROM nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 系统依赖：Python、音频库、ffmpeg（mp3 可选输出）
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    libsndfile1 \
    ffmpeg \
    curl \
    && ln -sf /usr/bin/python3 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*

# PyTorch（CUDA 12.8）
RUN pip install \
    torch==2.7.1 \
    torchvision==0.22.1 \
    torchaudio==2.7.1 \
    --index-url https://download.pytorch.org/whl/cu128

# 项目依赖
COPY requirements.txt requirements/
COPY requirements/base.txt requirements/api.txt requirements/
RUN pip install -r requirements.txt

# 应用代码
COPY app/ app/
COPY scripts/ scripts/
COPY asset/ asset/
COPY server.py .
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

RUN mkdir -p /app/models /app/output

EXPOSE 8000

# 模型加载较慢，给予充足启动宽限期
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD curl -sf http://127.0.0.1:8000/api/v1/tts/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "server.py"]
