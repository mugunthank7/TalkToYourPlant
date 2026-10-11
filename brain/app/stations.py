"""Click-a-station briefing: what is happening at a station, why, and what to do about it."""
import json
from pathlib import Path

from . import config

STATIONS = config.BRAIN_DIR / "data" / "out" / "stations.json"
COST_PER_MIN = 38000


class StationService:
    def __init__(self, brain):
        self.b = brain
        self.book = json.loads(STATIONS.read_text())["stations"] if STATIONS.exists() else {}

    def ids(self):
        return list(self.book)

    def machine_ids(self, sid):
        return [m["id"] for m in self.book.get(sid, {}).get("machines", [])]

    def focus_machine(self, sid, states=None):
        ms = self.machine_ids(sid)
        if not ms:
            return None
        states = states or {}
        for m in ms:                                   # alerting or stopped machine first
            st = states.get(m, {})
            if st.get("status") in ("critical", "warning", "fault", "repair") or st.get("machine_state") in ("fault", "repair"):
                return m
        return ms[0]

    # ------------------------------------------------------------------
    def briefing(self, sid, with_answer=True):
        if sid not in self.book:
            return {"error": f"unknown station {sid}", "known": self.ids()}
        st = self.book[sid]
        mids = self.machine_ids(sid)
        eng = self.b.sim.get_station(sid, mids, self.b.g) if mids else {"state": "run", "machines": []}
        states = {m["machine_id"]: m for m in eng.get("machines", [])}
        focus = self.focus_machine(sid, states)
        fstate = states.get(focus, {})
        problem = bool(fstate.get("alert")) or fstate.get("status") in ("critical", "warning", "fault", "repair") \
            or eng.get("state") in ("fault", "repair", "risk", "starved", "blocked")
        out = {"station": {k: st[k] for k in ("id", "name", "what_happens", "upstream", "downstream", "people", "hero")},
               "engine_state": eng.get("state"), "reason": eng.get("reason"), "problem": problem, "focus_machine": focus,
               "machines": [], "source": eng.get("source")}
        for m in st["machines"]:
            s = states.get(m["id"], {})
            r = s.get("readings") or {}
            out["machines"].append({"id": m["id"], "name": m["name"], "type": m["type"], "status": s.get("status"),
                                    "machine_state": s.get("machine_state"), "alert": (s.get("alert") or {}).get("severity"),
                                    "vib_multiple": s.get("vib_multiple"), "rul_min": s.get("remaining_useful_life_min"),
                                    "readings": {k: (v.get("value") if isinstance(v, dict) else v) for k, v in r.items()},
                                    "contributors": (s.get("alert") or {}).get("contributors"),
                                    "evidence": s.get("evidence"), "affected_stations": s.get("affected_stations"),
                                    "open_work_orders": s.get("open_work_orders")})
        out["failure_catalog"] = [{"machine_id": m["id"], **f} for m in st["machines"] for f in m["failure_modes"]]
        if focus:
            esc = self.b.g.escalation_chain(focus)
            out["escalation"] = esc and {"shift": esc["shift"], "chain": [
                {"level": l["level"], "name": l.get("name"), "role": l.get("role"), "extension": l.get("extension"),
                 "page_after_min": l.get("page_after_min")} for l in esc["chain"]], "vendor": esc["vendor"]}
            out["steps"] = self._steps(sid, focus, fstate, eng, esc)
            if with_answer:
                q = f"What is wrong with {focus} and what should we do?"
                a = self.b.ask(q, session_id=f"station-{sid}", focus_hint=[focus])
                out["diagnosis"] = {"text": a["answer"], "report": a.get("report"), "citations": [c["id"] for c in a["citations"]],
                                    "highlight": a["highlight"], "latency_s": a["meta"]["latency_s"]}
                if a.get("report") and a["report"].get("do_now"):
                    out["steps"] = a["report"]["do_now"]
        else:
            out["steps"] = ["Support area: no machines are monitored here."]
        return out

    def _steps(self, sid, mid, s, eng, esc):
        steps = []
        stopped = eng.get("state") in ("fault", "repair") or s.get("machine_state") in ("fault", "repair")
        alert = (s.get("alert") or {}).get("severity")
        l1 = next((l for l in (esc or {}).get("chain", []) if l["level"] == "L1_primary_tech"), None)
        fm = next((m for m in self.book[sid]["machines"] if m["id"] == mid), {"failure_modes": []})
        if mid == "M05" and alert:
            mode = next((f for f in fm["failure_modes"] if f["mode"] == "bearing_wear"), None)
        else:
            mode = fm["failure_modes"][0] if fm["failure_modes"] else None
        if stopped:
            steps.append(f"{sid} is stopped ({eng.get('reason') or s.get('machine_state')}). Operator: press the andon, tell the line lead, note the time.")
            if l1:
                steps.append(f"Page L1 {l1['name']} ({l1.get('extension')}); escalate to L2 after {esc['escalation_minutes']['L2_backup']} min if no answer.")
            steps.append(f"Every minute down costs about ${COST_PER_MIN:,} and starves or blocks the neighbouring stations.")
        elif alert:
            rul = s.get("remaining_useful_life_min")
            steps.append(f"{mid} has a {alert} anomaly alert" + (f"; about {rul:.0f} min of useful life left." if rul else "."))
            if l1:
                steps.append(f"Page L1 {l1['name']} ({l1.get('extension')}) now and plan the repair at the next buffer-protected stop (SOP-OPS-02).")
            if mode:
                steps.append(f"Likely repair: {mode['repair']} (about {mode['repair_min']:.0f} min). Bring spare part {mode['spare_part']} from S12.")
        else:
            steps.append(f"{sid} is running normally. No action needed.")
            if mode:
                steps.append(f"Watch for: {mode['mode']} ({mode['symptom']}).")
        return steps

    def plan_with_llm(self, sid):
        """Optional: ask the local LLM to turn the briefing into a short action plan."""
        b = self.briefing(sid, with_answer=False)
        if "error" in b:
            return b
        facts = json.dumps({"station": b["station"]["name"], "state": b["engine_state"], "reason": b["reason"],
                            "machines": b["machines"], "escalation": b.get("escalation"), "steps": b.get("steps"),
                            "failure_catalog": b["failure_catalog"][:4]}, default=str)[:3500]
        from . import prompts
        system = prompts.PLAN_SYSTEM
        try:
            text = self.b._ollama_chat(system, "FACTS:\n" + facts, num_predict=300)
        except Exception as e:  # noqa: BLE001
            return {"error": f"local LLM unavailable: {type(e).__name__}", "steps": b.get("steps")}
        return {"plan": text, "model": config.pick_model()}
