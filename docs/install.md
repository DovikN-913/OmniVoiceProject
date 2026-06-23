# 安装指南

本文档用于帮助你在本地开发环境中正确安装 `OmniVoiceProject`，并完成模型下载与基础验证。

## 适用环境

项目默认面向 GPU 推理场景，推荐以下环境组合：

| 项目 | 建议 |
| ---- | ---- |
| Python | `3.10+` |
| 操作系统 | Windows 10/11、Ubuntu 22.04+ |
| GPU | NVIDIA GPU，建议显存 `8 GB+` |
| CUDA | 推荐 `12.8` |
| 磁盘空间 | 模型约 `3 GB+`，建议预留更多缓存空间 |

> Windows 用户如果通过 Docker 部署，建议优先使用 WSL2 环境；如果直接在 Windows Python 环境中运行，请先确认 CUDA 与 PyTorch 匹配。

## 1. 克隆项目

```bash
git clone https://github.com/DovikN-913/OmniVoiceProject.git
cd OmniVoiceProject
```

## 2. 创建虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux / macOS：

```bash
python -m venv .venv
source .venv/bin/activate
```

## 3. 安装 PyTorch

请优先根据你的 CUDA 版本安装对应的 PyTorch。项目当前在 `CUDA 12.8 + torch 2.7.1` 组合下提供默认说明。

### 3.1 推荐安装命令

CUDA 12.8：

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu128
```

CPU 仅验证环境可用性时可使用：

```bash
pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1
```

> 说明：CPU 方案仅适合基本安装验证，不适合作为正式推理配置。

### 3.2 验证 PyTorch

```bash
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

如果输出中 `torch.cuda.is_available()` 为 `True`，说明 GPU 运行时已准备就绪。

## 4. 安装项目依赖

```bash
pip install -r requirements.txt
```

依赖中包含：

- `omnivoice`：模型推理核心
- `fastapi` / `uvicorn`：API 服务
- `modelscope`：模型下载
- `pydub`：`mp3` 输出支持
- `pypinyin`：拼音结果生成

## 5. 安装可选系统依赖

如果你需要输出 `mp3`，请确保系统已安装 `ffmpeg`。

Windows：

- 推荐通过 `winget`、`scoop` 或手动安装 `ffmpeg`
- 安装后确认 `ffmpeg` 已加入 `PATH`

Linux：

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

## 6. 下载 OmniVoice 模型

```bash
python scripts/download_model.py
```

下载完成后，模型默认保存在：

```text
./models/k2-fsa/OmniVoice/
```

如果需要自定义模型路径，可通过环境变量覆盖：

```powershell
$env:TTS_MODEL_PATH="D:\models\OmniVoice"
```

```bash
export TTS_MODEL_PATH="/data/models/OmniVoice"
```

## 7. 运行安装验证

### 7.1 本地推理验证

```bash
python scripts/infer.py
```

成功后将在 `./output/out_1.0.wav` 生成示例音频。

### 7.2 API 服务验证

```bash
python server.py
```

然后访问：

- `http://localhost:8000/`
- `http://localhost:8000/docs`
- `http://localhost:8000/api/v1/tts/health`

本地开发默认 API Key 为：

```text
dev-tts-api-key-change-me
```

## 8. 常见安装问题

### `No module named 'omnivoice'`

通常是依赖没有安装完整，或当前终端未激活正确的虚拟环境。

处理方式：

```bash
pip install -r requirements.txt
```

### `torch.cuda.is_available()` 返回 `False`

通常表示以下问题之一：

- 当前机器没有可用 NVIDIA GPU
- CUDA 驱动与 PyTorch 版本不匹配
- 安装了 CPU 版 PyTorch
- Windows 环境变量或驱动未正确配置

建议优先检查：

```bash
nvidia-smi
python -c "import torch; print(torch.version.cuda)"
```

### 合成 `mp3` 时报错

`mp3` 输出依赖 `ffmpeg`。如果 `wav` 正常但 `mp3` 失败，请先确认：

```bash
ffmpeg -version
```

### 模型下载很慢或失败

模型下载依赖 `modelscope` 网络访问。若下载失败，可重试以下命令：

```bash
python scripts/download_model.py
```

如果你已经有模型目录，也可以直接设置 `TTS_MODEL_PATH` 指向本地已下载路径。

## 9. 下一步

安装完成后，建议继续阅读：

- [项目首页](../README.md)
- [TTS API 文档](./TTS%20API.md)
- [Docker 部署指南](./docker.md)
