"""Station knowledge for the chatbot and the click-a-station panel.

Builds brain/data/out/stations.json and appends 'station' chunks to rag/rag_chunks.jsonl from:
  docs/STATIONS.md                    what each station does, machines, people
  data/out/layout.json                stations, machines (type, station), item flow
  data/out/history/failure_modes.csv  M's failure catalogue per machine type (the error simulations)
Read-only on M's files. Called from build_keyed.py; also runnable alone.
"""
import csv, json, re
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def _parse_stations_md():
    rows = {}
    for line in (ROOT / "docs/STATIONS.md").read_text().splitlines():
        m = re.match(r"\|\s*(S\d\d)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]*)\|\s*(P\d)", line)
        if m:
            rows[m.group(1)] = {"name": m.group(2).strip(), "what_happens": m.group(3).strip(), "priority": m.group(5)}
    return rows


def build(out_dir=None):
    out = Path(out_dir) if out_dir else HERE / "out"
    md = _parse_stations_md()
    layout = json.load(open(ROOT / "data/out/layout.json"))
    fm = defaultdict(list)
    p = ROOT / "data/out/history/failure_modes.csv"
    if p.exists():
        for r in csv.DictReader(open(p)):
            fm[r["machine_type"]].append({
                "mode": r["failure_mode"], "component": r["component"], "symptom": r["symptom"], "cause": r["cause"],
                "repair": r["repair_procedure"], "spare_part": r["spare_part"], "supplier": r.get("supplier"),
                "repair_min": float(r["typical_repair_min"]) if r.get("typical_repair_min") else None,
                "part_cost_usd": float(r["part_cost_usd"]) if r.get("part_cost_usd") else None})
    machines = {m["id"]: m for m in layout["machines"]}
    up, down = defaultdict(list), defaultdict(list)
    for e in layout.get("item_flow", []):
        down[e["from"]].append(e["to"])
        up[e["to"]].append(e["from"])
    people = {"S04": "line operator", "S05": "line operator", "S06": "line operator", "S07": "quality inspector",
              "S10": "maintenance technician (on call)", "S11": "line supervisor"}
    stations = {}
    for s in layout["stations"]:
        sid = s["id"]
        mach = []
        for mid in s.get("machines", []):
            m = machines.get(mid, {})
            mach.append({"id": mid, "name": m.get("name"), "type": m.get("type"),
                         "failure_modes": fm.get(m.get("type"), [])})
        info = md.get(sid, {})
        stations[sid] = {
            "id": sid, "name": s["name"], "what_happens": info.get("what_happens"), "priority": info.get("priority"),
            "machines": mach, "upstream": sorted(set(up.get(sid, []))), "downstream": sorted(set(down.get(sid, []))),
            "people": people.get(sid), "hero": sid == "S06",
        }
    (out).mkdir(parents=True, exist_ok=True)
    json.dump({"stations": stations}, open(out / "stations.json", "w"), indent=1)

    # RAG chunks so the chatbot can answer "what does S06 do?" and "what can go wrong at S06?"
    cp = out / "rag" / "rag_chunks.jsonl"
    chunks = [json.loads(l) for l in open(cp) if l.strip()]
    chunks = [c for c in chunks if c["source_type"] not in ("station", "station_failures")]
    n = 0

    def add(kind, sid, mid, title, text):
        nonlocal n
        n += 1
        chunks.append({"chunk_id": f"st{n:05d}", "source_type": kind, "source_id": f"{sid}" if kind == "station" else f"{sid}-FAIL",
                       "machine_id": mid, "area": None, "title": title, "text": text,
                       "metadata": {"source": "twin_layout+failure_catalogue", "station": sid}})
    for sid, s in stations.items():
        mt = ", ".join(f"{m['id']} {m['name']}" for m in s["machines"]) or "no machines (support area)"
        flow = (f" Receives from {', '.join(s['upstream'])}." if s["upstream"] else "") + \
               (f" Feeds {', '.join(s['downstream'])}." if s["downstream"] else "")
        add("station", sid, None, f"Station {sid} {s['name']}",
            f"Station {sid} ({s['name']}): {s['what_happens'] or 'support area'}. Machines: {mt}.{flow}"
            + (f" People: {s['people']}." if s["people"] else "") + (" This is the hero scenario station." if s["hero"] else ""))
        for m in s["machines"]:
            if not m["failure_modes"]:
                continue
            lines = [f"{f['mode']} on {f['component']}: symptom {f['symptom']}; cause {f['cause']}; repair: {f['repair']} "
                     f"(about {f['repair_min']:.0f} min, part {f['spare_part']})" for f in m["failure_modes"]]
            add("station_failures", sid, m["id"], f"Failure modes of {m['id']} {m['name']} at {sid}",
                f"Failure modes the simulator can inject on {m['id']} {m['name']} (station {sid}): " + " | ".join(lines))
    with open(cp, "w") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return len(stations), n


if __name__ == "__main__":
    print("stations, chunks:", build())
