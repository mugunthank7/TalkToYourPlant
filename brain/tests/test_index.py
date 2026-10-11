#!/usr/bin/env python3
"""Retrieval sanity tests. Run: python3 brain/tests/test_index.py"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.index import DocIndex  # noqa: E402

t0 = time.time()
ix = DocIndex()
print("index ready in %.1fs (embedded now: %d of %d)" % (time.time() - t0, ix.n_embedded_now, len(ix.chunks)))
fails = 0


def top(q, **kw):
    r = ix.search(q, k=kw.pop("k", 5), **kw)
    return r


def check(name, cond, info=""):
    global fails
    print(("PASS " if cond else "FAIL ") + name, info)
    fails += (not cond)


r = top("who do I page for M05 on shift A", machine_id="M05", doc_type="escalation")
check("who-to-page M05 shift A", r and r[0]["source_id"] == "M05-A", [x["source_id"] for x in r[:3]])
r = top("can we keep running 2 more hours with high vibration")
check("run-extension -> SOP-OPS-02", any(x["source_id"] == "SOP-OPS-02" for x in r[:3]), [x["source_id"] for x in r[:3]])
r = top("replace axis 1 joint bearing weld robot vibration rising")
check("bearing wear -> SOP-MNT-M05-01", any(x["source_id"] == "SOP-MNT-M05-01" for x in r[:3]), [x["source_id"] for x in r[:3]])
r = top("lockout tagout energy isolation procedure")
check("LOTO -> SOP-SAF-01", any(x["source_id"] == "SOP-SAF-01" for x in r[:3]), [x["source_id"] for x in r[:3]])
r = top("GP-SHOT-SLOW shot speed slow accumulator pre-charge", machine_id="CAS-GP-01")
check("CAS-GP-01 shot-slow chunks", r and all(x["machine_id"] in ("CAS-GP-01", None) for x in r), [(x["source_type"], x["source_id"]) for x in r[:3]])
r = top("oil leak gearbox seal", machine_id="BIW-WK-03")
check("BIW-WK-03 oil leak history", r and any("LEAK" in x["text"].upper() or "leak" in x["text"] for x in r[:3]), [x["source_id"] for x in r[:3]])
r = top("seal kit part for gear leak", fault_code="KSS-GEAR-LEAK", k=5)
check("fault_code filter", r and all("kss-gear-leak" in x["text"].lower() or (x["metadata"] or {}).get("fault_code") == "KSS-GEAR-LEAK" for x in r), len(r))
r = top("what does SRVO-062 mean", k=5)
check("SRVO-062 meaning", any("SRVO-062" in x["text"] for x in r[:3]), [x["source_id"] for x in r[:3]])
r = top("spare bearing 6208 in stock")
check("bearing_6208 stock chunk", any("6208" in x["text"] for x in r[:3]))
r = top("anything", machine_id="M05", doc_type="manual")
check("machine filter includes family manuals", r and all(x["source_type"] == "manual" for x in r))
t = time.time()
for _ in range(10):
    ix.search("why is the weld robot vibrating", k=6)
print("avg query latency %.0f ms" % ((time.time() - t) * 100))
print("FAILED:", fails)
sys.exit(1 if fails else 0)
