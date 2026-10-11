"""Sanity checks. Raise AssertionError on anything that would break the 3D scene or the engine."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from . import layout as L
from .schedule import SHIFT_S


def _rect(s):
    return (s["x"] - s["w"] / 2, s["z"] - s["d"] / 2, s["x"] + s["w"] / 2, s["z"] + s["d"] / 2)


def _seg_hits_rect(p, q, r) -> bool:
    x0, z0, x1, z1 = r
    for i in range(51):
        u = i / 50
        x, z = p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u
        if x0 + 0.01 < x < x1 - 0.01 and z0 + 0.01 < z < z1 - 0.01:
            return True
    return False


def layout(g: L.Graph) -> None:
    sts = [L.station(s[0]) for s in L.STATIONS]
    for i, a in enumerate(sts):
        ra = _rect(a)
        assert ra[0] >= 0 and ra[2] <= L.PLANT["width_m"] and ra[1] >= 0 and ra[3] <= L.PLANT["depth_m"], a["id"]
        for b in sts[i + 1:]:
            rb = _rect(b)
            overlap = not (ra[2] <= rb[0] or rb[2] <= ra[0] or ra[3] <= rb[1] or rb[3] <= ra[1])
            assert not overlap, f"{a['id']} overlaps {b['id']}"
    for u, nbrs in g.adj.items():
        for v, _ in nbrs:
            for s in sts:
                assert not _seg_hits_rect(g.xy(u), g.xy(v), _rect(s)), f"walkway {u}-{v} crosses {s['id']}"
    for s in sts:
        assert g.distance("GATE", s["id"]) < 400, f"{s['id']} unreachable"


def schedule(people: list[dict]) -> dict:
    coverage: dict[str, float] = {}
    for p in people:
        tl = p["timeline"]
        assert tl and tl[0]["s"] == 0, p["employee_id"]
        for a, b in zip(tl, tl[1:]):
            assert abs(a["e"] - b["s"]) < 1e-6, f"gap in {p['employee_id']} at {a['e']}"
            assert a["e"] >= a["s"], p["employee_id"]
        assert tl[-1]["e"] >= SHIFT_S - 1, f"{p['employee_id']} ends early: {tl[-1]['e']}"
        for s in tl:
            if s["k"] == "walk":
                for x, z in s["path"]:
                    assert 0 <= x <= L.PLANT["width_m"] and 0 <= z <= L.PLANT["depth_m"]
    # Fraction of the shift each operating station has someone at it (working or waiting for the next car).
    for st in {s for s in __import__("plantdata.people", fromlist=["x"]).OPERATOR_STATIONS}:
        covered = np.zeros(SHIFT_S, dtype=bool)
        for p in people:
            if p["role"] not in ("operator", "relief_operator"):
                continue
            for s in p["timeline"]:
                if s["k"] in ("work", "wait", "fetch") and s.get("station") == st:
                    covered[int(s["s"]):int(min(s["e"], SHIFT_S))] = True
        coverage[st] = round(float(covered.mean()), 3)
    assert min(coverage.values()) > 0.85, coverage
    return coverage


def sensors(df: pd.DataFrame, expect_fault: bool) -> None:
    assert not df.isna().any().any()
    assert (df["vibration_rms_mm_s"] > -0.5).all()
    m5 = df[df["machine_id"] == "M05"].set_index("t_s")
    if expect_fault:
        assert m5["fault_label"].sum() > 600, "fault label too short"
        base = m5.loc[:3 * 3600 - 1, "vibration_rms_mm_s"].mean()
        late = m5.loc[int(5.0 * 3600):int(5.1 * 3600), "vibration_rms_mm_s"].mean()
        assert late > 1.6 * base, (base, late)
        assert (m5.loc[m5.index > 7 * 3600, "degradation"] == 0).all()
    else:
        assert m5["fault_label"].sum() == 0
