#!/usr/bin/env python3
"""Check the optional LLM layer on a machine that can run a local model.

  ollama pull qwen2.5:14b-instruct            # or llama3.1:8b, qwen2.5:32b-instruct if you have the RAM
  LLM_MODE=assist OLLAMA_MODEL=qwen2.5:14b-instruct python3 brain/scripts/llm_check.py [--all]

Runs the demo questions through the brain in assist mode (mock engine unless SIM_MODE=live is set) and prints, per question:
the model's reply, whether the grounding guard accepted it, and the latency. A reply the guard rejects falls back to the
deterministic answer, so nothing ungrounded is ever shown. Aim for guard acceptance >= 90 percent; if lower, try a bigger
model or read the 'guard' reasons (number not in the facts, unknown source, disclaimer language).
"""
import json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from app import config  # noqa: E402
from app.agent import Brain  # noqa: E402


def main():
    if config.LLM_MODE != "assist":
        sys.exit("Set LLM_MODE=assist (and OLLAMA_MODEL=<model> or leave it as auto).")
    spec = json.load(open(HERE.parent / "eval" / "demo_questions.json"))
    qs = [(g["session"], q["q"]) for g in spec["groups"] for q in g["questions"]]
    if "--all" not in sys.argv:
        qs = qs[::2]
    b = Brain()
    print(f"model: {config.pick_model()}  engine: {b.sim.mode}  questions: {len(qs)}\n")
    used = 0
    for sid, q in qs:
        t = time.time()
        r = b.ask(q, session_id="llmcheck-" + sid)
        info = r["meta"].get("llm") or {}
        used += bool(info.get("used"))
        print(f"Q: {q}\n   {'LLM  ' if info.get('used') else 'RULES'} guard={info.get('guard')}  {time.time() - t:.1f}s")
        for line in r["answer"].split("\n")[:6]:
            print("   | " + line)
        print()
    print(f"LLM replies accepted by the guard: {used}/{len(qs)}")


if __name__ == "__main__":
    main()
