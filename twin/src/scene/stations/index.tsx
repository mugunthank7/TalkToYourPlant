import { useMemo, useRef, type ReactElement } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";
import { clock } from "../../clock";
import { toScene } from "../../data";
import { useTwin } from "../../state";
import { S01 } from "./S01";
import { S02 } from "./S02";
import { S03 } from "./S03";
import { S04 } from "./S04";
import { S05 } from "./S05";
import { S06 } from "./S06";
import { S07 } from "./S07";
import { S08 } from "./S08";
import { S09 } from "./S09";
import { S10 } from "./S10";
import { S11 } from "./S11";
import { S12 } from "./S12";

/** Stations that have a detailed model. The generic pad, props and machines are skipped for these. */
export const DETAILED: Record<string, () => ReactElement> = { S01, S02, S03, S04, S05, S06, S07, S08, S09, S10, S11, S12 };
export const DETAILED_IDS = new Set(Object.keys(DETAILED));
/** Machine ids drawn inside a detailed station model. */
export const MACHINES_IN_MODELS = new Set<string>(["M09", "M01", "M02", "M10", "M11", "M08", "M03", "M04", "M05", "M07"]);

/** Glowing path of the technician's response run (bay -> spares -> weld cell B), shown while it happens. */
function AlertTrail() {
  const data = useTwin((s) => s.data)!;
  const g = useRef<THREE.Group>(null!);
  const pts = useMemo(() => {
    const tech = data.schedule.shifts.A.find((p) => p.role === "technician");
    if (!tech) return [] as THREE.Vector3[];
    const h = data.hero;
    const out: THREE.Vector3[] = [];
    tech.timeline
      .filter((seg) => seg.k === "walk" && seg.path && seg.s >= h.t_dispatch_s - 1 && seg.e <= h.t_repair_start_s + 2)
      .forEach((seg) => seg.path!.forEach(([x, z]) => { const [sx, sz] = toScene(x, z); out.push(new THREE.Vector3(sx, 0.12, sz)); }));
    return out;
  }, [data]);
  useFrame(() => {
    const h = data.hero;
    g.current.visible = useTwin.getState().shift === "A" && clock.t >= h.t_dispatch_s && clock.t < h.t_repair_end_s;
  });
  if (pts.length < 2) return null;
  return (
    <group ref={g} visible={false}>
      <Line points={pts} color="#ff6b5e" lineWidth={7} transparent opacity={0.35} />
      <Line points={pts} color="#ff2a2a" lineWidth={2.5} />
    </group>
  );
}

export function StationModels() {
  return (
    <>
      <AlertTrail />
      {Object.entries(DETAILED).map(([id, C]) => (
        <C key={id} />
      ))}
    </>
  );
}
