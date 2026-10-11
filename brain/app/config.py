"""Config: reads brain/.env then process env. No third-party deps."""
import os
from pathlib import Path

BRAIN_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BRAIN_DIR / ".cache"


def _load_dotenv(path=BRAIN_DIR / ".env"):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()


def get(name, default=""):
    return os.environ.get(name, default)


def get_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


# Local-only: Ollama for open-ended questions, sentence-transformers for embeddings. No hosted APIs.
OLLAMA_URL = get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = get("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_NUM_CTX = get_int("OLLAMA_NUM_CTX", 6144)
LOCAL_EMBED_MODEL = get("LOCAL_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
JUDGE_MODEL = get("JUDGE_MODEL", "phi3:3.8b")          # RAGAS judge (Ollama)
