"""Synthetic employees and the task catalogue."""
from __future__ import annotations

import numpy as np
import pandas as pd

FIRST = ["Aisha", "Mateo", "Priya", "Jamal", "Chen", "Sofia", "Omar", "Hannah", "Diego", "Mei",
         "Tariq", "Elena", "Kofi", "Ingrid", "Ravi", "Lucia", "Noah", "Yuki", "Fatima", "Liam",
         "Zara", "Andre", "Nadia", "Samir"]
LAST = ["Alvarez", "Nguyen", "Okafor", "Patel", "Kim", "Rossi", "Haddad", "Johansson", "Silva",
        "Tanaka", "Mensah", "Novak", "Rahman", "Cohen", "Dubois", "Singh", "Garcia", "Walker"]

# Operators by home station. S06 has two people (hero cell), plus one relief operator.
OPERATOR_STATIONS = ["S02", "S04", "S05", "S06", "S06", "S07", "S08", "S09"]
SHIFTS = {"A": "06:00", "B": "14:00"}

# task_id, name, station, role, mean_s, std_s, trigger, period_s
TASKS = [
    ("T-S02-LOAD", "Load blanks and unload stamped part", "S02", "operator", 70, 10, "cycle", 90),
    ("T-S04-LOAD", "Load underbody parts into framing fixture", "S04", "operator", 85, 12, "cycle", 90),
    ("T-S05-WELD", "Load body, start weld program, unload", "S05", "operator", 70, 9, "cycle", 90),
    ("T-S06-WELD", "Load body, start weld program, unload", "S06", "operator", 70, 9, "cycle", 90),
    ("T-S07-CHECK", "Visual weld and gap check", "S07", "operator", 55, 8, "cycle", 90),
    ("T-S08-STACK", "Stack battery module", "S08", "operator", 80, 12, "cycle", 90),
    ("T-S09-SEAL", "Seal pack lid and run leak test", "S09", "operator", 75, 10, "cycle", 90),
    ("T-FETCH-PARTS", "Fetch part rack from buffer", "S03", "operator", 40, 8, "every_n_cycles", 12),
    ("T-FETCH-TIPS", "Fetch fresh electrode tips from spare cage", "S12", "operator", 45, 8, "every_n_cycles", 20),
    ("T-QA-SAMPLE", "Quality sampling at inspection gate", "S07", "inspector", 300, 40, "periodic", 1800),
    ("T-QA-AUDIT", "Audit weld cell", "S05", "inspector", 120, 20, "periodic", 1800),
    ("T-SUP-WALK", "Line walk, observe each station", "S04", "supervisor", 60, 10, "periodic", 2700),
    ("T-PM-CHECK", "Preventive maintenance check (lube, bolts)", "S10", "technician", 420, 60, "periodic", 7200),
    ("T-REPAIR-BEARING", "Replace joint bearing", "S06", "technician", 1500, 200, "event", 0),
    ("T-BREAK", "Short break", "S11", "any", 900, 0, "scheduled", 0),
    ("T-LUNCH", "Lunch", "S11", "any", 1500, 0, "scheduled", 0),
]

TASK_BY_STATION = {t[2]: t[0] for t in TASKS if t[3] == "operator" and t[6] == "cycle"}


def tasks_frame() -> pd.DataFrame:
    return pd.DataFrame(TASKS, columns=[
        "task_id", "name", "station", "role_required", "mean_s", "std_s", "trigger", "period_s_or_n"])


def make_roster(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    names = [(f, l) for f in FIRST for l in LAST]
    order = rng.permutation(len(names))
    n = 0

    def person(shift: str, role: str, tag: str, home: str, skill: int, certified: list[str]) -> dict:
        nonlocal n
        f, l = names[order[n]]
        n += 1
        # Higher skill is a little faster; stays within roughly +-15 percent.
        speed = float(np.exp(rng.normal(-0.05 * (skill - 3), 0.05)))
        return {
            "employee_id": f"{shift}-{tag}",
            "name": f"{f} {l}",
            "role": role,
            "shift": shift,
            "shift_start": SHIFTS[shift],
            "home_station": home,
            "skill_level": skill,
            "experience_years": int(np.clip(rng.normal(2 + 2.2 * skill, 2), 0, 30)),
            "certified_stations": ",".join(certified),
            "task_speed_factor": round(speed, 3),
            "walk_speed_mps": round(float(np.clip(rng.normal(1.3, 0.1), 1.0, 1.6)), 2),
        }

    for shift in SHIFTS:
        for i, st in enumerate(OPERATOR_STATIONS, start=1):
            rows.append(person(shift, "operator", f"OP{i:02d}", st, int(rng.integers(2, 5)), [st]))
        rows.append(person(shift, "relief_operator", "OP09", "S11", int(rng.integers(4, 6)),
                           sorted(set(OPERATOR_STATIONS))))
        rows.append(person(shift, "inspector", "QA01", "S07", int(rng.integers(3, 6)), ["S05", "S06", "S07"]))
        rows.append(person(shift, "supervisor", "SUP01", "S11", 5, ["S04", "S05", "S06", "S07"]))
        rows.append(person(shift, "technician", "TECH01", "S10", int(rng.integers(4, 6)), ["S05", "S06", "S04", "S07"]))
    return pd.DataFrame(rows)
