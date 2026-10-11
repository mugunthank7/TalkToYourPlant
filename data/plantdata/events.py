"""The scripted hero scenario: weld robot 2 (M05) develops joint-1 bearing wear in shift A."""
from __future__ import annotations

import math

import numpy as np

FAULT = {
    "machine_id": "M05",
    "component_id": "m05_joint1_bearing",
    "shift": "A",
    "onset_s": 3 * 3600,      # wear starts to show
    "ramp_s": 3 * 3600,       # until it would fail if left alone
    "tau_s": 3600,            # exponential growth time constant
    "vib_gain": 2.6,          # vibration rms ends at 1 + 2.6 = 3.6x baseline
    "band_gain": 14.0,        # bearing-defect band energy is the early signal
    "temp_rise_c": 14.0,
    "current_gain": 0.12,
    "alert_vib_multiple": 2.0,
}

DISPATCH_DELAY_S = 300   # alert to technician leaving the bay
PICKUP_S = 90            # grab the bearing from the spare cage
REPAIR_S = 1500


def degradation(t: np.ndarray, f: dict = FAULT) -> np.ndarray:
    """0 before onset, rising exponentially to 1 at onset+ramp."""
    x = np.clip((np.asarray(t, dtype=float) - f["onset_s"]) / f["ramp_s"], 0, 1)
    k = f["ramp_s"] / f["tau_s"]
    return (np.exp(x * k) - 1) / (math.exp(k) - 1)


def progress(t: np.ndarray, f: dict = FAULT) -> np.ndarray:
    return np.clip((np.asarray(t, dtype=float) - f["onset_s"]) / f["ramp_s"], 0, 1)


def alert_time(f: dict = FAULT) -> float:
    d = (f["alert_vib_multiple"] - 1) / f["vib_gain"]
    k = f["ramp_s"] / f["tau_s"]
    x = math.log(1 + d * (math.exp(k) - 1)) / k
    return f["onset_s"] + x * f["ramp_s"]


def hero_timeline(graph, tech_walk_speed: float) -> dict:
    """Alert, dispatch and repair times, using the same walking geometry as the schedule."""
    t_alert = alert_time()
    t_dispatch = t_alert + DISPATCH_DELAY_S
    w1 = graph.distance("S10", "S12") / tech_walk_speed
    w2 = graph.distance("S12", "S06") / tech_walk_speed
    t_pick = t_dispatch + w1
    t_arrive = t_pick + PICKUP_S + w2
    return {
        "fault": FAULT,
        "t_onset_s": FAULT["onset_s"],
        "t_alert_s": round(t_alert, 1),
        "t_dispatch_s": round(t_dispatch, 1),
        "t_pickup_s": round(t_pick, 1),
        "t_repair_start_s": round(t_arrive, 1),
        "t_repair_end_s": round(t_arrive + REPAIR_S, 1),
        "preventive_maintenance": [
            {"t_s": 3000, "machine_id": "M03", "station": "S04"},
            {"t_s": 9500, "machine_id": "M04", "station": "S05"},
            {"t_s": 15500, "machine_id": "M07", "station": "S07"},
            {"t_s": 25000, "machine_id": "M06", "station": "S04"},
        ],
    }
