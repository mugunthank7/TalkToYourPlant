// Knowledge-graph path (symptom -> failure mode -> component -> repair -> spare part) placed on the plant.
// The brain returns the nodes; the twin decides where each one lives: evidence at the machine, the repair at the maintenance
// bay (S10), the spare part at the spares cage (S12), procedures and people at the control room (S11).
import { toScene, type Layout } from "./data";

export interface PathNode { id: string; kind: string }
export interface GraphPath { nodes: PathNode[]; machine: string | null; t0: number }
export interface Anchor { node: PathNode; pos: [number, number, number]; label: string; tag: string; color: string }

const KIND: Record<string, { tag: string; color: string }> = {
  symptom: { tag: "Symptom", color: "#fbbf24" },
  failure_mode: { tag: "Failure mode", color: "#fb5a5a" },
  component: { tag: "Component", color: "#fb923c" },
  repair: { tag: "Repair", color: "#4cc2ff" },
  spare_part: { tag: "Spare part", color: "#34d399" },
  sop: { tag: "Procedure", color: "#a78bfa" },
  machine: { tag: "Machine", color: "#a78bfa" },
};

const pretty = (id: string) =>
  id.replace(/^m(\d+)_/i, (_, n) => `M${n} `).replace(/joint(\d)/, "joint $1").replace(/_/g, " ").replace(/\s+/g, " ").trim();

export function anchorsFor(layout: Layout, nodes: PathNode[], machine: string | null): Anchor[] {
  const m = layout.machines.find((x) => x.id === machine) ?? layout.machines.find((x) => x.id === "M05")!;
  const [mx, mz] = toScene(m.x, m.z);
  const st = (id: string): [number, number] => {
    const s = layout.stations.find((x) => x.id === id)!;
    return toScene(s.x, s.z);
  };
  const [bx, bz] = st("S10"), [sx, sz] = st("S12"), [cx, cz] = st("S11");
  const at = (kind: string): [number, number, number] => {
    switch (kind) {
      case "symptom": return [mx, 15.8, mz];
      case "failure_mode": return [mx, 9.2, mz];
      case "component": return [mx, 2.6, mz];
      case "repair": return [bx, 4.2, bz];
      case "spare_part": return [sx, 4.2, sz];
      case "sop": return [cx, 4.2, cz];
      default: return [mx, 3.2, mz];
    }
  };
  return nodes.map((node) => {
    const k = KIND[node.kind] ?? { tag: node.kind.replace(/_/g, " "), color: "#a78bfa" };
    const label = node.kind === "machine" ? `${node.id} ${m.name ?? ""}`.trim() : pretty(node.id);
    return { node, pos: at(node.kind), label, tag: k.tag, color: k.color };
  });
}

/** Camera pose that frames every anchor, shifted so the chain sits left of the right-hand dock. */
export function frameFor(anchors: Anchor[]): { pos: [number, number, number]; target: [number, number, number] } {
  const xs = anchors.map((a) => a.pos[0]), zs = anchors.map((a) => a.pos[2]);
  const cx = (Math.min(...xs) + Math.max(...xs)) / 2, cz = (Math.min(...zs) + Math.max(...zs)) / 2;
  const r = Math.max((Math.max(...xs) - Math.min(...xs)) * 1.5, (Math.max(...zs) - Math.min(...zs)) * 1.5, 16);
  const shift = r * 0.14;
  return { pos: [cx + shift, r * 0.85 + 22, cz + r * 0.8 + 20], target: [cx + shift, 0, cz] };
}
