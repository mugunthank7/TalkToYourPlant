"""Integration monitor: watches M's engine and the brain together, in one place.

  python3 brain/app/monitor.py      -> http://localhost:8300

Polls the engine (SIM_URL, default :8000) every 2 s, keeps a rolling history, detects changes
(new alerts, faults, stopped stations, work orders) and, on each, asks the brain (BRAIN_URL,
default :8100) what is wrong, so you can see how the brain reacts to what the plant does.
Buttons inject a fault, clear faults and ask the brain directly. Everything is local.
"""
import json, os, threading, time, urllib.request
from collections import deque
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

BRAIN = Path(__file__).resolve().parent.parent
SIM = os.environ.get("SIM_URL", "http://localhost:8000").rstrip("/")
BRAIN_URL = os.environ.get("BRAIN_URL", "http://localhost:8100").rstrip("/")
POLL_S = 2.0

app = FastAPI(title="Plant integration monitor")
lock = threading.Lock()
samples = deque(maxlen=900)
events = deque(maxlen=300)
asks = deque(maxlen=60)
state = {"engine_up": False, "brain_up": False, "brain_mode": None, "last_error": None, "ev_id": 0}
_prev = {"machines": {}, "stopped": set(), "wo": set(), "engine_up": None}
_last_auto = {}


def http(method, url, body=None, timeout=6):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def add_event(kind, text, machine=None, sim_t=None):
    with lock:
        state["ev_id"] += 1
        ev = {"id": state["ev_id"], "ts": time.time(), "kind": kind, "text": text, "machine": machine, "sim_t": sim_t}
        events.append(ev)
    return ev


def ask_brain(question, machine=None, event_id=None, session="monitor"):
    t = time.time()
    try:
        r = http("POST", BRAIN_URL + "/chat", {"message": question, "session_id": session}, timeout=400)
        rec = {"ts": time.time(), "question": question, "event_id": event_id, "machine": machine,
               "answer": r["answer"], "latency_s": round(time.time() - t, 2),
               "model": r["meta"].get("model"), "tools": r["meta"].get("tools"), "sim_mode": r["meta"].get("sim_mode"),
               "degraded": r["meta"].get("degraded"), "highlight": r["highlight"]["machine_ids"],
               "citations": [c["id"] for c in r["citations"]], "actions": [a["type"] for a in r.get("actions", [])]}
    except Exception as e:  # noqa: BLE001
        rec = {"ts": time.time(), "question": question, "event_id": event_id, "machine": machine,
               "answer": f"brain unreachable: {type(e).__name__}: {str(e)[:120]}", "latency_s": round(time.time() - t, 2),
               "degraded": True, "highlight": [], "citations": [], "tools": [], "actions": []}
    with lock:
        asks.append(rec)
    return rec


def _auto_ask(machine, why, event_id):
    now = time.time()
    if now - _last_auto.get(machine, 0) < 45:
        return
    _last_auto[machine] = now
    threading.Thread(target=ask_brain, args=(f"What is wrong with {machine} and what should we do?", machine, event_id, "auto-" + machine),
                     daemon=True).start()


def poll_once():
    try:
        s = http("GET", SIM + "/state", timeout=5)
    except Exception as e:  # noqa: BLE001
        if _prev["engine_up"] is not False:
            add_event("engine", f"engine unreachable ({type(e).__name__})")
        _prev["engine_up"] = False
        state.update(engine_up=False, last_error=f"{type(e).__name__}: {str(e)[:100]}")
        return
    if _prev["engine_up"] is False:
        add_event("engine", "engine reachable again")
    _prev["engine_up"] = True
    state.update(engine_up=True, last_error=None)
    k = s.get("kpis", {})
    machines = s.get("machines", {})
    hero = machines.get("M05", {})
    sample = {"ts": time.time(), "sim_t": s.get("t"), "oee": k.get("oee"), "units": k.get("units"),
              "throughput": k.get("throughput_per_hour"), "downtime_min": k.get("downtime_min"),
              "cost": k.get("downtime_cost_usd"), "availability": k.get("availability"), "quality": k.get("quality"),
              "m05_vib": hero.get("vib_multiple"), "m05_rul_min": (round(hero["rul_s"] / 60, 1) if hero.get("rul_s") is not None else None),
              "m05_score": (hero.get("anomaly") or {}).get("score"), "m05_alert": hero.get("alert"),
              "n_alert": sum(1 for m in machines.values() if m.get("alert")),
              "stopped": [sid for sid, v in s.get("stations", {}).items() if v.get("state") in ("fault", "repair")],
              "open_wo": sum(1 for w in s.get("work_orders", []) if w.get("status") != "closed")}
    with lock:
        samples.append(sample)
    # change detection
    for mid, m in machines.items():
        old = _prev["machines"].get(mid, {})
        if m.get("alert") != old.get("alert") and m.get("alert"):
            ev = add_event("alert", f"{mid} anomaly alert: {m['alert']}" + (f" (vibration {m['vib_multiple']}x)" if m.get("vib_multiple") else ""), mid, s.get("t"))
            _auto_ask(mid, "alert", ev["id"])
        if m.get("state") != old.get("state") and old.get("state") is not None:
            ev = add_event("machine", f"{mid} state {old.get('state')} -> {m.get('state')}", mid, s.get("t"))
            if m.get("state") in ("fault", "repair", "down", "failed"):
                _auto_ask(mid, "fault", ev["id"])
        _prev["machines"][mid] = {"alert": m.get("alert"), "state": m.get("state")}
    stopped = set(sample["stopped"])
    for sid in stopped - _prev["stopped"]:
        add_event("station", f"station {sid} stopped", None, s.get("t"))
    for sid in _prev["stopped"] - stopped:
        add_event("station", f"station {sid} running again", None, s.get("t"))
    _prev["stopped"] = stopped
    wo_ids = {w.get("id") for w in s.get("work_orders", [])}
    for w in s.get("work_orders", []):
        if w.get("id") not in _prev["wo"] and _prev["wo"] is not None:
            add_event("work_order", f"work order {w.get('id')} on {w.get('machine')} ({w.get('status')})", w.get("machine"), s.get("t"))
    _prev["wo"] = wo_ids if _prev["wo"] is not None else wo_ids


def poll_loop():
    first = True
    while True:
        try:
            if first:
                _prev["wo"] = set()
            poll_once()
            first = False
            try:
                h = http("GET", BRAIN_URL + "/health", timeout=3)
                state.update(brain_up=True, brain_mode=h.get("sim_mode"))
            except Exception:  # noqa: BLE001
                state.update(brain_up=False)
        except Exception as e:  # noqa: BLE001
            state["last_error"] = f"monitor: {e}"
        time.sleep(POLL_S)


@app.on_event("startup")
def _start():
    threading.Thread(target=poll_loop, daemon=True).start()


@app.get("/api/monitor")
def monitor(n: int = 300):
    with lock:
        return {"now": time.time(), "engine": {"up": state["engine_up"], "url": SIM, "error": state["last_error"]},
                "brain": {"up": state["brain_up"], "url": BRAIN_URL, "sim_mode": state["brain_mode"]},
                "samples": list(samples)[-n:], "events": list(events)[-80:], "asks": list(asks)[-12:]}


@app.post("/api/inject")
def inject(body: dict):
    try:
        r = http("POST", SIM + "/fault", {"machine": body["machine"], "repair_minutes": body.get("repair_minutes")})
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"engine: {e}")
    add_event("inject", f"fault injected on {body['machine']} (repair {body.get('repair_minutes') or 'default'} min)", body["machine"])
    return r


@app.post("/api/control")
def control(body: dict):
    try:
        r = http("POST", SIM + "/control", body)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"engine: {e}")
    add_event("control", f"engine control: {json.dumps(body)[:80]}")
    return r


@app.post("/api/ask")
def ask(body: dict):
    return ask_brain(body["question"], body.get("machine"), None, "manual")


@app.get("/")
def page():
    return FileResponse(BRAIN / "ui" / "monitor.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("MONITOR_PORT", "8300")))
