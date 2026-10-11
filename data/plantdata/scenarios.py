"""Named scenarios: sensors + production output for one 8 h shift.

ideal                 No stops, no scrap, takt exactly 90 s. The theoretical ceiling.
healthy_realistic     Normal micro-stops and scrap, no faults. The everyday baseline.
hero_timely_repair    Bearing wear on M05, technician dispatched at the alert (the demo).
hero_delayed_repair   Same fault, repair starts 40 min late, just before the robot would fail.
hero_ignored          Same fault, nobody acts: M05 seizes and the line stops until an emergency repair.
"""
from __future__ import annotations

import numpy as np

from . import events as ev
from . import outputs, sensors

EMERGENCY_REPAIR_S = 5400
DELAY_S = 2400
SHIFT_S = 8 * 3600


def hero_fault(kind: str, hero: dict) -> dict | None:
    fail_t = ev.FAULT["onset_s"] + ev.FAULT["ramp_s"]
    if kind == "timely":
        rs, re = hero["t_repair_start_s"], hero["t_repair_end_s"]
    elif kind == "delayed":
        rs = hero["t_repair_start_s"] + DELAY_S
        re = rs + ev.REPAIR_S
    elif kind == "ignored":
        rs, re = None, fail_t + EMERGENCY_REPAIR_S
    else:
        return None
    return sensors.make_fault(ev.FAULT["machine_id"], ev.FAULT["component_id"], ev.FAULT["onset_s"],
                              ev.FAULT["ramp_s"], rs, re)


SCENARIOS = {
    "ideal": dict(fault=None, micro=False, ideal=True,
                  about="Theoretical ceiling: no stops, no scrap, takt exactly 90 s."),
    "healthy_realistic": dict(fault=None, micro=True, ideal=False,
                              about="Normal day: micro-stops and base scrap, no faults."),
    "hero_timely_repair": dict(fault="timely", micro=True, ideal=False,
                               about="M05 bearing wear, alert acted on after 5 min. The demo path."),
    "hero_delayed_repair": dict(fault="delayed", micro=True, ideal=False,
                                about="Same fault, repair starts 40 min late, just before the robot would fail."),
    "hero_ignored": dict(fault="ignored", micro=True, ideal=False,
                         about="Same fault, ignored: M05 seizes at 6.0 h, line down until emergency repair."),
}


def run(name: str, seed: int, hero: dict):
    cfg = SCENARIOS[name]
    fault = hero_fault(cfg["fault"], hero) if cfg["fault"] else None
    rng = np.random.default_rng(seed)
    df, aux = sensors.generate(SHIFT_S, rng, [fault] if fault else [], micro_stops=cfg["micro"])
    minutes = outputs.minute_frame(aux, rng, ideal=cfg["ideal"])
    hourly = outputs.hourly(minutes, ideal_per_hour=3600 / outputs.TAKT_S)
    summ = outputs.summary(minutes) | {"about": cfg["about"]}
    if fault:
        summ |= {"t_alert_s": hero["t_alert_s"], "t_fail_if_ignored_s": fault["onset_s"] + fault["ramp_s"],
                 "remaining_useful_life_at_alert_min": round((fault["onset_s"] + fault["ramp_s"] - hero["t_alert_s"]) / 60, 1)}
    return df, minutes, hourly, summ
