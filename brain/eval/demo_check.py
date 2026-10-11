#!/usr/bin/env python3
"""Run the demo question set against the live brain and report confidence.

  python3 brain/eval/demo_check.py            # needs the stack: brain/scripts/start_all.sh
  python3 brain/eval/demo_check.py --reset    # first rewinds the engine to t=12500 and clears faults
Exit code 1 if any question is below high confidence, degraded, or misses its expected text.
"""
import argparse, json, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAIN, ENGINE = "http://localhost:8100", "http://localhost:8000"


def post(url, body, timeout=180):
    r = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r, timeout=timeout).read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    ap.add_argument("--write", help="write results json to this path")
    a = ap.parse_args()
    if a.reset:
        post(ENGINE + "/control", {"action": "clear_faults"})
        post(ENGINE + "/control", {"action": "seek", "t": 12500})
        post(ENGINE + "/control", {"action": "pause"})
    spec = json.load(open(HERE / "demo_questions.json"))
    bad, rows = 0, []
    for g in spec["groups"]:
        print(f"\n{g['name']}")
        for q in g["questions"]:
            d = post(BRAIN + "/chat", {"message": q["q"], "session_id": g["session"]})
            c = d["confidence"]
            miss = [e for e in q["expect"] if e.lower() not in d["answer"].lower()]
            ok = c["level"] == "high" and not d["meta"]["degraded"] and not miss
            bad += (not ok)
            print(f"  {'OK  ' if ok else 'FAIL'} [{c['level']:6s} {c['score']:.2f}] {d['meta']['latency_s']:5.1f}s  {q['q']}"
                  + (f"   missing {miss}" if miss else ""))
            rows.append({"group": g["name"], "q": q["q"], "why": q["why"], "ok": ok, "confidence": c, "answer": d["answer"],
                         "latency_s": d["meta"]["latency_s"], "highlight": d["highlight"]["machine_ids"]})
    print(f"\n{len(rows) - bad}/{len(rows)} high confidence and as expected")
    if a.write:
        Path(a.write).write_text(json.dumps(rows, indent=1))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
