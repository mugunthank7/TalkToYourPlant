#!/usr/bin/env python3
"""Compare local embedding models for the plant RAG (dense / BM25 / hybrid).

Query sets: 'gold' = 23 data-derived questions with a machine scope; 'para' = 20 natural
paraphrases without scope (harder). Metrics: hit@6, MRR, index time, dim, query latency.
Usage: python3 brain/eval/embed_experiment.py [--models a,b,c]
"""
import argparse, json, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from app.index import DocIndex, Embedder  # noqa: E402
from status import Status  # noqa: E402

MODELS = [
    ("sentence-transformers/all-MiniLM-L6-v2", "st"),
    ("BAAI/bge-small-en-v1.5", "st"),
    ("intfloat/e5-small-v2", "st"),
    ("sentence-transformers/all-mpnet-base-v2", "st"),
    ("nomic-embed-text", "ollama"),
]


def queries():
    gold = []
    for l in open(HERE / "questions.jsonl"):
        q = json.loads(l)
        if q["gold_sources"]:
            gold.append({"q": q["question"], "gold": q["gold_sources"], "machine": q["machine"], "set": "gold"})
    para = [{**json.loads(l), "machine": None, "set": "para"} for l in open(HERE / "paraphrases.jsonl")]
    return gold + para


def score(ix, qs, mode):
    out = {"gold": [], "para": []}
    t = time.time()
    for q in qs:
        r = ix.search(q["q"], k=6, machine_id=q["machine"], mode=mode)
        ids = [x["source_id"] for x in r]
        rank = next((i + 1 for i, s in enumerate(ids) if s in q["gold"]), None)
        out[q["set"]].append(rank)
    ms = (time.time() - t) / len(qs) * 1000
    res = {}
    for k, v in out.items():
        res[k] = {"hit6": round(sum(1 for r in v if r) / len(v), 3), "mrr": round(sum(1 / r for r in v if r) / len(v), 3), "n": len(v)}
    res["ms_per_query"] = round(ms)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="")
    a = ap.parse_args()
    models = [m for m in MODELS if not a.models or m[0] in a.models.split(",")]
    st = Status("embeddings")
    st.update(progress={"done": 0, "total": len(models)}, items=[], current="starting")
    qs = queries()
    results = []
    for name, kind in models:
        st.update(current=f"embedding corpus with {name}")
        st.log(f"start {name}")
        try:
            t0 = time.time()
            emb = Embedder(name, kind)
            ix = DocIndex(embedder=emb)
            build_s = time.time() - t0
            row = {"model": name, "kind": kind, "dim": int(ix.vecs.shape[1]), "build_s": round(build_s, 1),
                   "embedded_now": ix.n_embedded_now,
                   "dense": score(ix, qs, "dense"), "bm25": score(ix, qs, "bm25"), "hybrid": score(ix, qs, "hybrid")}
        except Exception as e:  # noqa: BLE001
            row = {"model": name, "kind": kind, "error": f"{type(e).__name__}: {str(e)[:200]}"}
        results.append(row)
        st.item(**row)
        st.log(f"done {name}: " + json.dumps({k: row.get(k) for k in ("dim", "build_s", "error")}))
        (HERE / "embed_experiment.json").write_text(json.dumps({"queries": len(qs), "results": results}, indent=1))
    st.finish("done")


if __name__ == "__main__":
    main()
