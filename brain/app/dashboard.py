"""Run dashboard: status of eval, RAGAS and embedding experiments, with start/stop.

  python3 brain/app/dashboard.py        -> http://localhost:8200
One heavy job at a time (8 GB machine). Everything local; no network calls.
"""
import json, os, signal, subprocess, sys, time, urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

BRAIN = Path(__file__).resolve().parent.parent
EVAL = BRAIN / "eval"
STATUS = EVAL / "status"
PY = sys.executable
JOBS = {
    "eval": [PY, "-u", str(EVAL / "run_eval.py")],
    "embeddings": [PY, "-u", str(EVAL / "embed_experiment.py")],
    "ragas": [PY, "-u", str(EVAL / "run_ragas.py"), "--every", "1", "--ctx-chars", "1400"],
}
STATUS.mkdir(exist_ok=True)
app = FastAPI(title="Plant brain: run dashboard")


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _read(name):
    try:
        d = json.loads((STATUS / f"{name}.json").read_text())
    except Exception:
        return None
    if d.get("state") == "running" and not _alive(d.get("pid", -1)):
        d["state"] = "stopped"          # process died without finishing
    return d


def _tail(name, n=30):
    try:
        return (STATUS / f"{name}.log").read_text().splitlines()[-n:]
    except Exception:
        return []


def _json(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def _ollama(path):
    try:
        with urllib.request.urlopen("http://localhost:11434" + path, timeout=2) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


@app.get("/api/status")
def status():
    jobs = {}
    for n in JOBS:
        d = _read(n)
        if d:
            d["log"] = _tail(n)
            if d.get("state") in ("running",) and d.get("started"):
                d["elapsed_s"] = round(time.time() - d["started"])
                done, tot = d["progress"]["done"], d["progress"]["total"]
                if done and tot:
                    d["eta_s"] = round(d["elapsed_s"] / done * (tot - done))
        jobs[n] = d
    ps = _ollama("/api/ps")
    tags = _ollama("/api/tags")
    return {"now": time.time(), "jobs": jobs,
            "embedding_experiment": _json(EVAL / "embed_experiment.json"),
            "eval_results": _json(EVAL / "results_latest.json"),
            "ragas_results": _json(EVAL / "ragas_latest.json"),
            "ollama": {"up": tags is not None, "loaded": [m["name"] for m in (ps or {}).get("models", [])],
                       "models": [m["name"] for m in (tags or {}).get("models", [])]}}


def _running():
    return [n for n in JOBS if (_read(n) or {}).get("state") == "running"]


@app.post("/api/start/{job}")
def start(job: str):
    if job not in JOBS:
        raise HTTPException(404, "unknown job")
    if _running():
        raise HTTPException(409, f"already running: {_running()}")
    for ext in (".json", ".log"):
        (STATUS / f"{job}{ext}").unlink(missing_ok=True)
    out = open(STATUS / f"{job}.out", "w")
    subprocess.Popen(JOBS[job], cwd=str(BRAIN.parent), stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    return {"started": job}


@app.post("/api/stop/{job}")
def stop(job: str):
    d = _read(job)
    if not d or d.get("state") != "running":
        raise HTTPException(409, "not running")
    try:
        os.killpg(os.getpgid(d["pid"]), signal.SIGTERM)
    except Exception:
        os.kill(d["pid"], signal.SIGTERM)
    d["state"] = "stopped"
    (STATUS / f"{job}.json").write_text(json.dumps(d))
    return {"stopped": job}


@app.get("/")
def page():
    return FileResponse(BRAIN / "ui" / "dashboard.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("DASH_PORT", "8200")))
