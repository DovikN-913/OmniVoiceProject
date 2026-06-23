# OmniVoiceProject

**[English](./README.en.md)** | 简体中文

基于 [OmniVoice](https://github.com/k2-fsa/OmniVoice) 的多语言零样本文本转语音（TTS）推理项目，支持声音克隆，内置多种预设音色参考音频。

OmniVoice 是一款支持 **600+ 语言** 的超大规模零样本 TTS 模型，基于扩散语言模型架构，具备高质量语音合成、快速推理和声音克隆能力。

## 功能特性

- **零样本声音克隆**：仅需一段参考音频及对应文本，即可合成目标音色
- **多语言支持**：支持中文及 600 多种语言的文本转语音
- **预设音色**：内置 Vivian、Serena、Ryan、Aiden、Sohee 等参考音色
- **语速调节**：通过 `speed` 参数控制合成语速
- **企业级 API**：HTTP / WebSocket 流式合成，详见 [API 文档](./docs/TTS%20API.md)
- **Docker 部署**：支持 GPU 容器化一键启动，详见 [部署文档](./docs/docker.md)
- **本地推理**：模型下载至本地，支持 GPU 离线推理

## 项目结构

```
OmniVoiceProject/
├── app/                        # TTS API 应用
│   ├── main.py                 # FastAPI 入口
│   ├── api/                    # 路由与依赖注入
│   │   ├── routes.py
│   │   └── dependencies.py
│   ├── core/                   # 配置与错误码
│   │   ├── config.py
│   │   └── errors.py
│   ├── models/                 # Pydantic 请求/响应模型
│   │   └── schemas.py
│   ├── services/               # TTS 引擎、音频编码、限流等
│   └── utils/
├── scripts/                    # 命令行脚本
│   ├── infer.py                # 本地单次推理
│   └── download_model.py       # 模型下载
├── docs/                       # 文档
│   ├── TTS API.md              # API 接口规范
│   ├── docker.md               # Docker 部署指南
│   └── install.md              # PyTorch 安装说明
├── requirements/               # 依赖分组
│   ├── base.txt                # 推理依赖
│   └── api.txt                 # API 服务依赖
├── asset/                      # 参考音频
├── models/                     # 模型权重（gitignore）
├── output/                     # 生成音频（gitignore）
├── server.py                   # 启动 API 服务
├── requirements.txt            # 完整依赖入口
├── .env.example
└── README.md
```

## 环境要求

- Python 3.10+
- NVIDIA GPU（推荐，需 CUDA 支持）
- 磁盘空间：模型约 3GB+

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/DovikN-913/OmniVoiceProject.git
cd OmniVoiceProject
```

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate
```

### 3. 安装 PyTorch

根据你的 CUDA 版本安装 PyTorch，详见 [docs/install.md](./docs/install.md)。本项目推荐 CUDA 12.8：

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

### 4. 安装项目依赖

```bash
# 仅推理
pip install -r requirements/base.txt

# 推理 + API 服务（完整）
pip install -r requirements.txt
```

## 下载模型

```bash
python scripts/download_model.py
```

下载完成后，模型保存至 `./models/k2-fsa/OmniVoice/`。

## 快速开始

### 本地推理

```bash
python scripts/infer.py
```

输出文件：`./output/out_1.0.wav`（24 kHz）

### 启动 API 服务

```bash
# 可选：配置 API Key
$env:TTS_API_KEYS="your-secret-key"

python server.py
```

- 服务地址：`http://localhost:8000`
- 交互文档：`http://localhost:8000/docs`
- 健康检查：`GET /api/v1/tts/health`

默认 API Key：`dev-tts-api-key-change-me`（仅用于本地开发）

### API 调用示例

```bash
# 音色列表
curl "http://localhost:8000/api/v1/tts/voices" ^
  -H "Authorization: Bearer dev-tts-api-key-change-me"

# 非流式合成
curl -X POST "http://localhost:8000/api/v1/tts/synthesize" ^
  -H "Authorization: Bearer dev-tts-api-key-change-me" ^
  -H "Content-Type: application/json" ^
  -d "{\"text\":\"你好，这是我的声音。\",\"voice_id\":\"Vivian\",\"speed\":1.0}"
```

完整接口说明见 [docs/TTS API.md](./docs/TTS%20API.md)。

### Docker 部署

```bash
python scripts/download_model.py   # 宿主机下载模型
cp .env.example .env               # 配置 API Key
docker compose up -d --build
```

详见 [docs/docker.md](./docs/docker.md)。

## 预设音色

音色配置位于 `app/core/config.py`：

| 音色   | 描述                     |
| ------ | ------------------------ |
| Vivian | 明亮、略带锋芒的年轻女声 |
| Serena | 温暖、柔和的年轻女声     |
| Ryan   | 节奏感强、富有动感的男声   |
| Aiden  | 阳光开朗的美式男声       |
| Sohee  | 情感丰富、温暖的女声     |

## 配置说明

主要配置项在 `app/core/config.py`，支持通过环境变量覆盖：

| 变量 | 说明 | 默认值 |
| ---- | ---- | ------ |
| `TTS_API_KEYS` | API 密钥（逗号分隔） | `dev-tts-api-key-change-me` |
| `TTS_DEVICE` | 推理设备 | `cuda:0` |
| `TTS_MODEL_PATH` | 模型路径 | `./models/k2-fsa/OmniVoice` |
| `TTS_API_PORT` | 服务端口 | `8000` |

参考 `.env.example` 获取完整列表。

## 相关链接

- **OmniVoice 官方仓库**：[k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice)
- **Hugging Face 模型**：[k2-fsa/OmniVoice](https://huggingface.co/k2-fsa/OmniVoice)
- **在线 Demo**：[Hugging Face Space](https://huggingface.co/spaces/k2-fsa/OmniVoice)
- **论文**：[OmniVoice: Towards Omnilingual Zero-Shot Text-to-Speech with Diffusion Language Models](https://huggingface.co/papers/2604.00688)

## 许可证

本项目代码仅供学习与推理使用。OmniVoice 模型遵循 [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) 许可证，详见 [官方仓库](https://github.com/k2-fsa/OmniVoice)。
