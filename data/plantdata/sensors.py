"""1 Hz sensor streams per machine: vibration, bearing-defect band, temperature, motor current.

Also returns the per-second "machine is up" matrix and the output penalties that the production
model (outputs.py) turns into throughput, so sensors and output always agree.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import lfilter, lfilter_zi

from . import events as ev

# id: (base vibration mm/s rms, temperature rise at full load C, motor current A at full load,
#      duty fraction, cycle seconds, vibration noise, mean seconds between micro-stops)
PROFILE = {
    "M01": (3.8, 28.0, 85.0, 0.55, 60, 0.10, 2700),
    "M02": (1.4, 16.0, 22.0, 0.60, 60, 0.05, 5400),
    "M03": (1.8, 14.0, 30.0, 0.70, 90, 0.06, 5400),
    "M04": (1.2, 18.0, 14.0, 0.65, 90, 0.04, 4500),
    "M05": (1.2, 18.0, 14.0, 0.65, 90, 0.04, 4500),
    "M06": (0.9, 10.0, 18.0, 1.00, 90, 0.03, 9000),
    "M07": (0.6, 8.0, 6.0, 0.30, 90, 0.02, 7200),
    "M08": (1.1, 12.0, 16.0, 0.50, 120, 0.04, 5400),
    "M09": (1.5, 15.0, 24.0, 0.60, 100, 0.05, 5400),
    "M10": (2.2, 20.0, 40.0, 0.80, 300, 0.07, 9000),
}
MACHINES = list(PROFILE)


def _load_curve(t: np.ndarray, duty: float, cycle: float, phase: float) -> np.ndarray:
    """Smooth on/off duty cycle in [0.08, 1]."""
    p = ((t + phase) % cycle) / cycle
    ramp = 0.08
    on = np.clip(np.minimum(p / ramp, (duty - p) / ramp), 0, 1) * (p < duty)
    return 0.08 + 0.92 * on


def _ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    return lfilter([1.0], [1.0, -phi], rng.normal(0, sigma, n))


def _micro_stops(rng: np.random.Generator, n: int, mean_gap_s: float) -> np.ndarray:
    stopped = np.zeros(n, dtype=bool)
    t = rng.exponential(mean_gap_s)
    while t < n:
        dur = float(np.clip(rng.lognormal(np.log(70), 0.5), 20, 300))
        stopped[int(t):int(t + dur)] = True
        t += dur + rng.exponential(mean_gap_s)
    return stopped


def make_fault(machine_id: str, component_id: str, onset_s: float, ramp_s: float, repair_start_s: float | None,
               repair_end_s: float, **over) -> dict:
    """A degradation episode. repair_start_s=None (or after failure) means it runs to failure."""
    f = dict(ev.FAULT)
    f.update(machine_id=machine_id, component_id=component_id, onset_s=onset_s, ramp_s=ramp_s,
             repair_start_s=repair_start_s, repair_end_s=repair_end_s)
    f.update(over)
    return f


def generate(seconds: int, rng: np.random.Generator, faults: list[dict] | None = None,
             micro_stops: bool = False, clock_start_s: float = 6 * 3600) -> tuple[pd.DataFrame, dict]:
    faults = faults or []
    by_machine = {f["machine_id"]: f for f in faults}
    t = np.arange(seconds, dtype=float)
    ambient = 24 + 3 * np.sin(2 * np.pi * ((t + clock_start_s) / 86400 - 0.3))
    frames = []
    up = np.ones((len(PROFILE), seconds), dtype=bool)
    cycle_mult = np.ones(seconds)
    quality_pen = np.zeros(seconds)

    for idx, (mid, (vib0, dtemp, cur0, duty, cycle, vnoise, stop_gap)) in enumerate(PROFILE.items()):
        phase = float(rng.uniform(0, cycle))
        load = _load_curve(t, duty, cycle, phase)
        stopped = _micro_stops(rng, seconds, stop_gap) if micro_stops else np.zeros(seconds, dtype=bool)
        load = np.where(stopped, 0.0, load)
        state = np.where(stopped, "stopped", np.where(load > 0.3, "running", "idle")).astype(object)

        d = np.zeros(seconds)
        x = np.zeros(seconds)
        down = np.zeros(seconds, dtype=bool)
        label = np.zeros(seconds, dtype=int)
        component = np.full(seconds, "", dtype=object)
        rul = np.full(seconds, np.nan)

        f = by_machine.get(mid)
        if f:
            d = ev.degradation(t, f)
            x = ev.progress(t, f)
            fail_t = f["onset_s"] + f["ramp_s"]
            rs, re = f["repair_start_s"], f["repair_end_s"]
            if rs is not None and rs < fail_t:
                down = (t >= rs) & (t < re)
                down_state, reset = "maintenance", t >= rs
            else:
                down = (t >= fail_t) & (t < re)
                down_state, reset = "failed", t >= re
            d = np.where(reset, 0.0, d)
            x = np.where(reset, 0.0, x)
            load = np.where(down, 0.0, load)
            state = np.where(down, down_state, state)
            active = (d > 0) & (1 + f["vib_gain"] * d >= 1.3) & ~down
            label = active.astype(int)
            component = np.where(active, f["component_id"], "")
            rul = np.where(active, fail_t - t, np.nan)
            cycle_mult = cycle_mult + f["cycle_penalty"] * x
            quality_pen = quality_pen + f["quality_penalty"] * x

        up[idx] = ~(stopped | down)

        g = ev.FAULT
        gains = f or g
        vib = vib0 * (0.55 + 0.45 * load) * (1 + gains["vib_gain"] * d) + _ar1(rng, seconds, 0.9, vnoise)
        band = (0.05 * vib0 * (0.7 + 0.3 * load)) * (1 + gains["band_gain"] * d) + np.abs(_ar1(rng, seconds, 0.8, 0.01 * vib0))
        target = ambient + dtemp * load + gains["temp_rise_c"] * x
        b, a = [1 / 900], [1, -(1 - 1 / 900)]
        temp = lfilter(b, a, target, zi=lfilter_zi(b, a) * target[:900].mean())[0] + rng.normal(0, 0.15, seconds)
        cur = cur0 * (0.30 + 0.70 * load) * (1 + gains["current_gain"] * d) + _ar1(rng, seconds, 0.7, 0.01 * cur0)
        vib = np.where(down, 0.05 + np.abs(rng.normal(0, 0.02, seconds)), vib)

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
            "rul_s": rul.round(0),
        }))
    aux = {"machines": MACHINES, "up": up, "cycle_mult": cycle_mult, "quality_pen": quality_pen}
    return pd.concat(frames, ignore_index=True), aux
