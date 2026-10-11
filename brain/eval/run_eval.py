#!/usr/bin/env python3
"""Evaluation: retrieval metrics (free, no LLM) and end-to-end answer checks.

  python3 brain/eval/run_eval.py --retrieval-only        # no quota used
  python3 brain/eval/run_eval.py                         # full run (about 3 LLM calls per question)
  python3 brain/eval/run_eval.py --cats who_to_page,hero --limit 5

Each question has deterministic checks drawn from the data (see make_questions.py):
  must_include   groups of substrings (any-of inside a group, all groups required)
  expect_tools   tools the agent must have called
  expect_highlight  machine ids that must be in highlight.machine_ids
  expect_action  action type that must appear
  expect_citation  at least one verified citation
Results are written to brain/eval/results_latest.json (per-question) and printed.
"""
import argparse, collections, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.index import get_index  # noqa: E402
from status import Status  # noqa: E402

HERE = Path(__file__).resolve().parent


def load(cats, limit):
    qs = [json.loads(l) for l in open(HERE / "questions.jsonl")]
    if cats:
        qs = [q for q in qs if q["category"] in cats]
    return qs[:limit] if limit else qs


def retrieval_eval(qs):
    ix = get_index()
    rows = []
    for q in qs:
        if not q["gold_sources"]:
            continue
        r = ix.search(q["question"], k=6, machine_id=q["machine"])
        ids = [x["source_id"] for x in r]
        rank = next((i + 1 for i, s in enumerate(ids) if s in q["gold_sources"]), None)
        rows.append({"id": q["id"], "category": q["category"], "rank": rank, "top": ids[:3]})
    n = len(rows)
    hit = sum(1 for r in rows if r["rank"]) / max(n, 1)
    mrr = sum(1 / r["rank"] for r in rows if r["rank"]) / max(n, 1)
    return rows, hit, mrr


def check_answer(q, res):
    ans = res["answer"].lower()
    fails = []
    for grp in q["must_include"]:
        if not any(s.lower() in ans for s in grp):
            fails.append(f"missing any of {grp}")
    tools = set(res["meta"].get("tools", []))
    for t in q["expect_tools"]:
        if t not in tools:
            fails.append(f"tool not called: {t}")
    hl = set(res["highlight"]["machine_ids"])
    for m in q["expect_highlight"]:
        if m not in hl:
            fails.append(f"not highlighted: {m}")
    if q["expect_action"] and not any(a["type"] == q["expect_action"] for a in res["actions"]):
        fails.append(f"no action {q['expect_action']}")
    if q["expect_citation"] and not res["citations"]:
        fails.append("no verified citation")
    if res["meta"].get("degraded"):
        fails.append("degraded: " + str(res["meta"].get("error")))
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--retrieval-only", action="store_true")
    ap.add_argument("--out", default="results_latest.json", help="results file name (use results_live.json for live-engine runs)")
    ap.add_argument("--cats", default="")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    qs = load(set(a.cats.split(",")) if a.cats else None, a.limit)

    st = Status("eval")
    st.update(progress={"done": 0, "total": len(qs)}, current="retrieval metrics")
    rows, hit, mrr = retrieval_eval(qs)
    st.update(retrieval={"hit_at_6": round(hit, 3), "mrr": round(mrr, 3), "n": len(rows),
                         "misses": [r["id"] for r in rows if not r["rank"]]})
    print(f"RETRIEVAL (no LLM, scoped search, k=6) over {len(rows)} questions with gold sources: hit@6={hit:.2f} MRR={mrr:.2f}")
    for r in rows:
        if not r["rank"]:
            print(f"  miss {r['id']} [{r['category']}] got {r['top']}")
    if a.retrieval_only:
        st.finish("done")
        return

    from app.agent import Brain
    b = Brain()
    results, by_cat = [], collections.defaultdict(list)
    t0 = time.time()
    for q in qs:
        st.update(current=f"{q['id']} {q['question'][:70]}")
        res = b.ask(q["question"], session_id="eval-" + q["id"])
        fails = check_answer(q, res)
        gold_seen = (not q["gold_sources"]) or any(s in res["meta"].get("sources_consulted", []) or
                                                  s in [c["id"] for c in res["citations"]] for s in q["gold_sources"])
        ok = not fails
        by_cat[q["category"]].append(ok)
        results.append({"id": q["id"], "category": q["category"], "question": q["question"], "pass": ok,
                        "fails": fails, "gold_source_seen": gold_seen, "answer": res["answer"],
                        "citations": [c["id"] for c in res["citations"]], "tools": res["meta"]["tools"],
                        "highlight": res["highlight"]["machine_ids"], "llm_calls": res["meta"]["llm_calls"],
                        "model": res["meta"]["model"], "cached": res["meta"]["cached"], "latency_s": res["meta"]["latency_s"],
                        "contexts": res["meta"].get("sources_consulted", []),
                        "contexts_text": res["meta"].get("contexts", [])})
        print(("PASS " if ok else "FAIL ") + f"{q['id']} [{q['category']}] {q['question'][:70]}"
              + ("" if ok else "  -> " + "; ".join(fails)))
        st.item(id=q["id"], category=q["category"], question=q["question"], **{"pass": ok}, fails=fails,
                latency_s=res["meta"]["latency_s"], llm_calls=res["meta"]["llm_calls"], answer=res["answer"][:400])
        st.log(f"{'PASS' if ok else 'FAIL'} {q['id']} {q['question'][:60]}")
    n_ok = sum(r["pass"] for r in results)
    print(f"\nANSWERS: {n_ok}/{len(results)} pass ({100*n_ok/max(len(results),1):.0f}%) in {time.time()-t0:.0f}s")
    for c, v in sorted(by_cat.items()):
        print(f"  {c:16s} {sum(v)}/{len(v)}")
    st.finish("done", summary={"pass": n_ok, "total": len(results), "by_category": {c: [sum(v), len(v)] for c, v in by_cat.items()}})
    (HERE / a.out).write_text(json.dumps(
        {"retrieval": {"hit_at_6": hit, "mrr": mrr, "n": len(rows)}, "answers": results}, indent=1))


if __name__ == "__main__":
    main()
