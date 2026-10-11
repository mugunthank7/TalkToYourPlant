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
from app.stations import StationService  # noqa: E402

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
    station_id: str | None = None      # the station the user has clicked in the 3D twin


@app.get("/health")
def health():
    g = get_graph()
    return {"status": "ok", "graph": g.stats()["nodes"], "llm": "local", "llm_mode": config.LLM_MODE, "ollama_model": config.pick_model() if config.LLM_MODE == "assist" else None,
            "embedder": config.LOCAL_EMBED_MODEL, "sim_mode": config.get("SIM_MODE", "mock")}


_stations = None


def stations():
    global _stations
    if _stations is None:
        _stations = StationService(brain())
    return _stations


@app.post("/chat")
def chat(body: ChatIn):
    hint = None
    if body.station_id:
        sv = stations()
        f = sv.focus_machine(body.station_id)
        hint = [f] if f else None
    return brain().ask(body.message, session_id=body.session_id, shift=body.shift, focus_hint=hint)


@app.get("/stations")
def station_list():
    sv = stations()
    return {"stations": [{"id": k, "name": v["name"], "machines": sv.machine_ids(k)} for k, v in sv.book.items()]}


@app.get("/station/{sid}")
def station(sid: str):
    return stations().briefing(sid.upper())


@app.post("/station/{sid}/plan")
def station_plan(sid: str):
    return stations().plan_with_llm(sid.upper())


@app.post("/station/{sid}/simulate")
def station_simulate(sid: str, body: dict | None = None):
    sv = stations()
    mid = (body or {}).get("machine_id") or sv.focus_machine(sid.upper())
    if not mid:
        return {"error": f"no machine at {sid}"}
    return brain().sim.inject_fault(mid, (body or {}).get("repair_minutes"))


@app.get("/")
def ui():
    return FileResponse(Path(__file__).resolve().parent.parent / "ui" / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(config.get("BRAIN_PORT", "8100")))
