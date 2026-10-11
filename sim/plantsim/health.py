"""Minute telemetry for the anomaly monitor, with the same dynamics as the data generator
(load cycle, first-order temperature lag, correlated vibration noise, wear curve), so the detector sees in
the simulation what it was trained on."""
from __future__ import annotations

import math
import zlib

import numpy as np
from scipy.signal import lfilter

from plantdata import events as ev
from plantdata import sensors as sensors_mod


class Telemetry:
    def __init__(self, seed: int, clock0: float) -> None:
        self.seed, self.clock0 = seed, clock0
        self.st: dict[str, dict] = {}

    def _state(self, mid: str, vib0: float) -> dict:
        if mid not in self.st:
            r = np.random.default_rng([self.seed, zlib.crc32(mid.encode()), 7])
            self.st[mid] = {"rng": r, "vz": np.zeros(1), "bz": np.zeros(1), "cz": np.zeros(1), "temp": None,
                            "phase": float(r.uniform(0, 1))}
        return self.st[mid]

    def minute(self, mid: str, t0: float, up: np.ndarray, producing: np.ndarray, hero_degr) -> dict:
        """One minute starting at sim time t0. `up` and `producing` are length-60 boolean arrays (per second)."""
        vib0, dtemp, cur0, duty, cycle, vnoise, _ = sensors_mod.PROFILE[mid]
        s = self._state(mid, vib0)
        r = s["rng"]
        t = t0 + np.arange(60.0)
        curve = sensors_mod._load_curve(t, duty, cycle, s["phase"] * cycle)
        load = np.where(up, np.where(producing, curve, 0.08), 0.0)
        d = x = np.zeros(60)
        if hero_degr is not None:
            d, x = hero_degr(t)
        f = ev.FAULT
        vz, bz, cz = s["vz"], s["bz"], s["cz"]
        vn, vz = lfilter([1.0], [1.0, -0.9], r.normal(0, vnoise, 60), zi=vz)
        bn, bz = lfilter([1.0], [1.0, -0.8], r.normal(0, 0.01 * vib0, 60), zi=bz)
        cn, cz = lfilter([1.0], [1.0, -0.7], r.normal(0, 0.01 * cur0, 60), zi=cz)
        s["vz"], s["bz"], s["cz"] = vz, bz, cz
        vib = vib0 * (0.55 + 0.45 * load) * (1 + f["vib_gain"] * d) + vn
        band = 0.05 * vib0 * (0.7 + 0.3 * load) * (1 + f["band_gain"] * d) + np.abs(bn)
        cur = cur0 * (0.30 + 0.70 * load) * (1 + f["current_gain"] * d) + cn
        amb = 24 + 3 * np.sin(2 * np.pi * ((t + self.clock0) / 86400 - 0.3))
        target = amb + dtemp * load + f["temp_rise_c"] * x
        a = 1 / 900
        if s["temp"] is None:   # as the generator: start at the mean target of the first 900 s
            t9 = t0 + np.arange(900.0)
            c9 = sensors_mod._load_curve(t9, duty, cycle, s["phase"] * cycle)
            a9 = 24 + 3 * np.sin(2 * np.pi * ((t9 + self.clock0) / 86400 - 0.3))
            s["temp"] = float((a9 + dtemp * c9).mean())
        tz = np.array([(1 - a) * s["temp"]])
        temp, tz = lfilter([a], [1, -(1 - a)], target, zi=tz * 1.0)
        s["temp"] = float(temp[-1])
        temp = temp + r.normal(0, 0.15, 60)
        return {"vib_mean": float(vib.mean()), "band_mean": float(band.mean()), "temp_mean": float(temp.mean()), "cur_mean": float(cur.mean()),
                "load_mean": float(load.mean() * 100), "up_frac": float(up.mean()), "clock_s": self.clock0 + t0}
