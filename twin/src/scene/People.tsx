import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { LiveLabel } from "./Label";
import * as THREE from "three";
import { clock } from "../clock";
import { Person, Seg, Pt, toScene } from "../data";
import { useTwin } from "../state";

const ROLE_COLOR: Record<string, string> = {
  operator: "#f97316",
  relief_operator: "#fbbf24",
  inspector: "#38bdf8",
  supervisor: "#22c55e",
  technician: "#ef4444",
};

const pathCache = new WeakMap<Seg, { cum: number[]; len: number }>();
function pathInfo(seg: Seg) {
  let c = pathCache.get(seg);
  if (!c) {
    const p = seg.path!;
    const cum = [0];
    for (let i = 1; i < p.length; i++) cum.push(cum[i - 1] + Math.hypot(p[i][0] - p[i - 1][0], p[i][1] - p[i - 1][1]));
    c = { cum, len: cum[cum.length - 1] };
    pathCache.set(seg, c);
  }
  return c;
}

function findSeg(tl: Seg[], t: number): number {
  let lo = 0;
  let hi = tl.length - 1;
  while (lo < hi) {
    const mid = (lo + hi + 1) >> 1;
    if (tl[mid].s <= t) lo = mid;
    else hi = mid - 1;
  }
  return lo;
}

interface Pose { x: number; z: number; heading: number; anim: Seg["anim"]; label: string }

function poseAt(p: Person, t: number): Pose {
  const seg = p.timeline[findSeg(p.timeline, t)];
  if (seg.k === "walk" && seg.path) {
    const { cum, len } = pathInfo(seg);
    const u = Math.min(Math.max((t - seg.s) / Math.max(seg.e - seg.s, 1e-6), 0), 1);
    const d = u * len;
    let i = 1;
    while (i < cum.length - 1 && cum[i] < d) i++;
    const [x0, z0] = seg.path[i - 1];
    const [x1, z1] = seg.path[i];
    const f = cum[i] > cum[i - 1] ? (d - cum[i - 1]) / (cum[i] - cum[i - 1]) : 0;
    return { x: x0 + (x1 - x0) * f, z: z0 + (z1 - z0) * f, heading: Math.atan2(x1 - x0, z1 - z0), anim: "walk", label: `walking to ${seg.to}` };
  }
  const at: Pt = seg.at ?? [0, 0];
  const face: Pt = seg.face ?? at;
  const heading = Math.atan2(face[0] - at[0], face[1] - at[1]);
  return { x: at[0], z: at[1], heading, anim: seg.anim, label: `${seg.k} ${seg.station ?? ""}` };
}

function Worker({ person }: { person: Person }) {
  const group = useRef<THREE.Group>(null!);
  const body = useRef<THREE.Group>(null!);
  const text = useRef("");
  const color = ROLE_COLOR[person.role] ?? "#ccc";
  const yaw = useRef(0);

  useFrame(() => {
    const pose = poseAt(person, clock.t);
    const [sx, sz] = toScene(pose.x, pose.z);
    group.current.position.set(sx, 0, sz);
    // Turn smoothly toward the heading.
    let d = pose.heading - yaw.current;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    yaw.current += d * 0.25;
    group.current.rotation.y = yaw.current;
    const t = performance.now() / 1000;
    const b = body.current;
    b.position.y = 0;
    b.rotation.set(0, 0, 0);
    b.scale.set(1, 1, 1);
    if (pose.anim === "walk") {
      b.position.y = Math.abs(Math.sin(t * 7 + person.timeline.length)) * 0.07;
      b.rotation.z = Math.sin(t * 7) * 0.05;
    } else if (pose.anim === "work") {
      b.rotation.x = 0.25 + Math.sin(t * 3 + person.home_station.length) * 0.08;
    } else if (pose.anim === "crouch") {
      b.scale.y = 0.62;
      b.rotation.x = 0.35;
    } else {
      b.position.y = Math.sin(t * 1.5) * 0.01;
    }
    text.current = `${person.employee_id}: ${pose.label}`;
  });

  return (
    <group ref={group}>
      <group ref={body}>
        <mesh position={[0, 0.85, 0]} castShadow>
          <capsuleGeometry args={[0.27, 0.85, 4, 12]} />
          <meshStandardMaterial color={color} roughness={0.7} />
        </mesh>
        <mesh position={[0, 1.62, 0]} castShadow>
          <sphereGeometry args={[0.2, 16, 12]} />
          <meshStandardMaterial color="#f1d3b3" roughness={0.8} />
        </mesh>
        <mesh position={[0, 1.74, 0]} castShadow>
          <sphereGeometry args={[0.215, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <meshStandardMaterial color="#fde047" roughness={0.5} />
        </mesh>
      </group>
      <LiveLabel getText={() => text.current} position={[0, 2.6, 0]} />
    </group>
  );
}

export function People() {
  const data = useTwin((s) => s.data)!;
  const shift = useTwin((s) => s.shift);
  const people = useMemo(() => data.schedule.shifts[shift], [data, shift]);
  return (
    <>
      {people.map((p) => (
        <Worker key={p.employee_id} person={p} />
      ))}
    </>
  );
}
