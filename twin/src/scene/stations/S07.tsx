import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../../clock";
import { AtStation, Andon, B, CellFence, Npc, Pad, RB, Screen } from "../kit";

const GREY = "#7c8795";

export function S07() {
  const lasers = useRef<THREE.MeshBasicMaterial[]>([]);
  useFrame(() => {
    lasers.current.forEach((m, i) => { if (m) m.opacity = 0.22 + 0.14 * Math.sin(clock.t * 4 + i * 1.7); });
  });
  const heat = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    ctx.fillStyle = "#06121a"; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#38bdf8"; ctx.font = "700 22px sans-serif"; ctx.fillText("BODY SCAN  DEFECT MAP", 14, 30);
    ctx.fillStyle = "#12345a"; ctx.beginPath(); ctx.ellipse(w / 2, h / 2 + 10, w * 0.38, h * 0.26, 0, 0, 7); ctx.fill();
    const g = ctx.createRadialGradient(w * 0.62, h * 0.5, 4, w * 0.62, h * 0.5, 50);
    g.addColorStop(0, "rgba(251,146,60,.95)"); g.addColorStop(1, "rgba(251,146,60,0)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#86efac"; ctx.font = "18px sans-serif"; ctx.fillText("1 minor mark · PASS", 14, h - 12);
  };
  return (
    <AtStation id="S07">
      {() => (
        <group>
          <Pad w={10} d={11} tone="#eef1f5" />
          {/* green frame like the plan */}
          <mesh position={[-4.6, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.6, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[4.6, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.6, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[0, 0.075, -5.0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[9.4, 0.6]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          <CellFence w={10} d={11} belt={3.4} />

          {/* camera arch */}
          <group position={[-1.0, 0, 0]}>
            {[-2.9, 2.9].map((z) => <RB key={z} p={[0, 1.9, z]} s={[0.4, 3.8, 0.4]} c={GREY} metal={0.6} r={0.05} />)}
            <RB p={[0, 3.75, 0]} s={[0.4, 0.4, 6.2]} c={GREY} metal={0.6} r={0.05} />
            {/* cameras: 3 on top, 2 per side */}
            {[-1.6, 0, 1.6].map((z) => (
              <group key={z} position={[0, 3.45, z]}>
                <B p={[0, 0, 0]} s={[0.3, 0.3, 0.3]} c="#1f2937" metal={0.6} />
                <B p={[0, -0.18, 0]} s={[0.14, 0.08, 0.14]} c="#38bdf8" emissive="#38bdf8" ei={1.2} />
              </group>
            ))}
            {[-2.55, 2.55].flatMap((z) => [1.0, 2.2].map((y) => (
              <group key={`${z}${y}`} position={[0, y, z]}>
                <B p={[0, 0, 0]} s={[0.28, 0.28, 0.28]} c="#1f2937" metal={0.6} />
                <B p={[0, 0, -Math.sign(z) * 0.16]} s={[0.12, 0.12, 0.06]} c="#38bdf8" emissive="#38bdf8" ei={1.2} />
              </group>
            )))}
            {/* blue scan planes over the belt */}
            {[0, 1, 2].map((i) => (
              <mesh key={i} position={[0.0 + i * 0.05, 1.6, 0]} rotation={[0, 0, 0]}>
                <boxGeometry args={[0.015, 2.5, 3.2]} />
                <meshBasicMaterial ref={(m) => { if (m) lasers.current[i] = m; }} color="#3aa5ff" transparent opacity={0.3} depthWrite={false} blending={THREE.AdditiveBlending} />
              </mesh>
            ))}
          </group>

          {/* LED inspection tunnel after the arch */}
          <group position={[2.8, 0, 0]}>
            {[-1.9, 1.9].map((z) => <RB key={z} p={[0, 1.5, z]} s={[3.4, 3.0, 0.15]} c="#f3f5f8" metal={0.2} rough={0.35} r={0.05} />)}
            <RB p={[0, 3.05, 0]} s={[3.4, 0.2, 4.0]} c="#f3f5f8" metal={0.2} rough={0.35} r={0.05} />
            {[-1.2, 0, 1.2].map((x) => <B key={x} p={[x, 2.92, 0]} s={[0.25, 0.04, 3.4]} c="#ffffff" emissive="#ffffff" ei={2.5} shadow={false} />)}
            {[-1.2, 0, 1.2].flatMap((x) => [-1.82, 1.82].map((z) => <B key={`${x}${z}`} p={[x, 1.5, z]} s={[0.25, 1.8, 0.04]} c="#ffffff" emissive="#ffffff" ei={2.0} shadow={false} />))}
          </group>

          {/* QA booth with defect monitor, inspector */}
          <group position={[1.2, 0, 3.7]}>
            <RB p={[0, 0.4, 0]} s={[1.8, 0.8, 0.9]} c="#e2e8f0" metal={0.3} />
            <RB p={[0, 1.35, -0.1]} s={[1.3, 0.8, 0.06]} c="#0b0f19" r={0.03} />
            <Screen p={[0, 1.35, -0.065]} s={[1.2, 0.72]} draw={heat} />
            <B p={[0, 0.95, -0.1]} s={[0.08, 0.3, 0.08]} c="#475569" />
          </group>
          <Npc p={[0.2, 0, 2.6]} rotY={0} color="#38bdf8" pose="stand" seed={2} />

          {/* tablet stand + gauge table */}
          <group position={[3.6, 0, 4.2]}>
            <B p={[0, 0.7, 0]} s={[1.0, 0.06, 0.7]} c="#cbd5e1" metal={0.5} />
            {[[-0.45, -0.3], [0.45, -0.3], [-0.45, 0.3], [0.45, 0.3]].map(([x, z], i) => <B key={i} p={[x, 0.35, z]} s={[0.05, 0.7, 0.05]} c="#94a3b8" />)}
            <B p={[-0.2, 0.76, 0]} s={[0.3, 0.05, 0.18]} c="#111827" />
            <B p={[0.25, 0.8, 0]} s={[0.22, 0.12, 0.22]} c="#475569" />
          </group>
          <group position={[3.0, 0, 3.0]}>
            <B p={[0, 0.55, 0]} s={[0.06, 1.1, 0.06]} c="#475569" />
            <B p={[0, 1.2, 0]} s={[0.55, 0.38, 0.04]} c="#0b0f19" rot={[-0.25, 0, 0]} />
          </group>

          {/* reject / rework bay with an empty skid */}
          <group position={[-3.0, 0, 3.6]}>
            {[[-1.9, 0, 3.8, 0.12], [1.9, 0, 3.8, 0.12]].map(([x, z], i) => <B key={i} p={[x * 0.5, 0.085, 0]} s={[0.12, 0.02, 3.0]} c="#facc15" shadow={false} />)}
            <B p={[0, 0.085, -1.5]} s={[3.8, 0.02, 0.12]} c="#facc15" shadow={false} />
            <B p={[0, 0.085, 1.5]} s={[3.8, 0.02, 0.12]} c="#facc15" shadow={false} />
            {[-0.9, 0, 0.9].map((z) => <B key={z} p={[0, 0.2, z]} s={[3.2, 0.1, 0.18]} c="#8b95a3" metal={0.7} />)}
            {[-1.4, 0, 1.4].map((x) => <B key={x} p={[x, 0.14, 0]} s={[0.18, 0.1, 2.0]} c="#8b95a3" metal={0.7} />)}
          </group>

          <Andon p={[-4.4, 0, -4.8]} state={() => "ok"} />
        </group>
      )}
    </AtStation>
  );
}
