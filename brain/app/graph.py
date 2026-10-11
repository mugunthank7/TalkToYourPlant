"""Deterministic knowledge graph over brain/data/out (no LLM extraction).

Built with NetworkX from rag/graph_nodes.jsonl + rag/graph_edges.jsonl, enriched with
master/*.csv|json (employees, escalation matrix, machines) and logs/work_orders.jsonl.

Node ids follow the dataset: MACHINE:<id>, FAMILY:<key>, FAULT:<fam>:<code>, EMP:<id>,
WO:<id>, DOC:<id>, PART:<no>, plus the twin hero nodes (vibration_high, bearing_wear,
m05_joint1_bearing, replace_bearing, bearing_6208).
All public methods accept ids with or without the type prefix.
"""
import csv
import json
import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import networkx as nx

from . import config

DATA = config.BRAIN_DIR / "data" / "out"
SHIFTS = {"A": (6, 14), "B": (14, 22), "C": (22, 6)}


def current_shift(now=None):
    h = (now or datetime.now()).hour
    return "A" if 6 <= h < 14 else "B" if 14 <= h < 22 else "C"


def _jsonl(p):
    with open(p) as f:
        return [json.loads(l) for l in f if l.strip()]


class PlantGraph:
    def __init__(self, data_dir=DATA):
        self.dir = Path(data_dir)
        self.g = nx.MultiDiGraph()
        self._wo_by_machine = None
        self._load()

    # ------------------------------------------------------------ build
    def _load(self):
        for n in _jsonl(self.dir / "rag/graph_nodes.jsonl"):
            self.g.add_node(n["id"], **{k: v for k, v in n.items() if k != "id"})
        for e in _jsonl(self.dir / "rag/graph_edges.jsonl"):
            attrs = {k: v for k, v in e.items() if k not in ("source", "target", "rel")}
            self.g.add_edge(e["source"], e["target"], key=None, rel=e["rel"], **attrs)
        self.employees = {}
        with open(self.dir / "master/employees.csv", newline="") as f:
            for r in csv.DictReader(f):
                self.employees[r["employee_id"]] = r
        self.escalation = {m["machine_id"]: m for m in json.load(open(self.dir / "master/escalation_matrix.json"))}
        self.machines = {}
        with open(self.dir / "master/machines.csv", newline="") as f:
            for r in csv.DictReader(f):
                self.machines[r["machine_id"]] = r
        # twin ids <-> voltara ids
        self.alias = {}
        for mid, r in self.machines.items():
            self.alias[mid.lower()] = mid
            if r.get("voltara_id"):
                self.alias[r["voltara_id"].lower()] = mid
            self.alias[r["name"].lower()] = mid
        # a few distinctive single words of twin machine names also resolve to the machine
        ok = {"conveyor", "decoiler", "stacker", "sealer", "fixture", "framing", "casting"}
        for mid, r in self.machines.items():
            if re.fullmatch(r"M\d\d", mid):
                for w in re.findall(r"[a-z]+", r["name"].lower()):
                    if w in ok:
                        self.alias.setdefault(w, mid)

    def _wos(self):
        if self._wo_by_machine is None:
            idx = {}
            for w in _jsonl(self.dir / "logs/work_orders.jsonl"):
                idx.setdefault(w["machine_id"], []).append(w)
            for v in idx.values():
                v.sort(key=lambda w: w.get("opened_ts") or "", reverse=True)
            self._wo_by_machine = idx
        return self._wo_by_machine

    # ------------------------------------------------------------ ids
    @staticmethod
    def _norm(x):
        return x if ":" in x else None

    def node_id(self, ident):
        """Resolve a loose id ('M05', 'CAS-GP-01', 'Giga Press 1') to a graph node id."""
        s = ident.strip()
        if s in self.g:
            return s
        for pre in ("MACHINE:", "EMP:", "WO:", "DOC:", "PART:", "FAMILY:", "FAULT:", "AREA:", "VENDOR:"):
            if pre + s in self.g:
                return pre + s
        mid = self.alias.get(s.lower())
        if mid and "MACHINE:" + mid in self.g:
            return "MACHINE:" + mid
        return None

    def machine_id(self, ident):
        nid = self.node_id(ident)
        if nid and nid.startswith("MACHINE:"):
            return nid.split(":", 1)[1]
        return None

    def find_machines(self, text, limit=5):
        """Entity linking: machine ids / names mentioned in free text."""
        t = text.lower()
        found = []
        for key, mid in self.alias.items():
            if len(key) >= 3 and re.search(r"(?<![a-z0-9-])" + re.escape(key) + r"(?![a-z0-9-])", t):
                if mid not in found:
                    found.append(mid)
        # voltara ids like 'cas-gp-01' without hyphen quirks are covered above
        return found[:limit]

    # ------------------------------------------------------------ queries
    def get_machine(self, ident):
        mid = self.machine_id(ident)
        if not mid:
            return None
        node = self.g.nodes["MACHINE:" + mid]
        row = self.machines.get(mid, {})
        fam = next((v for _, v, d in self.g.out_edges("MACHINE:" + mid, data=True) if d["rel"] == "INSTANCE_OF"), None)
        area = next((v for _, v, d in self.g.out_edges("MACHINE:" + mid, data=True) if d["rel"] == "LOCATED_IN"), None)
        return {
            "machine_id": mid, "name": node.get("name"), "criticality": node.get("criticality"),
            "family": fam.split(":", 1)[1] if fam else None,
            "family_name": self.g.nodes[fam].get("name") if fam else None,
            "area": area.split(":", 1)[1] if area else None,
            "voltara_id": row.get("voltara_id") or mid, "twin_station": row.get("twin_station") or None,
            "vendor": row.get("vendor"), "model": row.get("model"), "line": row.get("line"),
            "runtime_hours": row.get("runtime_hours"), "description": row.get("description"),
        }

    def neighbors(self, ident, edge_types=None, direction="both"):
        nid = self.node_id(ident)
        if not nid:
            return []
        out = []
        if direction in ("out", "both"):
            for _, v, d in self.g.out_edges(nid, data=True):
                if not edge_types or d["rel"] in edge_types:
                    out.append({"rel": d["rel"], "dir": "out", "id": v, **self._brief(v), **self._edge_attrs(d)})
        if direction in ("in", "both"):
            for u, _, d in self.g.in_edges(nid, data=True):
                if not edge_types or d["rel"] in edge_types:
                    out.append({"rel": d["rel"], "dir": "in", "id": u, **self._brief(u), **self._edge_attrs(d)})
        return out

    def _brief(self, nid):
        d = self.g.nodes[nid]
        return {"label": d.get("label"), "name": d.get("name") or d.get("title") or d.get("description") or d.get("code")}

    @staticmethod
    def _edge_attrs(d):
        return {k: v for k, v in d.items() if k != "rel"}

    def _emp(self, eid):
        r = self.employees.get(eid)
        if not r:
            return {"employee_id": eid}
        return {"employee_id": eid, "name": r["name"], "role": r["role"], "shift": r["shift"],
                "mobile": r["mobile"], "extension": r["extension"], "radio": r["radio"], "pager": r["pager_id"]}

    def escalation_chain(self, machine, shift=None, now=None):
        mid = self.machine_id(machine)
        if not mid or mid not in self.escalation:
            return None
        shift = (shift or current_shift(now)).upper()
        m = self.escalation[mid]
        chain = m["on_shift_chain"].get(shift)
        if chain is None:
            return None
        levels = [
            {"level": "L0_line_lead", **self._emp(chain["L0_line_lead"])},
            {"level": "L1_primary_tech", **self._emp(chain["L1_primary_tech"]), "page_after_min": m["escalation_minutes"]["L1_tech"]},
            {"level": "L2_backup_tech", **self._emp(chain["L2_backup_tech"]), "page_after_min": m["escalation_minutes"]["L2_backup"]},
            {"level": "L3_maintenance_supervisor", **self._emp(chain["L3_maintenance_supervisor"]), "page_after_min": m["escalation_minutes"]["L3_supervisor"]},
        ]
        eng = [{"level": f"L4_{k}", **self._emp(v)} for k, v in m["L4_engineers"].items()]
        return {
            "machine_id": mid, "shift": shift, "criticality": m["criticality"],
            "operator_action": chain.get("L0_operator_action"),
            "chain": levels, "engineers": eng, "vendor": m["L5_vendor"],
            "plant_management": m["L6_plant_mgmt"], "escalation_minutes": m["escalation_minutes"],
            "safety_triggers": m.get("safety_triggers", []),
            "source": f"escalation_matrix.json:{mid}",
        }

    def assigned_staff(self, machine, shift=None):
        nid = self.node_id(machine)
        if not nid:
            return []
        out = []
        for u, _, d in self.g.in_edges(nid, data=True):
            if d["rel"] == "ASSIGNED_TO" and (not shift or d.get("shift") == shift.upper()):
                out.append({**self._emp(u.split(":", 1)[1]), "assignment_role": d.get("role"), "assignment_shift": d.get("shift")})
        return out

    def fault_modes(self, machine):
        mid = self.machine_id(machine)
        if not mid:
            return []
        fam = next((v for _, v, d in self.g.out_edges("MACHINE:" + mid, data=True) if d["rel"] == "INSTANCE_OF"), None)
        if not fam:
            return []
        out = []
        for _, f, d in self.g.out_edges(fam, data=True):
            if d["rel"] != "HAS_FAULT_MODE":
                continue
            fd = self.g.nodes[f]
            parts, causes, sensors, docs = [], [], [], []
            for _, t, e in self.g.out_edges(f, data=True):
                td = self.g.nodes[t]
                if e["rel"] == "NEEDS_PART":
                    parts.append({"part_no": t.split(":", 1)[-1], "description": td.get("description") or td.get("name"),
                                  "unit_cost": td.get("unit_cost"), "on_hand": td.get("on_hand")})
                elif e["rel"] == "CAUSED_BY":
                    causes.append(td.get("text"))
                elif e["rel"] == "SHOWS_IN":
                    sensors.append({"channel": td.get("name"), "shape": e.get("shape")})
                elif e["rel"] == "DOCUMENTED_IN":
                    docs.append(t.split(":", 1)[-1])
            out.append({"fault_id": f, "code": fd.get("code") or f, "description": fd.get("description") or fd.get("name"),
                        "severity": fd.get("severity"), "source": fd.get("source"),
                        "parts": parts, "causes": causes, "sensors": sensors, "documents": docs})
        return out

    def recent_work_orders(self, machine, n=5, fault_code=None, wo_type=None):
        mid = self.machine_id(machine)
        if not mid:
            return []
        rows = self._wos().get(mid, [])
        if fault_code:
            rows = [w for w in rows if w.get("fault_code") == fault_code]
        if wo_type:
            rows = [w for w in rows if w.get("wo_type") == wo_type]
        keep = ("wo_id", "wo_type", "priority", "machine_id", "title", "opened_ts", "closed_ts", "status", "shift",
                "fault_code", "symptom", "diagnosis", "root_cause", "action_taken", "parts_used", "downtime_min",
                "assigned_tech", "escalation_level_reached", "sensor_snapshot")
        return [{k: w.get(k) for k in keep} for w in rows[:n]]

    def repeat_failures(self, machine, fault_code, days=90):
        rows = self.recent_work_orders(machine, n=10_000, fault_code=fault_code)
        if not rows:
            return {"count": 0}
        latest = max(w["opened_ts"] for w in rows)
        cutoff = datetime.fromisoformat(latest)
        n = sum(1 for w in rows if (cutoff - datetime.fromisoformat(w["opened_ts"])).days <= days)
        return {"fault_code": fault_code, "count_in_window": n, "window_days": days, "latest": latest, "total": len(rows)}

    def path_between(self, a, b, max_len=6):
        na, nb = self.node_id(a), self.node_id(b)
        if not na or not nb:
            return None
        und = self.g.to_undirected(as_view=True)
        try:
            p = nx.shortest_path(und, na, nb)
        except nx.NetworkXNoPath:
            return None
        if len(p) - 1 > max_len:
            return None
        hops = []
        for u, v in zip(p, p[1:]):
            rel = None
            if self.g.has_edge(u, v):
                rel = next(iter(self.g[u][v].values()))["rel"]
                direction = "out"
            else:
                rel = next(iter(self.g[v][u].values()))["rel"]
                direction = "in"
            hops.append({"from": u, "rel": rel, "dir": direction, "to": v})
        return {"nodes": [{"id": n, **self._brief(n)} for n in p], "hops": hops}

    # ------------------------------------------------------------ hero path for the twin
    def hero_graph_path(self, fault="bearing_wear"):
        """Ordered path for the twin's graph_path message, if the hero nodes exist."""
        order = [("vibration_high", "symptom"), ("bearing_wear", "failure_mode"),
                 ("m05_joint1_bearing", "component"), ("replace_bearing", "repair"), ("bearing_6208", "spare_part")]
        if not all(n in self.g for n, _ in order):
            return None
        return {"type": "graph_path", "nodes": [{"id": n, "kind": k} for n, k in order]}

    def stats(self):
        labels = {}
        for _, d in self.g.nodes(data=True):
            labels[d.get("label")] = labels.get(d.get("label"), 0) + 1
        return {"nodes": self.g.number_of_nodes(), "edges": self.g.number_of_edges(), "labels": labels}


@lru_cache(maxsize=1)
def get_graph():
    return PlantGraph()
