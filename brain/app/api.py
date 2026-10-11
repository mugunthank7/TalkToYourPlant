"""FastAPI service: POST /chat, GET /health, static chat UI at /.

Run: uvicorn brain.app.api:app --port 8100  (from repo root)  or  python3 -m brain.app.api
"""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import config  # noqa: E402
from app.agent import Brain  # noqa: E402
from app.graph import get_graph  # noqa: E402

app = FastAPI(title="Talk to Your Plant: brain")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
_brain = None


def brain():
    global _brain
    if _brain is None:
        _brain = Brain()
    return _brain


class ChatIn(BaseModel):
    message: str
    session_id: str = "default"
    shift: str | None = None


@app.get("/health")
def health():
    g = get_graph()
    return {"status": "ok", "graph": g.stats()["nodes"], "llm": "local", "ollama_model": config.OLLAMA_MODEL,
            "embedder": config.LOCAL_EMBED_MODEL, "sim_mode": config.get("SIM_MODE", "mock")}


@app.post("/chat")
def chat(body: ChatIn):
    return brain().ask(body.message, session_id=body.session_id, shift=body.shift)


@app.get("/")
def ui():
    return FileResponse(Path(__file__).resolve().parent.parent / "ui" / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(config.get("BRAIN_PORT", "8100")))
