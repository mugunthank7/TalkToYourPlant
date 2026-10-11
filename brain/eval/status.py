"""Tiny job-status helper shared by the eval runners and the dashboard (JSON file per job)."""
import json, os, time
from pathlib import Path

DIR = Path(__file__).resolve().parent / "status"


class Status:
    def __init__(self, name):
        self.name = name
        DIR.mkdir(exist_ok=True)
        self.path = DIR / f"{name}.json"
        self.logp = DIR / f"{name}.log"
        self.d = {"name": name, "state": "running", "pid": os.getpid(), "started": time.time(),
                  "progress": {"done": 0, "total": 0}, "current": "", "metrics": {}, "items": []}
        self.save()

    def save(self):
        self.d["updated"] = time.time()
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.d))
        os.replace(tmp, self.path)

    def update(self, **kw):
        self.d.update(kw)
        self.save()

    def item(self, **it):
        self.d["items"].append(it)
        self.d["progress"]["done"] = len(self.d["items"])
        self.save()

    def log(self, line):
        with open(self.logp, "a") as f:
            f.write(time.strftime("%H:%M:%S ") + line + "\n")

    def finish(self, state="done", **kw):
        self.d.update(kw, state=state, finished=time.time(), current="")
        self.save()


def read(name):
    try:
        return json.loads((DIR / f"{name}.json").read_text())
    except Exception:
        return None


def tail(name, n=40):
    try:
        return (DIR / f"{name}.log").read_text().splitlines()[-n:]
    except Exception:
        return []
