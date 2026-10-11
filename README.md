# Talk to Your Plant: Digital Twin

A live 3D digital twin of a fictional EV assembly plant, with animated machines and people. A simulation engine drives it, and an AI copilot (LLM + knowledge-graph RAG) lets you ask what is wrong, why, and what happens if something changes.

Status: data layer done, 3D next. Teammate integration notes: [docs/FOR_TEAMMATE.md](docs/FOR_TEAMMATE.md). See [docs/STATIONS.md](docs/STATIONS.md), [docs/ASSETS.md](docs/ASSETS.md), [DECISIONS.md](DECISIONS.md) and [CLAUDE.md](CLAUDE.md).

## System flow

![System flow](docs/img/system-flow.png)

Blue is the twin and simulation side (this repo). Green is the knowledge and LLM side. Grey is shared. Editable source: [system-flow.svg](docs/img/system-flow.svg).

What is new versus the first idea: the simulation engine sits at the center and produces everything the twin shows, and the LLM can both explain faults and run what-if scenarios. The work order loops back into the simulation, so a technician agent walks to the machine and the fault clears.

## Hero scenario (90 seconds)

```mermaid
sequenceDiagram
  autonumber
  actor U as User or judge
  participant S as Simulation engine
  participant A as Anomaly detection
  participant T as Live 3D twin
  participant L as LLM brain
  participant K as Knowledge base

  S->>T: Line runs, people walk, live KPIs
  U->>S: Inject fault on weld robot 2
  S->>A: Vibration and current drift up
  A->>T: Robot glows red, SHAP heatmap
  A->>L: Alert with top signals
  U->>L: "What's wrong with weld robot 2?"
  L->>K: Symptom to cause to repair to spare part
  K-->>L: Bearing wear, procedure, part in stock
  L->>T: Animate graph path on the machines
  L-->>U: Spoken answer
  U->>L: "What if we keep running 2 more hours?"
  L->>S: Run what-if scenario
  S-->>L: Throughput and downtime forecast
  L-->>U: Spoken comparison
  L->>S: Create work order
  S->>T: Technician walks to the robot and repairs it
  S->>T: Robot returns to green, KPIs recover
```

## Run it

```bash
cd data && pip install -r requirements.txt && python -m plantdata --seed 42 --out out --copy-to ../twin/public/data
cd ../twin && npm install && npm run dev   # http://localhost:5180
```

## Credits

Third-party assets are listed with licences in [docs/ASSETS.md](docs/ASSETS.md).
