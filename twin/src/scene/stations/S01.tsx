import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../../clock";
import { AtStation, B, Cyl, Npc, Pad, RB, Screen } from "../kit";

const BLUE = "#1d5fd0";
const COIL = "#c9d1dc";

function Coil({ p, r = 0.8, w = 1.5, rot = [0, 0, Math.PI / 2] as [number, number, number] }: { p: [number, number, number]; r?: number; w?: number; rot?: [number, number, number] }) {
  return (
    <group position={p}>
      <mesh rotation={rot} castShadow receiveShadow>
        <cylinderGeometry args={[r, r, w, 36]} />
        <meshStandardMaterial color={COIL} metalness={0.95} roughness={0.28} />
      </mesh>
      <mesh rotation={rot}>
        <cylinderGeometry args={[r * 0.35, r * 0.35, w * 1.02, 24]} />
        <meshStandardMaterial color="#1f2937" metalness={0.6} roughness={0.5} />
      </mesh>
    </group>
  );
}

function Hoist() {
  const trolley = useRef<THREE.Group>(null!);
  useFrame(() => { trolley.current.position.x = 2.5 + Math.sin(clock.t / 17) * 2.0; });
  return (
    <group>
      <B p={[0, 7.4, 0]} s={[18, 0.35, 0.3]} c="#f59e0b" metal={0.4} />
      <group ref={trolley} position={[2.5, 7.2, 1.5]}>
        <B p={[0, 0, 0]} s={[1.0, 0.4, 0.6]} c="#1f2937" />
        {[-0.18, 0.18].map((x) => <Cyl key={x} p={[x, -3.2, 0]} r={0.012} h={6.2} c="#475569" />)}
        <B p={[0, -6.3, 0]} s={[0.55, 0.22, 0.15]} c="#facc15" metal={0.5} />
        <B p={[0, -6.5, 0]} s={[0.1, 0.22, 0.1]} c="#475569" metal={0.8} />
      </group>
    </group>
  );
}

export function S01() {
  return (
    <AtStation id="S01">
      {() => (
        <group>
          <Pad w={18} d={14} tone="#e7eaee" />
          {/* green walkway frame inside the pad */}
          <mesh position={[0, 0.075, 6.4]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[17.4, 0.9]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[-8.3, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.9, 13]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          {/* decoiler with a big coil on the mandrel */}
          <group position={[-5.8, 0, -3.8]}>
            <RB p={[0, 0.3, 0]} s={[3.4, 0.6, 2.4]} c={BLUE} metal={0.5} />
            <RB p={[-1.2, 1.4, 0]} s={[0.4, 1.8, 2.0]} c={BLUE} metal={0.5} />
            <RB p={[1.2, 1.4, 0]} s={[0.4, 1.8, 2.0]} c={BLUE} metal={0.5} />
            <Coil p={[0, 1.6, 0]} r={0.95} w={1.9} />
            <B p={[1.9, 0.9, 0]} s={[0.5, 1.2, 1.2]} c="#334155" />
          </group>

          {/* straightener + feed table, ending in a stack of blanks */}
          <group position={[0.2, 0, -3.8]}>
            <RB p={[-1.4, 0.95, 0]} s={[1.6, 1.0, 1.6]} c={BLUE} metal={0.5} />
            {[-0.5, 0, 0.5].map((x) => <Cyl key={x} p={[-1.4 + x, 1.55, 0]} r={0.14} h={1.5} c="#aeb7c4" metal={0.9} rot={[Math.PI / 2, 0, 0]} seg={14} />)}
            <B p={[2.4, 0.78, 0]} s={[4.2, 0.1, 1.6]} c="#8e99a8" metal={0.8} rough={0.35} />
            {[0.4, 1.4, 2.4, 3.4, 4.4].map((x) => [-0.7, 0.7].map((z) => <B key={`${x}${z}`} p={[x, 0.38, z]} s={[0.08, 0.76, 0.08]} c={BLUE} />))}
            <B p={[2.4, 0.7, 0]} s={[4.2, 0.04, 1.5]} c={BLUE} />
          </group>
          <group position={[6.6, 0, -3.8]}>
            <B p={[0, 0.12, 0]} s={[2.2, 0.24, 1.7]} c="#64748b" />
            {Array.from({ length: 14 }).map((_, i) => <B key={i} p={[0, 0.3 + i * 0.07, 0]} s={[2.0, 0.05, 1.5]} c="#b9c1cc" metal={0.9} rough={0.3} />)}
          </group>

          {/* coil rack with four coils in V-cradles */}
          <group position={[2.4, 0, 2.2]}>
            {[-3.0, -1.0, 1.0, 3.0].map((x, i) => (
              <group key={i} position={[x * 0.8, 0, 0]}>
                <B p={[0, 0.3, 0]} s={[1.9, 0.2, 2.2]} c={BLUE} metal={0.5} />
                <B p={[0, 0.65, -0.6]} s={[1.7, 0.1, 0.5]} c={BLUE} rot={[0.6, 0, 0]} />
                <B p={[0, 0.65, 0.6]} s={[1.7, 0.1, 0.5]} c={BLUE} rot={[-0.6, 0, 0]} />
                <Coil p={[0, 1.15, 0]} r={0.8} w={1.5} />
              </group>
            ))}
          </group>
          <Hoist />

          {/* banding station */}
          <group position={[-6.8, 0, 3.8]}>
            {[[-0.8, -0.7], [0.8, -0.7], [-0.8, 0.7], [0.8, 0.7]].map(([x, z], i) => <B key={i} p={[x, 1.0, z]} s={[0.1, 2.0, 0.1]} c={BLUE} />)}
            <B p={[0, 2.0, 0]} s={[1.7, 0.1, 1.5]} c={BLUE} />
            <Cyl p={[0, 0.7, 0]} r={0.55} h={0.35} c="#1f2937" rot={[Math.PI / 2, 0, 0]} />
          </group>

          {/* bollards and light curtain at the feed table */}
          {[-1.6, -0.4, 0.8, 2.0].map((x) => <Cyl key={x} p={[x, 0.55, -1.2]} r={0.1} h={1.1} c="#facc15" metal={0.2} />)}
          {[-1.6, 2.0].map((x) => <B key={x} p={[x, 1.0, -1.7]} s={[0.1, 2.0, 0.1]} c="#334155" />)}
          <B p={[0.2, 1.2, -1.7]} s={[3.5, 0.02, 0.02]} c="#ef4444" emissive="#ef4444" ei={1.5} shadow={false} />
          <B p={[0.2, 1.7, -1.7]} s={[3.5, 0.02, 0.02]} c="#ef4444" emissive="#ef4444" ei={1.5} shadow={false} />

          {/* HMI stand + people */}
          <group position={[-3.2, 0, 3.2]}>
            <B p={[0, 0.5, 0]} s={[0.1, 1.0, 0.1]} c="#475569" />
            <RB p={[0, 1.15, 0]} s={[0.7, 0.5, 0.08]} c="#1d5fd0" r={0.03} rot={[-0.2, 0, 0]} />
            <Screen p={[0, 1.15, 0.045]} s={[0.62, 0.4]} rot={[-0.2, 0, 0]} draw={(ctx, w, h) => { ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h); ctx.fillStyle = "#38bdf8"; ctx.font = "700 30px sans-serif"; ctx.fillText("DECOILER 1", 14, 44); ctx.fillStyle = "#22c55e"; ctx.fillText("coil 1.9 t · RUN", 14, 92); }} />
          </group>
          <Npc p={[-1.8, 0, 2.7]} rotY={-1.2} color="#facc15" pose="stand" seed={1} />
          <Npc p={[1.0, 0, 0.2]} rotY={0.4} color="#facc15" pose="work" seed={5} />
        </group>
      )}
    </AtStation>
  );
}
