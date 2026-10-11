"""Adapter between the brain and M's simulation engine.

SIM_MODE=mock (default): answers from M's committed outputs (data/out/events.json,
data/out/scenarios/summary.json) and the Voltara contract (simulator_interface.json).
SIM_MODE=live: M's engine (sim/plantsim) through its /tools endpoints: get_machine_health,
get_anomaly_report, run_what_if, create_work_order.

All methods return plain dicts. Everything the mock returns carries "source": "mock...".
"""
import itertools
import json
import os
import urllib.request
from pathlib import Path

from . import config

ROOT = config.BRAIN_DIR.parent                 # repo root
OUT = config.BRAIN_DIR / "data" / "out"
COST_PER_MIN = 38000                            # M's D-024 (Siemens 2024)
_wo_counter = itertools.count(1042)


def _load(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return default


class MockSim:
    mode = "mock"

    def __init__(self):
        self.events = _load(ROOT / "data/out/events.json", {})
        self.summary = _load(ROOT / "data/out/scenarios/summary.json", {})
        self.contract = _load(OUT / "contracts/simulator_interface.json", {})
        self.fault_active = {"M05"}             # hero fault active in the demo state
        self.work_orders = []

    # ---- sensors ---------------------------------------------------------
    def get_sensor_state(self, machine_id, graph=None):
        mid = machine_id
        if mid == "M05" and self.events.get("fault"):
            f = self.events["fault"]
            t = self.events.get("t_alert_s", 18436.0)
            frac = max(0.0, min(1.0, (t - f["onset_s"]) / f["ramp_s"]))
            base = {"vibration_rms": 0.42, "temperature_c": 61.5, "motor_current_a": 14.2}
            vib = base["vibration_rms"] * (1 + (f["vib_gain"] - 1) * frac)
            return {
                "machine_id": mid, "status": "warning", "source": "mock:events.json",
                "readings": {
                    "vibration_rms": {"value": round(vib, 2), "nominal": base["vibration_rms"],
                                      "ratio": round(vib / base["vibration_rms"], 2), "alert_at_ratio": f["alert_vib_multiple"]},
                    "temperature_c": {"value": round(base["temperature_c"] + f["temp_rise_c"] * frac, 1), "nominal": base["temperature_c"]},
                    "motor_current_a": {"value": round(base["motor_current_a"] * (1 + f["current_gain"] * frac), 1), "nominal": base["motor_current_a"]},
                },
                "alert": {"type": "alert", "machine_id": mid, "severity": "warning", "score": 0.93,
                          "contributors": [{"signal": "vibration_rms", "shap": 0.61}, {"signal": "temperature_c", "shap": 0.22},
                                           {"signal": "motor_current_a", "shap": 0.10}],
                          "component_id": f.get("component_id", "m05_joint1_bearing")},
                "remaining_useful_life_min": self.summary.get("hero_timely_repair", {}).get("remaining_useful_life_at_alert_min"),
                "note": "SHAP contributors are illustrative until anomaly detection exists (D-019, D-023).",
            }
        # storyline machines and the rest: derive from the family contract
        g = graph
        voltara = (g.get_machine(mid) or {}).get("voltara_id", mid) if g else mid
        fam_key = (g.get_machine(mid) or {}).get("family") if g else None
        fam = (self.contract.get("families") or {}).get(fam_key, {})
        bad = (self.contract.get("bad_actors") or {}).get(voltara)
        sigs = {s["code"]: s for s in fam.get("fault_signatures", [])}
        readings = {}
        for s in fam.get("sensors", []):
            readings[s["name"]] = {"value": s["nominal"], "nominal": s["nominal"], "warn": s["warn"], "alarm": s["alarm"], "unit": s.get("unit")}
        status = "ok"
        if bad and bad["fault_code"] in sigs:
            sig = sigs[bad["fault_code"]]
            r = readings.get(sig["sensor"])
            if r:
                r["value"] = round(r["nominal"] + 0.75 * (r["warn"] - r["nominal"]), 2)   # 75% of the way to warn
                status = "degrading"
            return {"machine_id": mid, "status": status, "source": "mock:contract+storyline",
                    "storyline_fault": bad["fault_code"], "drifting_channel": sig["sensor"], "shape": sig["shape"],
                    "readings": readings}
        return {"machine_id": mid, "status": status, "source": "mock:contract-nominal", "readings": readings}

    # ---- what-if ----------------------------------------------------------
    def run_scenario(self, machine_id, hours, op="keep_running", baseline="hero_timely_repair"):
        s = self.summary
        rul_h = (s.get("hero_timely_repair", {}).get("remaining_useful_life_at_alert_min") or 52.7) / 60.0
        if machine_id != "M05":
            return {"error": f"mock what-if only models the hero fault on M05, not {machine_id}",
                    "source": "mock", "supported": ["M05"]}
        if hours <= 0.1:
            name = "hero_timely_repair"
        elif hours <= rul_h:
            name = "hero_delayed_repair"
        else:
            name = "hero_ignored"
        sc, base = s.get(name, {}), s.get(baseline, {})
        fail_p = 0.05 if name == "hero_timely_repair" else 0.35 if name == "hero_delayed_repair" else 0.97
        return {
            "type": "scenario_result", "id": f"SC-{next(_wo_counter)}", "source": "mock:scenarios/summary.json",
            "query": {"op": op, "machine_id": machine_id, "hours": hours},
            "matched_scenario": name, "rul_hours_at_alert": round(rul_h, 2),
            "kpis": {
                "throughput_per_hr": {"baseline": base.get("units_per_hour_mean"), "scenario": sc.get("units_per_hour_mean")},
                "downtime_min": {"baseline": base.get("downtime_min"), "scenario": sc.get("downtime_min")},
                "oee": {"baseline": base.get("oee"), "scenario": sc.get("oee")},
                "units": {"baseline": base.get("units"), "scenario": sc.get("units")},
                "failure_probability": fail_p, "cost_usd": sc.get("downtime_cost_usd"),
            },
            "about": sc.get("about"),
            "caveat": "failure_probability is an estimate chosen per matched scenario, not a model output.",
        }

    # ---- work orders ------------------------------------------------------
    def create_work_order(self, machine_id, component_id=None, spare_part=None, fault_code=None, priority="P2", note=None):
        wo = {"type": "work_order", "id": f"WO-{next(_wo_counter)}", "machine_id": machine_id,
              "component_id": component_id, "spare_part": spare_part, "fault_code": fault_code,
              "priority": priority, "note": note, "downtime_cost_per_min": COST_PER_MIN, "source": "mock"}
        self.work_orders.append(wo)
        return wo


class LiveSim:
    """M's SimPy engine (sim/plantsim/api.py): reads and acts through its /tools endpoints.

    Response shapes are taken from sim/plantsim/tools.py and snapshot.py. Machines the engine does
    not simulate (everything except M01..M10) fall back to the mock storyline data.
    """
    mode = "live"
    SIMULATED = {f"M{i:02d}" for i in range(1, 11)}

    def __init__(self, base=None):
        self.base = (base or config.get("SIM_URL", "http://localhost:8000")).rstrip("/")
        self.fallback = MockSim()

    def _req(self, method, path, body=None, timeout=60):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data=data, method=method,
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def _tool(self, name, args):
        return self._req("POST", f"/tools/{name}", args)

    @staticmethod
    def _contrib(raw):
        out = []
        for c in raw or []:
            if isinstance(c, dict):
                sig = c.get("signal") or c.get("name") or c.get("feature")
                val = c.get("shap", c.get("value", c.get("contribution")))
                if sig is not None:
                    out.append({"signal": sig, "shap": val})
            elif isinstance(c, (list, tuple)) and len(c) >= 2:
                out.append({"signal": c[0], "shap": c[1]})
        return out

    def get_sensor_state(self, machine_id, graph=None):
        if machine_id not in self.SIMULATED:
            return self.fallback.get_sensor_state(machine_id, graph)
        h = self._tool("get_machine_health", {"machine_id": machine_id})
        if h.get("error"):
            return {"machine_id": machine_id, "status": "unknown", "source": "live", "error": h["error"]}
        try:
            an = self._tool("get_anomaly_report", {"machine_id": machine_id})
        except Exception:  # noqa: BLE001
            an = {}
        level = h.get("alert")
        status = {"critical": "critical", "watch": "warning"}.get(level, "ok" if h.get("state") in (None, "run", "idle") else h.get("state"))
        readings = {k: {"value": v} for k, v in (h.get("sensors") or {}).items()}
        out = {"machine_id": machine_id, "status": status, "machine_state": h.get("state"),
               "readings": readings, "source": "live:/tools/get_machine_health",
               "vib_multiple": h.get("vib_multiple")}
        if h.get("rul_s") is not None:
            out["remaining_useful_life_min"] = round(h["rul_s"] / 60.0, 1)
        if level:
            out["alert"] = {"type": "alert", "machine_id": machine_id,
                            "severity": "critical" if level == "critical" else "warning",
                            "score": (an.get("anomaly") or {}).get("score") if isinstance(an, dict) else None,
                            "contributors": self._contrib(h.get("contributors") or an.get("contributors")),
                            "component_id": h.get("component_id")}
        return out

    def run_scenario(self, machine_id, hours, op="keep_running", baseline="live"):
        changes = [{"op": op, "hours": hours}]
        if op != "keep_running":
            changes = [{"op": op, "machine": machine_id}]
        res = self._tool("run_what_if", {"changes": changes})
        if res.get("error"):
            return {"error": res["error"], "source": "live:/tools/run_what_if"}
        b, s = (res.get("baseline") or {}).get("kpis", {}), (res.get("scenario") or {}).get("kpis", {})
        shift_h = max(((res.get("baseline") or {}).get("kpis", {}).get("t_s") or 28800) / 3600.0, 1.0)
        rul_h = None
        try:
            h = self._tool("get_machine_health", {"machine_id": machine_id})
            if h.get("rul_s") is not None:
                rul_h = round(h["rul_s"] / 3600.0, 2)
        except Exception:  # noqa: BLE001
            pass
        pick = lambda k: {"baseline": b.get(k), "scenario": s.get(k)}
        return {
            "type": "scenario_result", "id": f"SC-{next(_wo_counter)}", "source": "live:/tools/run_what_if",
            "query": {"op": op, "machine_id": machine_id, "hours": hours},
            "matched_scenario": "live simulation (branch from now to end of shift)", "rul_hours_at_alert": rul_h,
            "kpis": {"throughput_per_hr": {"baseline": round((b.get("units") or 0) / 8.0, 1), "scenario": round((s.get("units") or 0) / 8.0, 1)},
                     "downtime_min": pick("downtime_min"), "oee": pick("oee"), "units": pick("units"),
                     "failure_probability": None, "cost_usd": s.get("downtime_cost_usd")},
            "about": res.get("summary"), "delta": res.get("delta"),
            "caveat": "throughput_per_hr = units / 8 h shift; failure probability is not modelled by the engine.",
        }

    def create_work_order(self, machine_id, component_id=None, spare_part=None, fault_code=None, priority="P2", note=None):
        reason = note or (f"{fault_code} on {component_id}" if fault_code else "requested by brain")
        wo = self._tool("create_work_order", {"machine_id": machine_id, "reason": reason})
        return {"type": "work_order", "id": wo.get("id") or wo.get("wo_id"), "machine_id": machine_id,
                "component_id": component_id, "spare_part": spare_part, "fault_code": fault_code,
                "priority": priority, "note": reason, "downtime_cost_per_min": COST_PER_MIN,
                "source": "live:/tools/create_work_order", "engine_response": wo}


def get_sim():
    return LiveSim() if config.get("SIM_MODE", "mock").lower() == "live" else MockSim()
