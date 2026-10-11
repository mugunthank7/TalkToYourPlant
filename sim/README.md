# Plant simulation engine (SimPy)

A discrete-event model of Voltline EV Works. It is the source of truth for plant state, KPIs and what-if
answers; the 3D twin and the LLM tools read from it.

```bash
cd sim
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn plantsim.api:app --port 8000        # API + WebSocket
.venv/bin/python -m pytest tests -q                    # 7 tests, about 1 minute
```
Open the twin with `http://localhost:5180/?sim=ws://localhost:8000/ws` (or press the "SimPy off" button in the top bar).

## What is modelled
- Car bodies flow S04 -> S05 -> S06 -> S07 -> S09 on a paced line (takt 90 s). Each station is a SimPy `Resource`
  with a machine that can fail **mid-job**. Each segment holds two cars, so a stopped station really starves
  downstream and blocks upstream. Strict pitch: a slot with no car released is lost production.
- Supply: coil yard -> press -> stamped-parts buffer; battery line -> pack buffer; the pack and the body meet at S09.
- Weld robot 2 follows the scripted bearing-wear curve (same parameters as the data generator): watch alert, then a
  critical alert at 2x vibration (about 52 minutes of remaining useful life), and the robot slows the belt as it wears.
  If nobody acts it seizes and needs the 90-minute emergency repair.
- A technician and work orders: dispatch delay, walk bay -> spares -> machine, repair, walk back.
- Micro-stops per machine, optional random breakdowns (Weibull), scrap that rises with wear.
- All randomness uses named streams, so the same seed replays identically until something changes.
  That is what makes what-if branching exact: replay to now, apply the change, run to the end of the shift.

## Calibration
`MICRO_X = 4.5` (micro-stop frequency) makes everyday OEE match the plant data. Against the generated scenario
summaries (mean of 3 seeds, tolerance 8 percent, enforced by the tests):

| Scenario | Engine | Data |
|---|---:|---:|
| ideal | 320 | 320 |
| healthy_realistic | about 288 | 287 |
| hero_timely_repair | about 269 | 264 |
| hero_delayed_repair | about 263 | 251 |
| hero_ignored | about 224 | 218 |

## API
| Endpoint | What |
|---|---|
| `GET /state` | Snapshot: stations (run, starved, blocked, repair, fault, micro), machines + sensors, belt + cars, buffers, KPIs, alerts, work orders, bottleneck |
| `GET /station/{id}`, `GET /machine/{id}`, `GET /kpis`, `GET /events`, `GET /workorders`, `GET /series` | Slices |
| `POST /control` | `{action: play, pause, seek {t}, reset {seed, shift}, clear_faults, policy {hero_policy, hero_delay_s}, speed}` |
| `POST /fault` | `{machine, repair_minutes?}` breaks a machine now |
| `POST /scenario` | `{changes: [...]}` what-if from now vs doing nothing. Ops: `keep_running {hours}`, `dispatch_now`, `add_operator {station}`, `remove_operator {station}`, `inject_fault {machine, repair_min}`, `set_takt {takt_s}`, `schedule_pm {machine, minutes}` |
| `WS /ws` | 10 Hz `state` messages plus `alert`, `fault`, `work_order`, `dispatched`, `repair_start`, `repair_done` events. Send `{"type":"control",...}` or `{"type":"ui_event","event":"inject_fault","machine_id":"M03"}` |
| `GET /tools`, `POST /tools/{name}` | LLM tools with JSON schemas: `get_plant_state`, `get_station`, `get_machine_health`, `get_kpis`, `get_diagnosis_context`, `run_what_if`, `create_work_order`, `inject_fault` |

`get_diagnosis_context` bundles sensor trends, plain-language evidence, affected stations, open work orders, candidate
failure modes from the knowledge catalogue, and what happens if we act now versus wait two hours (with the dollar difference).

Example:
```bash
curl -s -X POST localhost:8000/control -H 'content-type: application/json' -d '{"action":"seek","t":18700}'
curl -s -X POST localhost:8000/tools/run_what_if -H 'content-type: application/json' \
  -d '{"changes":[{"op":"keep_running","hours":2}]}' | python3 -m json.tool | head -30
```
