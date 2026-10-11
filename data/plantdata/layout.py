"""Plant layout: stations, machines and the pedestrian graph.

Units are metres. x runs east, z runs south, y is up (same axes as Three.js, so
(x, z) can be used directly as floor coordinates). Origin is the plant's NW corner.
"""
from __future__ import annotations

import heapq
import math

PLANT = {"width_m": 160, "depth_m": 90}

# id, name, cx, cz, width, depth, access point (where people stand), lane node
STATIONS = [
    ("S01", "Coil yard", 14, 18, 22, 16, (14, 27), "N14"),
    ("S02", "Casting and press", 42, 18, 26, 18, (42, 28), "N42"),
    ("S03", "Parts buffer", 68, 18, 16, 14, (68, 26), "N68"),
    ("S04", "Framing", 92, 44, 14, 12, (92, 52), "A92"),
    ("S05", "Weld cell A", 112, 44, 14, 12, (112, 52), "A112"),
    ("S06", "Weld cell B", 132, 44, 14, 12, (132, 52), "A132"),
    ("S07", "Inspection gate", 150, 44, 10, 12, (150, 52), "A150"),
    ("S08", "Battery module line", 118, 76, 18, 12, (118, 68), "A118"),
    ("S09", "Pack closing and EOL test", 146, 76, 18, 12, (146, 68), "A146"),
    ("S10", "Maintenance bay", 20, 72, 18, 12, (20, 64), "A20"),
    ("S11", "Control room and break room", 50, 76, 16, 10, (50, 69), "A50"),
    ("S12", "Spare parts cage", 72, 66, 12, 8, (72, 60), "A72"),
]

# id, name, type, station, x, z, rotation in degrees
MACHINES = [
    ("M01", "Casting press", "press", "S02", 36, 18, 0),
    ("M02", "Press transfer robot", "robot", "S02", 50, 18, 0),
    ("M03", "Framing fixture", "fixture", "S04", 92, 44, 0),
    ("M04", "Weld robot 1", "weld_robot", "S05", 112, 46, 0),
    ("M05", "Weld robot 2", "weld_robot", "S06", 132, 46, 0),
    ("M06", "Main conveyor", "conveyor", "S04", 119, 44, 0),
    ("M07", "Vision inspection gate", "vision_gate", "S07", 150, 44, 0),
    ("M08", "Battery module stacker", "gantry", "S08", 118, 76, 0),
    ("M09", "Pack sealer", "sealer", "S09", 146, 76, 0),
    ("M10", "Decoiler", "decoiler", "S01", 10, 18, 0),
    ("M11", "Rack AGV", "agv", "S03", 68, 26, 0),
]

CONVEYOR_PATH = [(80, 44), (158, 44)]

# Item (vehicle body, parts, packs) flow between stations and how it moves.
ITEM_FLOW = [
    ("S01", "S02", "agv"),
    ("S02", "S03", "agv"),
    ("S03", "S04", "agv"),
    ("S04", "S05", "conveyor"),
    ("S05", "S06", "conveyor"),
    ("S06", "S07", "conveyor"),
    ("S07", "S09", "agv"),
    ("S08", "S09", "agv"),
]

# People leave the robots alone: weld cells get a light-curtain zone (rect around station).
SAFETY_ZONES = [("S05", 2.0), ("S06", 2.0)]

GATE = (6, 56)
AISLE_Z = 56
ROW_Z = 30


class Graph:
    """Pedestrian graph. Every station has a node named '<id>.in' at its access point."""

    def __init__(self) -> None:
        self.xy_of: dict[str, tuple[float, float]] = {}
        self.adj: dict[str, list[tuple[str, float]]] = {}

    def add_node(self, name: str, x: float, z: float) -> None:
        self.xy_of[name] = (float(x), float(z))
        self.adj.setdefault(name, [])

    def add_edge(self, a: str, b: str) -> None:
        d = math.dist(self.xy_of[a], self.xy_of[b])
        self.adj[a].append((b, d))
        self.adj[b].append((a, d))

    def xy(self, name: str) -> tuple[float, float]:
        return self.xy_of[name]

    def node_for(self, place: str) -> str:
        return "GATE" if place == "GATE" else f"{place}.in"

    def route(self, a: str, b: str) -> list[str]:
        """Shortest node path between two places (station ids or 'GATE')."""
        src, dst = self.node_for(a), self.node_for(b)
        dist = {src: 0.0}
        prev: dict[str, str] = {}
        pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if u == dst:
                break
            if d > dist.get(u, math.inf):
                continue
            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist.get(v, math.inf):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))
        path = [dst]
        while path[-1] != src:
            path.append(prev[path[-1]])
        return path[::-1]

    def polyline(self, a: str, b: str) -> list[tuple[float, float]]:
        pts: list[tuple[float, float]] = []
        for n in self.route(a, b):
            p = self.xy(n)
            if not pts or pts[-1] != p:
                pts.append(p)
        return pts

    def distance(self, a: str, b: str) -> float:
        pts = self.polyline(a, b)
        return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def build_graph() -> Graph:
    g = Graph()
    g.add_node("GATE", *GATE)

    aisle_xs = sorted({10, 20, 50, 72, 76, 92, 112, 118, 132, 146, 150, 155})
    for x in aisle_xs:
        g.add_node(f"A{x}", x, AISLE_Z)
    g.add_edge("GATE", f"A{aisle_xs[0]}")
    for a, b in zip(aisle_xs, aisle_xs[1:]):
        g.add_edge(f"A{a}", f"A{b}")

    row_xs = [14, 42, 68, 76]
    for x in row_xs:
        g.add_node(f"N{x}", x, ROW_Z)
    for a, b in zip(row_xs, row_xs[1:]):
        g.add_edge(f"N{a}", f"N{b}")
    g.add_node("C76", 76, 43)
    g.add_edge("N76", "C76")
    g.add_edge("C76", "A76")

    for sid, _n, _cx, _cz, _w, _d, access, lane in STATIONS:
        g.add_node(f"{sid}.in", *access)
        g.add_edge(f"{sid}.in", lane)
    return g


def station(sid: str) -> dict:
    for s in STATIONS:
        if s[0] == sid:
            return {"id": s[0], "name": s[1], "x": s[2], "z": s[3], "w": s[4], "d": s[5], "access": list(s[6])}
    raise KeyError(sid)


def to_json(g: Graph) -> dict:
    machines_by_station: dict[str, list[str]] = {}
    for m in MACHINES:
        machines_by_station.setdefault(m[3], []).append(m[0])
    nodes = [{"id": n, "x": x, "z": z} for n, (x, z) in g.xy_of.items()]
    edges = sorted({tuple(sorted((a, b))) for a, nbrs in g.adj.items() for b, _ in nbrs})
    return {
        "units": "metres; x east, z south, y up; origin NW corner",
        "plant": PLANT,
        "stations": [
            {**station(s[0]), "machines": machines_by_station.get(s[0], [])} for s in STATIONS
        ],
        "machines": [
            {"id": m[0], "name": m[1], "type": m[2], "station": m[3], "x": m[4], "z": m[5], "rot_deg": m[6]}
            for m in MACHINES
        ],
        "conveyor_path": [list(p) for p in CONVEYOR_PATH],
        "item_flow": [{"from": a, "to": b, "mode": m} for a, b, m in ITEM_FLOW],
        "safety_zones": [
            {"station": sid, "x": station(sid)["x"], "z": station(sid)["z"],
             "w": station(sid)["w"] + 2 * margin, "d": station(sid)["d"] + 2 * margin}
            for sid, margin in SAFETY_ZONES
        ],
        "gate": list(GATE),
        "walk_graph": {"nodes": nodes, "edges": [list(e) for e in edges]},
    }
