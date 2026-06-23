# OmniVoiceProject

**[English](./docs/README-EN.md)** | 简体中文

`OmniVoiceProject` 是一个围绕 [OmniVoice](https://github.com/k2-fsa/OmniVoice) 封装的多语言零样本文本转语音项目，目标不是只演示模型推理，而是把模型整理成一套真正可运行、可集成、可部署的工程化 TTS 服务。

项目同时提供本地推理脚本、FastAPI HTTP 接口、WebSocket 流式合成、预设参考音色、限流与幂等支持，以及基于 Docker Compose 的 GPU 部署方案，适合本地实验、服务接入和二次开发。

## 项目亮点

- **零样本声音克隆**：通过参考音频和参考文本合成目标音色
- **多语言推理**：底层模型支持 600+ 语言的零样本 TTS 能力
- **双调用方式**：同时提供 HTTP 非流式接口与 WebSocket 流式接口
- **工程化 API**：内置 API Key 鉴权、限流、幂等键、统一响应结构
- **预设音色开箱即用**：仓库内置 Vivian、Serena、Ryan、Aiden、Sohee 五种音色参考
- **本地与容器双运行模式**：既可直接运行 Python 服务，也可通过 Docker GPU 部署

## 文档导航

- [快速开始](#快速开始)：最快跑通本地推理和 API 服务
- [安装指南](./docs/install.md)：环境准备、PyTorch 安装和依赖排查
- [TTS API 文档](./docs/TTS%20API.md)：HTTP / WebSocket 接口说明与示例
- [Docker 部署指南](./docs/docker.md)：GPU 容器部署、运维命令与常见问题
- [English README](./docs/README-EN.md)：英文说明文档

## 适用场景

- 为前端应用、业务后台或智能硬件提供 TTS 服务
- 快速验证 OmniVoice 模型的推理效果和接口封装方式
- 作为自定义音色、鉴权体系、业务编排的二次开发基础
- 在单机 GPU 环境中搭建可调用的内部语音合成服务

## 项目结构

```text
OmniVoiceProject/
├── app/
│   ├── api/                     # 路由、依赖注入、鉴权
│   ├── core/                    # 配置、错误码、全局常量
│   ├── models/                  # Pydantic 请求/响应模型
│   ├── services/                # TTS 引擎、切分、音频编码、限流等
│   ├── utils/                   # request_id / task_id 等工具
│   └── main.py                  # FastAPI 应用入口
├── asset/                       # 预设音色参考音频
├── docs/                        # 项目文档
│   ├── README-EN.md            # 英文项目说明
│   ├── TTS API.md              # API 接口规范
│   ├── docker.md               # Docker 部署指南
│   └── install.md              # 安装指南
├── scripts/
│   ├── download_model.py        # 下载 OmniVoice 模型权重
│   ├── infer.py                 # 本地单次推理示例
│   └── docker-entrypoint.sh     # Docker 启动检查脚本
├── Dockerfile                   # GPU 镜像定义
├── docker-compose.yaml          # 容器编排配置
├── server.py                    # API 服务启动脚本
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例
└── README.md
```

## 环境要求

- Python `3.10+`
- NVIDIA GPU 与 CUDA 环境（推荐，API 与推理场景默认面向 GPU）
- 模型存储空间约 `3 GB+`
- 若需要 `mp3` 输出，系统需额外安装 `ffmpeg`

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/DovikN-913/OmniVoiceProject.git
cd OmniVoiceProject
```

### 2. 创建虚拟环境

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. 安装 PyTorch

请根据 CUDA 版本安装对应的 PyTorch。项目当前推荐 `CUDA 12.8`，更完整的安装说明见 [docs/install.md](./docs/install.md)。

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

### 4. 安装项目依赖

```bash
pip install -r requirements.txt
```

### 5. 下载模型

```bash
python scripts/download_model.py
```

下载完成后，模型默认位于 `./models/k2-fsa/OmniVoice/`。

### 6. 运行本地推理示例

```bash
python scripts/infer.py
```

成功后会在 `./output/out_1.0.wav` 生成 24 kHz 音频。

### 7. 启动 API 服务

本地开发可直接使用默认 API Key，也可以先自定义：

```powershell
$env:TTS_API_KEYS="your-secret-key"
python server.py
```

```bash
export TTS_API_KEYS="your-secret-key"
python server.py
```

启动后可访问：

- 服务首页：`http://localhost:8000/`
- Swagger 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/api/v1/tts/health`

本地默认 API Key：`dev-tts-api-key-change-me`

### 8. 调用接口

获取音色列表：

```bash
curl "http://localhost:8000/api/v1/tts/voices" \
  -H "Authorization: Bearer dev-tts-api-key-change-me"
```

发起非流式合成：

```bash
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" \
  -H "Authorization: Bearer dev-tts-api-key-change-me" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你好，这是我的声音。",
    "voice_id": "Vivian",
    "speed": 1.0
  }'
```

更完整的请求和响应格式见 [docs/TTS API.md](./docs/TTS%20API.md)。

## 预设音色

预设音色配置位于 `app/core/config.py`，仓库内置以下参考音频：

| 音色 | 语言 | 描述 |
| ---- | ---- | ---- |
| Vivian | `zh` | 明亮、略带锋芒的年轻女声 |
| Serena | `zh` | 温暖、柔和的年轻女声 |
| Ryan   | `zh` | 节奏感强、富有动感的男声 |
| Aiden  | `en` | 阳光开朗、音色清晰的美式男声 |
| Sohee  | `zh` | 情感丰富、温暖的女声 |

> 接口层对 `voice_id` 做了大小写兼容处理，例如 `Sohee` 和 `sohee` 都可以被解析。

## 配置说明

常用环境变量如下，完整列表见 `.env.example`：

| 变量 | 默认值 | 说明 |
| ---- | ------ | ---- |
| `TTS_API_KEYS` | `dev-tts-api-key-change-me` | API Key，支持逗号分隔多个值 |
| `TTS_API_HOST` | `0.0.0.0` | 服务监听地址 |
| `TTS_API_PORT` | `8000` | 服务端口 |
| `TTS_DEVICE` | `cuda:0` | 推理设备，如 `cpu`、`cuda:0` |
| `TTS_MODEL_PATH` | `./models/k2-fsa/OmniVoice` | 模型目录 |
| `TTS_RATE_LIMIT_QPS` | `10` | 每个 API Key 每秒请求上限 |
| `TTS_RATE_LIMIT_DAILY` | `100000` | 每个 API Key 每日调用上限 |
| `TTS_WS_MAX_CONNECTIONS` | `5` | 每个 API Key 的 WebSocket 并发连接数 |
| `TTS_PINYIN_WITH_TONE` | `true` | 返回拼音时是否包含音调 |

## Docker 部署

如果你希望直接部署成 GPU 服务，推荐使用 Docker Compose：

```bash
python scripts/download_model.py
cp .env.example .env
docker compose up -d --build
```

Windows PowerShell 可改用：

```powershell
python scripts/download_model.py
Copy-Item .env.example .env
docker compose up -d --build
```

详细说明见 [docs/docker.md](./docs/docker.md)。

## 开发说明

- HTTP 合成接口支持 `wav`、`pcm`、`mp3` 三种输出格式
- `response_mode=binary` 时接口会直接返回音频二进制
- WebSocket 流式接口支持 `synthesize`、`cancel`、`pong` 三类客户端动作
- 服务启动时会预加载模型，模型尚未加载完成时健康检查可能返回 `503`

## 相关链接

- [OmniVoice 官方仓库](https://github.com/k2-fsa/OmniVoice)
- [Hugging Face 模型](https://huggingface.co/k2-fsa/OmniVoice)
- [在线 Demo](https://huggingface.co/spaces/k2-fsa/OmniVoice)
- [OmniVoice 论文](https://huggingface.co/papers/2604.00688)

## 许可证

本仓库代码用于学习、测试和服务封装示例。OmniVoice 模型许可证与使用边界请以其官方仓库和模型页面说明为准。
