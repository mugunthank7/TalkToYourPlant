#!/usr/bin/env python3
"""RAGAS *library* run with a LOCAL judge (Ollama). NOT USED: on this 8 GB M2 the first metric
stalled for 8+ minutes at 0% CPU with qwen2.5:7b (instructor tool-calling over Ollama), so the
project uses run_ragas.py (same metric definitions, direct local calls). Kept for reference.

  python3 -m venv brain/.venv-ragas && brain/.venv-ragas/bin/pip install ragas==0.4.3
  brain/.venv-ragas/bin/pip install "langchain-community==0.3.31" "langchain-core<1.0" "langchain<1.0" "langchain-openai<1.0"
  ollama create qwen-judge -f brain/eval/Modelfile.judge
  python3 brain/eval/run_eval.py                              # writes results_latest.json with contexts
  brain/.venv-ragas/bin/python brain/eval/run_ragas.py --every 2

Metrics: faithfulness, answer_relevancy, context_precision, context_recall.
Contexts are the tool outputs the brain saw (capped per context for the small judge).
"""
import argparse, asyncio, json, statistics, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from app import config  # noqa: E402
from status import Status  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=2)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ctx-chars", type=int, default=900)
    ap.add_argument("--max-ctx", type=int, default=6)
    ap.add_argument("--metrics", default="faithfulness,answer_relevancy,context_precision,context_recall")
    ap.add_argument("--judge", default=config.get("JUDGE_MODEL", "qwen-judge"))
    ap.add_argument("--embed", default="nomic-embed-text")
    a = ap.parse_args()
    want = a.metrics.split(",")

    st = Status("ragas")
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.embeddings import embedding_factory
    from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall

    oa = AsyncOpenAI(api_key="ollama", base_url=config.OLLAMA_URL.rstrip("/") + "/v1", timeout=600, max_retries=1)
    llm = llm_factory(a.judge, provider="openai", client=oa)
    metrics = {}
    if "faithfulness" in want:
        metrics["faithfulness"] = Faithfulness(llm=llm)
    if "answer_relevancy" in want:
        emb = embedding_factory("openai", model=a.embed, client=oa)
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
        st.finish("failed", error="no rows with contexts_text; run run_eval.py first")
        sys.exit("No rows with contexts_text. Run brain/eval/run_eval.py first.")
    st.update(progress={"done": 0, "total": len(rows)}, judge=a.judge, embed=a.embed, metrics_list=list(metrics))
    st.log(f"RAGAS {len(rows)} questions judge={a.judge} metrics={list(metrics)}")

    async def one(r):
        q = qs[r["id"]]
        ctx = [c[:a.ctx_chars] for c in r["contexts_text"][:a.max_ctx]]
        out = {"id": r["id"], "category": r["category"], "question": q["question"]}
        for name, m in metrics.items():
            st.update(current=f"{r['id']} {name}")
            t = time.time()
            try:
                if name == "faithfulness":
                    v = await m.ascore(user_input=q["question"], response=r["answer"], retrieved_contexts=ctx)
                elif name == "answer_relevancy":
                    v = await m.ascore(user_input=q["question"], response=r["answer"])
                else:
                    v = await m.ascore(user_input=q["question"], retrieved_contexts=ctx, reference=q["reference"])
                out[name] = None if v.value is None else round(float(v.value), 3)
            except Exception as e:  # noqa: BLE001
                out[name] = None
                out[name + "_error"] = f"{type(e).__name__}: {str(e)[:160]}"
            st.log(f"{r['id']} {name} = {out[name]} ({time.time()-t:.0f}s)")
        return out

    async def run():
        scored = []
        for r in rows:
            s = await one(r)
            scored.append(s)
            st.item(**s)
            means = {}
            for n in metrics:
                vals = [x[n] for x in scored if isinstance(x.get(n), float)]
                means[n] = {"mean": round(statistics.mean(vals), 3) if vals else None, "n": len(vals), "of": len(scored)}
            st.update(metrics=means)
            (HERE / "ragas_latest.json").write_text(json.dumps({"judge": a.judge, "embed": a.embed, "summary": means,
                                                                "rows": scored, "partial": len(scored) < len(rows)}, indent=1))
        return scored

    try:
        asyncio.run(run())
        st.finish("done")
    except Exception as e:  # noqa: BLE001
        st.finish("failed", error=f"{type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    main()
