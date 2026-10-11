import statistics as st

import pytest
from fastapi.testclient import TestClient

from plantsim import PlantSim, Params, config as C
from plantsim.api import app, live
from plantsim.scenarios import what_if

IDEAL = dict(ideal=True, hero_fault=False, micro_stops=False, scrap_base=0)
SCEN = {"ideal": IDEAL, "healthy_realistic": dict(hero_fault=False), "hero_timely_repair": dict(hero_policy="timely"),
        "hero_delayed_repair": dict(hero_policy="delayed", hero_delay_s=2400), "hero_ignored": dict(hero_policy="ignored")}


def units(**kw) -> float:
    return st.mean(PlantSim(Params(seed=s, **kw)).run().kpis()["units"] for s in (1, 2, 3))


def test_ideal_is_the_ceiling():
    assert PlantSim(Params(**IDEAL)).run().kpis()["units"] == 320


def test_scenarios_rank_and_match_plant_data():
    target = C.scenario_summary()
    got = {k: units(**kw) for k, kw in SCEN.items()}
    assert got["ideal"] > got["healthy_realistic"] > got["hero_timely_repair"] > got["hero_delayed_repair"] > got["hero_ignored"]
    for k, v in got.items():
        assert abs(v - target[k]["units"]) / target[k]["units"] < 0.08, (k, v, target[k]["units"])


def test_deterministic_and_replayable():
    a = PlantSim(Params(seed=7)).run().kpis()
    b = PlantSim(Params(seed=7)).run().kpis()
    assert a == b
    s1 = PlantSim(Params(seed=7)); s1.run_until(10000); s2 = PlantSim(Params(seed=7)); s2.run_until(5000); s2.run_until(10000)
    assert s1.completed == s2.completed


def test_alert_matches_data_generator():
    sim = PlantSim(Params()).run()
    crit = [a for a in sim.alerts if a["severity"] == "critical"][0]
    assert abs(crit["t"] - C.hero_events()["t_alert_s"]) < 5
    assert 3000 < crit["rul_s"] < 3300


def test_injected_fault_stops_and_starves_the_line():
    sim = PlantSim(Params(hero_fault=False, injected=[{"machine": "M03", "t0": 3600, "repair_s": 1500}]))
    sim.run_until(3600 + 600)
    from plantsim.snapshot import stations_info
    s = stations_info(sim)
    assert s["S04"]["state"] in ("fault", "repair")
    assert s["S06"]["state"] == "starved"          # downstream starves once the cars in transit run out
    sim.run_until(3600 + 300 + 3000)
    assert sim.machines["M03"].state == "up"
    assert units(hero_fault=False) > PlantSim(Params(hero_fault=False, injected=[{"machine": "M03", "t0": 3600}])).run().kpis()["units"]


def test_waiting_costs_more_than_acting():
    p = Params()
    now = C.hero_events()["t_alert_s"] + 60
    act = what_if(p, [{"op": "dispatch_now"}], now)
    wait = what_if(p, [{"op": "keep_running", "hours": 2}], now)
    assert wait["scenario"]["kpis"]["downtime_cost_usd"] > act["scenario"]["kpis"]["downtime_cost_usd"]
    assert wait["scenario"]["kpis"]["units"] < act["scenario"]["kpis"]["units"]


def test_api_endpoints():
    c = TestClient(app)
    live.control({"action": "reset"})
    assert c.get("/health").json()["ok"]
    c.post("/control", json={"action": "seek", "t": 12400})
    s = c.get("/state").json()
    assert s["t"] == 12400 and "S06" in s["stations"] and s["alerts"]
    assert c.get("/machine/M05").json()["rul_s"] > 0
    an = c.get("/anomaly/M05").json()
    assert an["alert"] and an["contributors"] and an["thresholds"]["critical"] > an["thresholds"]["watch"]
    assert "M05" in c.get("/anomaly").json()["machines"]
    r = c.post("/scenario", json={"changes": [{"op": "keep_running", "hours": 2}]}).json()
    assert r["delta"]["units"] <= 0 and "summary" in r
    tools = {t["name"] for t in c.get("/tools").json()}
    assert {"get_plant_state", "run_what_if", "get_diagnosis_context"} <= tools
    d = c.post("/tools/get_diagnosis_context", json={"machine_id": "M05"}).json()
    assert d["evidence"] and d["decision"]["cost_of_waiting_usd"] > 0 and d["candidate_failure_modes"]
    f = c.post("/fault", json={"machine": "M07"}).json()
    assert f["injected"]["machine"] == "M07"
    live.control({"action": "reset"})


def test_exported_dashboard_matches_live_engine():
    """kpi.json comes from the engine: the 'repaired on alert' scenario is exactly the live run (same seed)."""
    import json
    k = json.loads((C.OUT / "kpi.json").read_text())
    s = PlantSim(Params(detector="hero")).run()
    ex = k["summary"]["hero_timely_repair"]
    kp = s.kpis()
    assert ex["units"] == kp["units"] and abs(ex["downtime_min"] - kp["downtime_min"]) < 0.1
    assert k["series"]["hero_timely_repair"]["cum_units"][-1] == kp["units"]
    assert k["summary"]["ideal"]["units"] == 320 and k["summary"]["hero_ignored"]["units"] < ex["units"]


def test_cars_on_the_belt_never_overlap():
    """Cars queued at a station used to share its position; bodies are 4.6 m long, so centres must be well apart (6.5 m)."""
    from plantsim.snapshot import cars
    s = PlantSim(Params(detector=False))
    for t in range(1200, 28800, 1500):
        s.run_until(t)
        d = sorted(c["d_m"] for c in cars(s))
        assert all(b - a >= 6.5 for a, b in zip(d, d[1:])), (t, d)
        assert len({c["k"] % 12 for c in cars(s)}) == len(cars(s))        # unique render slots in the twin


def test_cars_never_overtake():
    from plantsim.snapshot import cars
    s = PlantSim(Params(detector=False))
    prev = {}
    for t in range(1000, 14000, 20):
        s.run_until(t)
        pos = {c["k"]: c["d_m"] for c in cars(s)}
        for a in pos:
            for b in pos:
                if a < b and a in prev and b in prev:
                    assert not (prev[a] > prev[b] and pos[a] < pos[b]), (t, a, b)   # the older car stays ahead
        assert all(0 <= c["build"] <= 1 for c in cars(s))
        prev = pos
