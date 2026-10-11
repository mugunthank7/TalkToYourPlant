"""The brain: local-only (no hosted LLM, no API key).

intent router -> tools (graph_lookup, escalation_chain, search_docs, get_sensor_state,
run_scenario, create_work_order, highlight) -> deterministic renderer. A local Ollama model
is used only for questions the router cannot classify.
Returns {answer, highlight:{machine_ids, graph_path}, citations, actions, meta}.
"""
import hashlib
import json
import re
import time
from collections import OrderedDict

from . import config
from .graph import get_graph, current_shift
from .index import get_index
from .sim_adapter import get_sim

CTX_CHARS_PER_CHUNK = 600
CTX_CHARS_TOTAL = 5000

LOCAL_SYSTEM = """You are the plant brain of an EV assembly plant digital twin. Users: managers, technicians, operators.
Answer ONLY from the TOOL RESULTS below. Never invent ids, names, numbers, phone numbers or procedures. If something is not in the results, say it is not available.
Style: a short direct answer first, then bullets. No tables.
Citations: put source ids in square brackets, using ONLY ids from the ALLOWED CITATIONS list, e.g. [SOP-OPS-02] or [M05-A]. Never cite tool names.
- Who to page: list L1, L2, L3 with name, role, extension/mobile, and the page-after minutes; mention the vendor hotline for problems beyond L3.
- Keep running: state the matched scenario numbers (downtime, cost, throughput, failure probability) and the SOP-OPS-02 rule, then give a clear recommendation.
- Created work order: state its id, machine, component, spare part.
- Refer to machines by the id the user used."""

_CODE_RX = re.compile(r"\b[A-Z]{2,5}(?:-[A-Z0-9]{2,12}){1,3}\b")
_HOURS_RX = re.compile(r"(\d+(?:\.\d+)?)\s*(?:more\s+)?(hours?|hrs?|h\b|minutes?|mins?)", re.I)


PROMPT_VERSION = hashlib.sha1(LOCAL_SYSTEM.encode()).hexdigest()[:10]


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
                want = a.get("fault_code")
                if want:                      # relevant fault mode first, so truncation never hides it
                    fm = sorted(fm, key=lambda f: f["code"] != want)
                for f in fm:
                    ctx["cite"].update(f.get("documents") or [])
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
            ctx["actions"].append({"type": "create_work_order", "work_order": wo})
            ctx["cite"].add(wo["id"])
            return wo
        if name == "highlight":
            ids = [g.machine_id(m) or m for m in a.get("machine_ids", [])]
            ctx["highlight_ids"] = ids
            if a.get("graph_path"):
                ctx["graph_path_ids"] = a["graph_path"]
            return {"ok": True, "machine_ids": ids}
        return {"error": f"unknown tool {name}"}

    # ------------------------------------------------------------ local (Ollama) pipeline
    def _run(self, name, args, ctx):
        try:
            out = self._tool(name, args, ctx)
        except Exception as e:  # noqa: BLE001
            out = {"error": f"{type(e).__name__}: {e}"}
        ctx["trace"].append({"tool": name, "args": args})
        ctx.setdefault("raw", []).append((name, args, out))
        ctx["tool_outputs"].append(f"{name}({json.dumps(args, default=str)[:160]}) -> "
                                   f"{json.dumps(out, default=str, ensure_ascii=False)[:1400]}")
        return out

    def _known_codes(self):
        if not hasattr(self, "_codes"):
            self._codes = {d.get("code") for _, d in self.g.g.nodes(data=True) if d.get("label") == "FaultMode" and d.get("code")}
        return self._codes

    def _route(self, q, ctx, focus, shift):
        """Deterministic intent router: runs the right tools, no LLM needed to pick them."""
        ql = q.lower()
        mids = self.g.find_machines(q) or focus
        mid = mids[0] if mids else None
        codes = [c for c in _CODE_RX.findall(q) if c in self._known_codes()]
        code = codes[0] if codes else None
        hm = _HOURS_RX.search(q)
        hours = None
        if hm:
            hours = float(hm.group(1)) / (60.0 if hm.group(2).lower().startswith("min") else 1.0)
        did = False
        ctx["intent"] = "other"
        if re.search(r"create|raise|open|issue|make", ql) and "work order" in ql and mid:
            self._run("create_work_order", {"machine_id": mid}, ctx)
            ctx["intent"] = "work_order"
            did = True
        elif re.search(r"keep (it )?running|run (it )?(on|longer)|more hours?|continue running|extend", ql) and mid:
            self._run("get_sensor_state", {"machine_id": mid}, ctx)
            self._run("run_scenario", {"machine_id": mid, "hours": hours if hours is not None else 2.0}, ctx)
            self._run("search_docs", {"query": "run-extension risk decision keep running more hours", "doc_type": "sop", "k": 2}, ctx)
            ctx["intent"] = "keep_running"
            did = True
        elif re.search(r"who (do|should|to|is)|\bpage\b|escalat|on.?call|contact", ql) and mid:
            args = {"machine_id": mid}
            m = re.search(r"\bshift\s+([abc])\b", ql)
            if m or shift:
                args["shift"] = (m.group(1) if m else shift).upper()
            self._run("escalation_chain", args, ctx)
            ctx["intent"] = "page"
            did = True
        elif re.search(r"how many times|repeat|last \d+ days|recurr", ql) and mid and code:
            self._run("graph_lookup", {"entity": mid, "what": "repeats", "fault_code": code}, ctx)
            self._run("graph_lookup", {"entity": mid, "what": "work_orders", "fault_code": code, "n": 3}, ctx)
            ctx["intent"], ctx["code"] = "repeats", code
            did = True
        elif re.search(r"which sop|what sop|procedure|protocol|\bsop\b", ql) and not mid:
            self._run("search_docs", {"query": q, "doc_type": "sop", "k": 4}, ctx)
            ctx["intent"] = "sop"
            did = True
        elif re.search(r"what does .{0,40}mean|meaning|fault code", ql) or (code and re.search(r"\bpart|spare|replace|needed", ql)):
            if mid:
                self._run("graph_lookup", {"entity": mid, "what": "fault_modes", **({"fault_code": code} if code else {})}, ctx)
            a = {"query": q, "k": 3}
            if mid:
                a["machine_id"] = mid
            if code:
                a["fault_code"] = code
            self._run("search_docs", a, ctx)
            ctx["intent"], ctx["code"] = "fault_code", code
            did = True
        elif mid and re.search(r"part|spare|stock|bearing|replace|needed", ql):
            fc = code or ("bearing_wear" if mid == "M05" else None)
            self._run("graph_lookup", {"entity": mid, "what": "fault_modes", **({"fault_code": fc} if fc else {})}, ctx)
            ctx["intent"], ctx["code"] = "parts", code
            did = True
        elif mid:   # why red / what's wrong / status
            st = self._run("get_sensor_state", {"machine_id": mid}, ctx)
            fc = (st or {}).get("storyline_fault") or ("bearing_wear" if mid == "M05" else None)
            self._run("graph_lookup", {"entity": mid, "what": "fault_modes", **({"fault_code": fc} if fc else {})}, ctx)
            self._run("graph_lookup", {"entity": mid, "what": "work_orders", "n": 3}, ctx)
            self._run("search_docs", {"query": q, "machine_id": mid, "k": 3}, ctx)
            self._run("escalation_chain", {"machine_id": mid, **({"shift": shift} if shift else {})}, ctx)
            ctx["intent"] = "status"
            did = True
        if not did:
            self._run("search_docs", {"query": q, "k": 5}, ctx)
        if mid:
            ctx["highlight_ids"] = ctx["highlight_ids"] or list(dict.fromkeys(mids))
        ctx["mid"] = mid
        return mid

    # ---- deterministic renderers: grounded, instant, no LLM -------------------
    @staticmethod
    def _contact(p):
        bits = [x for x in (p.get("extension"), p.get("mobile"), p.get("radio") and "radio " + p["radio"]) if x]
        return ", ".join(bits)

    def _render(self, ctx):
        raw = {}
        for n, a, o in ctx.get("raw", []):
            raw.setdefault(n, []).append((a, o))
        intent, mid = ctx.get("intent"), ctx.get("mid")
        L = []

        def first(name, pred=lambda a, o: True):
            return next((o for a, o in raw.get(name, []) if pred(a, o)), None)

        esc = first("escalation_chain")
        if intent == "page" and esc and "chain" in esc:
            L.append(f"Shift {esc['shift']} escalation for {esc['machine_id']} [{esc['id']}]:")
            for l in esc["chain"]:
                after = f", page after {l['page_after_min']} min" if l.get("page_after_min") else ""
                L.append(f"- {l['level'].split('_', 1)[0]} {l['level'].split('_', 1)[1].replace('_', ' ')}: "
                         f"{l.get('name')} ({l.get('role')}), {self._contact(l)}{after}")
            v = esc["vendor"]
            L.append(f"- Beyond L3: {v['vendor']} hotline {v['hotline']} ({v.get('contract')}, phone response {v.get('phone_response_h')} h)")
            if esc.get("operator_action"):
                L.append(f"- Operator first: {esc['operator_action']}")
            return "\n".join(L)

        if intent == "work_order":
            wo = first("create_work_order")
            if wo and wo.get("id"):
                return (f"Work order {wo['id']} created for {wo['machine_id']}: component {wo.get('component_id')}, "
                        f"spare part {wo.get('spare_part')}, fault {wo.get('fault_code')}, priority {wo.get('priority')}. "
                        f"Downtime cost ${wo.get('downtime_cost_per_min'):,}/min. Sent to the simulator ({wo.get('source')}).")

        if intent == "keep_running":
            st, sc = first("get_sensor_state"), first("run_scenario")
            rule = next((x for x in ctx["retrieved"] if x["source_id"] == "SOP-OPS-02"), None)
            if sc and "kpis" in sc:
                k = sc["kpis"]
                h = sc["query"]["hours"]
                L.append(f"{mid}: keeping it running {h:g} more hours matches scenario '{sc['matched_scenario']}'"
                         + (f" ({sc['about']})" if sc.get("about") else ""))
                if st and st.get("remaining_useful_life_min"):
                    L.append(f"- Remaining useful life at alert: about {st['remaining_useful_life_min']} min (bearing wear).")
                L.append(f"- Downtime: {k['downtime_min']['scenario']} min vs {k['downtime_min']['baseline']} min if repaired now.")
                L.append(f"- Throughput: {k['throughput_per_hr']['scenario']}/h vs {k['throughput_per_hr']['baseline']}/h; "
                         f"OEE {k['oee']['scenario']} vs {k['oee']['baseline']}.")
                fp = k.get("failure_probability")
                cost, cost_b = k.get("cost_usd"), k.get("cost_baseline_usd")
                L.append("- Downtime cost: " + (f"${cost:,.0f}" if cost is not None else "n/a")
                         + (f" vs ${cost_b:,.0f} if repaired now" if cost_b is not None else "")
                         + (f"; failure probability about {fp:.0%} (estimate)." if fp is not None else "."))
                rul_h, rul_low = sc.get("rul_hours_at_alert"), sc.get("rul_low_hours")
                if rul_h is not None:
                    L.append(f"- Predicted remaining useful life: {rul_h * 60:.0f} min"
                             + (f" (80% interval lower bound {rul_low * 60:.0f} min)" if rul_low is not None else "") + ".")
                better = cost is not None and cost_b is not None and cost < cost_b
                inside = rul_low is not None and h <= rul_low
                if sc["matched_scenario"] == "hero_ignored" or (rul_h is not None and h > rul_h):
                    rec = "Do not extend. The run is longer than the remaining useful life, so failure is likely. Repair now."
                elif h > 1.0:
                    rec = (f"{h:g} h exceeds the SOP-OPS-02 limit for a rising warn-level trend (current batch, about 30 to 60 min). "
                           + ("The engine projects lower downtime cost, but that is not a licence to exceed the rule: it needs written Maintenance Manager approval, 15-minute re-checks and a technician on standby. " if better else "")
                           + ("Inside the predicted RUL interval, " if inside else "")
                           + "plan the repair at the next buffer-protected stop.")
                else:
                    rec = "Allowed only for the current batch with supervisor approval and 30-minute re-checks; repair at the next buffer-protected stop."
                L.append(f"Recommendation: {rec}" + (" [SOP-OPS-02]" if rule else ""))
            elif sc:
                L.append(sc.get("error", "No scenario result."))
            return "\n".join(L)

        if intent == "repeats":
            r = first("graph_lookup", lambda a, o: "count_in_window" in o or o.get("count") is not None)
            wos = first("graph_lookup", lambda a, o: "work_orders" in o)
            if r and r.get("count", 1) != 0 and "count_in_window" in r:
                ids = [w["wo_id"] for w in (wos or {}).get("work_orders", [])]
                return (f"{mid} had {ctx.get('code')} {r['count_in_window']} times in the last {r['window_days']} days "
                        f"({r['total']} total in the history, latest {r['latest']}). Most recent work orders: "
                        + ", ".join(f"[{i}]" for i in ids) + ".")
            return f"No {ctx.get('code')} history found for {mid}."

        if intent in ("fault_code", "parts"):
            fm = first("graph_lookup", lambda a, o: "fault_modes" in o)
            code = ctx.get("code")
            if fm:
                modes = fm["fault_modes"]
                sel = [f for f in modes if f["code"] == code] or ([f for f in modes if f["code"] == "bearing_wear"]
                                                                  if mid == "M05" else modes[:3])
                for f in sel[:3]:
                    parts = ", ".join(f"{p['part_no']} ({p['description']}" + (f", {p['on_hand']} on hand" if p.get("on_hand") is not None else "") + ")"
                                      for p in f["parts"]) or "none listed"
                    doc = f" [{f['documents'][0]}]" if f.get("documents") else ""
                    L.append(f"{f['code']} on {mid}: {f['description']}{doc}.")
                    if f["causes"]:
                        L.append("- Likely causes: " + "; ".join(c for c in f["causes"] if c))
                    L.append(f"- Parts: {parts}")
                    if f["sensors"]:
                        L.append("- Shows in: " + ", ".join(f"{s['channel']} ({s['shape']})" for s in f["sensors"]))
                return "\n".join(L)

        if intent == "sop":
            res = first("search_docs") or {}
            seen = []
            for r in res.get("results", []):
                if r["id"] not in seen:
                    seen.append(r["id"])
                    title = r["text"].split("\n", 1)[0].strip("[]")
                    L.append(f"- [{r['id']}] {title}")
            return "Relevant procedures:\n" + "\n".join(L) if L else None

        if intent == "status":
            st = first("get_sensor_state")
            if st:
                L.append(f"{mid} status: {st.get('status')}.")
                for ch, v in (st.get("readings") or {}).items():
                    if not isinstance(v, dict):
                        continue
                    nom, val = v.get("nominal"), v.get("value")
                    if "ratio" in v:
                        L.append(f"- {ch}: {val} (nominal {nom}, {v['ratio']}x; alert at {v.get('alert_at_ratio')}x)")
                    elif nom is None or val != nom:
                        L.append(f"- {ch}: {val}" + (f" {v['unit']}" if v.get("unit") else "")
                                 + (f" (nominal {nom}" + (f", warn {v['warn']}" if v.get("warn") is not None else "") + ")" if nom is not None else ""))
                if st.get("vib_multiple"):
                    L.append(f"- Vibration is {st['vib_multiple']}x its healthy level.")
                if st.get("remaining_useful_life_min") and not any("ratio" in (x or {}) for x in (st.get("readings") or {}).values() if isinstance(x, dict)):
                    L.append(f"- Remaining useful life about {st['remaining_useful_life_min']} min.")
                if st.get("alert"):
                    c = ", ".join(f"{x['signal']} {x['shap']}" if x.get("shap") is not None else str(x["signal"])
                                  for x in st["alert"].get("contributors") or [])
                    L.append(f"- Alert ({st['alert'].get('severity')}), score {st['alert'].get('score')}"
                             + (f"; top signals: {c}" if c else "") + f"; component {st['alert'].get('component_id')}.")
                if st.get("storyline_fault"):
                    L.append(f"- Ongoing fault: {st['storyline_fault']} (drifting channel {st['drifting_channel']}, {st['shape']}).")
            fm = first("graph_lookup", lambda a, o: "fault_modes" in o)
            if fm:
                want = (first("get_sensor_state") or {}).get("storyline_fault") or ("bearing_wear" if mid == "M05" else None)
                f = next((x for x in fm["fault_modes"] if x["code"] == want), None)
                if f:
                    parts = ", ".join(f"{p['part_no']} ({p['on_hand']} on hand)" if p.get("on_hand") is not None else p["part_no"] for p in f["parts"])
                    causes = "; ".join(c for c in f["causes"] if c)
                    L.append(f"- Fault mode {f['code']}: {f['description']}." + (f" Causes: {causes}." if causes else "")
                             + f" Parts: {parts or 'none listed'}.")
            wo = first("graph_lookup", lambda a, o: "work_orders" in o)
            if wo and wo["work_orders"]:
                w = wo["work_orders"][0]
                L.append(f"- Latest work order [{w['wo_id']}] {w['opened_ts'][:10]}: {w.get('fault_code') or w.get('wo_type')}"
                         + (f", root cause: {w['root_cause']}" if w.get("root_cause") else "") + ".")
            def _applies(sid):
                m = re.match(r"SOP-[A-Z]+-(M\d\d)-\d+", sid)       # machine-specific SOPs only apply to their machine
                return not m or m.group(1) == mid
            sop = next((x for x in ctx["retrieved"] if x["source_id"].startswith("SOP-") and _applies(x["source_id"])), None)
            if st and st.get("evidence"):
                for e in st["evidence"][:3]:
                    L.append(f"- {e}")
            if st and st.get("affected_stations"):
                L.append("- Affected stations: " + ", ".join(f"{a['station']} ({a['state']}{', ' + a['reason'] if a.get('reason') else ''})"
                                                            for a in st["affected_stations"][:4]))
            if st and st.get("open_work_orders"):
                L.append("- Open work orders: " + ", ".join(f"{w['id']} ({w['status']})" for w in st["open_work_orders"][:3]))
            if not first("graph_lookup", lambda a, o: "fault_modes" in o and o["fault_modes"]):
                L.append(f"- No fault catalogue for {mid} in the knowledge base.")
            if sop:
                L.append(f"- Procedure: [{sop['source_id']}].")
            if esc and "chain" in esc:
                l1 = next(l for l in esc["chain"] if l["level"] == "L1_primary_tech")
                L.append(f"- Page L1 {l1.get('name')} ({self._contact(l1)}) [{esc['id']}]; then L2 after {esc['escalation_minutes']['L2_backup']} min.")
            return "\n".join(L) if len(L) > 1 else None
        return None

    def _ollama_chat(self, system, user):
        import urllib.request
        body = {"model": config.OLLAMA_MODEL, "stream": False, "keep_alive": "30m",
                "options": {"temperature": 0.1, "num_ctx": config.OLLAMA_NUM_CTX, "num_predict": 600},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        r = urllib.request.Request(config.OLLAMA_URL.rstrip("/") + "/api/chat", data=json.dumps(body).encode(),
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=300) as resp:
            return json.loads(resp.read().decode())["message"]["content"].strip()

    def _local(self, question, history, ctx, focus, shift):
        self._route(question, ctx, focus, shift)
        if config.get("LOCAL_NARRATE", "0") != "1":
            text = self._render(ctx)
            if text:
                return text
        ctx["llm_calls"] += 1
        res = "\n\n".join(ctx["tool_outputs"])[:7000]
        allowed = ", ".join(sorted(ctx["cite"])[:30]) or "(none)"
        prior = ""
        if history:
            prior = "PREVIOUS TURNS:\n" + "\n".join(f"{h['role']}: {h['text'][:300]}" for h in history[-4:]) + "\n\n"
        user = f"{prior}TOOL RESULTS:\n{res}\n\nALLOWED CITATIONS: {allowed}\n\nQUESTION: {question}"
        return self._ollama_chat(LOCAL_SYSTEM, user)

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

    def ask(self, question, session_id="default", shift=None, premium=False):
        t0 = time.time()
        sess = self.sessions.setdefault(session_id, {"history": []})
        focus = self.g.find_machines(question)
        key = hashlib.sha1(json.dumps([PROMPT_VERSION, config.OLLAMA_MODEL, "render-v5", config.get("SIM_MODE", "mock"), config.get("LOCAL_NARRATE", "0"), question.strip().lower(), shift or current_shift(),
                                       sess["history"][-2:] if sess["history"] else []]).encode()).hexdigest()
        live = config.get("SIM_MODE", "mock").lower() == "live"     # live plant state changes: never serve cached answers
        hit = None if live else self.cache.get(key)
        if hit:
            return {**hit, "meta": {**hit["meta"], "cached": True, "latency_s": round(time.time() - t0, 2)}}
        ctx = {"machines": [], "cite": set(), "retrieved": [], "alerts": [], "actions": [], "trace": [], "tool_outputs": [],
               "llm_calls": 0, "highlight_ids": None}
        q = question if not shift else f"{question} (shift {shift})"
        answer, used, err = None, None, None
        try:
            answer = self._local(question if not shift else q, sess["history"], ctx, focus or sess.get("focus", []), shift)
            used = "ollama:" + config.OLLAMA_MODEL if ctx["llm_calls"] else "local-pipeline"
        except Exception as e:  # noqa: BLE001
            err = f"ollama: {type(e).__name__}: {str(e)[:160]}"
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
                     "llm_calls": ctx["llm_calls"], "contexts": ctx["tool_outputs"][:10], "sources_consulted": list(dict.fromkeys(r["source_id"] for r in ctx["retrieved"]))[:12], "tools": [t["tool"] for t in ctx["trace"]],
                     "shift": shift or current_shift(), "sim_mode": self.sim.mode,
                     "latency_s": round(time.time() - t0, 2), "cached": False},
        }
        if not degraded and not live:
            self.cache.put(key, result)
        if mids:
            sess["focus"] = mids[:2]
        sess["history"] += [{"role": "user", "text": question}, {"role": "model", "text": answer}]
        sess["history"] = sess["history"][-8:]
        return result
