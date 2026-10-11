"""Adapter between the brain and M's simulation engine.

SIM_MODE=mock (default): answers from M's committed outputs (data/out/events.json,
data/out/scenarios/summary.json) and the Voltara contract (simulator_interface.json).
SIM_MODE=live: HTTP calls to M's FastAPI (D-016): GET /state, GET /kpis, POST /scenario,
POST /work_order. Endpoint shapes are proposals until M confirms (see docs/CONTRACT_PROPOSALS.md).

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
    mode = "live"

    def __init__(self, base=None):
        self.base = (base or config.get("SIM_URL", "http://localhost:8000")).rstrip("/")

    def _req(self, method, path, body=None, timeout=8):
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(self.base + path, data=data, method=method,
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def get_sensor_state(self, machine_id, graph=None):
        st = self._req("GET", "/state")
        m = (st.get("machines") or {}).get(machine_id) if isinstance(st, dict) else None
        return {"machine_id": machine_id, "source": "live:/state", **(m or {"status": "unknown"})}

    def run_scenario(self, machine_id, hours, op="keep_running", baseline="live"):
        body = {"type": "run_scenario", "id": f"SC-{next(_wo_counter)}", "base": baseline,
                "changes": [{"op": op, "machine_id": machine_id, "hours": hours}]}
        return {**self._req("POST", "/scenario", body, timeout=60), "source": "live:/scenario"}

    def create_work_order(self, machine_id, component_id=None, spare_part=None, fault_code=None, priority="P2", note=None):
        body = {"type": "work_order", "machine_id": machine_id, "component_id": component_id,
                "spare_part": spare_part, "fault_code": fault_code, "priority": priority, "note": note}
        return {**self._req("POST", "/work_order", body), "source": "live:/work_order"}


def get_sim():
    return LiveSim() if config.get("SIM_MODE", "mock").lower() == "live" else MockSim()
