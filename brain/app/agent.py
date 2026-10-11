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

from . import config, prompts
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


PROMPT_VERSION = hashlib.sha1((LOCAL_SYSTEM + prompts.NARRATE_SYSTEM + prompts.ANSWER_SYSTEM).encode()).hexdigest()[:10]


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
            ctx.setdefault("search", []).extend(
                {"source_id": r["source_id"], "type": r["source_type"], "dense": r["dense"], "bm25": r["bm25"],
                 "text": r["text"], "machine": r["machine_id"]} for r in res)
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
        if name == "get_kpis":
            return self.sim.get_kpis()
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
        ctx["q"] = q
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
        elif re.search(r"how many (cars|vehicles|units|bodies)|\boutput\b|throughput|\boee\b(?! mean)|how are we doing|production (so far|today)|are we on (plan|target)", ql) \
                and not re.search(r"(what is|what's|explain|define|meaning of|what does)\b.*\boee\b", ql):
            self._run("get_kpis", {}, ctx)
            ctx["intent"] = "kpi"
            did = True
        elif re.search(r"(explain|describe|walk me through|overview|summar\w+|how (does|do|is|are))\b.*\b(process|production|plant|factory|line|flow|car (is )?(built|made|assembled)|cars? (are )?(built|made|assembled)|works?)\b", ql) \
                and not re.search(r"\b(m\d{2}|s\d{2})\b|oee|mtbf|mttr|\brul\b|shap|takt|loto|work order|fault|wrong|red\b", ql):
            ctx["intent"] = "process"
            did = True
        elif re.search(r"what (does|do|is)\b.*\b(do|for)\b|tell me about|describe|what happens (at|in)", ql) and \
                not re.search(r"\bwrong|red|alarm|fault|fail", ql):
            self._run("search_docs", {"query": q, "doc_type": ["station", "station_failures"], "k": 3}, ctx)
            ctx["intent"] = "describe"
            did = True
        elif mid and re.search(r"what (happens|would happen)|what if|if (the |it )?.*(stops?|fails?|breaks?|goes down|is down)", ql) \
                and re.search(r"stops?|fails?|break|down|jam", ql):
            self._run("run_scenario", {"machine_id": mid, "hours": 30, "op": "inject_fault"}, ctx)
            ctx["intent"] = "whatif_fault"
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
        ctx["mids"] = mids
        return mid


    # ---- structured report: the one output format every answer follows ---------
    SECTIONS = (("what_happened", "WHAT HAPPENED"), ("impact", "IMPACT"), ("do_now", "DO NOW"),
                ("contacts", "WHO TO PAGE"), ("parts", "PART"), ("procedure", "PROCEDURE"))

    @staticmethod
    def _card(r):
        sev = {"critical": "CRITICAL", "warning": "WARNING", "ok": "OK", "info": "INFO"}.get(r["severity"], "INFO")
        L = [f"{r['title']}  |  {sev}", r["headline"]]
        for key, label in Brain.SECTIONS:
            v = r.get(key)
            if not v:
                continue
            L.append("")
            L.append(label)
            if key == "do_now":
                L += [f"{i}. {x}" for i, x in enumerate(v, 1)]
            else:
                L += [f"- {x}" for x in v]
        if r.get("sources"):
            L += ["", "Sources: " + " ".join(f"[{x}]" for x in r["sources"])]
        return "\n".join(L)

    @staticmethod
    def _what(st):
        w = re.sub(r"\*\*", "", st["what_happens"]).strip().rstrip(".")
        if "Hero scenario" in w:
            w = "Second weld robot (M05) welds the body; this is where the demo's bearing wear develops"
        return w + "."

    def _process_steps(self):
        """Stations in material-flow order (from the station book's upstream/downstream links), then the support areas."""
        import json as _json
        book = _json.loads((config.BRAIN_DIR / "data" / "out" / "stations.json").read_text())["stations"]
        # line order is the station numbering (S01 coil yard ... S09 pack and end-of-line test); S08 feeds S09 from the side
        order = sorted(k for k, v in book.items() if v.get("upstream") or v.get("downstream"))
        seen = set(order)
        support = [k for k in book if k not in seen]
        return book, order, support

    def _report(self, ctx):
        """Build the structured report for the matched intent from tool results. None if not covered."""
        raw = {}
        for n, a, o in ctx.get("raw", []):
            raw.setdefault(n, []).append((a, o))
        first = lambda name, pred=lambda a, o: True: next((o for a, o in raw.get(name, []) if pred(a, o)), None)
        intent, mid = ctx.get("intent"), ctx.get("mid")
        g = self.g
        m = g.get_machine(mid) if mid else None
        name = f"{mid} {m['name']}" if m else (mid or "Plant")
        st_id = (m or {}).get("twin_station")
        title = name + (f" (station {st_id})" if st_id else "")
        esc = first("escalation_chain")
        src = []

        def contacts(e, n=3):
            out = []
            for l in (e or {}).get("chain", [])[1:1 + n]:
                lvl = l["level"].split("_")[0]
                after = "now" if lvl == "L1" else f"after {l.get('page_after_min')} min if no answer"
                out.append(f"{lvl} {l.get('name')} ({l.get('role')}), {self._contact(l)}: {after}")
            return out

        if intent == "page" and esc and "chain" in esc:
            src.append(esc["id"])
            return {"title": title, "severity": "info", "headline": f"On shift {esc['shift']}, page in this order.",
                    "what_happened": [], "impact": [], "do_now": [esc["operator_action"]] if esc.get("operator_action") else [],
                    "contacts": [f"L0 {esc['chain'][0].get('name')} (line lead), {self._contact(esc['chain'][0])}"] + contacts(esc)
                    + [f"Beyond L3: {esc['vendor']['vendor']} hotline {esc['vendor']['hotline']}"],
                    "sources": src, "intent": intent}

        if intent == "whatif_fault":
            sc = first("run_scenario")
            if not (sc and "kpis" in sc):
                return None
            k = sc["kpis"]
            u0, u1 = (k.get("units") or {}).get("baseline"), (k.get("units") or {}).get("scenario")
            c0, c1 = k.get("cost_baseline_usd"), k.get("cost_usd")
            lost = (u0 - u1) if (u0 is not None and u1 is not None) else None
            head = f"If {name} stops for 30 minutes: " + (f"about {lost:.0f} fewer cars" if lost is not None else "output drops") + \
                   (f" and ${c1 - c0:,.0f} extra downtime cost." if c0 is not None and c1 is not None else ".")
            imp = [f"Downtime {k['downtime_min']['scenario']} min versus {k['downtime_min']['baseline']} min."]
            if (k.get("oee") or {}).get("scenario") is not None:
                imp.append(f"OEE {k['oee']['scenario']} versus {k['oee']['baseline']}.")
            return {"title": title, "severity": "warning", "headline": head,
                    "what_happened": [sc["about"]] if sc.get("about") else [], "impact": imp,
                    "do_now": ["Keep a technician and the likely spare part ready; the line starves downstream and blocks upstream while it is down."],
                    "sources": [], "intent": intent}

        if intent == "process":
            book, order, support = self._process_steps()
            steps = [f"{k} {book[k]['name']}: {self._what(book[k])}" for k in order]
            sup = [f"{k} {book[k]['name']}: {self._what(book[k])}" for k in support]
            return {"title": "How the plant builds a car", "severity": "info", "intent": intent,
                    "headline": f"Coils become cars through {len(order)} stations, then three support areas keep the line running.",
                    "what_happened": steps, "impact": ["The belt is paced at one car every 90 seconds (takt); a stopped station starves or blocks its neighbours."],
                    "procedure": sup, "sources": ["STATIONS"]}

        if intent == "kpi":
            k = first("get_kpis")
            if not k or k.get("units") is None:
                return None
            plan = k.get("plan_units")
            line = f"{k['units']} cars so far this shift" + (f" against a plan of {plan}." if plan else ".")
            imp = []
            if k.get("oee") is not None:
                imp.append(f"OEE {k['oee']}, throughput {k.get('throughput_per_hour')} cars per hour.")
            if k.get("downtime_min") is not None:
                imp.append(f"Downtime {k['downtime_min']} min, about ${k.get('downtime_cost_usd', 0):,}.")
            note = []
            if re.search(r"yesterday|last (week|month|shift)|previous", ctx.get("q", "").lower()):
                note.append("I only have the current shift live, not earlier days.")
            return {"title": "Plant output", "severity": "info", "headline": line, "what_happened": note, "impact": imp,
                    "sources": [], "intent": intent}

        if intent == "work_order":
            wo = first("create_work_order")
            if wo and wo.get("id"):
                src.append(wo["id"])
                return {"title": title, "severity": "info", "headline": f"Work order {wo['id']} created.",
                        "what_happened": [f"Component {wo.get('component_id') or 'not specified'}; fault {wo.get('fault_code') or 'not specified'}."],
                        "impact": [f"Downtime costs about ${wo.get('downtime_cost_per_min'):,} per minute until it is fixed."],
                        "do_now": ["A technician is dispatched; the engine opens the work order."],
                        "parts": [wo["spare_part"]] if wo.get("spare_part") else [], "sources": src, "intent": intent}

        if intent == "keep_running":
            sc, stt = first("run_scenario"), first("get_sensor_state")
            if not (sc and "kpis" in sc):
                return None
            k, h = sc["kpis"], sc["query"]["hours"]
            rul_h, rul_low = sc.get("rul_hours_at_alert"), sc.get("rul_low_hours")
            rule = next((x for x in ctx["retrieved"] if x["source_id"] == "SOP-OPS-02"), None)
            beyond = (rul_h is not None and h > rul_h) or sc.get("matched_scenario") == "hero_ignored"
            over_rule = h > 1.0
            verdict = ("NO. Longer than the remaining life; failure is likely." if beyond else
                       "NOT RECOMMENDED. Exceeds the SOP-OPS-02 limit for a rising trend." if over_rule else
                       "ONLY the current batch, with supervisor approval.")
            sev = "critical" if beyond else "warning"
            cost, cost_b = k.get("cost_usd"), k.get("cost_baseline_usd")
            imp = [f"Downtime {k['downtime_min']['scenario']} min if you wait, versus {k['downtime_min']['baseline']} min if repaired now."]
            if cost is not None and cost_b is not None:
                imp.append(f"Downtime cost ${cost:,.0f} versus ${cost_b:,.0f}.")
            imp.append(f"OEE {k['oee']['scenario']} versus {k['oee']['baseline']}.")
            if rul_h is not None:
                imp.append(f"Predicted remaining life {rul_h * 60:.0f} min" + (f" (safe lower bound {rul_low * 60:.0f} min)." if rul_low else "."))
            do = ["Repair at the next buffer-protected stop; do not plan to run past the remaining life."]
            if over_rule:
                do.insert(0, "Anything beyond the current batch needs written Maintenance Manager approval, 15-minute re-checks and a technician on standby.")
            if rule:
                src.append("SOP-OPS-02")
            return {"title": title, "severity": sev, "headline": f"Keep running {h:g} more hours? {verdict}",
                    "what_happened": [sc.get("about")] if sc.get("about") else [], "impact": imp, "do_now": do,
                    "contacts": contacts(first("escalation_chain")), "sources": src, "intent": intent}

        if intent == "repeats":
            r = first("graph_lookup", lambda a, o: "count_in_window" in o)
            wos = first("graph_lookup", lambda a, o: "work_orders" in o) or {}
            if r and "count_in_window" in r:
                ids = [w["wo_id"] for w in wos.get("work_orders", [])]
                src += ids[:3]
                n = r["count_in_window"]
                return {"title": title, "severity": "warning" if n >= 2 else "info",
                        "headline": f"{ctx.get('code')} happened {n} times in the last {r['window_days']} days.",
                        "what_happened": [f"{r['total']} times in the whole history; latest {r['latest'][:10]}."],
                        "impact": ["Repeat faults should be treated as at least warning level (SOP-OPS-02)."] if n >= 2 else [],
                        "do_now": ["Ask the engineer for a root-cause review if it keeps coming back."] if n >= 2 else [],
                        "sources": src, "intent": intent}
            return None

        if intent in ("fault_code", "parts"):
            fm = first("graph_lookup", lambda a, o: "fault_modes" in o)
            if not fm:
                return None
            code = ctx.get("code")
            modes = fm["fault_modes"]
            f = next((x for x in modes if x["code"] == code), None) or (next((x for x in modes if x["code"] == "bearing_wear"), None) if mid == "M05" else None) or (modes[0] if modes else None)
            if not f:
                return None
            if f.get("documents"):
                src.append(f["documents"][0])
            parts = [f"{p['part_no']} ({p['description']})" + (f", {p['on_hand']} in stock" if p.get("on_hand") is not None else "") for p in f["parts"]]
            return {"title": title, "severity": "info", "headline": f"{f['code']}: {f['description']}.",
                    "what_happened": ["Likely causes: " + "; ".join(c for c in f["causes"] if c)] if any(f["causes"]) else [],
                    "impact": [("Shows in " + ", ".join(f"{s['channel']} ({s['shape']})" for s in f["sensors"]))] if f["sensors"] else [],
                    "parts": parts, "sources": src, "intent": intent}

        if intent == "sop":
            res = first("search_docs") or {}
            seen, lines = [], []
            for r in res.get("results", []):
                if r["id"] not in seen:
                    seen.append(r["id"])
                    lines.append(f"{r['id']}: " + r["text"].split("\n", 1)[0].strip("[]").split(": ", 1)[-1])
            if not lines:
                return None
            return {"title": "Procedures", "severity": "info", "headline": f"{len(lines)} relevant procedure(s).",
                    "procedure": lines, "sources": seen[:4], "intent": intent}

        if intent == "status":
            stt = first("get_sensor_state")
            if not stt:
                return None
            alert = stt.get("alert") or {}
            sev_raw = alert.get("severity") or stt.get("status")
            stopped = stt.get("machine_state") in ("fault", "repair", "down") or stt.get("status") in ("fault", "repair")
            sev = "critical" if (sev_raw in ("critical", "fault", "repair") or stopped) else "warning" if sev_raw in ("warning", "watch") else "ok"
            fm = first("graph_lookup", lambda a, o: "fault_modes" in o)
            want = stt.get("storyline_fault") or ("bearing_wear" if mid == "M05" and (alert or stt.get("vib_multiple", 0) and stt["vib_multiple"] > 1.2) else None)
            f = next((x for x in (fm or {}).get("fault_modes", []) if x["code"] == want), None) if want else None
            what = []
            if stopped:
                what.append(f"{name} is stopped ({stt.get('machine_state') or stt.get('status')}).")
            if f:
                what.append(f"{f['description']} ({f['code']}).")
                if any(f["causes"]):
                    what.append("Likely cause: " + f["causes"][0].lower() + ".")
            if stt.get("vib_multiple") and stt["vib_multiple"] > 1.05:
                what.append(f"Vibration is {stt['vib_multiple']}x the healthy level.")
            if alert.get("contributors"):
                top = [c for c in alert["contributors"] if c.get("shap") is not None][:2]
                if top:
                    what.append("Flagged because of: " + ", ".join(c["signal"] for c in top) + ".")
            impact = []
            if stt.get("remaining_useful_life_min") and not stopped:
                impact.append(f"About {stt['remaining_useful_life_min']:.0f} minutes of useful life left.")
            aff = [f"{a['station']} {a['state']}" for a in (stt.get("affected_stations") or []) if a.get("state") not in ("run", "micro")][:4]
            if aff:
                impact.append("Affected stations: " + ", ".join(aff) + ".")
            if stopped:
                impact.append("Downtime costs about $38,000 per minute.")
            wos = stt.get("open_work_orders") or []
            if wos:
                impact.append("Open work order: " + ", ".join(w["id"] for w in wos[:2]) + ".")
                src += [w["id"] for w in wos[:2]]
            do = []
            if stopped:
                do.append("Operator: press the andon, tell the line lead, note the time.")
            l1 = next((l for l in (esc or {}).get("chain", []) if l["level"] == "L1_primary_tech"), None)
            if l1 and (sev != "ok"):
                do.append(f"Page L1 {l1['name']} ({l1.get('extension')}) now.")
            part = (f["parts"][0] if f and f["parts"] else None)
            if part and sev != "ok":
                do.append(f"Bring {part['part_no']} from the spares cage (S12)" + (f"; {part['on_hand']} in stock." if part.get("on_hand") is not None else "."))
            sop = next((x for x in ctx["retrieved"] if x["source_id"].startswith("SOP-") and
                        not (re.match(r"SOP-[A-Z]+-(M\d\d)-\d+", x["source_id"]) and re.match(r"SOP-[A-Z]+-(M\d\d)-\d+", x["source_id"]).group(1) != mid)), None)
            if sop and sev != "ok":
                do.append(f"Follow {sop['source_id']}.")
                src.append(sop["source_id"])
            if sev == "ok":
                do = ["Nothing to do. Keep watching vibration and temperature."]
            if esc and sev != "ok":
                src.append(esc["id"])
            headline = {"critical": "Needs action now." , "warning": "Needs attention soon.", "ok": "Running normally."}[sev]
            return {"title": title, "severity": sev, "headline": headline, "what_happened": what, "impact": impact, "do_now": do,
                    "contacts": contacts(esc, 2) if sev != "ok" else [], "parts": [f"{part['part_no']} ({part['description']})"] if part and sev != "ok" else [],
                    "procedure": [sop["source_id"]] if sop and sev != "ok" else [], "sources": list(dict.fromkeys(src)), "intent": intent}
        return None


    # ---- conversational fallback: what to say when no card applies --------------
    _STOP = set("the a an is are was were do does did how what why who when where which can could should would to of in on for "
                "and or it this that with at by from be as i we you my our me us tell about please there any some".split())
    _TYPE_W = {"sop": 3.0, "manual": 3.0, "station": 3.0, "station_failures": 3.0, "machine_profile": 2.0, "rca": 2.0,
               "incident": 2.0, "employee": 2.0, "vendor": 2.0, "escalation": 1.0, "service_log": 1.0,
               "work_order": 0.5, "shift_handover": 0.5}
    _LABEL = {"sop": "the procedure", "manual": "the machine manual", "station": "the station record",
              "station_failures": "the failure catalogue", "rca": "the root-cause report", "incident": "an incident report",
              "employee": "the staff list", "vendor": "the vendor record", "machine_profile": "the machine profile",
              "service_log": "a vendor service log", "work_order": "a past work order", "shift_handover": "a shift handover note",
              "escalation": "the escalation list"}

    @staticmethod
    def _clean_text(t):
        out = []
        for line in t.splitlines():
            l = line.strip()
            if not l or l.startswith("[") and l.endswith("]"):
                continue
            if "Synthetic training document" in l or l.startswith("**Area:**") or l.startswith("> **Synthetic"):
                continue
            l = re.sub(r"[#>*`]+", "", l)
            l = re.sub(r"^\s*[-\d.)]+\s+", "", l)
            l = re.sub(r"\s+", " ", l).strip()
            if l:
                out.append(l)
        return " ".join(out)

    def _best_sentences(self, text, question, n=2):
        words = {w for w in re.findall(r"[a-z0-9\-]+", question.lower()) if w not in self._STOP and len(w) > 2}
        sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", self._clean_text(text)) if len(x.strip()) > 25]
        if not sents:
            return ""
        scored = sorted(((len(words & set(re.findall(r"[a-z0-9\-]+", x.lower()))), -i, x) for i, x in enumerate(sents)), reverse=True)
        picked = sorted(scored[:n], key=lambda t: -t[1])
        return " ".join(x for _, _, x in picked)[:420]

    def _suggestions(self, focus):
        m = focus[0] if focus else "M05"
        return [f"Why is {m} red?", f"Who do I page for {m}?", f"Can we keep running {m} 2 more hours?"]

    def _confidence_from_search(self, ctx):
        hits = ctx.get("search") or []
        if not hits:
            return "low", 0.0, "nothing retrieved"
        best = max(hits, key=lambda h: h["bm25"] * self._TYPE_W.get(h["type"], 1.0))
        score = min(1.0, best["bm25"] / 15.0) * 0.7 + max(0.0, min(1.0, (best["dense"] - 0.55) / 0.3)) * 0.3
        if best["bm25"] < 3:
            return "low", round(score, 2), "no keyword overlap with the plant records"
        return ("high" if score >= 0.6 else "medium" if score >= 0.35 else "low"), round(score, 2), f"best match {best['source_id']}"

    def _fallback(self, question, ctx, focus):
        """Plain, direct answer when no structured card applies. Never sounds like a model disclaimer."""
        ql = question.lower().strip()
        sug = self._suggestions(focus)
        tips = "Try: " + " / ".join(f'"{x}"' for x in sug)
        report = {"title": "Plant brain", "severity": "info", "intent": "fallback", "what_happened": [], "sources": []}

        def done(text, level, score, reason, head=None):
            report.update(headline=head or text.split("\n")[0], confidence={"level": level, "score": score, "reason": reason},
                          suggestions=sug)
            ctx["report"] = report
            return text

        if re.match(r"^(hi|hello|hey|good (morning|afternoon|evening)|yo)\b", ql):
            return done("Hi. I'm watching the plant. Ask me about any machine or station, or click a station in the 3D view.\n" + tips,
                        "high", 1.0, "greeting")
        if re.search(r"\b(thanks|thank you|cheers|great)\b", ql) and len(ql) < 40:
            return done("Anytime. Ask me the next one when you're ready.", "high", 1.0, "thanks")
        if re.search(r"what can you do|what do you do|how (do|can) i use|help me|who are you|what are you", ql):
            return done("I can tell you why a machine is alarming, what is likely wrong, who to page, which part and procedure apply, "
                        "and what happens if you keep running. Click a station in the 3D view and I'll focus on it.\n" + tips,
                        "high", 1.0, "capabilities")
        if re.search(r"\bjoke\b|weather|football|cricket|news|stock price|movie", ql):
            return done("That one is outside the plant. I can help with machines, stations, faults, parts and who to call.\n" + tips,
                        "low", 0.0, "off topic")
        gm = re.search(r"(what is|what's|what are|explain|define|meaning of|what does)\s+(a |an |the )?(oee|mtbf|mttr|rul|shap|andon|takt|loto|bom|rca|pm)\b", ql)
        if gm:
            G = {"oee": "OEE (overall equipment effectiveness) is availability x performance x quality: how much of the planned production time the line really produces good cars.",
                 "mtbf": "MTBF is mean time between failures: the average running time before a machine breaks.",
                 "mttr": "MTTR is mean time to repair: the average time from a breakdown to the machine running again.",
                 "rul": "RUL is remaining useful life: the model's estimate of how many minutes a machine can keep running before it fails.",
                 "shap": "SHAP values show which signals pushed the anomaly score up, so you can see why a machine was flagged.",
                 "andon": "The andon is the light and button at a station that calls the line lead when something is wrong. Press it first when a machine stops.",
                 "takt": "Takt is the pace of the line: one car every 90 seconds here.",
                 "loto": "LOTO (lockout/tagout) is isolating and locking a machine's energy before anyone works on it. The procedure is SOP-SAF-01.",
                 "bom": "A BOM is the bill of materials: the list of parts that go into a car.",
                 "rca": "An RCA is a root-cause analysis written after a significant failure.",
                 "pm": "PM is preventive maintenance: planned checks and part changes to stop failures before they happen."}
            if gm.group(3) == "loto":
                ctx["cite"].add("SOP-SAF-01")
            return done(G[gm.group(3)] + (" [SOP-SAF-01]" if gm.group(3) == "loto" else ""), "high", 1.0, "glossary")
        if "andon" in ql and re.search(r"reset|clear|turn off|acknowledge|how", ql):
            ctx["cite"].add("SOP-OPS-01")
            return done("The andon is the light and button that calls the line lead to a stopped station. The line lead clears it once the "
                        "station is running again. I don't have a step-by-step reset in the plant records; the restart rules are in "
                        "SOP-OPS-01 (line restart after a shutdown) [SOP-OPS-01].", "medium", 0.6, "partial: no reset steps recorded")
        area = re.search(r"\b(paint|painting|stamping|general assembly|drive unit|e-axle|trim|chassis|body shop|body-in-white|logistics|utilities)\b", ql)
        if area:
            try:
                stn = json.loads((config.BRAIN_DIR / "data" / "out" / "stations.json").read_text())["stations"]
                line = " -> ".join(f"{k} {v['name']}" for k, v in stn.items() if k in [f"S{i:02d}" for i in range(1, 10)])
                return done(f"This plant has no separate {area.group(1)} area. The line runs {line}. Ask about any of those, "
                            "or click one in the 3D view.", "high", 0.8, "area not in this plant")
            except Exception:  # noqa: BLE001
                pass
        if re.search(r"\b(order|buy|purchase|reorder|raise a po)\b", ql) and re.search(r"part|bearing|spare|seal|filter|motor", ql):
            n = self.g.g.nodes.get("bearing_6208", {}) if "bearing" in ql else {}
            extra = (f" Bearing 6208 for M05: {n.get('on_hand')} in stock at the spares cage (S12), lead time {n.get('lead_time_days')} days. "
                     "Ask purchasing to reorder once stock drops below 1.") if n else ""
            return done("I can't place purchase orders from here." + extra, "high", 0.9, "action outside scope")
        bad = [m for m in re.findall(r"\bM(\d{1,3})\b", question, re.I) if f"M{int(m):02d}" not in self.g.machines]
        if bad:
            ids = ", ".join(sorted(k for k in self.g.machines if re.fullmatch(r"M\d\d", k)))
            return done(f"There is no M{int(bad[0]):02d} in this plant. The line machines are {ids}.\n" + tips,
                        "high", 0.9, "unknown machine id")

        level, score, reason = self._confidence_from_search(ctx)
        hits = ctx.get("search") or []
        live = ""
        if focus and level != "high":
            try:
                st = self.sim.get_sensor_state(focus[0], self.g)
                if st.get("status") and st["status"] not in ("unknown",):
                    live = f"{focus[0]} is {st['status']} right now" + (f", vibration {st['vib_multiple']}x normal" if st.get("vib_multiple") and st["vib_multiple"] > 1.05 else "") + ". "
                    ctx["machines"].append(focus[0])
            except Exception:  # noqa: BLE001
                pass
        if level == "low":
            return done(f"{live}I don't have anything specific on that in the plant records. "
                        "I can answer questions about machines, stations, faults, parts, procedures and who to page.\n" + tips,
                        "low", score, reason, "No specific record found.")
        best = max(hits, key=lambda h: h["bm25"] * self._TYPE_W.get(h["type"], 1.0))
        title = ""
        if best["type"] == "sop":
            same = [h for h in hits if h["source_id"] == best["source_id"]]
            purpose = next((h for h in same if re.search(r"##\s*Purpose", h["text"])), None)
            if purpose:
                best = purpose
            mt = re.match(r"\[[A-Z0-9\-]+: ([^\]]+)\]", best["text"])
            title = mt.group(1) if mt else ""
        sent = self._best_sentences(best["text"], question)
        words = {w for w in re.findall(r"[a-z0-9\-]+", ql) if w not in self._STOP and len(w) > 2}
        chunk_words = set(re.findall(r"[a-z0-9\-]+", (best.get("text", "") + " " + best.get("source_id", "")).lower()))
        overlap = max(len(words & set(re.findall(r"[a-z0-9\-]+", sent.lower()))), len(words & chunk_words) - 1)
        if best["dense"] >= 0.78 and best["bm25"] >= 15:      # strong semantic and keyword agreement
            overlap = max(overlap, 2)
        if best["type"] == "employee":
            mm = re.search(r"([A-Z][\w .'-]+?) \((BAP-E\d+|[A-Z]-[A-Z]+\d+)\) - ([^,]+)", self._clean_text(best["text"]).replace("*", ""))
            ph = re.search(r"Contact: ([^\[]+)", self._clean_text(best["text"]))
            if mm:
                sent = f"{mm.group(1).strip()} is the {mm.group(3).strip()}." + (f" Contact: {ph.group(1).strip().split(',')[0]}." if ph else "")
                overlap = 3
        if sent and overlap < (1 if len(words) <= 2 else 2) and best["type"] != "employee":
            return done(f"{live}I don't have a record that answers that. "
                        "I can answer questions about machines, stations, faults, parts, procedures and who to page.\n" + tips,
                        "low", min(score, 0.3), "retrieved text does not match the question terms", "No specific record found.")
        if not sent:
            return done(f"{live}That isn't something the plant records cover.\n" + tips, "low", score, "no usable sentence")
        label = self._LABEL.get(best["type"], "the plant records")
        ctx["cite"].add(best["source_id"])
        ctx["retrieved"].append({"source_id": best["source_id"], "chunk_id": "", "text": best["text"]})
        lead = "From " + label + ": " if level == "high" else "The closest thing I have is " + label + ": "
        if title:
            lead = f"From {best['source_id']}, {title}: " if level == "high" else f"The closest thing I have is {best['source_id']}, {title}: "
        text = f"{live}{lead}{sent} [{best['source_id']}]"
        if level != "high" and best["type"] != "employee":
            text += "\nIf that isn't what you meant, tell me the machine or station.\n" + tips
        elif level != "high":
            text = text.replace("The closest thing I have is the staff list: ", "")
        report["sources"] = [best["source_id"]]
        return done(text, level, score, reason, sent.split(". ")[0][:140])

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

        if intent == "process":
            book, order, support = self._process_steps()
            return "\n".join(["How the plant builds a car:"] + [f"{i + 1}. {k} {book[k]['name']}: {self._what(book[k])}" for i, k in enumerate(order)]
                              + ["Support areas:"] + [f"- {k} {book[k]['name']}: {self._what(book[k])}" for k in support])

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

    def _ollama_chat(self, system, user, json_mode=False, num_predict=600):
        import urllib.request
        body = {"model": config.pick_model(), "stream": False, "keep_alive": "30m",
                "options": {"temperature": 0.1, "num_ctx": config.OLLAMA_NUM_CTX, "num_predict": num_predict},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        if json_mode:
            body["format"] = "json"
        r = urllib.request.Request(config.OLLAMA_URL.rstrip("/") + "/api/chat", data=json.dumps(body).encode(),
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=config.LLM_TIMEOUT) as resp:
            return json.loads(resp.read().decode())["message"]["content"].strip()

    _NO_LLM_REASONS = ("greeting", "thanks", "capabilities", "off topic", "unknown machine id", "glossary", "area not in this plant",
                       "action outside scope")

    def _assist(self, question, ctx, history):
        """Optional LLM phrasing of the deterministic result, behind the grounding guard. Returns (reply, info)."""
        if config.LLM_MODE != "assist":
            return None, None
        rep = ctx.get("report")
        info = {"mode": "assist", "model": config.pick_model(), "used": False}
        if time.time() < getattr(self, "_llm_pause_until", 0):          # circuit breaker after repeated timeouts/errors
            info["guard"] = "paused after repeated failures"
            return None, info
        try:
            if rep and rep.get("intent") not in (None, "fallback"):
                keep = {k: rep.get(k) for k in ("title", "severity", "headline", "what_happened", "impact", "do_now",
                                                  "contacts", "parts", "procedure") if rep.get(k)}
                facts = "CARD:\n" + json.dumps(keep, ensure_ascii=False) + "\n\nTOOL RESULTS:\n" + "\n".join(ctx["tool_outputs"])[:3500]
                system = prompts.NARRATE_SYSTEM
                allowed = set(ctx["cite"]) | set(rep.get("sources") or [])
            elif rep and rep.get("intent") == "fallback" and \
                    (rep.get("confidence") or {}).get("reason") not in self._NO_LLM_REASONS:
                hits = [h for h in (ctx.get("search") or []) if h["bm25"] > 0][:4]
                if not hits:
                    return None, info
                facts = "PASSAGES:\n" + "\n".join(f"[{h['source_id']}] {self._clean_text(h['text'])[:700]}" for h in hits)
                system = prompts.ANSWER_SYSTEM
                allowed = {h["source_id"] for h in hits}
            else:
                return None, info
            raw = self._ollama_chat(system, prompts.build_user(question, facts, allowed, history), json_mode=True, num_predict=350)
            reply, _src, _clar = prompts.parse_reply(raw)
            ok, why = prompts.validate_reply(reply, facts + " " + question, allowed)
            info.update(used=ok, guard=why)
            self._llm_fails = 0
            if ok:
                ctx["cite"].update(c for c in re.findall(r"\[([A-Za-z0-9_.:\-]+)\]", reply) if c in allowed)
                return reply, info
        except Exception as e:  # noqa: BLE001
            info.update(guard=f"error: {type(e).__name__}")
            self._llm_fails = getattr(self, "_llm_fails", 0) + 1
            if self._llm_fails >= 2:                                      # stop paying the timeout on every question
                self._llm_pause_until = time.time() + 300
                self._llm_fails = 0
        return None, info

    def _local(self, question, history, ctx, focus, shift):
        self._route(question, ctx, focus, shift)
        if config.get("LOCAL_NARRATE", "0") != "1":
            rep = self._report(ctx)
            if rep:
                ctx["report"] = rep
                return self._card(rep)
            text = self._render(ctx)
            if text:
                ctx.setdefault("report", None)
                return text
            return self._fallback(question, ctx, focus or ctx.get("mids") or [])
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

    def ask(self, question, session_id="default", shift=None, premium=False, focus_hint=None):
        t0 = time.time()
        sess = self.sessions.setdefault(session_id, {"history": []})
        focus = self.g.find_machines(question) or list(focus_hint or [])
        key = hashlib.sha1(json.dumps([PROMPT_VERSION, config.LLM_MODE, config.pick_model() if config.LLM_MODE == "assist" else "", "render-v17", config.get("SIM_MODE", "mock"), config.get("LOCAL_NARRATE", "0"), question.strip().lower(), shift or current_shift(),
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
            follow = len(question.split()) <= 9 and re.search(
                r"\b(it|its|this|that|there|here|them)\b|^(and|so|what should|how long|why|who do|who should)\b", question.lower())
            answer = self._local(question if not shift else q, sess["history"], ctx,
                                 focus or (sess.get("focus", []) if follow else []), shift)
            used = "ollama:" + config.pick_model() if ctx["llm_calls"] else "local-pipeline"
        except Exception as e:  # noqa: BLE001
            err = f"ollama: {type(e).__name__}: {str(e)[:160]}"
        llm_info = None
        if answer is not None:
            reply, llm_info = self._assist(question, ctx, sess["history"])
            if reply:
                ctx["card_text"] = answer
                answer = reply
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
            "card": ctx.get("card_text"),
            "report": ctx.get("report"),
            "confidence": (ctx.get("report") or {}).get("confidence") or {"level": "high", "score": 0.9, "reason": "matched a known question type"},
            "highlight": {"machine_ids": mids[:8], "graph_path": self.graph_path_for(ctx)},
            "citations": citations,
            "actions": ctx["actions"],
            "meta": {"model": used, "degraded": degraded, "error": err if degraded else None,
                     "llm_calls": ctx["llm_calls"], "contexts": ctx["tool_outputs"][:10], "sources_consulted": list(dict.fromkeys(r["source_id"] for r in ctx["retrieved"]))[:12], "tools": [t["tool"] for t in ctx["trace"]],
                     "shift": shift or current_shift(), "sim_mode": self.sim.mode,
                     "latency_s": round(time.time() - t0, 2), "cached": False, "llm": llm_info},
        }
        if not degraded and not live:
            self.cache.put(key, result)
        if mids:
            sess["focus"] = mids[:2]
        sess["history"] += [{"role": "user", "text": question}, {"role": "model", "text": answer}]
        sess["history"] = sess["history"][-8:]
        return result
