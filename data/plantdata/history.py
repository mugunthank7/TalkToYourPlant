"""About a month of shifts for forecasting: hourly output, shift KPIs, 1-minute sensors, incidents.

Each shift can contain one degradation episode on a random machine. Outcomes: repaired in time,
repaired late (still before failure) or run to failure. Saturday runs a slower takt (lower demand),
Sunday is off, and each day has its own operator efficiency.
"""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from . import events as ev
from . import outputs, sensors

SHIFT_S = 8 * 3600
CLOCK = {"A": 6 * 3600, "B": 14 * 3600}
CANDIDATES = ["M01", "M03", "M04", "M05", "M09", "M10"]
START = dt.date(2026, 9, 1)


def build(days: int, seed: int) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    hourly_rows, sensor_rows, shift_rows, incidents = [], [], [], []
    for day in range(days):
        date = START + dt.timedelta(days=day)
        if date.weekday() == 6:
            continue
        takt = 120.0 if date.weekday() == 5 else outputs.TAKT_S
        day_eff = float(np.clip(rng.normal(0.97, 0.02), 0.9, 1.0))
        for shift in ("A", "B"):
            sid = f"{date.isoformat()}-{shift}"
            faults = []
            if rng.random() < 0.15:
                mid = str(rng.choice(CANDIDATES))
                onset = float(rng.uniform(0.3, 4.0) * 3600)
                ramp = float(rng.uniform(2.0, 3.5) * 3600)
                f0 = sensors.make_fault(mid, f"{mid.lower()}_main_bearing", onset, ramp, None, 0.0,
                                        vib_gain=float(rng.uniform(2.2, 3.0)))
                alert = ev.alert_time(f0)
                fail_t = onset + ramp
                outcome = rng.choice(["timely", "late", "failure"], p=[0.65, 0.20, 0.15])
                if outcome == "timely":
                    rs = alert + rng.uniform(8, 20) * 60
                elif outcome == "late":
                    rs = alert + 0.5 * (fail_t - alert)
                else:
                    rs = None
                re = (rs + ev.REPAIR_S) if rs is not None else fail_t + 5400
                f0.update(repair_start_s=rs, repair_end_s=float(re))
                faults.append(f0)
                incidents.append({"shift_id": sid, "date": date.isoformat(), "shift": shift, "machine_id": mid,
                                  "component_id": f0["component_id"], "onset_s": round(onset), "alert_s": round(alert),
                                  "failure_s_if_ignored": round(fail_t), "outcome": str(outcome),
                                  "repair_start_s": None if rs is None else round(rs), "repair_end_s": round(re)})
            df, aux = sensors.generate(SHIFT_S, rng, faults, micro_stops=True, clock_start_s=CLOCK[shift])
            minutes = outputs.minute_frame(aux, rng, takt_s=takt, efficiency=day_eff)
            hourly = outputs.hourly(minutes, ideal_per_hour=3600 / takt)
            hourly.insert(0, "shift_id", sid)
            hourly_rows.append(hourly)
            summ = outputs.summary(minutes, takt_s=takt)
            shift_rows.append({"shift_id": sid, "date": date.isoformat(), "weekday": date.weekday(), "shift": shift,
                               "takt_s": takt, "operator_efficiency": round(day_eff, 3),
                               "demand_plan_units": int(SHIFT_S / takt), "had_incident": bool(faults), **summ})
            m = df.assign(minute=df["t_s"] // 60)
            agg = m.groupby(["minute", "machine_id"]).agg(
                vib_mean=("vibration_rms_mm_s", "mean"), vib_max=("vibration_rms_mm_s", "max"),
                band_mean=("vib_bpfo_band", "mean"), temp_mean=("temperature_c", "mean"),
                current_mean=("motor_current_a", "mean"), load_mean=("load_pct", "mean"),
                state=("state", lambda s: s.mode().iat[0]), fault_label=("fault_label", "max"),
                rul_s=("rul_s", "min")).reset_index()
            agg.insert(0, "shift_id", sid)
            sensor_rows.append(agg.round(3))
    return {
        "history_hourly": pd.concat(hourly_rows, ignore_index=True),
        "history_shifts": pd.DataFrame(shift_rows),
        "history_sensors_1min": pd.concat(sensor_rows, ignore_index=True),
        "history_incidents": pd.DataFrame(incidents),
    }
