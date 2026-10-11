"""Plant layout: stations, machines and the pedestrian graph.

Units are metres. x runs east, z runs south, y is up (same axes as Three.js, so
(x, z) can be used directly as floor coordinates). Origin is the plant's NW corner.
"""
from __future__ import annotations

import heapq
import math

PLANT = {"width_m": 128, "depth_m": 72}

# id, name, cx, cz, width, depth, access point (where people stand), lane node
STATIONS = [
    ("S01", "Coil yard", 11, 13, 18, 14, (11, 22), "N11"),
    ("S02", "Casting and press", 33, 13, 22, 16, (33, 22), "N33"),
    ("S03", "Parts buffer", 53, 13, 14, 12, (53, 21), "N53"),
    ("S04", "Framing", 68, 34, 11, 11, (68, 42), "A68"),
    ("S05", "Weld cell A", 84, 34, 12, 11, (84, 42), "A84"),
    ("S06", "Weld cell B", 100, 34, 12, 11, (100, 42), "A100"),
    ("S07", "Inspection gate", 116, 34, 10, 11, (116, 42), "A116"),
    ("S08", "Battery module line", 88, 60, 16, 11, (88, 52), "A88"),
    ("S09", "Pack closing and EOL test", 112, 60, 16, 11, (112, 52), "A112"),
    ("S10", "Maintenance bay", 14, 60, 18, 11, (14, 52), "A14"),
    ("S11", "Control room and break room", 38, 60, 16, 10, (38, 52), "A38"),
    ("S12", "Spare parts cage", 58, 59, 12, 8, (58, 51), "A58"),
]

# id, name, type, station, x, z, rotation in degrees
MACHINES = [
    ("M01", "Casting press", "press", "S02", 29, 13, 0),
    ("M02", "Press transfer robot", "robot", "S02", 40, 13, 0),
    ("M03", "Framing fixture", "fixture", "S04", 68, 34, 0),
    ("M04", "Weld robot 1", "weld_robot", "S05", 84, 35.8, 0),
    ("M05", "Weld robot 2", "weld_robot", "S06", 100, 35.8, 0),
    ("M06", "Main conveyor", "conveyor", "S04", 93.5, 34, 0),
    ("M07", "Vision inspection gate", "vision_gate", "S07", 116, 34, 0),
    ("M08", "Battery module stacker", "gantry", "S08", 88, 60, 0),
    ("M09", "Pack sealer", "sealer", "S09", 112, 60, 0),
    ("M10", "Decoiler", "decoiler", "S01", 8, 13, 0),
    ("M11", "Rack AGV", "agv", "S03", 53, 21, 0),
]

CONVEYOR_PATH = [(63, 34), (122, 34)]

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

# Visible logistics for the 3D scene: (id, name, from node, to node, vehicle, load, period s, speed m/s, extra end point)
LOGISTICS = [
    ("L1", "Coil AGV", "S01.in", "S02.in", "agv", "coil", 300, 1.2, None),
    ("L2", "Stamped-parts AGV", "S02.in", "S03.in", "agv", "rack", 180, 1.2, None),
    ("L3", "Underbody AGV", "S03.in", "C61", "agv", "pan", 90, 1.2, (63, 34)),
    ("L4", "Body AGV", "E124", "S09.in", "agv", "car", 90, 1.2, (115.6, 61.2)),
    ("L5", "Battery pack AGV", "S08.in", "S09.in", "agv", "pack", 90, 1.2, (106.6, 62.1)),
    ("L6", "Pallet forklift", "S03.in", "S12.in", "forklift", "pallet", 900, 1.6, None),
    ("L7", "Spares cart", "S12.in", "S10.in", "cart", "boxes", 600, 1.0, None),
]

# People leave the robots alone: weld cells get a light-curtain zone (rect around station).
SAFETY_ZONES = [("S05", 2.0), ("S06", 2.0)]

GATE = (3, 46)
AISLE_Z = 46
ROW_Z = 24


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
        return self.route_nodes(self.node_for(a), self.node_for(b))

    def route_nodes(self, src: str, dst: str) -> list[str]:
        """Shortest node path between two graph node names."""
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

    aisle_xs = sorted({14, 38, 58, 61, 68, 84, 88, 100, 112, 116, 124})
    for x in aisle_xs:
        g.add_node(f"A{x}", x, AISLE_Z)
    g.add_edge("GATE", f"A{aisle_xs[0]}")
    for a, b in zip(aisle_xs, aisle_xs[1:]):
        g.add_edge(f"A{a}", f"A{b}")

    row_xs = [11, 33, 53, 61]
    for x in row_xs:
        g.add_node(f"N{x}", x, ROW_Z)
    for a, b in zip(row_xs, row_xs[1:]):
        g.add_edge(f"N{a}", f"N{b}")
    g.add_node("C61", 61, 35)
    g.add_edge("N61", "C61")
    g.add_edge("C61", "A61")

    # East end of the conveyor: bodies leave here for the pack and EOL station.
    g.add_node("E124", 124, 34)
    g.add_edge("E124", "A124")

    for sid, _n, _cx, _cz, _w, _d, access, lane in STATIONS:
        g.add_node(f"{sid}.in", *access)
        g.add_edge(f"{sid}.in", lane)
    return g


def station(sid: str) -> dict:
    for s in STATIONS:
        if s[0] == sid:
            return {"id": s[0], "name": s[1], "x": s[2], "z": s[3], "w": s[4], "d": s[5], "access": list(s[6])}
    raise KeyError(sid)


def _route_points(g: Graph, a: str, b: str, extra) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for n in g.route_nodes(a, b):
        p = g.xy(n)
        if not pts or pts[-1] != p:
            pts.append(p)
    if extra:
        pts.append(tuple(extra))
    return pts


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
        "logistics": [
            {"id": i, "name": n, "from": f, "to": t, "vehicle": v, "load": ld, "period_s": p, "speed_mps": sp,
             "route": [list(pt) for pt in _route_points(g, f, t, extra)]}
            for i, n, f, t, v, ld, p, sp, extra in LOGISTICS
        ],
        "walk_graph": {"nodes": nodes, "edges": [list(e) for e in edges]},
    }
