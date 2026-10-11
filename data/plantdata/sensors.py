"""1 Hz sensor streams per machine: vibration, bearing-defect band, temperature, motor current."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import lfilter, lfilter_zi

from . import events as ev

# id: (base vibration mm/s rms, temperature rise at full load C, motor current A at full load,
#      duty fraction, cycle seconds, vibration noise)
PROFILE = {
    "M01": (3.8, 28.0, 85.0, 0.55, 60, 0.10),
    "M02": (1.4, 16.0, 22.0, 0.60, 60, 0.05),
    "M03": (1.8, 14.0, 30.0, 0.70, 90, 0.06),
    "M04": (1.2, 18.0, 14.0, 0.65, 90, 0.04),
    "M05": (1.2, 18.0, 14.0, 0.65, 90, 0.04),
    "M06": (0.9, 10.0, 18.0, 1.00, 90, 0.03),
    "M07": (0.6, 8.0, 6.0, 0.30, 90, 0.02),
    "M08": (1.1, 12.0, 16.0, 0.50, 120, 0.04),
    "M09": (1.5, 15.0, 24.0, 0.60, 100, 0.05),
    "M10": (2.2, 20.0, 40.0, 0.80, 300, 0.07),
}


def _load_curve(t: np.ndarray, duty: float, cycle: float, phase: float) -> np.ndarray:
    """Smooth on/off duty cycle in [0.08, 1]."""
    p = ((t + phase) % cycle) / cycle
    ramp = 0.08
    on = np.clip(np.minimum(p / ramp, (duty - p) / ramp), 0, 1) * (p < duty)
    return 0.08 + 0.92 * on


def _ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    return lfilter([1.0], [1.0, -phi], rng.normal(0, sigma, n))


def generate(seconds: int, rng: np.random.Generator, fault: bool, hero: dict | None) -> pd.DataFrame:
    t = np.arange(seconds, dtype=float)
    ambient = 24 + 3 * np.sin(2 * np.pi * (t / 86400 - 0.3))
    frames = []
    for mid, (vib0, dtemp, cur0, duty, cycle, vnoise) in PROFILE.items():
        phase = float(rng.uniform(0, cycle))
        load = _load_curve(t, duty, cycle, phase)
        state = np.where(load > 0.3, "running", "idle").astype(object)

        d = np.zeros_like(t)
        x = np.zeros_like(t)
        label = np.zeros(seconds, dtype=int)
        component = np.full(seconds, "", dtype=object)

        if fault and hero and mid == ev.FAULT["machine_id"]:
            f = ev.FAULT
            d = ev.degradation(t, f)
            x = ev.progress(t, f)
            r0, r1 = hero["t_repair_start_s"], hero["t_repair_end_s"]
            # Repair: motor off during the work, wear resets after the bearing is replaced.
            in_repair = (t >= r0) & (t < r1)
            after = t >= r1
            d = np.where(t >= r0, 0.0, d)
            x = np.where(t >= r0, 0.0, x)
            load = np.where(in_repair, 0.0, load)
            state = np.where(in_repair, "maintenance", state)
            label = ((d > 0.0) & (1 + f["vib_gain"] * d >= 1.3) & ~after).astype(int)
            component = np.where(label == 1, f["component_id"], "")

        f = ev.FAULT
        vib = vib0 * (0.55 + 0.45 * load) * (1 + f["vib_gain"] * d) + _ar1(rng, seconds, 0.9, vnoise)
        band = (0.05 * vib0 * (0.7 + 0.3 * load)) * (1 + f["band_gain"] * d) + np.abs(_ar1(rng, seconds, 0.8, 0.01 * vib0))
        target = ambient + dtemp * load + f["temp_rise_c"] * x
        b, a = [1 / 900], [1, -(1 - 1 / 900)]
        temp = lfilter(b, a, target, zi=lfilter_zi(b, a) * target[:900].mean())[0] + rng.normal(0, 0.15, seconds)
        cur = cur0 * (0.30 + 0.70 * load) * (1 + f["current_gain"] * d) + _ar1(rng, seconds, 0.7, 0.01 * cur0)
        vib = np.where(state == "maintenance", 0.05 + np.abs(rng.normal(0, 0.02, seconds)), vib)

        frames.append(pd.DataFrame({
            "t_s": t.astype(int),
            "machine_id": mid,
            "vibration_rms_mm_s": vib.round(3),
            "vib_bpfo_band": band.round(4),
            "temperature_c": temp.round(2),
            "motor_current_a": cur.round(2),
            "load_pct": (load * 100).round(1),
            "state": state,
            "fault_label": label,
            "fault_component": component,
            "degradation": d.round(4),
        }))
    return pd.concat(frames, ignore_index=True)
