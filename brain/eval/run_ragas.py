#!/usr/bin/env python3
"""RAGAS analysis of the brain's answers (LLM-judged), run in the isolated venv:

  python3 -m venv brain/.venv-ragas
  brain/.venv-ragas/bin/pip install ragas==0.4.3 google-genai
  brain/.venv-ragas/bin/pip install "langchain-community==0.3.31" "langchain-core<1.0" "langchain<1.0" "langchain-openai<1.0"
  python3 brain/eval/run_eval.py                       # produces results_latest.json (with contexts)
  brain/.venv-ragas/bin/python brain/eval/run_ragas.py --every 2

Judge = MODEL_LITE through Gemini's OpenAI-compatible endpoint, throttled by the same rate
limiter as the agent (RPM/RPD/TPM). Contexts = the tool outputs the agent actually saw.
Metrics: faithfulness, answer_relevancy, context_precision, context_recall.
"""
import argparse, asyncio, json, statistics, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from app import config, ratelimit  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=2, help="evaluate every Nth question (budget control)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--metrics", default="faithfulness,answer_relevancy,context_precision,context_recall")
    a = ap.parse_args()
    want = set(a.metrics.split(","))

    from openai import AsyncOpenAI
    from google import genai
    from ragas.llms import llm_factory
    from ragas.embeddings import GoogleEmbeddings
    from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall

    async def throttled(role, fn, est, *a, **kw):
        """Async wrapper: shared rate limiter + backoff on 429/5xx/402."""
        import random
        for attempt in range(5):
            await asyncio.to_thread(ratelimit.limiter(role).acquire, est)
            try:
                return await fn(*a, **kw)
            except ratelimit.DailyBudgetExceeded:
                raise
            except Exception as e:  # noqa: BLE001
                if attempt == 4 or not ratelimit._retryable(e) and "402" not in str(e):
                    raise
                d = ratelimit._retry_after(e) or (15.0 * (attempt + 1) if "402" in str(e) else min(60, 2.0 ** attempt))
                await asyncio.sleep(d + random.uniform(0, 0.5))

    oa = AsyncOpenAI(api_key=config.API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    _create = oa.chat.completions.create

    async def limited(*args, **kw):
        est = sum(len(str(m.get("content", ""))) for m in kw.get("messages", [])) // 3
        return await throttled("lite", _create, est, *args, **kw)
    oa.chat.completions.create = limited
    llm = llm_factory(config.MODELS["lite"], provider="openai", client=oa)

    gclient = genai.Client(api_key=config.API_KEY)
    _aembed = gclient.aio.models.embed_content

    async def aembed(*x, **k):
        return await throttled("embed", _aembed, 400, *x, **k)
    gclient.aio.models.embed_content = aembed
    emb = GoogleEmbeddings(client=gclient, model=config.MODELS["embed"])

    metrics = {}
    if "faithfulness" in want:
        metrics["faithfulness"] = Faithfulness(llm=llm)
    if "answer_relevancy" in want:
        metrics["answer_relevancy"] = AnswerRelevancy(llm=llm, embeddings=emb)
    if "context_precision" in want:
        metrics["context_precision"] = ContextPrecision(llm=llm)
    if "context_recall" in want:
        metrics["context_recall"] = ContextRecall(llm=llm)

    qs = {q["id"]: q for q in (json.loads(l) for l in open(HERE / "questions.jsonl"))}
    res = json.load(open(HERE / "results_latest.json"))["answers"]
    rows = [r for i, r in enumerate(res) if i % a.every == 0 and r.get("contexts_text")]
    if a.limit:
        rows = rows[:a.limit]
    if not rows:
        sys.exit("No rows with contexts_text. Re-run brain/eval/run_eval.py first (it now stores contexts).")
    print(f"RAGAS on {len(rows)} questions, metrics={list(metrics)}, judge={config.MODELS['lite']}")

    async def score_one(r):
        q = qs[r["id"]]
        ctx = r["contexts_text"]
        kw = {"user_input": q["question"], "response": r["answer"], "retrieved_contexts": ctx, "reference": q["reference"]}
        out = {}
        for name, m in metrics.items():
            try:
                if name == "faithfulness":
                    v = await m.ascore(user_input=kw["user_input"], response=kw["response"], retrieved_contexts=ctx)
                elif name == "answer_relevancy":
                    v = await m.ascore(user_input=kw["user_input"], response=kw["response"])
                else:
                    v = await m.ascore(user_input=kw["user_input"], retrieved_contexts=ctx, reference=kw["reference"])
                out[name] = None if v.value is None else float(v.value)
            except Exception as e:  # noqa: BLE001
                out[name] = None
                out[name + "_error"] = f"{type(e).__name__}: {str(e)[:140]}"
        return {"id": r["id"], "category": r["category"], **out}

    async def run():
        scored = []
        for r in rows:
            t = time.time()
            s = await score_one(r)
            scored.append(s)
            show = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items() if not k.endswith("_error") and k not in ("id", "category")}
            print(f"{s['id']} [{s['category']}] {show} ({time.time()-t:.0f}s)", flush=True)
        return scored

    scored = asyncio.run(run())
    print("\nMEAN SCORES")
    summary = {}
    for name in metrics:
        vals = [s[name] for s in scored if isinstance(s.get(name), float)]
        summary[name] = {"mean": round(statistics.mean(vals), 3) if vals else None, "n": len(vals), "of": len(scored)}
        print(f"  {name:18s} {summary[name]['mean']}  (n={len(vals)}/{len(scored)})")
    cats = {}
    for s in scored:
        for name in metrics:
            if isinstance(s.get(name), float):
                cats.setdefault(s["category"], {}).setdefault(name, []).append(s[name])
    print("\nBY CATEGORY (mean)")
    by_cat = {c: {n: round(statistics.mean(v), 2) for n, v in d.items()} for c, d in cats.items()}
    for c, d in sorted(by_cat.items()):
        print(f"  {c:16s} {d}")
    (HERE / "ragas_latest.json").write_text(json.dumps({"judge": config.MODELS["lite"], "summary": summary,
                                                        "by_category": by_cat, "rows": scored}, indent=1))
    print("wrote brain/eval/ragas_latest.json")


if __name__ == "__main__":
    main()
