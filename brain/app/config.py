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


API_KEY = get("GEMINI_API_KEY")
MODELS = {
    "agent": get("MODEL_AGENT", "gemini-3.5-flash-lite"),
    "lite": get("MODEL_LITE", "gemini-3.1-flash-lite"),
    "fallback": get("MODEL_FALLBACK", "gemini-3.1-flash-lite"),
    "premium": get("MODEL_PREMIUM", "gemini-3.8-flash"),
    "embed": get("MODEL_EMBED", "gemini-embedding-001"),
}
# Client-side budgets, set just under the real free-tier limits seen on the AI Studio
# usage page (2026-10-11): 3.5-flash-lite 15 RPM / 500 RPD, 3.1-flash-lite 15 / 500,
# 3.8-flash 5 / 20, embeddings 100 RPM / 30K TPM / 1K RPD. Quotas are per model.
RPM = {"agent": get_int("RPM_AGENT", 12), "lite": get_int("RPM_LITE", 12),
       "premium": get_int("RPM_PREMIUM", 4), "embed": get_int("RPM_EMBED", 80)}
RPD = {"agent": get_int("RPD_AGENT", 450), "lite": get_int("RPD_LITE", 450),
       "premium": get_int("RPD_PREMIUM", 16), "embed": get_int("RPD_EMBED", 900)}
TPM = {"agent": get_int("TPM_AGENT", 200000), "lite": get_int("TPM_LITE", 200000),
       "premium": get_int("TPM_PREMIUM", 200000), "embed": get_int("TPM_EMBED", 25000)}
EMBED_BACKEND = get("EMBED_BACKEND", "local")  # local | gemini
LOCAL_EMBED_MODEL = get("LOCAL_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
