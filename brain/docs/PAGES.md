# What each page does

| URL | Page | What it does | Who it is for |
|---|---|---|---|
| http://localhost:5180 | **3D twin** (M's app) | Live 3D plant driven by the engine. Top bar: Live 3D and Dashboard tabs, shift, play, speed. **Click a station** to open the brain panel. **Ask your plant** (bottom right) is the chat. Fault card: break any machine and watch the line starve and block. | Everyone, the demo |
| (panel inside the twin) | **Station panel** | For the clicked station: what it does, live state and reason, each machine's sensors/alert/RUL/SHAP, a structured card (what happened, impact, do now, who to page, part, procedure), "Ask the local LLM for a plan", "Simulate failure here", and the failure modes that can be simulated. Refreshes every 4 s. | Operator, technician |
| http://localhost:8100 | **Brain chat** | Plain chat page for the brain (same answers as the twin chat). Shows highlighted machines, graph path chips, citations, model and latency. | Testing, fallback if the twin is down |
| http://localhost:8300 | **Integration monitor** | Polls the engine every 2 s: OEE, throughput, M05 vibration and RUL, downtime cost with event markers; a feed of what changed (alerts, machine states, stopped stations, work orders); the brain's automatic answer to each new alert or fault with latency; Inject fault / Clear faults / Ask buttons; baseline-versus-now impact table. | You and M while building and in the demo |
| http://localhost:8200 | **Run dashboard** | Starts, stops and shows the eval, RAGAS and embedding-experiment jobs (progress, ETA, logs, partial metrics, per-question results, embedding comparison). | Developers |
| http://localhost:8000 | **Engine API** (M's) | SimPy plant engine: `/state`, `/tools/*`, `/scenario`, `/fault`, `/control`, `/ws`. No page; see `sim/README.md`. | The brain and the twin |

Start everything with `brain/scripts/start_all.sh`, stop with `brain/scripts/stop_all.sh`.
