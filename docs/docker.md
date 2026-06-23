# Docker 部署指南

本文介绍如何使用 Docker / Docker Compose 部署 OmniVoice TTS API 服务。

## 前置要求

### 硬件

| 项目 | 要求 |
| ---- | ---- |
| GPU | NVIDIA GPU，显存建议 ≥ 8GB |
| 磁盘 | 模型约 3GB+，镜像约 8GB+ |

### 软件

| 组件 | 说明 |
| ---- | ---- |
| Docker | 20.10+ |
| Docker Compose | v2.0+（`docker compose` 命令） |
| NVIDIA Container Toolkit | GPU 容器必需，[安装文档](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html) |

验证 GPU 是否可用：

```bash
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

---

## 快速开始

### 1. 准备模型

模型不包含在镜像中，需在宿主机先下载：

```bash
# 在项目根目录
pip install modelscope
python scripts/download_model.py
```

完成后应存在目录：`./models/k2-fsa/OmniVoice/`。

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，**生产环境务必修改 API Key**：

```env
TTS_API_KEYS=your-production-api-key
TTS_DEVICE=cuda:0
TTS_API_PORT=8000
```

### 3. 构建并启动

```bash
docker compose up -d --build
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8000/api/v1/tts/health

# 音色列表
curl http://localhost:8000/api/v1/tts/voices \
  -H "Authorization: Bearer your-production-api-key"
```

- 交互式文档：http://localhost:8000/docs  
- 健康检查：`GET /api/v1/tts/health`  
- 首次启动模型加载约 1~3 分钟，`health` 在加载完成前可能返回 `503`

---

## 文件说明

| 文件 | 说明 |
| ---- | ---- |
| `Dockerfile` | GPU 镜像构建定义（CUDA 12.8 + PyTorch 2.7.1） |
| `docker-compose.yaml` | 单服务编排，挂载模型与输出目录 |
| `.dockerignore` | 构建上下文排除规则 |
| `scripts/docker-entrypoint.sh` | 启动前检查模型目录 |

---

## 常用命令

```bash
# 后台启动
docker compose up -d --build

# 查看日志
docker compose logs -f tts-api

# 停止
docker compose down

# 重新构建（代码或依赖变更后）
docker compose build --no-cache
docker compose up -d
```

---

## 环境变量

完整列表见 `.env.example`：

| 变量 | 默认值 | 说明 |
| ---- | ------ | ---- |
| `TTS_API_KEYS` | `dev-tts-api-key-change-me` | API 密钥，逗号分隔 |
| `TTS_API_PORT` | `8000` | 宿主机映射端口 |
| `TTS_DEVICE` | `cuda:0` | 推理设备 |
| `TTS_MODEL_PATH` | `/app/models/k2-fsa/OmniVoice` | 容器内模型路径 |
| `TTS_RATE_LIMIT_QPS` | `10` | 每 Key 每秒请求上限 |
| `TTS_RATE_LIMIT_DAILY` | `100000` | 每 Key 日调用上限 |
| `TTS_WS_MAX_CONNECTIONS` | `5` | 每 Key WebSocket 并发上限 |
| `NVIDIA_VISIBLE_DEVICES` | `all` | 可见 GPU，如 `0` 或 `0,1` |

---

## 目录挂载

```yaml
volumes:
  - ./models:/app/models    # 模型权重（必需）
  - ./output:/app/output    # 合成输出（可选）
```

**建议**：模型通过 volume 挂载，不要打入镜像，便于升级与节省镜像体积。

---

## 生产部署建议

### 1. 安全

- 修改默认 `TTS_API_KEYS`
- 前置 Nginx / Traefik 做 HTTPS 终结
- 不要将 `.env` 提交到 Git

### 2. 资源

- 单容器单 GPU 推理，默认 `uvicorn` 单 worker
- 高并发场景建议多实例 + 负载均衡，每实例绑定独立 GPU

### 3. 反向代理示例（Nginx）

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

### 4. 健康检查与编排

Compose 已配置 `healthcheck`。Kubernetes 可复用：

```yaml
livenessProbe:
  httpGet:
    path: /api/v1/tts/health
    port: 8000
  initialDelaySeconds: 180
  periodSeconds: 30
```

---

## Windows 注意事项

1. 使用 **WSL2** 后端运行 Docker Desktop  
2. 安装 [NVIDIA Container Toolkit for WSL2](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)  
3. 在 WSL2 终端中执行 `docker compose` 命令  
4. 确保 `./models` 路径在 WSL 文件系统内（如 `/home/user/OmniVoiceProject`），避免跨文件系统挂载性能问题

---

## 故障排查

### 健康检查返回 503

```json
{"status":"degraded","model_loaded":false,...}
```

**原因**：模型未挂载或路径错误。  
**处理**：确认宿主机 `./models/k2-fsa/OmniVoice` 存在，且 `TTS_MODEL_PATH` 与挂载一致。

### 容器无法使用 GPU

```bash
# 检查 toolkit
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu22.04 nvidia-smi
```

若第二条失败，请重装 NVIDIA Container Toolkit。

### 合成接口返回 1006

模型加载失败。查看日志：

```bash
docker compose logs tts-api | tail -100
```

### 端口被占用

修改 `.env` 中 `TTS_API_PORT=8080`，然后 `docker compose up -d`。

---

## 仅构建镜像（不使用 Compose）

```bash
docker build -t omnivoice-tts-api:latest .

docker run -d \
  --name omnivoice-tts-api \
  --gpus all \
  -p 8000:8000 \
  -e TTS_API_KEYS=your-api-key \
  -v "$(pwd)/models:/app/models" \
  -v "$(pwd)/output:/app/output" \
  omnivoice-tts-api:latest
```

---

## 相关文档

- [TTS API 接口文档](./TTS%20API.md)
- [PyTorch 安装说明](./install.md)
- [项目 README](../README.md)
