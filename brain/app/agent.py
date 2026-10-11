"""Gemini function-calling agent ("the brain").

Plain tool loop on google-genai. Tools: graph_lookup, escalation_chain, search_docs,
get_sensor_state, run_scenario, create_work_order, highlight.
Returns {answer, highlight:{machine_ids, graph_path}, citations, actions, meta}.
Degrades gracefully: model fallback, then a deterministic no-LLM answer.
"""
import hashlib
import json
import re
import time
from collections import OrderedDict

from . import config, ratelimit
from .graph import get_graph, current_shift
from .index import get_index
from .sim_adapter import get_sim

MAX_STEPS = 6
CTX_CHARS_PER_CHUNK = 600
CTX_CHARS_TOTAL = 5000

SYSTEM = """You are the plant brain of Voltline/Voltara EV Works, a fictional EV assembly plant digital twin.
Users are plant managers, maintenance technicians and operators.

RULES
- Answer ONLY from tool results. If data is missing, say what is missing; never guess or invent IDs, names, numbers or phone numbers.
- Always call tools before answering a plant question. Use the machine ID the user gave (twin ids M01..M11 like M05, or ids like CAS-GP-01).
- "Who do I page / who is on call": call escalation_chain for the CURRENT shift (pass no shift unless the user names one) and list L1, L2, L3 with names, extensions/mobile, and the page-after minutes. Mention the vendor hotline if the problem is beyond L3.
- "Can we keep running N more hours": call get_sensor_state, search_docs for SOP-OPS-02, and run_scenario (keep_running). State the rule that applies, the numbers, and a clear recommendation.
- Why is a machine red/alarming: call get_sensor_state, graph_lookup (fault_modes, work_orders), search_docs (scoped to the machine) and escalation_chain; explain symptom with the numbers, likely cause, parts and stock, the SOP to follow, and who to page. Then call highlight with the machine ids.
- Only call create_work_order when the user explicitly asks to create/raise one.
- Cite sources inline in square brackets using exact document ids from tool results (the "id" field of search_docs results, work-order ids, escalation ids like M05-A): e.g. [SOP-MNT-M05-01], [SOP-OPS-02], [WO-2026-007763], [M05-A], [RCA-049]. NEVER cite tool names. Do not cite ids you did not receive.
- Be concise: a short direct answer first, then bullets for details. No markdown tables.
- Voltline twin ids (M01..M11) are the plant's machine ids; mention the Voltara id only if useful."""

TOOLS = [
    {"name": "graph_lookup",
     "description": "Query the plant knowledge graph. what: machine (details), neighbors, fault_modes (family fault list with parts/causes/signals), staff (assigned people), work_orders (recent history), repeats (repeat-failure count for a fault code), path (shortest path to target).",
     "parameters": {"type": "object", "properties": {
         "entity": {"type": "string", "description": "Machine id or name, e.g. M05, CAS-GP-01, 'Giga Press 1'"},
         "what": {"type": "string", "enum": ["machine", "neighbors", "fault_modes", "staff", "work_orders", "repeats", "path"]},
         "shift": {"type": "string", "description": "A, B or C (for staff)"},
         "fault_code": {"type": "string", "description": "Fault code filter for work_orders/repeats, e.g. GP-SHOT-SLOW"},
         "target": {"type": "string", "description": "Target node id for path"},
         "n": {"type": "integer", "description": "Number of work orders (default 5)"}},
         "required": ["entity", "what"]}},
    {"name": "escalation_chain",
     "description": "Who to page for a machine on a shift: operator action, L0 line lead, L1/L2 technicians, L3 maintenance supervisor, L4 engineers, L5 vendor hotline, timers and safety triggers. Omit shift for the current shift.",
     "parameters": {"type": "object", "properties": {
         "machine_id": {"type": "string"}, "shift": {"type": "string", "description": "A, B or C; omit for current shift"}},
         "required": ["machine_id"]}},
    {"name": "search_docs",
     "description": "Search SOPs, manuals, work orders, RCA/incident reports, service logs, handover notes. Use machine_id to scope to one machine (also returns its family manual). doc_type one of: sop, manual, work_order, rca, incident, service_log, shift_handover, escalation, machine_profile.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string"}, "machine_id": {"type": "string"}, "doc_type": {"type": "string"},
         "fault_code": {"type": "string"}, "k": {"type": "integer", "description": "1-8, default 5"}},
         "required": ["query"]}},
    {"name": "get_sensor_state",
     "description": "Latest sensor readings, status and any active alert (with SHAP contributors) for a machine from the simulator.",
     "parameters": {"type": "object", "properties": {"machine_id": {"type": "string"}}, "required": ["machine_id"]}},
    {"name": "run_scenario",
     "description": "What-if via the simulator: keep a machine running N more hours with its current fault. Returns baseline vs scenario throughput, downtime, OEE, failure probability and cost.",
     "parameters": {"type": "object", "properties": {
         "machine_id": {"type": "string"}, "hours": {"type": "number"}, "op": {"type": "string", "enum": ["keep_running"]}},
         "required": ["machine_id", "hours"]}},
    {"name": "create_work_order",
     "description": "Create a corrective work order in the simulator. Only when the user asks.",
     "parameters": {"type": "object", "properties": {
         "machine_id": {"type": "string"}, "component_id": {"type": "string"}, "spare_part": {"type": "string"},
         "fault_code": {"type": "string"}, "priority": {"type": "string", "enum": ["P1", "P2", "P3"]}, "note": {"type": "string"}},
         "required": ["machine_id"]}},
    {"name": "highlight",
     "description": "Tell the 3D twin which machines to highlight and optionally animate a knowledge-graph path.",
     "parameters": {"type": "object", "properties": {
         "machine_ids": {"type": "array", "items": {"type": "string"}},
         "graph_path": {"type": "array", "items": {"type": "string"}, "description": "Ordered node ids"}},
         "required": ["machine_ids"]}},
]


class _AnswerCache:
    def __init__(self, path, cap=500):
        self.path, self.cap = path, cap
        self.d = OrderedDict()
        try:
            self.d = OrderedDict(json.loads(path.read_text()))
        except Exception:
            pass

    def get(self, k):
        return self.d.get(k)

    def put(self, k, v):
        self.d[k] = v
        self.d.move_to_end(k)
        while len(self.d) > self.cap:
            self.d.popitem(last=False)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.d))
        except Exception:
            pass


class Brain:
    def __init__(self, sim=None, graph=None, index=None):
        self.g = graph or get_graph()
        self.ix = index or get_index()
        self.sim = sim or get_sim()
        self.cache = _AnswerCache(config.CACHE_DIR / "answers.json")
        self._client = None
        self.sessions = {}

    # ------------------------------------------------------------ tools
    def _tool(self, name, a, ctx):
        g = self.g
        if name == "graph_lookup":
            ent, what = a["entity"], a["what"]
            mid = g.machine_id(ent)
            if mid:
                ctx["machines"].append(mid)
            if what == "machine":
                return g.get_machine(ent) or {"error": f"unknown machine {ent}"}
            if what == "neighbors":
                return {"neighbors": g.neighbors(ent)[:40]}
            if what == "fault_modes":
                fm = g.fault_modes(ent)
                return {"machine_id": mid, "fault_modes": fm[:14], "total": len(fm)}
            if what == "staff":
                return {"staff": g.assigned_staff(ent, a.get("shift"))}
            if what == "work_orders":
                rows = g.recent_work_orders(ent, min(int(a.get("n", 5)), 8), fault_code=a.get("fault_code"))
                for w in rows:
                    ctx["cite"].add(w["wo_id"])
                    for k in ("action_taken", "diagnosis", "root_cause"):
                        if w.get(k):
                            w[k] = str(w[k])[:240]
                return {"machine_id": mid, "work_orders": rows}
            if what == "repeats":
                return g.repeat_failures(ent, a.get("fault_code", ""))
            if what == "path":
                return g.path_between(ent, a.get("target", "")) or {"error": "no path"}
            return {"error": "bad what"}
        if name == "escalation_chain":
            r = g.escalation_chain(a["machine_id"], a.get("shift"))
            mid = g.machine_id(a["machine_id"])
            if mid:
                ctx["machines"].append(mid)
            if not r:
                return {"error": f"no escalation data for {a['machine_id']}"}
            ctx["cite"].add(f"{mid}-{r['shift']}")
            return {"id": f"{mid}-{r['shift']}", **r}
        if name == "search_docs":
            k = max(1, min(int(a.get("k", 5)), 8))
            if a.get("machine_id"):
                mid = g.machine_id(a["machine_id"]) or a["machine_id"]
                ctx["machines"].append(mid)
            res = self.ix.search(a["query"], k=k, machine_id=a.get("machine_id"),
                                 doc_type=a.get("doc_type"), fault_code=a.get("fault_code"))
            out, used = [], 0
            for r in res:
                t = r["text"][:CTX_CHARS_PER_CHUNK]
                if used + len(t) > CTX_CHARS_TOTAL:
                    break
                used += len(t)
                ctx["cite"].add(r["source_id"])
                ctx["retrieved"].append({"source_id": r["source_id"], "chunk_id": r["chunk_id"], "text": r["text"]})
                out.append({"id": r["source_id"], "type": r["source_type"], "machine": r["machine_id"], "text": t})
            return {"results": out}
        if name == "get_sensor_state":
            mid = g.machine_id(a["machine_id"]) or a["machine_id"]
            ctx["machines"].append(mid)
            st = self.sim.get_sensor_state(mid, g)
            if st.get("alert"):
                ctx["alerts"].append(st["alert"])
            return st
        if name == "run_scenario":
            mid = g.machine_id(a["machine_id"]) or a["machine_id"]
            ctx["machines"].append(mid)
            r = self.sim.run_scenario(mid, float(a["hours"]), a.get("op", "keep_running"))
            ctx["actions"].append({"type": "run_scenario", "machine_id": mid, "hours": a["hours"], "result": r})
            return r
        if name == "create_work_order":
            mid = g.machine_id(a["machine_id"]) or a["machine_id"]
            ctx["machines"].append(mid)
            comp, part = a.get("component_id"), a.get("spare_part")
            if mid == "M05":
                comp, part = comp or "m05_joint1_bearing", part or "bearing_6208"
            wo = self.sim.create_work_order(mid, comp, part, a.get("fault_code") or ("bearing_wear" if mid == "M05" else None),
                                            a.get("priority", "P2"), a.get("note"))
            ctx["actions"].append({"type": "create_work_order", **wo})
            ctx["cite"].add(wo["id"])
            return wo
        if name == "highlight":
            ids = [g.machine_id(m) or m for m in a.get("machine_ids", [])]
            ctx["highlight_ids"] = ids
            if a.get("graph_path"):
                ctx["graph_path_ids"] = a["graph_path"]
            return {"ok": True, "machine_ids": ids}
        return {"error": f"unknown tool {name}"}

    # ------------------------------------------------------------ model
    def _gem(self):
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=config.API_KEY)
        return self._client

    def _generate(self, role, model, contents):
        from google.genai import types
        cfg = types.GenerateContentConfig(
            system_instruction=SYSTEM, temperature=0.1,
            tools=[types.Tool(function_declarations=[types.FunctionDeclaration(**t) for t in TOOLS])],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True))
        est = sum(len(str(c)) for c in contents) // 3
        return ratelimit.call_with_retry(
            role, lambda: self._gem().models.generate_content(model=model, contents=contents, config=cfg),
            est_tokens=est, max_tries=4)

    def _loop(self, question, history, role, model, ctx):
        from google.genai import types
        contents = []
        for h in history[-6:]:
            contents.append(types.Content(role=h["role"], parts=[types.Part.from_text(text=h["text"])]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=question)]))
        for step in range(MAX_STEPS):
            resp = self._generate(role, model, contents)
            calls = resp.function_calls or []
            ctx["llm_calls"] += 1
            if not calls:
                return (resp.text or "").strip()
            contents.append(resp.candidates[0].content)
            parts = []
            for fc in calls:
                args = dict(fc.args or {})
                try:
                    out = self._tool(fc.name, args, ctx)
                except Exception as e:  # noqa: BLE001
                    out = {"error": f"{type(e).__name__}: {e}"}
                ctx["trace"].append({"tool": fc.name, "args": args})
                parts.append(types.Part.from_function_response(name=fc.name, response={"result": out}))
            contents.append(types.Content(role="user", parts=parts))
        return "I could not finish within the tool-call limit; see the highlighted machines and sources."

    # ------------------------------------------------------------ no-LLM fallback
    def _degraded(self, question, ctx, reason):
        q = question.lower()
        mids = self.g.find_machines(question)
        lines = [f"(Offline mode: {reason}. Answering directly from plant data.)"]
        for mid in mids[:1]:
            ctx["machines"].append(mid)
            if re.search(r"page|call|who|escalat|on.?call", q):
                r = self.g.escalation_chain(mid)
                if r:
                    ctx["cite"].add(f"{mid}-{r['shift']}")
                    lines.append(f"Shift {r['shift']} escalation for {mid}:")
                    for l in r["chain"]:
                        lines.append(f"- {l['level']}: {l.get('name')} ({l.get('role')}), {l.get('extension') or l.get('mobile')}")
                    lines.append(f"Vendor: {r['vendor']['vendor']} {r['vendor']['hotline']}")
                    return "\n".join(lines)
            st = self.sim.get_sensor_state(mid, self.g)
            lines.append(f"{mid} status: {st.get('status')}.")
            if st.get("alert"):
                ctx["alerts"].append(st["alert"])
        res = self.ix.search(question, k=3, machine_id=mids[0] if mids else None)
        for r in res:
            ctx["cite"].add(r["source_id"])
            ctx["retrieved"].append({"source_id": r["source_id"], "chunk_id": r["chunk_id"], "text": r["text"]})
            lines.append(f"- [{r['source_id']}] {r['text'][:220].strip()}")
        return "\n".join(lines)

    # ------------------------------------------------------------ public
    def graph_path_for(self, ctx):
        ids = ctx.get("graph_path_ids")
        g = self.g
        if ids:
            return [{"id": i, "kind": g.g.nodes[i].get("kind") if i in g.g else None} for i in ids if i in g.g]
        if "M05" in ctx["machines"] and any(k in json.dumps(ctx["trace"]) for k in ("bearing", "vibration")) or \
           (ctx["alerts"] and ctx["alerts"][0].get("machine_id") == "M05"):
            hp = g.hero_graph_path()
            return hp["nodes"] if hp else []
        return []

    def ask(self, question, session_id="default", premium=False, shift=None):
        t0 = time.time()
        sess = self.sessions.setdefault(session_id, {"history": []})
        focus = self.g.find_machines(question)
        key = hashlib.sha1(json.dumps([question.strip().lower(), shift or current_shift(), premium,
                                       sess["history"][-2:] if sess["history"] else []]).encode()).hexdigest()
        hit = self.cache.get(key)
        if hit:
            return {**hit, "meta": {**hit["meta"], "cached": True, "latency_s": round(time.time() - t0, 2)}}
        ctx = {"machines": [], "cite": set(), "retrieved": [], "alerts": [], "actions": [], "trace": [],
               "llm_calls": 0, "highlight_ids": None}
        q = question if not shift else f"{question} (shift {shift})"
        models = [("premium", config.MODELS["premium"])] if premium else []
        models += [("agent", config.MODELS["agent"]), ("lite", config.MODELS["fallback"])]
        answer, used, err = None, None, None
        if not config.API_KEY:
            err = "GEMINI_API_KEY not set"
        else:
            for role, model in models:
                try:
                    answer = self._loop(q, sess["history"], role, model, ctx)
                    used = model
                    break
                except ratelimit.DailyBudgetExceeded as e:
                    err = str(e)
                except Exception as e:  # noqa: BLE001
                    err = f"{type(e).__name__}: {str(e)[:160]}"
        degraded = answer is None
        if degraded:
            answer = self._degraded(question, ctx, err or "model unavailable")
        # citations: only ids that were actually retrieved AND appear in the answer
        cited = [c for c in re.findall(r"\[([A-Za-z0-9_.:\-]+)\]", answer) if c in ctx["cite"]]
        cited = list(dict.fromkeys(cited))
        by_id = {r["source_id"]: r for r in ctx["retrieved"]}
        citations = [{"id": c, "excerpt": (by_id[c]["text"][:200] if c in by_id else None)} for c in cited]
        mids = ctx["highlight_ids"] or list(dict.fromkeys(m for m in ctx["machines"] if m)) or focus
        mids = [m for m in mids if m in self.g.machines] or mids
        result = {
            "answer": answer,
            "highlight": {"machine_ids": mids[:8], "graph_path": self.graph_path_for(ctx)},
            "citations": citations,
            "actions": ctx["actions"],
            "meta": {"model": used, "degraded": degraded, "error": err if degraded else None,
                     "llm_calls": ctx["llm_calls"], "sources_consulted": list(dict.fromkeys(r["source_id"] for r in ctx["retrieved"]))[:12], "tools": [t["tool"] for t in ctx["trace"]],
                     "shift": shift or current_shift(), "sim_mode": self.sim.mode,
                     "latency_s": round(time.time() - t0, 2), "cached": False},
        }
        if not degraded:
            self.cache.put(key, result)
        sess["history"] += [{"role": "user", "text": question}, {"role": "model", "text": answer}]
        sess["history"] = sess["history"][-8:]
        return result
