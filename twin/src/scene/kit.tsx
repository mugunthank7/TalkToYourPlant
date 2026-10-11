import { useEffect, useMemo, useRef, type ReactNode } from "react";
import { useFrame } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import { useTwin } from "../state";
import { toScene } from "../data";

export type V3 = [number, number, number];

/** Rounded box. p = centre, s = size. */
export function RB({ p, s, c = "#94a3b8", r = 0.04, metal = 0.35, rough = 0.5, rot, emissive, ei = 1, opacity, shadow = true }:
  { p: V3; s: V3; c?: string; r?: number; metal?: number; rough?: number; rot?: V3; emissive?: string; ei?: number; opacity?: number; shadow?: boolean }) {
  return (
    <RoundedBox args={s} radius={Math.min(r, Math.min(...s) / 2.2)} smoothness={3} position={p} rotation={rot} castShadow={shadow} receiveShadow>
      <meshStandardMaterial color={c} metalness={metal} roughness={rough} emissive={emissive ?? "#000000"} emissiveIntensity={emissive ? ei : 0}
        transparent={opacity !== undefined} opacity={opacity ?? 1} />
    </RoundedBox>
  );
}

/** Plain box, cheaper than RB for small or hidden details. */
export function B({ p, s, c = "#94a3b8", metal = 0.3, rough = 0.55, rot, emissive, ei = 1, shadow = true }:
  { p: V3; s: V3; c?: string; metal?: number; rough?: number; rot?: V3; emissive?: string; ei?: number; shadow?: boolean }) {
  return (
    <mesh position={p} rotation={rot} castShadow={shadow} receiveShadow>
      <boxGeometry args={s} />
      <meshStandardMaterial color={c} metalness={metal} roughness={rough} emissive={emissive ?? "#000000"} emissiveIntensity={emissive ? ei : 0} />
    </mesh>
  );
}

export function Cyl({ p, r, h, c = "#94a3b8", metal = 0.5, rough = 0.4, rot, seg = 24, emissive, ei = 1, rb }:
  { p: V3; r: number; h: number; c?: string; metal?: number; rough?: number; rot?: V3; seg?: number; emissive?: string; ei?: number; rb?: number }) {
  return (
    <mesh position={p} rotation={rot} castShadow receiveShadow>
      <cylinderGeometry args={[r, rb ?? r, h, seg]} />
      <meshStandardMaterial color={c} metalness={metal} roughness={rough} emissive={emissive ?? "#000000"} emissiveIntensity={emissive ? ei : 0} />
    </mesh>
  );
}

export function Glass({ p, s, tint = "#a5d8ff", opacity = 0.16 }: { p: V3; s: V3; tint?: string; opacity?: number }) {
  return (
    <mesh position={p}>
      <boxGeometry args={s} />
      <meshPhysicalMaterial color={tint} transparent opacity={opacity} roughness={0.05} metalness={0} side={THREE.DoubleSide} depthWrite={false} />
    </mesh>
  );
}

/** A wall run of glass panes with metal mullions. Along x (axis="x") or z (axis="z"). */
export function GlassWall({ p, len, h = 3, axis = "x", every = 2 }: { p: V3; len: number; h?: number; axis?: "x" | "z"; every?: number }) {
  const n = Math.max(1, Math.round(len / every));
  const posts = Array.from({ length: n + 1 }, (_, i) => -len / 2 + (i * len) / n);
  const rot: V3 = [0, axis === "x" ? 0 : Math.PI / 2, 0];
  return (
    <group position={p} rotation={rot}>
      <Glass p={[0, h / 2, 0]} s={[len, h - 0.2, 0.04]} />
      <B p={[0, 0.08, 0]} s={[len, 0.16, 0.12]} c="#cbd5e1" />
      <B p={[0, h - 0.05, 0]} s={[len, 0.1, 0.12]} c="#94a3b8" />
      {posts.map((x) => (
        <B key={x} p={[x, h / 2, 0]} s={[0.06, h, 0.1]} c="#9aa7b5" metal={0.7} />
      ))}
    </group>
  );
}

/** Round the station footprint: slab plus painted yellow/green edge, relative to the station centre. */
export function Pad({ w, d, tone = "#e5e9ee" }: { w: number; d: number; tone?: string }) {
  return (
    <group>
      <mesh position={[0, 0.03, 0]} receiveShadow>
        <boxGeometry args={[w, 0.06, d]} />
        <meshStandardMaterial color={tone} roughness={0.45} metalness={0.05} />
      </mesh>
      {[
        [0, d / 2 - 0.08, w, 0.16], [0, -d / 2 + 0.08, w, 0.16], [w / 2 - 0.08, 0, 0.16, d], [-w / 2 + 0.08, 0, 0.16, d],
      ].map(([x, z, ww, dd], i) => (
        <mesh key={i} position={[x, 0.07, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[ww, dd]} />
          <meshStandardMaterial color="#facc15" roughness={0.6} />
        </mesh>
      ))}
    </group>
  );
}

/** Hazard stripe plate (yellow/black), e.g. around presses. */
export function Hazard({ p, s }: { p: V3; s: [number, number] }) {
  const tex = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const x = c.getContext("2d")!;
    x.fillStyle = "#facc15";
    x.fillRect(0, 0, 64, 64);
    x.fillStyle = "#111827";
    for (let i = -64; i < 128; i += 32) {
      x.beginPath();
      x.moveTo(i, 64); x.lineTo(i + 16, 64); x.lineTo(i + 80, 0); x.lineTo(i + 64, 0); x.closePath();
      x.fill();
    }
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
  useEffect(() => { tex.repeat.set(s[0] / 1.2, s[1] / 1.2); tex.needsUpdate = true; }, [tex, s]);
  return (
    <mesh position={[p[0], p[1] + 0.075, p[2]]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={s} />
      <meshStandardMaterial map={tex} roughness={0.7} />
    </mesh>
  );
}

/** Emissive screen drawn with the 2D canvas. `draw` is called ~2x per second and on mount. */
export function Screen({ p, s, rot, draw, hz = 2, bright = 1.1 }:
  { p: V3; s: [number, number]; rot?: V3; draw: (ctx: CanvasRenderingContext2D, w: number, h: number) => void; hz?: number; bright?: number }) {
  const { canvas, tex } = useMemo(() => {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = Math.max(64, Math.round((512 * s[1]) / s[0]));
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    return { canvas, tex };
  }, [s]);
  const last = useRef(-1);
  useFrame(() => {
    const now = performance.now();
    if (now - last.current < 1000 / hz) return;
    last.current = now;
    draw(canvas.getContext("2d")!, canvas.width, canvas.height);
    tex.needsUpdate = true;
  });
  return (
    <mesh position={p} rotation={rot}>
      <planeGeometry args={s} />
      <meshStandardMaterial map={tex} emissiveMap={tex} emissive="#ffffff" emissiveIntensity={bright} toneMapped={false} />
    </mesh>
  );
}

/** Static or lightly animated person (not on the schedule): stand, sit, carry, work. */
export function Npc({ p, rotY = 0, color = "#f97316", pose = "stand", seed = 0 }: { p: V3; rotY?: number; color?: string; pose?: "stand" | "sit" | "work" | "carry"; seed?: number }) {
  const arms = useRef<THREE.Group[]>([]);
  const torso = useRef<THREE.Group>(null!);
  useFrame(() => {
    const t = performance.now() / 1000 + seed * 3;
    if (torso.current) torso.current.rotation.x = (pose === "work" ? 0.25 : pose === "sit" ? 0.08 : 0) + Math.sin(t * 1.4) * 0.015;
    if (arms.current[0] && pose === "work") { arms.current[0].rotation.x = -1.0 + Math.sin(t * 3) * 0.2; arms.current[1].rotation.x = -1.1 + Math.cos(t * 2.6) * 0.2; }
  });
  const sit = pose === "sit";
  const legRot = sit ? -1.5 : 0;
  const armRot = pose === "carry" ? -1.2 : pose === "sit" ? -0.9 : pose === "work" ? -1.0 : 0;
  const hip = sit ? 0.5 : 0.92;
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      {[-0.12, 0.12].map((x) => (
        <group key={x} position={[x, hip, 0]} rotation={[legRot, 0, 0]}>
          <mesh position={[0, -0.45, 0]} castShadow><capsuleGeometry args={[0.09, 0.74, 4, 8]} /><meshStandardMaterial color="#1f2a44" roughness={0.8} /></mesh>
        </group>
      ))}
      {sit && [-0.12, 0.12].map((x) => (
        <mesh key={x} position={[x, 0.28, 0.5]} castShadow><capsuleGeometry args={[0.08, 0.5, 4, 8]} /><meshStandardMaterial color="#1f2a44" roughness={0.8} /></mesh>
      ))}
      <group ref={torso} position={[0, hip, 0]}>
        <mesh position={[0, 0.3, 0]} castShadow><boxGeometry args={[0.44, 0.62, 0.26]} /><meshStandardMaterial color={color} roughness={0.7} /></mesh>
        <mesh position={[0, 0.3, 0.001]}><boxGeometry args={[0.45, 0.08, 0.27]} /><meshStandardMaterial color="#e2e8f0" emissive="#e2e8f0" emissiveIntensity={0.25} /></mesh>
        <mesh position={[0, 0.74, 0]} castShadow><sphereGeometry args={[0.15, 16, 12]} /><meshStandardMaterial color="#e0b896" roughness={0.8} /></mesh>
        <mesh position={[0, 0.8, 0]} castShadow><sphereGeometry args={[0.17, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2]} /><meshStandardMaterial color="#fde047" roughness={0.4} /></mesh>
        {[-0.29, 0.29].map((x, i) => (
          <group key={x} ref={(g) => { if (g) arms.current[i] = g; }} position={[x, 0.56, 0]} rotation={[armRot, 0, 0]}>
            <mesh position={[0, -0.31, 0]} castShadow><capsuleGeometry args={[0.07, 0.48, 4, 8]} /><meshStandardMaterial color={color} roughness={0.8} /></mesh>
          </group>
        ))}
      </group>
    </group>
  );
}

export function Chair({ p, rotY = 0, c = "#64748b" }: { p: V3; rotY?: number; c?: string }) {
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <B p={[0, 0.45, 0]} s={[0.46, 0.06, 0.46]} c={c} rough={0.7} />
      <B p={[0, 0.78, -0.21]} s={[0.46, 0.5, 0.05]} c={c} rough={0.7} />
      {[[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]].map(([x, z], i) => (
        <B key={i} p={[x, 0.22, z]} s={[0.04, 0.44, 0.04]} c="#cbd5e1" metal={0.8} />
      ))}
    </group>
  );
}

export function Plant({ p, s = 1 }: { p: V3; s?: number }) {
  return (
    <group position={p} scale={s}>
      <Cyl p={[0, 0.25, 0]} r={0.25} h={0.5} c="#475569" metal={0.1} rough={0.7} rb={0.2} />
      {[[0, 0.9, 0, 0.42], [0.2, 0.75, 0.1, 0.3], [-0.2, 0.8, -0.1, 0.3]].map(([x, y, z, r], i) => (
        <mesh key={i} position={[x, y, z]} castShadow><sphereGeometry args={[r, 12, 10]} /><meshStandardMaterial color="#2f9e57" roughness={0.8} /></mesh>
      ))}
    </group>
  );
}

export function Andon({ p, state }: { p: V3; state: () => "ok" | "warn" | "bad" }) {
  const mats = useRef<THREE.MeshStandardMaterial[]>([]);
  useFrame(() => {
    const s = state();
    const on = s === "bad" ? 0 : s === "warn" ? 1 : 2;
    const pulse = s === "bad" ? 0.6 + 0.4 * Math.sin(performance.now() / 160) : 1;
    mats.current.forEach((m, i) => { if (m) m.emissiveIntensity = i === on ? 2.4 * pulse : 0.06; });
  });
  return (
    <group position={p}>
      <Cyl p={[0, 1.4, 0]} r={0.05} h={2.8} c="#334155" />
      {["#ef4444", "#f59e0b", "#22c55e"].map((c, i) => (
        <mesh key={c} position={[0, 2.95 + i * 0.3, 0]}>
          <cylinderGeometry args={[0.18, 0.18, 0.26, 16]} />
          <meshStandardMaterial ref={(m) => { if (m) mats.current[i] = m; }} color={c} emissive={c} emissiveIntensity={0.06} />
        </mesh>
      ))}
    </group>
  );
}

/** Wraps a station model at its station centre (scene coordinates). */
export function AtStation({ id, children }: { id: string; children: (w: number, d: number) => ReactNode }) {
  const st = useTwin((s) => s.data)!.layout.stations.find((x) => x.id === id)!;
  const [x, z] = toScene(st.x, st.z);
  return <group position={[x, 0, z]}>{children(st.w, st.d)}</group>;
}

/** Static text sign drawn on a canvas. */
export function TextBoard({ p, s, rot, text, bg = "#1e293b", fg = "#ffffff", sub, emissive = false }:
  { p: V3; s: [number, number]; rot?: V3; text: string; bg?: string; fg?: string; sub?: string; emissive?: boolean }) {
  const tex = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = 512;
    c.height = Math.max(64, Math.round((512 * s[1]) / s[0]));
    const x = c.getContext("2d")!;
    x.fillStyle = bg;
    x.fillRect(0, 0, c.width, c.height);
    x.fillStyle = fg;
    x.textAlign = "center";
    x.textBaseline = "middle";
    let f = c.height * 0.42;
    x.font = `700 ${f}px Helvetica, Arial, sans-serif`;
    while (x.measureText(text).width > c.width * 0.9 && f > 10) { f -= 2; x.font = `700 ${f}px Helvetica, Arial, sans-serif`; }
    x.fillText(text, c.width / 2, sub ? c.height * 0.4 : c.height / 2);
    if (sub) { x.font = `500 ${f * 0.55}px Helvetica, Arial, sans-serif`; x.fillText(sub, c.width / 2, c.height * 0.75); }
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    return t;
  }, [s, text, bg, fg, sub]);
  return (
    <mesh position={p} rotation={rot}>
      <planeGeometry args={s} />
      <meshStandardMaterial map={tex} emissiveMap={emissive ? tex : null} emissive={emissive ? "#ffffff" : "#000000"} emissiveIntensity={emissive ? 0.9 : 0} roughness={0.5} />
    </mesh>
  );
}

/** Welded wire mesh panel (semi transparent grid) with a frame. */
export function WireMesh({ p, s, axis = "x", frame = "#1d4ed8" }: { p: V3; s: [number, number]; axis?: "x" | "z"; frame?: string }) {
  const tex = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const x = c.getContext("2d")!;
    x.strokeStyle = "#ffffff";
    x.lineWidth = 12;
    x.strokeRect(0, 0, 64, 64);
    const t = new THREE.CanvasTexture(c);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
  useEffect(() => { tex.repeat.set(s[0] / 0.16, s[1] / 0.16); tex.needsUpdate = true; }, [tex, s]);
  return (
    <group position={p} rotation={[0, axis === "x" ? 0 : Math.PI / 2, 0]}>
      <mesh position={[0, s[1] / 2, 0]}>
        <planeGeometry args={s} />
        <meshStandardMaterial map={tex} alphaMap={tex} transparent side={THREE.DoubleSide} metalness={0.6} roughness={0.5} alphaTest={0.08} depthWrite={false} />
      </mesh>
      <B p={[0, 0.05, 0]} s={[s[0], 0.1, 0.08]} c={frame} />
      <B p={[0, s[1] - 0.05, 0]} s={[s[0], 0.1, 0.08]} c={frame} />
      {[-s[0] / 2, s[0] / 2].map((x) => <B key={x} p={[x, s[1] / 2, 0]} s={[0.08, s[1], 0.08]} c={frame} />)}
    </group>
  );
}

/** Yellow safety fence with clear panels around a station. The conveyor runs west-east through the middle:
 * `belt` is the opening width on the west/east sides, `gate` the person gate on the south side (centre x, width). */
export function CellFence({ w, d, belt = 3.4, gate, tall = 2.0 }: { w: number; d: number; belt?: number; gate?: [number, number]; tall?: number }) {
  const hw = w / 2 - 0.25;
  const hd = d / 2 - 0.25;
  const panel = (len: number, key: string, p: V3, rotY = 0) => (
    <group key={key} position={p} rotation={[0, rotY, 0]}>
      <mesh position={[0, tall / 2, 0]}>
        <boxGeometry args={[len, tall - 0.4, 0.03]} />
        <meshPhysicalMaterial color="#9ad0ff" transparent opacity={0.13} roughness={0.05} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <B p={[0, tall - 0.04, 0]} s={[len, 0.07, 0.09]} c="#facc15" />
      <B p={[0, 0.3, 0]} s={[len, 0.07, 0.09]} c="#facc15" />
      <B p={[0, tall / 2, 0]} s={[len, 0.05, 0.07]} c="#facc15" />
    </group>
  );
  const post = (x: number, z: number, key: string) => <B key={key} p={[x, tall / 2, z]} s={[0.1, tall, 0.1]} c="#facc15" />;
  const out: ReactNode[] = [];
  // north (full), south (with a gate)
  out.push(panel(2 * hw, "n", [0, 0, -hd]));
  const gx = gate ? gate[0] : 0, gw = gate ? gate[1] : 0;
  if (gate) {
    out.push(panel(gx - gw / 2 + hw, "sa", [(-hw + gx - gw / 2) / 2, 0, hd]));
    out.push(panel(hw - (gx + gw / 2), "sb", [(gx + gw / 2 + hw) / 2, 0, hd]));
    out.push(post(gx - gw / 2, hd, "g1"), post(gx + gw / 2, hd, "g2"));
  } else out.push(panel(2 * hw, "s", [0, 0, hd]));
  // west / east: full panels except the belt opening
  [-hw, hw].forEach((x) => {
    const seg = hd - belt / 2;
    out.push(panel(seg, `w${x}a`, [x, 0, -(belt / 2 + seg / 2)], Math.PI / 2));
    out.push(panel(seg, `w${x}b`, [x, 0, belt / 2 + seg / 2], Math.PI / 2));
    out.push(post(x, -belt / 2, `p${x}a`), post(x, belt / 2, `p${x}b`));
    // light curtain across the belt opening
    [0.35, 0.9, 1.45].forEach((y) => out.push(<B key={`lc${x}${y}`} p={[x, y, 0]} s={[0.02, 0.02, belt]} c="#ef4444" emissive="#ef4444" ei={1.6} shadow={false} />));
  });
  [[-hw, -hd], [hw, -hd], [-hw, hd], [hw, hd]].forEach(([x, z], i) => out.push(post(x, z, `c${i}`)));
  return <group>{out}</group>;
}
