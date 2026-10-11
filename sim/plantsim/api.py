"""FastAPI app: REST endpoints, a WebSocket stream for the twin, and the tool endpoints for the LLM side.

Run:  cd sim && .venv/bin/uvicorn plantsim.api:app --port 8000
"""
from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any

from fastapi import Body, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import config as C
from .config import Params
from .model import PlantSim, REPAIR_MIN
from .scenarios import what_if
from .snapshot import kpi_live, machine_info, snapshot, stations_info
from .tools import TOOLS, anomaly_report, call_tool


class Live:
    """The running plant. Deterministic: seeking just rebuilds the model and runs it to the requested time."""

    def __init__(self) -> None:
        self.params = Params(detector="all")
        self.speed = 60.0
        self.playing = False
        self.clients: set[WebSocket] = set()
        self.sim = PlantSim(self.params.copy())
        self.sent = 0

    def rebuild(self, t: float = 0.0) -> None:
        self.sim = PlantSim(self.params.copy())
        self.sim.run_until(t)
        self.sent = len(self.sim.events)

    def seek(self, t: float) -> None:
        self.rebuild(max(0.0, min(t, self.params.horizon_s)))

    def advance(self, dt: float) -> None:
        if self.playing and self.sim.now < self.params.horizon_s:
            self.sim.run_until(min(self.params.horizon_s, self.sim.now + dt * self.speed))

    def inject(self, machine: str, repair_minutes: float | None = None) -> dict:
        if machine not in self.sim.machines:
            raise HTTPException(404, f"unknown machine {machine}")
        f = {"machine": machine, "t0": round(self.sim.now, 1)}
        if repair_minutes:
            f["repair_s"] = float(repair_minutes) * 60
        self.params.injected.append(f)
        self.sim.env.process(self.sim._injected(dict(f)))
        self.sim.run_until(self.sim.now + 0.001)
        return {"injected": f, "default_repair_min": REPAIR_MIN.get(self.sim.machines[machine].type, 30)}

    def create_work_order(self, machine: str, reason: str) -> dict:
        wo = self.sim._open_wo(machine, "breakdown", self.sim.now + self.params.dispatch_delay_s, REPAIR_MIN.get(self.sim.machines[machine].type, 30) * 60.0)
        return {**wo.as_dict(), "reason": reason}

    def control(self, body: dict) -> dict:
        a = body.get("action")
        if "speed" in body:
            self.speed = float(body["speed"])
        if a == "play":
            self.playing = True
        elif a == "pause":
            self.playing = False
        elif a == "seek":
            self.seek(float(body["t"]))
        elif a == "reset":
            if "seed" in body:
                self.params.seed = int(body["seed"])
            if "shift" in body:
                self.params.shift = str(body["shift"])
            self.params.injected.clear()
            self.rebuild(0.0)
        elif a == "clear_faults":
            now = self.sim.now
            self.params.injected.clear()
            self.rebuild(now)
        elif a == "policy":
            self.params.hero_policy = body.get("hero_policy", "timely")
            self.params.hero_delay_s = float(body.get("hero_delay_s", 0))
            self.rebuild(self.sim.now)
        return {"playing": self.playing, "speed": self.speed, "t": round(self.sim.now, 1), "params": {"seed": self.params.seed, "shift": self.params.shift, "hero_policy": self.params.hero_policy}}

    async def broadcast(self, msg: dict) -> None:
        dead = []
        for ws in list(self.clients):
            try:
                await ws.send_text(json.dumps(msg))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)


live = Live()


async def _loop() -> None:
    dt = 0.1
    while True:
        await asyncio.sleep(dt)
        live.advance(dt)
        if live.clients:
            snap = snapshot(live.sim)
            await live.broadcast({"type": "state", **snap})
            new = live.sim.events[live.sent:]
            live.sent = len(live.sim.events)
            for e in new:
                await live.broadcast(e)


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_loop())
    yield
    task.cancel()


app = FastAPI(title="Voltline plant simulation", version="0.1", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health() -> dict:
    return {"ok": True, "t": round(live.sim.now, 1), "playing": live.playing, "speed": live.speed}


@app.get("/state")
def state() -> dict:
    return snapshot(live.sim)


@app.get("/station/{sid}")
def station(sid: str) -> dict:
    r = call_tool(live, "get_station", {"station_id": sid})
    if "error" in r:
        raise HTTPException(404, r["error"])
    return r


@app.get("/machine/{mid}")
def machine(mid: str) -> dict:
    if mid not in live.sim.machines:
        raise HTTPException(404, f"unknown machine {mid}")
    return machine_info(live.sim, mid)


@app.get("/anomaly")
def anomaly() -> dict:
    return anomaly_report(live.sim)


@app.get("/anomaly/{mid}")
def anomaly_machine(mid: str) -> dict:
    r = anomaly_report(live.sim, mid)
    if "error" in r:
        raise HTTPException(404, r["error"])
    return r


@app.get("/kpis")
def kpis() -> dict:
    return call_tool(live, "get_kpis", {})


@app.get("/events")
def events(since: float = 0.0) -> list[dict]:
    return [e for e in live.sim.events if e["t"] >= since]


@app.get("/workorders")
def workorders() -> list[dict]:
    return [w.as_dict() for w in live.sim.work_orders]


@app.get("/series")
def series() -> list[dict]:
    """Per-minute KPI frame so far (for the dashboard)."""
    return live.sim.minute_frame().to_dict(orient="records")


@app.post("/control")
def control(body: dict[str, Any] = Body(...)) -> dict:
    return live.control(body)


@app.post("/fault")
def fault(body: dict[str, Any] = Body(...)) -> dict:
    return live.inject(body["machine"], body.get("repair_minutes"))


@app.post("/scenario")
def scenario(body: dict[str, Any] = Body(...)) -> dict:
    return what_if(live.params, body.get("changes", []), live.sim.now)


@app.get("/tools")
def tools() -> list[dict]:
    return TOOLS


@app.post("/tools/{name}")
def run_tool(name: str, body: dict[str, Any] = Body(default_factory=dict)) -> dict:
    return call_tool(live, name, body)


@app.websocket("/ws")
async def ws(sock: WebSocket) -> None:
    await sock.accept()
    live.clients.add(sock)
    await sock.send_text(json.dumps({"type": "hello", "t": live.sim.now, "stations": [s["id"] for s in live.sim.layout["stations"]],
                                     "tools": [t["name"] for t in TOOLS]}))
    try:
        while True:
            msg = json.loads(await sock.receive_text())
            if msg.get("type") == "control":
                await sock.send_text(json.dumps({"type": "control_ack", **live.control(msg)}))
            elif msg.get("type") == "ui_event" and msg.get("event") == "inject_fault":
                await sock.send_text(json.dumps({"type": "fault_ack", **live.inject(msg["machine_id"], msg.get("repair_minutes"))}))
    except WebSocketDisconnect:
        pass
    finally:
        live.clients.discard(sock)
