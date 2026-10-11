"""Time to move an item between stations, and walking times between stations."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import layout as L

# mode: (speed m/s, load+unload handling seconds)
MODES = {"conveyor": (0.25, 8.0), "agv": (1.2, 25.0), "walk": (1.3, 0.0)}


def build(g: L.Graph) -> pd.DataFrame:
    rows = []
    for a, b, mode in L.ITEM_FLOW:
        speed, handling = MODES[mode]
        if mode == "conveyor":
            dist = abs(L.station(b)["x"] - L.station(a)["x"])
        else:
            dist = g.distance(a, b)
        mean = dist / speed + handling
        rows.append({"kind": "item", "from_station": a, "to_station": b, "mode": mode,
                     "distance_m": round(dist, 1), "mean_s": round(mean, 1), "std_s": round(0.12 * mean, 1)})
    ids = [s[0] for s in L.STATIONS]
    speed, _ = MODES["walk"]
    for a in ids:
        for b in ids:
            if a == b:
                continue
            dist = g.distance(a, b)
            rows.append({"kind": "walk", "from_station": a, "to_station": b, "mode": "walk",
                         "distance_m": round(dist, 1), "mean_s": round(dist / speed, 1),
                         "std_s": round(0.08 * dist / speed, 1)})
    return pd.DataFrame(rows)
