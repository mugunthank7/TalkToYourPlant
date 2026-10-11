import type { Layout, Pt } from "./data";

/** Shortest walk path between two graph node ids (same walkway graph the schedule uses). */
export function route(layout: Layout, a: string, b: string): Pt[] {
  const nodes = new Map(layout.walk_graph.nodes.map((n) => [n.id, [n.x, n.z] as Pt]));
  const adj = new Map<string, string[]>();
  for (const [u, v] of layout.walk_graph.edges) {
    (adj.get(u) ?? adj.set(u, []).get(u)!).push(v);
    (adj.get(v) ?? adj.set(v, []).get(v)!).push(u);
  }
  const dist = new Map<string, number>([[a, 0]]);
  const prev = new Map<string, string>();
  const todo = new Set([a]);
  while (todo.size) {
    let u = "";
    let best = Infinity;
    todo.forEach((n) => { if ((dist.get(n) ?? Infinity) < best) { best = dist.get(n)!; u = n; } });
    todo.delete(u);
    if (u === b) break;
    for (const v of adj.get(u) ?? []) {
      const nu = nodes.get(u)!, nv = nodes.get(v)!;
      const d = best + Math.hypot(nu[0] - nv[0], nu[1] - nv[1]);
      if (d < (dist.get(v) ?? Infinity)) { dist.set(v, d); prev.set(v, u); todo.add(v); }
    }
  }
  const path = [b];
  while (path[path.length - 1] !== a && prev.has(path[path.length - 1])) path.push(prev.get(path[path.length - 1])!);
  return path.reverse().map((n) => nodes.get(n)!);
}

export const length = (p: Pt[]) => p.reduce((s, q, i) => (i ? s + Math.hypot(q[0] - p[i - 1][0], q[1] - p[i - 1][1]) : 0), 0);
