// Volty, the plant assistant: a small floating 3D robot built from primitives, drawn from the character sheet.
// The face is a canvas texture, so every mood is a redraw; colour, hands, antenna and aura follow the state.
import { useEffect, useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import { useTwin, type BotState } from "../state";

export const BOT_LABEL: Record<BotState, string> = {
  idle: "Ready", listening: "Listening", thinking: "Thinking", answering: "Answering", happy: "All clear", searching: "Searching",
  pointing: "Look here", warning: "Warning", danger: "Danger", sleeping: "Offline",
};
const THEME: Record<BotState, { glow: string; eye: string; body: string }> = {
  idle: { glow: "#5eead4", eye: "#5ee7f2", body: "#6f93d8" },
  listening: { glow: "#8fa8ff", eye: "#a9bcff", body: "#6f93d8" },
  thinking: { glow: "#a78bfa", eye: "#b69cff", body: "#6f93d8" },
  answering: { glow: "#38bdf8", eye: "#67e8f9", body: "#6f93d8" },
  happy: { glow: "#4ade80", eye: "#6dff9a", body: "#6f93d8" },
  searching: { glow: "#38bdf8", eye: "#67e8f9", body: "#6f93d8" },
  pointing: { glow: "#22d3ee", eye: "#67e8f9", body: "#6f93d8" },
  warning: { glow: "#fbbf24", eye: "#ffc93c", body: "#7d92c9" },
  danger: { glow: "#ff4d4d", eye: "#ff5a5a", body: "#c4687e" },
  sleeping: { glow: "#9ca3af", eye: "#9ca3af", body: "#8a909b" },
};
const GOLD = "#c9a45c", GREY = "#3b414d";

// ---- face texture ----------------------------------------------------------------------------------------
function drawFace(c: HTMLCanvasElement, state: BotState, t: number, blink: boolean) {
  const g = c.getContext("2d")!;
  const W = c.width, H = c.height;
  const col = THEME[state].eye;
  g.clearRect(0, 0, W, H);
  const bg = g.createLinearGradient(0, 0, 0, H);
  bg.addColorStop(0, "#0d1524"); bg.addColorStop(1, "#05080f");
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  g.lineCap = "round"; g.lineJoin = "round";
  g.shadowColor = col; g.shadowBlur = 26; g.fillStyle = col; g.strokeStyle = col;
  const ex = [150, 362], ey = 140;
  const eye = (x: number, y: number, w: number, h: number, lash = true) => {
    g.beginPath(); g.ellipse(x, y, w, h, 0, 0, Math.PI * 2); g.fill();
    g.shadowBlur = 0; g.fillStyle = "rgba(255,255,255,.85)"; g.beginPath(); g.ellipse(x - w * 0.3, y - h * 0.35, w * 0.22, h * 0.22, 0, 0, Math.PI * 2); g.fill();
    g.shadowBlur = 26; g.fillStyle = col;
    if (lash) { g.lineWidth = 6; for (const s of [-1, 1]) { g.beginPath(); g.moveTo(x + s * w * 0.9, y - h * 0.5); g.lineTo(x + s * (w + 20), y - h * 0.95); g.stroke(); } }
  };
  const arch = (x: number, y: number, w: number) => { g.lineWidth = 16; g.beginPath(); g.arc(x, y + 22, w, Math.PI * 1.08, Math.PI * 1.92); g.stroke(); };
  const line = (x: number, y: number, w: number) => { g.lineWidth = 12; g.beginPath(); g.moveTo(x - w, y); g.lineTo(x + w, y); g.stroke(); };
  const lookX = state === "pointing" ? 22 : state === "thinking" ? -14 : 0;
  const lookY = state === "thinking" ? -20 : 0;
  if (blink && state !== "sleeping" && state !== "danger") { for (const x of ex) line(x, ey + 6, 38); }
  else switch (state) {
    case "happy": for (const x of ex) arch(x, ey, 40); break;
    case "sleeping": for (const x of ex) line(x, ey + 10, 40); break;
    case "searching": for (const x of ex) { g.beginPath(); g.ellipse(x, ey + 8, 44, 24, 0, 0, Math.PI * 2); g.fill(); g.fillStyle = "#05080f"; g.fillRect(x - 50, ey - 22, 100, 20); g.fillStyle = col; } break;
    case "danger": for (const [i, x] of ex.entries()) { g.beginPath(); const s = i ? -1 : 1; g.moveTo(x - 48 * s, ey - 18); g.lineTo(x + 46 * s, ey - 38); g.lineTo(x + 40 * s, ey + 40); g.quadraticCurveTo(x - 10 * s, ey + 54, x - 46 * s, ey + 30); g.closePath(); g.fill(); } break;
    case "warning": for (const x of ex) eye(x, ey + 6, 36, 40, false); g.lineWidth = 10; g.beginPath(); g.moveTo(104, ey - 56); g.lineTo(176, ey - 34); g.moveTo(408, ey - 56); g.lineTo(336, ey - 34); g.stroke(); break;
    case "listening": for (const x of ex) { g.lineWidth = 10; g.beginPath(); g.arc(x, ey, 34, 0, Math.PI * 2); g.stroke(); g.beginPath(); g.arc(x, ey, 9, 0, Math.PI * 2); g.fill(); } break;
    case "answering": for (const x of ex) eye(x, ey, 40, 50); break;
    default: for (const x of ex) eye(x + lookX, ey + lookY, 38, 46);
  }
  // cheeks
  g.shadowBlur = 0;
  if (state !== "danger" && state !== "sleeping" && state !== "warning") for (const x of [88, 424]) {
    const r = g.createRadialGradient(x, 240, 4, x, 240, 40); r.addColorStop(0, "rgba(255,140,110,.7)"); r.addColorStop(1, "rgba(255,140,110,0)");
    g.fillStyle = r; g.beginPath(); g.arc(x, 240, 40, 0, Math.PI * 2); g.fill();
  }
  // mouth
  g.shadowBlur = 20; g.shadowColor = col; g.strokeStyle = col; g.fillStyle = col; g.lineWidth = 12;
  const mx = 256, my = 258;
  if (state === "answering") {
    g.lineWidth = 8; g.beginPath();
    for (let i = 0; i <= 40; i++) { const x = mx - 90 + i * 4.5; const a = 26 * Math.sin(t * 14 + i * 0.6) * Math.sin((i / 40) * Math.PI); i ? g.lineTo(x, my + a) : g.moveTo(x, my + a); }
    g.stroke();
  } else if (state === "happy") { g.beginPath(); g.moveTo(mx - 44, my - 6); g.quadraticCurveTo(mx, my + 56, mx + 44, my - 6); g.closePath(); g.fill(); }
  else if (state === "danger") { g.beginPath(); g.moveTo(mx - 34, my + 18); g.lineTo(mx + 34, my + 18); g.lineTo(mx, my - 24); g.closePath(); g.fill(); }
  else if (state === "warning") { g.beginPath(); g.moveTo(mx - 50, my + 12); for (let i = 1; i <= 4; i++) g.lineTo(mx - 50 + i * 25, my + 12 + (i % 2 ? -14 : 8)); g.stroke(); }
  else if (state === "thinking") { g.beginPath(); g.moveTo(mx - 36, my + 6); g.quadraticCurveTo(mx - 10, my - 10, mx + 36, my + 8); g.stroke(); }
  else if (state === "sleeping") { /* no mouth */ }
  else if (state === "listening") { g.beginPath(); g.arc(mx, my + 4, 9, 0, Math.PI * 2); g.fill(); }
  else { g.beginPath(); g.arc(mx, my - 18, 40, Math.PI * 0.18, Math.PI * 0.82); g.stroke(); }
}

function useFaceTexture() {
  return useMemo(() => {
    const c = document.createElement("canvas"); c.width = 512; c.height = 360;
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4;
    return { c, tex };
  }, []);
}

function textSprite(text: string, color: string, bg: string | null, size = 128) {
  const c = document.createElement("canvas"); c.width = c.height = size;
  const g = c.getContext("2d")!;
  if (bg) { g.fillStyle = bg; g.beginPath(); g.roundRect(6, 14, size - 12, size - 40, 26); g.fill(); }
  g.fillStyle = color; g.font = `700 ${size * 0.5}px Inter, system-ui, sans-serif`; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(text, size / 2, size / 2 - 4);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
function glowTexture() {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d")!; const r = g.createRadialGradient(64, 64, 4, 64, 64, 64);
  r.addColorStop(0, "rgba(255,255,255,.9)"); r.addColorStop(0.45, "rgba(255,255,255,.28)"); r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new THREE.CanvasTexture(c);
}

// ---- poses -----------------------------------------------------------------------------------------------
type P = [number, number, number, number];
function poses(s: BotState, t: number): { l: P; r: P } {
  const sw = Math.sin(t * 6);
  switch (s) {
    case "listening": return { l: [-0.92, 0.5, 0.3, 0.4], r: [1.05, -0.3, 0.15, -0.3] };
    case "thinking": return { l: [-1.05, -0.3, 0.15, 0.3], r: [0.5, -0.32, 0.88, 0] };
    case "answering": return { l: [-1.12, -0.05 + 0.14 * sw, 0.3, 0.5], r: [1.12, -0.05 - 0.14 * sw, 0.3, -0.5] };
    case "happy": return { l: [-1.05, -0.35, 0.15, 0.3], r: [1.0, 0.25 + 0.05 * sw, 0.45, -0.2] };
    case "searching": return { l: [-1.05, -0.3, 0.15, 0.3], r: [0.95 + 0.08 * Math.cos(t * 2), 0.05 + 0.08 * Math.sin(t * 2), 0.55, -0.4] };
    case "pointing": return { l: [-1.05, -0.3, 0.15, 0.3], r: [1.55, 0.05, 0.25, -1.57] };
    case "warning": return { l: [-1.05, -0.3, 0.15, 0.3], r: [1.1, 0.65, 0.3, -0.3 + 0.3 * sw] };
    case "danger": return { l: [-1.12, 0.75 + 0.05 * sw, 0.2, 0.5 + 0.3 * sw], r: [1.12, 0.75 - 0.05 * sw, 0.2, -0.5 - 0.3 * sw] };
    case "sleeping": return { l: [-0.95, -0.55, 0.1, 0.2], r: [0.95, -0.55, 0.1, -0.2] };
    default: return { l: [-1.05, -0.3, 0.15, 0.3], r: [1.05, -0.3, 0.15, -0.3] };
  }
}

function Hand({ g, bodyMat }: { g: React.Ref<THREE.Group>; bodyMat: THREE.Material }) {
  return (
    <group ref={g}>
      <mesh material={bodyMat} scale={[1, 1.15, 0.95]}><sphereGeometry args={[0.21, 20, 16]} /></mesh>
      <mesh position={[0, 0.17, 0]} rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.17, 0.035, 10, 24]} /><meshStandardMaterial color={GOLD} roughness={0.4} metalness={0.4} /></mesh>
      {[-0.1, 0, 0.1].map((x) => <mesh key={x} position={[x, -0.2, 0.04]}><sphereGeometry args={[0.055, 10, 8]} /><meshStandardMaterial color={GREY} roughness={0.7} /></mesh>)}
    </group>
  );
}

const egg = (() => {
  const pts: THREE.Vector2[] = [];
  const H = 1.0, R = 0.84;
  for (let i = 0; i <= 48; i++) { const y = -H + (2 * H * i) / 48; const k = y / H; pts.push(new THREE.Vector2(Math.max(0.001, R * Math.sqrt(Math.max(0, 1 - k * k)) * (1 - 0.1 * k)), y)); }
  return new THREE.LatheGeometry(pts, 56);
})();
const bolt = (() => {
  const s = new THREE.Shape();
  [[0.05, 0.5], [-0.17, 0.02], [-0.03, 0.02], [-0.1, -0.5], [0.17, 0.08], [0.03, 0.08], [0.12, 0.5]].forEach(([x, y], i) => (i ? s.lineTo(x, y) : s.moveTo(x, y)));
  s.closePath(); return new THREE.ExtrudeGeometry(s, { depth: 0.08, bevelEnabled: false });
})();

function Bot({ state }: { state: BotState }) {
  const root = useRef<THREE.Group>(null!);
  const body = useRef<THREE.Group>(null!);
  const lh = useRef<THREE.Group>(null!), rh = useRef<THREE.Group>(null!);
  const aura = useRef<THREE.Sprite>(null!);
  const ring = useRef<THREE.Mesh>(null!);
  const siren = useRef<THREE.Group>(null!), boltG = useRef<THREE.Mesh>(null!), rays = useRef<THREE.Group>(null!);
  const dots = useRef<THREE.Group>(null!);
  const mag = useRef<THREE.Group>(null!);
  const bubble = useRef<THREE.Sprite>(null!), bang = useRef<THREE.Sprite>(null!), zz = useRef<THREE.Sprite>(null!), spark = useRef<THREE.Group>(null!);
  const { c: faceC, tex: faceTex } = useFaceTexture();
  const bodyMat = useMemo(() => new THREE.MeshPhysicalMaterial({ color: "#6f93d8", roughness: 0.42, clearcoat: 0.5, clearcoatRoughness: 0.35 }), []);
  const rimMat = useMemo(() => new THREE.MeshStandardMaterial({ color: "#5ee7f2", emissive: "#5ee7f2", emissiveIntensity: 1.4, toneMapped: false }), []);
  const boltMat = useMemo(() => new THREE.MeshStandardMaterial({ color: "#ffe14a", emissive: "#ffd21f", emissiveIntensity: 1.3, toneMapped: false }), []);
  const ringMat = useMemo(() => new THREE.MeshBasicMaterial({ color: "#5eead4", transparent: true, opacity: 0.8, toneMapped: false, depthWrite: false }), []);
  const sirenMat = useMemo(() => new THREE.MeshStandardMaterial({ color: "#ff2a2a", emissive: "#ff1a1a", emissiveIntensity: 1.6, toneMapped: false }), []);
  const tex = useMemo(() => ({ glow: glowTexture(), bubble: textSprite("...", "#ffffff", "#a78bfa"), bang: textSprite("!", "#ffffff", "#ef4444", 128), zz: textSprite("z z", "#cbd5e1", null), star: textSprite("✦", "#bbf7d0", null, 96) }), []);
  const col = useMemo(() => ({ body: new THREE.Color(), glow: new THREE.Color(), eye: new THREE.Color() }), []);
  const cur = useRef({ key: "", blinkAt: 2, blinkUntil: 0 });
  const pos = useRef({ l: [-1.05, -0.3, 0.15, 0.3] as P, r: [1.05, -0.3, 0.15, -0.3] as P });

  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    const th = THEME[state];
    // colours follow the state smoothly
    col.body.set(th.body); bodyMat.color.lerp(col.body, 0.08);
    col.glow.set(th.glow); rimMat.color.lerp(col.glow, 0.12); rimMat.emissive.lerp(col.glow, 0.12);
    ringMat.color.lerp(col.glow, 0.12);
    (aura.current.material as THREE.SpriteMaterial).color.lerp(col.glow, 0.12);
    // face (redraw only when something changed)
    if (t > cur.current.blinkAt) { cur.current.blinkUntil = t + 0.13; cur.current.blinkAt = t + 2.2 + Math.random() * 2.6; }
    const blink = t < cur.current.blinkUntil;
    const key = `${state}${blink ? "b" : ""}${state === "answering" ? Math.floor(t * 14) : ""}`;
    if (key !== cur.current.key) { cur.current.key = key; drawFace(faceC, state, t, blink); faceTex.needsUpdate = true; }
    // body motion
    const danger = state === "danger", sleeping = state === "sleeping";
    const bob = Math.sin(t * (sleeping ? 0.8 : 1.7)) * (sleeping ? 0.03 : 0.07) + (state === "happy" ? Math.abs(Math.sin(t * 4)) * 0.12 : 0) - (sleeping ? 0.15 : 0);
    root.current.position.set(danger ? Math.sin(t * 46) * 0.035 : 0, bob, 0);
    const talk = state === "answering" ? 1 + 0.025 * Math.sin(t * 12) : 1;
    body.current.scale.set(talk, 1 / talk, talk);
    root.current.rotation.set(0, state === "idle" ? Math.sin(t * 0.7) * 0.18 : state === "thinking" ? Math.sin(t * 1.1) * 0.25 : state === "pointing" ? -0.35 : state === "searching" ? Math.sin(t * 1.5) * 0.2 : 0,
      state === "listening" ? 0.14 : state === "thinking" ? 0.08 : danger ? Math.sin(t * 40) * 0.04 : sleeping ? 0.08 : 0);
    // hands
    const p = poses(state, t);
    for (const [grp, key, side] of [[lh, "l", -1], [rh, "r", 1]] as const) {
      const cp = pos.current[key], tp = p[key];
      for (let i = 0; i < 4; i++) cp[i] += (tp[i] - cp[i]) * 0.14;
      grp.current.position.set(cp[0] * 1.1, cp[1] + Math.sin(t * 2 + side) * 0.03, cp[2] + 0.1);
      grp.current.rotation.z = cp[3];
    }
    mag.current.visible = state === "searching";
    // antenna: bolt normally, siren in danger
    siren.current.visible = danger; boltG.current.visible = !danger;
    const pulse = 0.55 + 0.45 * Math.sin(t * (danger ? 14 : state === "warning" ? 8 : 3));
    boltMat.emissive.set(state === "thinking" ? "#c4b5fd" : state === "warning" ? "#ffc93c" : sleeping ? "#6b7280" : "#ffd21f");
    boltMat.emissiveIntensity = sleeping ? 0.2 : 0.8 + pulse * 0.9;
    sirenMat.emissiveIntensity = 0.8 + pulse * 1.8;
    rays.current.rotation.y = t * 9;
    // aura, ring
    const sp = aura.current.material as THREE.SpriteMaterial;
    sp.opacity = sleeping ? 0.08 : danger ? 0.5 + 0.25 * Math.sin(t * 10) : state === "idle" ? 0.2 : 0.32;
    aura.current.scale.setScalar(danger ? 4.6 + 0.4 * Math.sin(t * 10) : 3.9);
    ring.current.scale.setScalar(1 + 0.08 * Math.sin(t * 2.4));
    // extras
    dots.current.visible = state === "thinking";
    dots.current.rotation.y = t * 2.4;
    bubble.current.visible = state === "thinking"; bubble.current.position.y = 1.7 + Math.sin(t * 2) * 0.05;
    bang.current.visible = danger; bang.current.scale.setScalar(0.62 + 0.1 * Math.sin(t * 12));
    zz.current.visible = sleeping; zz.current.position.y = 1.2 + ((t * 0.3) % 1) * 0.5; (zz.current.material as THREE.SpriteMaterial).opacity = 1 - ((t * 0.3) % 1);
    spark.current.visible = state === "happy"; spark.current.rotation.y = t * 2;
    rimMat.emissiveIntensity = state === "sleeping" ? 0.2 : 1.1 + 0.5 * Math.sin(t * 3);
  });

  return (
    <>
      <sprite ref={aura} position={[0, 0.1, -0.5]} scale={[3.9, 3.9, 1]}><spriteMaterial map={tex.glow} color="#5eead4" transparent opacity={0.25} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} /></sprite>
      <mesh ref={ring} position={[0, -1.3, 0]} rotation={[-Math.PI / 2, 0, 0]}><torusGeometry args={[0.55, 0.035, 10, 48]} /><primitive object={ringMat} attach="material" /></mesh>
      <group ref={root}>
        <group ref={body}>
          <mesh geometry={egg} material={bodyMat} />
          {/* waist band */}
          <mesh position={[0, -0.3, 0]} rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.83, 0.03, 10, 64]} /><meshStandardMaterial color={GOLD} roughness={0.4} metalness={0.4} /></mesh>
          {/* face */}
          <group position={[0, 0.36, 0.8]} rotation={[-0.12, 0, 0]}>
            <RoundedBox args={[1.3, 1.0, 0.16]} radius={0.3} smoothness={5}><meshStandardMaterial color={GOLD} roughness={0.35} metalness={0.5} /></RoundedBox>
            <RoundedBox args={[1.14, 0.84, 0.14]} radius={0.26} smoothness={5} position={[0, 0, 0.035]}><meshStandardMaterial color="#05080f" roughness={0.1} metalness={0.2} /></RoundedBox>
            <mesh position={[0, 0, 0.115]}><planeGeometry args={[1.08, 0.78]} /><meshBasicMaterial map={faceTex} toneMapped={false} /></mesh>
          </group>
          {/* ears */}
          {[-1, 1].map((s) => (
            <group key={s} position={[s * 0.88, 0.38, 0.02]} rotation={[0, 0, Math.PI / 2]}>
              <mesh><cylinderGeometry args={[0.22, 0.22, 0.16, 28]} /><meshStandardMaterial color={GREY} roughness={0.55} /></mesh>
              <mesh position={[0, s * 0.09, 0]}><torusGeometry args={[0.17, 0.03, 10, 32]} /><primitive object={rimMat} attach="material" /></mesh>
            </group>
          ))}
          {/* antenna */}
          <mesh position={[0, 1.12, 0]}><cylinderGeometry args={[0.025, 0.035, 0.3, 10]} /><meshStandardMaterial color="#9b8bd0" roughness={0.5} /></mesh>
          <mesh ref={boltG} geometry={bolt} material={boltMat} position={[0, 1.55, -0.04]} scale={0.8} />
          <group ref={siren} position={[0, 1.24, 0]}>
            <mesh><cylinderGeometry args={[0.16, 0.19, 0.08, 20]} /><meshStandardMaterial color={GREY} /></mesh>
            <mesh position={[0, 0.04, 0]} material={sirenMat}><sphereGeometry args={[0.15, 20, 14, 0, Math.PI * 2, 0, Math.PI / 2]} /></mesh>
            <group ref={rays} position={[0, 0.1, 0]}>
              {[0, Math.PI / 2].map((r) => <mesh key={r} rotation={[0, r, 0]} position={[0, 0.12, 0]}><planeGeometry args={[0.9, 0.22]} /><meshBasicMaterial color="#ff3b3b" transparent opacity={0.32} side={THREE.DoubleSide} depthWrite={false} blending={THREE.AdditiveBlending} toneMapped={false} /></mesh>)}
            </group>
          </group>
          {/* thinking dots */}
          <group ref={dots} position={[0, 0.5, 0]}>
            {[0, 2.1, 4.2].map((a, i) => <mesh key={i} position={[Math.cos(a) * 1.05, 0.15 * Math.sin(a * 1.5), Math.sin(a) * 1.05]}><sphereGeometry args={[0.07, 12, 10]} /><meshBasicMaterial color="#b69cff" toneMapped={false} /></mesh>)}
          </group>
          {/* sparkles */}
          <group ref={spark} position={[0, 0.5, 0]}>
            {[[0.95, 0.5], [-0.9, 0.7], [0.6, 0.95]].map(([x, y], i) => <sprite key={i} position={[x, y, 0.3]} scale={[0.26, 0.26, 1]}><spriteMaterial map={tex.star} transparent depthWrite={false} toneMapped={false} /></sprite>)}
          </group>
        </group>
        <Hand g={lh} bodyMat={bodyMat} />
        <group ref={rh}>
          <Hand g={null} bodyMat={bodyMat} />
          <group ref={mag} position={[0.05, 0.25, 0.1]} rotation={[0, 0, 0.5]}>
            <mesh position={[0, 0.3, 0]}><torusGeometry args={[0.24, 0.035, 10, 32]} /><meshStandardMaterial color="#b983ff" roughness={0.3} /></mesh>
            <mesh position={[0, 0.3, 0]}><circleGeometry args={[0.23, 28]} /><meshStandardMaterial color="#bfe9ff" transparent opacity={0.28} /></mesh>
            <mesh position={[0, -0.08, 0]}><cylinderGeometry args={[0.03, 0.03, 0.34, 8]} /><meshStandardMaterial color="#ef4444" /></mesh>
          </group>
        </group>
        <sprite ref={bubble} position={[0.95, 1.7, 0.3]} scale={[0.7, 0.7, 1]}><spriteMaterial map={tex.bubble} transparent depthWrite={false} toneMapped={false} /></sprite>
        <sprite ref={bang} position={[1.15, 1.3, 0.3]} scale={[0.62, 0.62, 1]}><spriteMaterial map={tex.bang} transparent depthWrite={false} toneMapped={false} /></sprite>
        <sprite ref={zz} position={[0.9, 1.2, 0.3]} scale={[0.7, 0.7, 1]}><spriteMaterial map={tex.zz} transparent depthWrite={false} toneMapped={false} /></sprite>
      </group>
    </>
  );
}

/** The bot in its own small canvas. State comes from the store (`bot`) unless given. */
export function Volty({ state, height = 150 }: { state?: BotState; height?: number }) {
  const storeState = useTwin((s) => s.bot);
  const s = state ?? storeState;
  const wrap = useRef<HTMLDivElement>(null);
  useEffect(() => { /* canvas sizes itself to the wrapper */ }, []);
  return (
    <div ref={wrap} className={`volty s-${s}`} style={{ height }}>
      <Canvas dpr={1} gl={{ alpha: true, antialias: true }} camera={{ position: [0, 0.38, 5.7], fov: 37 }} style={{ background: "transparent" }}>
        <ambientLight intensity={1.05} />
        <directionalLight position={[3, 5, 5]} intensity={1.7} />
        <directionalLight position={[-4, 1, 3]} intensity={0.6} color="#9ec5ff" />
        <Bot state={s} />
      </Canvas>
      <span className="vlabel">{BOT_LABEL[s]}</span>
    </div>
  );
}

/** Dev page: every state side by side. Open the twin with ?botdemo=1 */
export function BotGallery() {
  const all = Object.keys(BOT_LABEL) as BotState[];
  return (
    <div style={{ position: "fixed", inset: 0, overflow: "auto", background: "#cfd6e0", padding: 16, display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8 }}>
      {all.map((s) => <div key={s} className="h3" style={{ position: "relative", inset: "auto" }}><Volty state={s} height={210} /></div>)}
    </div>
  );
}
