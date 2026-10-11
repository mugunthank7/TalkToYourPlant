import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../clock";
import { Machine, Status, m05Status, toScene } from "../data";
import { useTwin } from "../state";

const GREY = "#8b95a1";
const DARK = "#374151";
const ORANGE = "#f59e0b";

function Box({ p, s, c = GREY, ...rest }: { p: [number, number, number]; s: [number, number, number]; c?: string } & Record<string, unknown>) {
  return (
    <mesh position={p} castShadow receiveShadow {...rest}>
      <boxGeometry args={s} />
      <meshStandardMaterial color={c} roughness={0.6} metalness={0.3} />
    </mesh>
  );
}

const STATUS_COLOR: Record<Status, string> = { healthy: "#22c55e", alert: "#ef4444", repair: "#f59e0b", repaired: "#22c55e" };

function WeldRobot({ m, hero }: { m: Machine; hero: boolean }) {
  const a1 = useRef<THREE.Group>(null!);
  const a2 = useRef<THREE.Group>(null!);
  const glow = useRef<THREE.MeshStandardMaterial>(null!);
  const data = useTwin((s) => s.data)!;
  const shift = useTwin((s) => s.shift);
  useFrame(() => {
    const t = clock.t;
    const st = hero ? m05Status(t, shift, data.hero) : "healthy";
    const working = st !== "repair";
    const k = working ? 1 : 0;
    const speed = st === "alert" ? 3.2 : 2;
    a1.current.rotation.y = Math.sin(t * 0.8 * speed) * 0.9 * k;
    a2.current.rotation.z = -0.5 + Math.sin(t * 1.3 * speed) * 0.5 * k;
    if (hero && glow.current) {
      const base = new THREE.Color(STATUS_COLOR[st]);
      glow.current.emissive.copy(base);
      const pulse = st === "alert" ? 0.6 + 0.4 * Math.sin(performance.now() / 150) : st === "repair" ? 0.5 : 0.05;
      glow.current.emissiveIntensity = pulse;
    }
  });
  return (
    <group position={[0, 0, 0]}>
      <Box p={[0, 0.25, 0]} s={[1.6, 0.5, 1.6]} c={DARK} />
      <group ref={a1} position={[0, 0.5, 0]}>
        <mesh position={[0, 0.9, 0]} castShadow>
          <cylinderGeometry args={[0.35, 0.4, 1.8, 20]} />
          <meshStandardMaterial ref={glow} color={hero ? "#f3f4f6" : ORANGE} roughness={0.4} metalness={0.4} emissive="#000000" />
        </mesh>
        <group ref={a2} position={[0, 1.8, 0]}>
          <Box p={[0, 0.9, 0]} s={[0.35, 1.8, 0.35]} c={hero ? "#e5e7eb" : ORANGE} />
          <Box p={[0.55, 1.85, 0]} s={[1.2, 0.3, 0.3]} c={hero ? "#e5e7eb" : ORANGE} />
          <mesh position={[1.2, 1.5, 0]} castShadow>
            <cylinderGeometry args={[0.08, 0.14, 0.7, 12]} />
            <meshStandardMaterial color="#9ca3af" metalness={0.8} roughness={0.3} />
          </mesh>
        </group>
      </group>
    </group>
  );
}

function Press() {
  const ram = useRef<THREE.Mesh>(null!);
  useFrame(() => {
    ram.current.position.y = 3.2 + Math.max(0, Math.sin(clock.t * 0.7 * 2)) * -1.2;
  });
  return (
    <group>
      <Box p={[-2.2, 3, 0]} s={[1, 6, 4]} c="#4b5563" />
      <Box p={[2.2, 3, 0]} s={[1, 6, 4]} c="#4b5563" />
      <Box p={[0, 6.2, 0]} s={[5.4, 1, 4]} c="#374151" />
      <Box p={[0, 0.5, 0]} s={[4, 1, 3.5]} c="#6b7280" />
      <mesh ref={ram} position={[0, 3.2, 0]} castShadow>
        <boxGeometry args={[3.4, 1.4, 3]} />
        <meshStandardMaterial color="#9ca3af" metalness={0.6} roughness={0.35} />
      </mesh>
    </group>
  );
}

function Decoiler() {
  const spin = useRef<THREE.Mesh>(null!);
  useFrame(() => {
    spin.current.rotation.z = clock.t * 0.3;
  });
  return (
    <group>
      <Box p={[0, 0.3, 0]} s={[3, 0.6, 2.4]} c={DARK} />
      <mesh ref={spin} position={[0, 1.8, 0]} rotation={[0, 0, 0]} castShadow>
        <cylinderGeometry args={[1.5, 1.5, 1.6, 28]} />
        <meshStandardMaterial color="#cbd5e1" metalness={0.8} roughness={0.35} />
      </mesh>
    </group>
  );
}

function Generic({ type }: { type: string }) {
  switch (type) {
    case "press":
      return <Press />;
    case "decoiler":
      return <Decoiler />;
    case "robot":
      return <WeldRobot m={{} as Machine} hero={false} />;
    case "fixture":
      return (
        <group>
          <Box p={[0, 0.4, 0]} s={[6, 0.8, 4]} c={DARK} />
          <Box p={[-2.4, 1.2, 1.5]} s={[0.4, 1.6, 0.4]} c="#60a5fa" />
          <Box p={[2.4, 1.2, 1.5]} s={[0.4, 1.6, 0.4]} c="#60a5fa" />
          <Box p={[-2.4, 1.2, -1.5]} s={[0.4, 1.6, 0.4]} c="#60a5fa" />
          <Box p={[2.4, 1.2, -1.5]} s={[0.4, 1.6, 0.4]} c="#60a5fa" />
        </group>
      );
    case "vision_gate":
      return (
        <group>
          <Box p={[0, 3.2, 0]} s={[0.5, 0.5, 6.4]} c="#334155" />
          <Box p={[0, 1.6, 3]} s={[0.5, 3.2, 0.5]} c="#334155" />
          <Box p={[0, 1.6, -3]} s={[0.5, 3.2, 0.5]} c="#334155" />
          <Box p={[0, 2.8, 0]} s={[0.3, 0.3, 0.9]} c="#38bdf8" />
        </group>
      );
    case "gantry":
      return (
        <group>
          <Box p={[0, 3, 0]} s={[8, 0.4, 0.5]} c="#475569" />
          <Box p={[-4, 1.5, 0]} s={[0.4, 3, 0.4]} c="#475569" />
          <Box p={[4, 1.5, 0]} s={[0.4, 3, 0.4]} c="#475569" />
          <Box p={[0, 0.6, 2]} s={[5, 1.2, 2.4]} c="#a3e635" />
        </group>
      );
    case "sealer":
      return (
        <group>
          <Box p={[0, 1, 0]} s={[6, 2, 4]} c="#64748b" />
          <Box p={[0, 2.4, 0]} s={[5, 0.8, 3]} c="#94a3b8" />
        </group>
      );
    case "agv":
      return <Box p={[0, 0.4, 0]} s={[2.4, 0.8, 1.4]} c="#facc15" />;
    default:
      return <Box p={[0, 1, 0]} s={[2, 2, 2]} />;
  }
}

export function Machines() {
  const data = useTwin((s) => s.data)!;
  return (
    <>
      {data.layout.machines
        .filter((m) => m.type !== "conveyor")
        .map((m) => {
          const [x, z] = toScene(m.x, m.z);
          return (
            <group key={m.id} position={[x, 0, z]} rotation={[0, (m.rot_deg * Math.PI) / 180, 0]}>
              {m.type === "weld_robot" ? <WeldRobot m={m} hero={m.id === "M05"} /> : <Generic type={m.type} />}
            </group>
          );
        })}
    </>
  );
}
