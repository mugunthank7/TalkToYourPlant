# brain/

Knowledge base, answer engine, click-a-station briefing and run tooling for Talk to Your Plant (the "T" side).

Start here: [`docs/HANDOFF.md`](docs/HANDOFF.md) (what changed, how to run, what is open).
Then: [`docs/BRAIN.md`](docs/BRAIN.md) (architecture, API, answer format), [`docs/PAGES.md`](docs/PAGES.md) (what each page does), [`docs/DEMO_QUESTIONS.md`](docs/DEMO_QUESTIONS.md) (18 verified demo questions).

```
app/       graph, hybrid retrieval, agent (intent router + cards), stations, sim adapter, chat API, dashboard, monitor
data/      keyed dataset builder, crosswalks, station knowledge; out/ is the generated, committed dataset
eval/      40 eval questions, demo questions, embedding experiment, RAGAS, run_eval, demo_check
scripts/   start_all.sh, stop_all.sh
ui/        brain chat page, run dashboard, integration monitor
tests/     graph and index tests
```
Run: `brain/scripts/start_all.sh`, check: `python3 brain/eval/demo_check.py --reset`.
