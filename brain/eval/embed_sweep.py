#!/usr/bin/env python3
"""Fusion-weight sweep per embedding model (uses cached embeddings, fast).
Weights are (dense, bm25) in reciprocal-rank fusion. Appends 'sweep' to embed_experiment.json."""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
from app.index import DocIndex, Embedder  # noqa: E402
from embed_experiment import queries, MODELS  # noqa: E402
from status import Status  # noqa: E402

WEIGHTS = [(1, 0), (1, 1), (1, 2), (1, 3), (0, 1)]
qs = queries()
st = Status("sweep")
st.update(progress={"done": 0, "total": len(MODELS) - 1})
out = []
for name, kind in MODELS[:-1]:                      # skip nomic (worst, slow)
    st.update(current=name)
    ix = DocIndex(embedder=Embedder(name, kind))
    row = {"model": name, "weights": []}
    for wd, wb in WEIGHTS:
        res = {"gold": [], "para": []}
        for q in qs:
            r = ix.search(q["q"], k=6, machine_id=q["machine"], w_dense=wd, w_bm25=wb)
            ids = [x["source_id"] for x in r]
            res[q["set"]].append(next((i + 1 for i, s in enumerate(ids) if s in q["gold"]), None))
        row["weights"].append({"dense": wd, "bm25": wb, **{k: {"hit6": round(sum(1 for x in v if x) / len(v), 3),
                               "mrr": round(sum(1 / x for x in v if x) / len(v), 3)} for k, v in res.items()}})
    out.append(row)
    st.item(model=name)
    print(name, [(w["dense"], w["bm25"], w["gold"]["hit6"], w["para"]["hit6"], w["para"]["mrr"]) for w in row["weights"]], flush=True)
p = HERE / "embed_experiment.json"
d = json.loads(p.read_text()); d["sweep"] = out; p.write_text(json.dumps(d, indent=1))
st.finish("done")
