# Docker 部署指南

本文档介绍如何使用仓库自带的 `Dockerfile` 与 `docker-compose.yaml` 部署 `OmniVoiceProject`。当前镜像面向 GPU 推理场景，默认基于 `CUDA 12.8`。

## 部署方式概览

仓库内的容器方案具有以下特点：

- 使用 `nvidia/cuda:12.8.0-cudnn-runtime-ubuntu22.04` 作为基础镜像
- 镜像内安装 `PyTorch 2.7.1` 与项目 Python 依赖
- 通过 volume 挂载本地模型目录，避免把模型权重打进镜像
- 启动时执行健康检查，模型未加载完成前容器可能暂时处于 `starting`

## 前置要求

### 硬件要求

| 项目 | 建议 |
| ---- | ---- |
| GPU | NVIDIA GPU，建议显存 `8 GB+` |
| 磁盘 | 模型约 `3 GB+`，镜像与缓存建议预留 `8 GB+` |

### 软件要求

| 组件 | 说明 |
| ---- | ---- |
| Docker | `20.10+` |
| Docker Compose | `v2+`，使用 `docker compose` 命令 |
| NVIDIA Container Toolkit | GPU 容器运行必需 |

验证 GPU 容器能力：

```bash
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

如果该命令失败，请先修复 Docker 与 NVIDIA 运行时环境。

## 1. 准备模型

模型文件默认不打包进镜像，需要先在宿主机下载：

```bash
python scripts/download_model.py
```

下载完成后，请确认目录存在：

```text
./models/k2-fsa/OmniVoice/
```

## 2. 准备环境变量

复制模板：

```bash
cp .env.example .env
```

Windows PowerShell 可使用：

```powershell
Copy-Item .env.example .env
```

至少建议修改以下配置：

```env
TTS_API_KEYS=your-production-api-key
TTS_API_PORT=8000
TTS_DEVICE=cuda:0
TTS_MODEL_PATH=/app/models/k2-fsa/OmniVoice
```

> 生产环境不要继续使用默认的 `dev-tts-api-key-change-me`。

## 3. 启动服务

```bash
docker compose up -d --build
```

Compose 服务名为 `tts-api`，容器名默认是：

```text
omnivoice-tts-api
```

## 4. 验证部署

### 健康检查

```bash
curl http://localhost:8000/api/v1/tts/health
```

### 音色列表

```bash
curl http://localhost:8000/api/v1/tts/voices \
  -H "Authorization: Bearer your-production-api-key"
```

### 页面入口

- Swagger：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/tts/health`

首次启动时服务会预加载模型，通常需要 `1` 到 `3` 分钟，期间健康检查可能返回 `503`。

## Compose 配置说明

当前 `docker-compose.yaml` 的核心行为如下：

```yaml
services:
  tts-api:
    ports:
      - "${TTS_API_PORT:-8000}:8000"
    env_file:
      - .env
    volumes:
      - ./models:/app/models
      - ./output:/app/output
    gpus: all
```

说明：

- `./models` 挂载到容器内 `/app/models`
- `./output` 用于持久化合成结果
- 端口由 `.env` 中的 `TTS_API_PORT` 控制
- `gpus: all` 表示容器默认可见所有 GPU

## 常用运维命令

后台启动：

```bash
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f tts-api
```

查看容器状态：

```bash
docker compose ps
```

停止服务：

```bash
docker compose down
```

代码或依赖更新后重新构建：

```bash
docker compose build --no-cache
docker compose up -d
```

## 环境变量

完整列表见 `.env.example`。容器部署常用项如下：

| 变量 | 默认值 | 说明 |
| ---- | ------ | ---- |
| `TTS_API_KEYS` | `dev-tts-api-key-change-me` | API Key，支持多个值 |
| `TTS_API_HOST` | `0.0.0.0` | 服务监听地址 |
| `TTS_API_PORT` | `8000` | 宿主机映射端口 |
| `TTS_DEVICE` | `cuda:0` | 推理设备 |
| `TTS_MODEL_PATH` | `/app/models/k2-fsa/OmniVoice` | 容器内模型路径 |
| `TTS_RATE_LIMIT_QPS` | `10` | 每 Key 每秒请求限制 |
| `TTS_RATE_LIMIT_DAILY` | `100000` | 每 Key 每日请求限制 |
| `TTS_WS_MAX_CONNECTIONS` | `5` | 每 Key WebSocket 并发连接数 |
| `TTS_IDEMPOTENCY_TTL` | `86400` | 幂等缓存保留时间，秒 |
| `NVIDIA_VISIBLE_DEVICES` | `all` | 可见 GPU，如 `0`、`0,1` |

## 生产部署建议

### 安全

- 替换默认 API Key
- 通过 Nginx、Traefik 或云负载均衡提供 `HTTPS` / `WSS`
- 不要把 `.env`、模型目录和输出音频提交到代码仓库

### 资源规划

- 单实例默认适合单 GPU 推理
- 高并发场景建议按 GPU 做多实例部署
- 每个实例前放置反向代理或网关统一做证书、限流和审计

### 健康检查

镜像与 Compose 已内置健康检查：

```bash
curl -sf http://127.0.0.1:8000/api/v1/tts/health
```

如果迁移到 Kubernetes，可沿用该探针地址。

## Nginx 反向代理示例

```nginx
server {
    listen 443 ssl;
    server_name tts.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/v1/tts/stream {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
    }
}
```

## Windows 使用建议

如果你在 Windows 上使用 Docker Desktop：

1. 启用 **WSL2** 后端
2. 按需安装适用于 WSL2 的 NVIDIA Container Toolkit
3. 尽量在 WSL2 文件系统内运行项目，例如 `/home/<user>/OmniVoiceProject`
4. 避免把大型模型目录放在 Windows 与 WSL 跨文件系统挂载路径上，以减少 I/O 性能损失

## 故障排查

### 健康检查一直返回 `503`

常见原因：

- 模型还在预加载
- 模型目录未正确挂载
- `TTS_MODEL_PATH` 与容器内路径不一致

建议先查看日志：

```bash
docker compose logs -f tts-api
```

### 容器无法识别 GPU

先检查宿主机和 Docker 运行时：

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

如果第二条失败，通常是 NVIDIA Container Toolkit 或 Docker GPU 支持未正确安装。

### 接口返回 `1006`

`1006` 对应内部错误，通常表示模型加载或推理过程异常。请优先查看容器日志中的错误信息。

### 端口冲突

修改 `.env`：

```env
TTS_API_PORT=8080
```

然后重新启动：

```bash
docker compose up -d
```

## 仅构建镜像

如果你不想使用 Compose，也可以直接构建并运行镜像：

```bash
docker build -t omnivoice-tts-api:latest .
```

```bash
docker run -d \
  --name omnivoice-tts-api \
  --gpus all \
  -p 8000:8000 \
  -e TTS_API_KEYS=your-api-key \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/output:/app/output" \
  omnivoice-tts-api:latest
```

## 相关文档

- [项目首页](../README.md)
- [安装指南](./install.md)
- [TTS API 文档](./TTS%20API.md)
