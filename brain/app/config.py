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
    "agent": get("MODEL_AGENT", "gemini-2.5-flash"),
    "lite": get("MODEL_LITE", "gemini-2.5-flash-lite"),
    "fallback": get("MODEL_FALLBACK", "gemini-2.5-flash-lite"),
    "embed": get("MODEL_EMBED", "gemini-embedding-001"),
}
# conservative client-side budgets per role
RPM = {"agent": get_int("RPM_AGENT", 8), "lite": get_int("RPM_LITE", 12), "embed": get_int("RPM_EMBED", 50)}
RPD = {"agent": get_int("RPD_AGENT", 200), "lite": get_int("RPD_LITE", 800), "embed": get_int("RPD_EMBED", 5000)}
