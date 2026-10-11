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

function Spark({ on }: { on: () => boolean }) {
  const m = useRef<THREE.Mesh>(null!);
  const l = useRef<THREE.PointLight>(null!);
  useFrame(() => {
    const live = on() && Math.sin(performance.now() / 90) > 0.2;
    m.current.visible = live;
    l.current.intensity = live ? 3 + Math.random() * 3 : 0;
    m.current.scale.setScalar(0.6 + Math.random() * 0.8);
  });
  return (
    <group>
      <mesh ref={m}>
        <icosahedronGeometry args={[0.12, 0]} />
        <meshBasicMaterial color="#fff7c2" toneMapped={false} />
      </mesh>
      <pointLight ref={l} color="#ffd9a0" distance={5} intensity={0} />
    </group>
  );
}

const COLORS = {
  healthy: new THREE.Color("#22c55e"), alert: new THREE.Color("#ef4444"),
  repair: new THREE.Color("#f59e0b"), repaired: new THREE.Color("#22c55e"),
} as const;

function WeldRobot({ m, hero, color }: { m: Machine; hero: boolean; color?: string }) {
  const a1 = useRef<THREE.Group>(null!);
  const a2 = useRef<THREE.Group>(null!);
  const a3 = useRef<THREE.Group>(null!);
  const bodyMats = useRef<THREE.MeshStandardMaterial[]>([]);
  const bearing = useRef<THREE.MeshStandardMaterial>(null!);
  const data = useTwin((s) => s.data)!;
  const shift = useTwin((s) => s.shift);
  const status = useRef<Status>("healthy");
  const base = color ?? (hero ? "#f1f5f9" : "#f97316");
  useFrame(() => {
    const t = clock.t;
    const st = hero ? m05Status(t, shift, data.hero) : "healthy";
    status.current = st;
    const k = st === "repair" ? 0 : 1;
    const sp = (st === "alert" ? 1.5 : 1) * 0.9;
    const phase = t * sp + (m.id ? m.id.charCodeAt(2) : 0);
    a1.current.rotation.y = Math.sin(phase * 0.7) * 0.65 * k;
    a2.current.rotation.z = 0.7 + Math.sin(phase * 1.1) * 0.3 * k;
    a3.current.rotation.z = -1.25 + Math.sin(phase * 1.7) * 0.35 * k;
    if (hero) {
      const col = COLORS[st];
      const pulse = st === "alert" ? 0.7 + 0.5 * Math.sin(performance.now() / 150) : st === "repair" ? 0.5 : 0;
      bodyMats.current.forEach((mt) => {
        if (!mt) return;
        mt.emissive.copy(col);
        mt.emissiveIntensity = pulse * 0.45;
      });
      if (bearing.current) {
        bearing.current.emissive.copy(col);
        bearing.current.emissiveIntensity = st === "healthy" || st === "repaired" ? 0.0 : pulse * 3;
      }
    }
  });
  const body = (i: number) => (
    <meshStandardMaterial ref={(mt) => { if (mt) bodyMats.current[i] = mt; }} color={base} roughness={0.35} metalness={0.45} />
  );
  return (
    <group rotation={[0, Math.PI / 2, 0]}>
      <Box p={[0, 0.2, 0]} s={[1.9, 0.4, 1.9]} c={DARK} />
      <mesh position={[0, 0.55, 0]} castShadow>
        <cylinderGeometry args={[0.6, 0.65, 0.3, 28]} />
        <meshStandardMaterial color="#cbd5e1" roughness={0.3} metalness={0.7} />
      </mesh>
      {/* joint 1 bearing ring: m05_joint1_bearing, the hero component */}
      <mesh position={[0, 0.72, 0]} rotation={[Math.PI / 2, 0, 0]} name={hero ? "m05_joint1_bearing" : undefined}>
        <torusGeometry args={[0.52, 0.07, 12, 32]} />
        <meshStandardMaterial ref={bearing} color="#475569" metalness={0.8} roughness={0.3} emissive="#000000" />
      </mesh>
      <group ref={a1} position={[0, 0.7, 0]}>
        <mesh position={[0, 0.7, 0]} castShadow>
          <boxGeometry args={[0.7, 1.4, 0.7]} />
          {body(0)}
        </mesh>
        <mesh position={[0, 1.45, 0]} castShadow>
          <sphereGeometry args={[0.42, 20, 16]} />
          {body(1)}
        </mesh>
        <group ref={a2} position={[0, 1.45, 0]}>
          <mesh position={[0.9, 0, 0]} castShadow>
            <boxGeometry args={[1.8, 0.42, 0.5]} />
            {body(2)}
          </mesh>
          <group ref={a3} position={[1.8, 0, 0]}>
            <mesh castShadow><sphereGeometry args={[0.3, 16, 12]} />{body(3)}</mesh>
            <mesh position={[0.7, 0, 0]} castShadow>
              <boxGeometry args={[1.4, 0.3, 0.36]} />
              {body(4)}
            </mesh>
            <group position={[1.4, 0, 0]}>
              <mesh position={[0.15, -0.1, 0]} castShadow>
                <cylinderGeometry args={[0.14, 0.14, 0.3, 12]} />
                <meshStandardMaterial color="#334155" metalness={0.7} roughness={0.35} />
              </mesh>
              <mesh position={[0.3, -0.45, 0.1]} castShadow><boxGeometry args={[0.1, 0.7, 0.08]} /><meshStandardMaterial color="#94a3b8" metalness={0.9} roughness={0.25} /></mesh>
              <mesh position={[0.3, -0.45, -0.1]} castShadow><boxGeometry args={[0.1, 0.7, 0.08]} /><meshStandardMaterial color="#94a3b8" metalness={0.9} roughness={0.25} /></mesh>
              <group position={[0.3, -0.85, 0]}>
                <Spark on={() => status.current !== "repair"} />
              </group>
            </group>
          </group>
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
      return <WeldRobot m={{ id: "M02" } as Machine} hero={false} color="#fbbf24" />;
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
