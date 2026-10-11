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
OLLAMA_MODEL = get("OLLAMA_MODEL", "auto")        # "auto" picks the best installed model from MODEL_PREFERENCE
OLLAMA_NUM_CTX = get_int("OLLAMA_NUM_CTX", 6144)
LOCAL_EMBED_MODEL = get("LOCAL_EMBED_MODEL", "BAAI/bge-small-en-v1.5")
JUDGE_MODEL = get("JUDGE_MODEL", "phi3:3.8b")          # RAGAS judge (Ollama)

# LLM layer. off = deterministic answers only (works on any laptop). assist = a local model phrases the answer from the
# deterministic facts, behind a grounding guard (needs a machine that can run the model; see brain/docs/LLM.md).
LLM_MODE = get("LLM_MODE", "off")
LLM_TIMEOUT = get_int("LLM_TIMEOUT", 60)
MODEL_PREFERENCE = ["qwen2.5:32b-instruct", "qwen2.5:32b", "qwen3:32b", "qwen2.5:14b-instruct", "qwen2.5:14b", "qwen3:14b",
                    "llama3.1:70b", "llama3.1:8b-instruct", "llama3.1:8b", "gemma2:9b", "qwen2.5:7b-instruct", "qwen2.5:7b",
                    "phi3:medium", "phi3:3.8b"]
_picked = {}


def pick_model():
    """Resolve OLLAMA_MODEL. 'auto' = first MODEL_PREFERENCE entry that Ollama has installed."""
    if OLLAMA_MODEL not in ("", "auto"):
        return OLLAMA_MODEL
    if "m" in _picked:
        return _picked["m"]
    import json as _j, urllib.request as _u
    try:
        with _u.urlopen(OLLAMA_URL.rstrip("/") + "/api/tags", timeout=3) as r:
            have = {m["name"] for m in _j.loads(r.read().decode()).get("models", [])}
    except Exception:  # noqa: BLE001
        return "qwen2.5:7b"
    names = have | {n.split(":latest")[0] for n in have}
    for m in MODEL_PREFERENCE:
        if m in names:
            _picked["m"] = m
            return m
    _picked["m"] = sorted(have)[0] if have else "qwen2.5:7b"
    return _picked["m"]
