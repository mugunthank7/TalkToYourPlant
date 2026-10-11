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

const PANTS = "#1f2a44";
const SKIN = "#e0b896";

function Limb({ r, len, color }: { r: number; len: number; color: string }) {
  return (
    <mesh position={[0, -len / 2, 0]} castShadow>
      <capsuleGeometry args={[r, len - 2 * r, 4, 8]} />
      <meshStandardMaterial color={color} roughness={0.8} />
    </mesh>
  );
}

function Worker({ person }: { person: Person }) {
  const group = useRef<THREE.Group>(null!);
  const body = useRef<THREE.Group>(null!);
  const lLeg = useRef<THREE.Group>(null!);
  const rLeg = useRef<THREE.Group>(null!);
  const lArm = useRef<THREE.Group>(null!);
  const rArm = useRef<THREE.Group>(null!);
  const torso = useRef<THREE.Group>(null!);
  const text = useRef("");
  const color = ROLE_COLOR[person.role] ?? "#ccc";
  const yaw = useRef(0);
  const phase = useRef(Math.random() * 6);

  useFrame((_, dt) => {
    const pose = poseAt(person, clock.t);
    const [sx, sz] = toScene(pose.x, pose.z);
    group.current.position.set(sx, 0, sz);
    let d = pose.heading - yaw.current;
    d = Math.atan2(Math.sin(d), Math.cos(d));
    yaw.current += d * Math.min(1, dt * 10);
    group.current.rotation.y = yaw.current;

    const walking = pose.anim === "walk";
    phase.current += dt * (walking ? 7.5 : 3);
    const sw = Math.sin(phase.current);
    const b = body.current;
    b.position.y = 0;
    torso.current.rotation.set(0, 0, 0);
    let ll = 0, rl = 0, la = 0, ra = 0, lz = 0, rz = 0;
    if (walking) {
      ll = sw * 0.65; rl = -sw * 0.65; la = -sw * 0.55; ra = sw * 0.55;
      b.position.y = Math.abs(Math.cos(phase.current)) * 0.05;
    } else if (pose.anim === "work") {
      torso.current.rotation.x = 0.22;
      la = -1.0 + Math.sin(phase.current * 1.3) * 0.25;
      ra = -1.15 + Math.cos(phase.current * 1.1) * 0.25;
    } else if (pose.anim === "crouch") {
      b.position.y = -0.34;
      ll = -1.15; rl = -1.15;
      torso.current.rotation.x = 0.55;
      la = -0.9 + Math.sin(phase.current * 1.5) * 0.2; ra = -0.7;
    } else {
      torso.current.rotation.x = Math.sin(phase.current * 0.5) * 0.02;
      lz = 0.05; rz = -0.05;
    }
    lLeg.current.rotation.x = ll; rLeg.current.rotation.x = rl;
    lArm.current.rotation.set(la, 0, lz); rArm.current.rotation.set(ra, 0, rz);
    text.current = `${person.employee_id}: ${pose.label}`;
  });

  return (
    <group ref={group}>
      <group ref={body}>
        <group ref={lLeg} position={[-0.12, 0.92, 0]}>
          <Limb r={0.09} len={0.92} color={PANTS} />
          <mesh position={[0, -0.9, 0.06]} castShadow><boxGeometry args={[0.16, 0.1, 0.28]} /><meshStandardMaterial color="#111827" /></mesh>
        </group>
        <group ref={rLeg} position={[0.12, 0.92, 0]}>
          <Limb r={0.09} len={0.92} color={PANTS} />
          <mesh position={[0, -0.9, 0.06]} castShadow><boxGeometry args={[0.16, 0.1, 0.28]} /><meshStandardMaterial color="#111827" /></mesh>
        </group>
        <group ref={torso} position={[0, 0.92, 0]}>
          <mesh position={[0, 0.3, 0]} castShadow>
            <boxGeometry args={[0.44, 0.62, 0.26]} />
            <meshStandardMaterial color={color} roughness={0.7} />
          </mesh>
          <mesh position={[0, 0.3, 0.001]}>
            <boxGeometry args={[0.45, 0.08, 0.27]} />
            <meshStandardMaterial color="#e2e8f0" emissive="#e2e8f0" emissiveIntensity={0.25} />
          </mesh>
          <mesh position={[0, 0.74, 0]} castShadow>
            <sphereGeometry args={[0.15, 16, 12]} />
            <meshStandardMaterial color={SKIN} roughness={0.8} />
          </mesh>
          <mesh position={[0, 0.8, 0]} castShadow>
            <sphereGeometry args={[0.17, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2]} />
            <meshStandardMaterial color="#fde047" roughness={0.4} />
          </mesh>
          <mesh position={[0, 0.79, 0.12]} castShadow>
            <boxGeometry args={[0.3, 0.025, 0.16]} />
            <meshStandardMaterial color="#fde047" roughness={0.4} />
          </mesh>
          <group ref={lArm} position={[-0.29, 0.56, 0]}>
            <Limb r={0.07} len={0.62} color={color} />
          </group>
          <group ref={rArm} position={[0.29, 0.56, 0]}>
            <Limb r={0.07} len={0.62} color={color} />
          </group>
        </group>
      </group>
      <LiveLabel getText={() => text.current} position={[0, 2.35, 0]} height={0.6} />
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
