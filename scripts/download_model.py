from pathlib import Path
from modelscope import snapshot_download

# 当前文件所在目录
CURRENT_DIR = Path(__file__).resolve().parent

# ../models
MODELS_DIR = CURRENT_DIR.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """下载 OmniVoice 模型权重到本地 models 目录。"""
    model_dir = snapshot_download(
        "k2-fsa/OmniVoice",
        cache_dir=str(MODELS_DIR)
    )
    print(f"Model downloaded to: {model_dir}")

if __name__ == "__main__":
    main()
