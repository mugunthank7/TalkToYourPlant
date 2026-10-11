#!/usr/bin/env python3
"""RAGAS metrics with a LOCAL judge (Ollama) and LOCAL embeddings. No API, no key, stdlib + numpy.

Re-implements the four RAGAS metrics with the same definitions (the ragas library hung on this
8 GB machine with a local judge, see run_ragas_lib.py):
  faithfulness       = supported statements / statements in the answer         (2 judge calls)
  answer_relevancy   = mean cosine(question, 3 questions generated from answer) (1 call + embeddings)
  context_precision  = average precision of useful contexts vs the reference    (1 call)
  context_recall     = reference sentences attributable to the contexts         (1 call)

  python3 brain/eval/run_eval.py          # writes results_latest.json with contexts
  python3 brain/eval/run_ragas.py            # all 40 questions, about 1 min each with phi3:3.8b
"""
import argparse, json, re, statistics, sys, time, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from app import config  # noqa: E402
from status import Status  # noqa: E402

JUDGE = config.get("JUDGE_MODEL", "phi3:3.8b")


def chat(prompt, num_predict=420, system="You are a strict evaluation judge. Output valid JSON only."):
    body = {"model": JUDGE, "stream": False, "format": "json", "keep_alive": "30m",
            "options": {"temperature": 0, "num_ctx": 4096, "num_predict": num_predict},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]}
    for attempt in range(2):
        r = urllib.request.Request(config.OLLAMA_URL.rstrip("/") + "/api/chat", data=json.dumps(body).encode(),
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=420) as resp:
            txt = json.loads(resp.read().decode())["message"]["content"]
        try:
            return json.loads(txt)
        except Exception:
            body["messages"][-1]["content"] = prompt + "\nReturn ONLY a JSON object, nothing else."
    raise ValueError("judge returned invalid JSON")


def ctx_block(ctxs):
    return "\n".join(f"[{i+1}] {c}" for i, c in enumerate(ctxs))


def faithfulness(question, answer, ctxs):
    clean = re.sub(r"\[[A-Za-z0-9_.:\-]+\]", "", answer)
    s = chat(f"Break the ANSWER into short, self-contained factual statements (max 10). Skip greetings and advice words.\n"
             f"QUESTION: {question}\nANSWER: {clean}\n"
             'Return {"statements": ["...", "..."]}', 350).get("statements", [])
    s = [x for x in s if isinstance(x, str) and x.strip()][:10]
    if not s:
        return None
    v = chat("Decide for each statement whether it can be directly inferred from the CONTEXT. "
             "Answer false if the context does not contain it.\nCONTEXT:\n" + ctx_block(ctxs)
             + "\nSTATEMENTS:\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(s))
             + '\nReturn {"verdicts": [{"n": 1, "supported": true}, ...]}', 300).get("verdicts", [])
    ok = {x.get("n") for x in v if isinstance(x, dict) and x.get("supported") is True and isinstance(x.get("n"), int)}
    return min(1.0, len([n for n in ok if 1 <= n <= len(s)]) / len(s))


def answer_relevancy(question, answer, emb):
    clean = re.sub(r"\[[A-Za-z0-9_.:\-]+\]", "", answer)
    qs = chat(f"Write 3 different questions to which the following ANSWER is a good response.\nANSWER: {clean[:900]}\n"
              'Return {"questions": ["...", "...", "..."]}', 200).get("questions", [])
    qs = [q for q in qs if isinstance(q, str) and q.strip()][:3]
    if not qs:
        return None
    import numpy as np
    v = emb.embed([question] + qs, kind="query")
    return float(np.mean(v[1:] @ v[0]))


def context_precision(question, reference, ctxs):
    v = chat(f"QUESTION: {question}\nREFERENCE ANSWER: {reference}\nFor each numbered context decide if it is useful to "
             "arrive at the reference answer.\nCONTEXTS:\n" + ctx_block(ctxs)
             + '\nReturn {"verdicts": [{"n": 1, "useful": true}, ...]}', 250).get("verdicts", [])
    use = {}
    for x in v:
        if isinstance(x, dict) and isinstance(x.get("n"), int):
            use[x["n"]] = x.get("useful") is True
    flags = [use.get(i + 1, False) for i in range(len(ctxs))]
    if not any(flags):
        return 0.0
    hits, tot = 0, 0.0
    for k, f in enumerate(flags, 1):
        if f:
            hits += 1
            tot += hits / k
    return tot / hits


def context_recall(reference, ctxs):
    sents = [x.strip() for x in re.split(r"(?<=[.!?;])\s+", reference) if x.strip()]
    v = chat("For each REFERENCE sentence decide if it can be attributed to the CONTEXT.\nCONTEXT:\n" + ctx_block(ctxs)
             + "\nREFERENCE SENTENCES:\n" + "\n".join(f"{i+1}. {x}" for i, x in enumerate(sents))
             + '\nReturn {"verdicts": [{"n": 1, "attributed": true}, ...]}', 250).get("verdicts", [])
    ok = {x.get("n") for x in v if isinstance(x, dict) and x.get("attributed") is True and isinstance(x.get("n"), int)}
    return min(1.0, len([n for n in ok if 1 <= n <= len(sents)]) / len(sents)) if sents else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ctx-chars", type=int, default=1400)
    ap.add_argument("--max-ctx", type=int, default=6)
    ap.add_argument("--ids", default="", help="comma list of question ids to (re)score and merge into ragas_latest.json")
    ap.add_argument("--metrics", default="faithfulness,answer_relevancy,context_precision,context_recall")
    a = ap.parse_args()
    want = a.metrics.split(",")
    st = Status("ragas")
    qs = {q["id"]: q for q in (json.loads(l) for l in open(HERE / "questions.jsonl"))}
    res = json.load(open(HERE / "results_latest.json"))["answers"]
    rows = [r for i, r in enumerate(res) if i % a.every == 0 and r.get("contexts_text")]
    prev = {}
    if a.ids:
        want_ids = set(a.ids.split(","))
        rows = [r for r in res if r["id"] in want_ids and r.get("contexts_text")]
        try:
            prev = {x["id"]: x for x in json.load(open(HERE / "ragas_latest.json"))["rows"]}
        except Exception:
            prev = {}
    if a.limit:
        rows = rows[:a.limit]
    if not rows:
        st.finish("failed", error="no rows with contexts_text; run run_eval.py first")
        sys.exit("run brain/eval/run_eval.py first")
    emb = None
    if "answer_relevancy" in want:
        from app.index import Embedder
        emb = Embedder()
    st.update(progress={"done": 0, "total": len(rows)}, judge=JUDGE, embed=config.LOCAL_EMBED_MODEL, metrics_list=want)
    st.log(f"RAGAS-definitions, local judge {JUDGE}, {len(rows)} questions, metrics {want}")
    scored = []
    for r in rows:
        q = qs[r["id"]]
        ctx = [c[:a.ctx_chars] for c in r["contexts_text"][:a.max_ctx]]
        out = {"id": r["id"], "category": r["category"], "question": q["question"]}
        for name in want:
            st.update(current=f"{r['id']} {name}")
            t = time.time()
            try:
                if name == "faithfulness":
                    v = faithfulness(q["question"], r["answer"], ctx)
                elif name == "answer_relevancy":
                    v = answer_relevancy(q["question"], r["answer"], emb)
                elif name == "context_precision":
                    v = context_precision(q["question"], q["reference"], ctx)
                else:
                    v = context_recall(q["reference"], ctx)
                out[name] = None if v is None else round(float(v), 3)
            except Exception as e:  # noqa: BLE001
                out[name] = None
                out[name + "_error"] = f"{type(e).__name__}: {str(e)[:140]}"
            st.log(f"{r['id']} {name} = {out[name]} ({time.time()-t:.0f}s)")
        scored.append(out)
        st.item(**out)
        allrows = list({**prev, **{x["id"]: x for x in scored}}.values()) if a.ids else scored
        allrows.sort(key=lambda x: x["id"])
        means = {}
        for n in want:
            vals = [x[n] for x in allrows if isinstance(x.get(n), float)]
            means[n] = {"mean": round(statistics.mean(vals), 3) if vals else None, "n": len(vals), "of": len(allrows)}
        st.update(metrics=means)
        (HERE / "ragas_latest.json").write_text(json.dumps(
            {"judge": JUDGE, "embed": config.LOCAL_EMBED_MODEL, "impl": "ragas definitions, local judge",
             "summary": means, "rows": allrows, "partial": (not a.ids) and len(scored) < len(rows)}, indent=1))
    st.finish("done")


if __name__ == "__main__":
    main()
