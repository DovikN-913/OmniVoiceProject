"""从 ModelScope 下载 OmniVoice 模型权重。"""

import sys
from pathlib import Path
from modelscope import snapshot_download
from app.core.config import MODELS_DIR

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def main() -> None:
    model_dir = snapshot_download("k2-fsa/OmniVoice", cache_dir=str(MODELS_DIR))
    print(f"Model downloaded to: {model_dir}")


if __name__ == "__main__":
    main()
