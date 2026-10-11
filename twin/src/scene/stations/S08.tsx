import { useLayoutEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../../clock";
import { Andon, AtStation, B, Cyl, GlassWall, Npc, Pad, RB, Screen, TextBoard } from "../kit";
import { WeldRobot } from "../Machines";
import type { Machine } from "../../data";
import { Model } from "../Props";

const BLUE = "#1d5fd0";
const COPPER = "#c9772e";

/** Grid of cylindrical battery cells, one InstancedMesh for the whole grid. */
function CellGrid({ p, cols, rows, gap = 0.17, r = 0.07, h = 0.3, capColors = ["#ef4444", "#3b82f6"] }:
  { p: [number, number, number]; cols: number; rows: number; gap?: number; r?: number; h?: number; capColors?: string[] }) {
  const body = useRef<THREE.InstancedMesh>(null!);
  const cap = useRef<THREE.InstancedMesh>(null!);
  useLayoutEffect(() => {
    const m = new THREE.Matrix4();
    const c = new THREE.Color();
    let i = 0;
    for (let a = 0; a < cols; a++)
      for (let b = 0; b < rows; b++) {
        const x = (a - (cols - 1) / 2) * gap;
        const z = (b - (rows - 1) / 2) * gap;
        m.setPosition(x, 0, z); body.current.setMatrixAt(i, m);
        m.setPosition(x, h / 2 + 0.01, z); cap.current.setMatrixAt(i, m);
        cap.current.setColorAt(i, c.set(capColors[(a + b) % capColors.length]));
        i++;
      }
    body.current.instanceMatrix.needsUpdate = true;
    cap.current.instanceMatrix.needsUpdate = true;
    if (cap.current.instanceColor) cap.current.instanceColor.needsUpdate = true;
  }, [cols, rows, gap, h, capColors]);
  return (
    <group position={p}>
      <instancedMesh ref={body} args={[undefined, undefined, cols * rows]} castShadow>
        <cylinderGeometry args={[r, r, h, 12]} />
        <meshStandardMaterial color="#c3cbd6" metalness={0.9} roughness={0.28} />
      </instancedMesh>
      <instancedMesh ref={cap} args={[undefined, undefined, cols * rows]}>
        <cylinderGeometry args={[r * 0.82, r * 0.82, 0.03, 12]} />
        <meshStandardMaterial color="#ffffff" metalness={0.3} roughness={0.5} />
      </instancedMesh>
    </group>
  );
}

function Rail({ x0, z0, x1, z1 }: { x0: number; z0: number; x1: number; z1: number }) {
  const len = Math.hypot(x1 - x0, z1 - z0);
  const a = -Math.atan2(z1 - z0, x1 - x0);
  const n = Math.max(1, Math.round(len / 2.4));
  return (
    <group>
      <B p={[(x0 + x1) / 2, 1.0, (z0 + z1) / 2]} s={[len, 0.07, 0.07]} c="#facc15" rot={[0, a, 0]} />
      <B p={[(x0 + x1) / 2, 0.55, (z0 + z1) / 2]} s={[len, 0.07, 0.07]} c="#facc15" rot={[0, a, 0]} />
      {Array.from({ length: n + 1 }).map((_, k) => <B key={k} p={[x0 + ((x1 - x0) * k) / n, 0.5, z0 + ((z1 - z0) * k) / n]} s={[0.08, 1.0, 0.08]} c="#facc15" />)}
    </group>
  );
}

function RollerTable({ p }: { p: [number, number, number] }) {
  return (
    <group position={p}>
      <B p={[0, 0.75, 0]} s={[4.0, 0.08, 1.4]} c="#9aa7b5" metal={0.7} />
      {[-1.9, 1.9].flatMap((x) => [-0.6, 0.6].map((z) => <B key={`${x}${z}`} p={[x, 0.37, z]} s={[0.08, 0.75, 0.08]} c={BLUE} metal={0.5} />))}
      <B p={[0, 0.5, 0]} s={[3.9, 0.06, 1.3]} c={BLUE} />
      {Array.from({ length: 12 }).map((_, i) => <Cyl key={i} p={[-1.7 + i * 0.31, 0.82, 0]} r={0.04} h={1.3} c="#dbe1e8" rot={[Math.PI / 2, 0, 0]} seg={8} />)}
      <B p={[0, 0.88, 0]} s={[3.4, 0.05, 1.1]} c="#2f3743" />
      <CellGrid p={[-0.9, 1.04, 0]} cols={9} rows={6} />
      <CellGrid p={[1.0, 1.04, 0]} cols={9} rows={6} />
    </group>
  );
}

function Gantry() {
  const trolley = useRef<THREE.Group>(null!);
  const head = useRef<THREE.Group>(null!);
  useFrame(() => {
    const t = clock.t;
    trolley.current.position.z = Math.sin(t / 5) * 2.3 - 0.4;
    head.current.position.y = -1.2 - Math.max(0, Math.sin(t / 2.5)) * 0.9;
  });
  return (
    <group>
      {[-4.0, 3.4].map((z) => <RB key={z} p={[0, 1.9, z]} s={[0.5, 3.8, 0.5]} c={BLUE} metal={0.5} r={0.06} />)}
      <RB p={[0, 3.7, -0.3]} s={[0.55, 0.5, 8.2]} c={BLUE} metal={0.5} r={0.06} />
      <group ref={trolley} position={[0, 3.2, -0.4]}>
        <B p={[0, 0.2, 0]} s={[0.9, 0.5, 0.9]} c="#1f2937" metal={0.6} />
        <group ref={head} position={[0, -1.2, 0]}>
          <Cyl p={[0, 0.5, 0]} r={0.05} h={1.5} c="#94a3b8" />
          <B p={[0, 0, 0]} s={[0.9, 0.12, 0.6]} c="#334155" metal={0.7} />
          {[-0.3, 0.3].map((x) => <Cyl key={x} p={[x, -0.15, 0]} r={0.09} h={0.12} c="#111827" />)}
        </group>
      </group>
    </group>
  );
}

export function S08() {
  const volt = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    ctx.fillStyle = "#06121a"; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#38bdf8"; ctx.font = "700 24px sans-serif"; ctx.fillText("MODULE TEST  M-2210", 16, 34);
    for (let i = 0; i < 12; i++) {
      const v = 0.78 + Math.sin(clock.t * 0.8 + i) * 0.03;
      ctx.fillStyle = "#0f2b1d"; ctx.fillRect(18 + i * 40, 60, 28, h - 110);
      ctx.fillStyle = "#22c55e"; ctx.fillRect(18 + i * 40, 60 + (h - 110) * (1 - v), 28, (h - 110) * v);
    }
    ctx.fillStyle = "#86efac"; ctx.font = "18px monospace"; ctx.fillText("3.68 V avg   12/12 cells OK   PASS", 16, h - 24);
  };
  return (
    <AtStation id="S08">
      {() => (
        <group>
          <Pad w={16} d={11} tone="#3fae6a" />
          {/* ESD mats and floor border */}
          <B p={[4.2, 0.085, 0.2]} s={[4.6, 0.02, 2.4]} c="#1f6b3f" rough={0.9} metal={0} shadow={false} />
          <B p={[-1.2, 0.085, 0.4]} s={[5.0, 0.02, 4.4]} c="#1f6b3f" rough={0.9} metal={0} shadow={false} />

          {/* yellow rails: north, west, east */}
          <Rail x0={-7.6} z0={-5.1} x1={7.6} z1={-5.1} />
          <Rail x0={-7.6} z0={-5.1} x1={-7.6} z1={5.0} />
          <Rail x0={7.6} z0={-5.1} x1={7.6} z1={5.0} />
          <GlassWall p={[0, 0, 5.2]} len={15.2} axis="x" h={2.2} every={3.8} />

          {/* 1. cell infeed */}
          <RollerTable p={[-5.6, 0, -2.3]} />
          <RollerTable p={[-5.6, 0, 1.2]} />
          {/* 2. gantry pick and place */}
          <group position={[-2.9, 0, 0]}><Gantry /></group>
          {/* 3. stacking + busbar cell */}
          <group position={[-0.6, 0, -0.9]}>
            <B p={[0, 0.5, 0]} s={[3.5, 1.0, 2.0]} c="#c8cfd9" metal={0.7} rough={0.35} />
            <B p={[0, 1.02, 0]} s={[3.2, 0.05, 1.7]} c="#2f3743" />
            {[-0.9, 0.3].map((x) => (
              <group key={x} position={[x, 1.08, 0]}>
                <RB p={[0, 0.12, 0]} s={[1.0, 0.24, 1.3]} c="#aab4c0" metal={0.8} rough={0.3} />
                <CellGrid p={[0, 0.2, 0]} cols={5} rows={7} gap={0.18} r={0.065} h={0.22} />
                {[-0.3, 0, 0.3].map((z) => <B key={z} p={[0, 0.34, z]} s={[0.9, 0.012, 0.07]} c={COPPER} metal={0.9} rough={0.25} />)}
              </group>
            ))}
            {/* ionizer bars */}
            <B p={[0, 3.2, 0]} s={[3.0, 0.1, 0.18]} c="#e5e7eb" metal={0.4} />
            {[-1.2, 1.2].map((x) => <Cyl key={x} p={[x, 3.7, 0]} r={0.015} h={1.0} c="#94a3b8" />)}
            {[-1.0, -0.3, 0.4, 1.1].map((x) => <B key={x} p={[x, 3.08, 0]} s={[0.04, 0.14, 0.04]} c="#38bdf8" emissive="#38bdf8" ei={0.8} shadow={false} />)}
          </group>
          <group position={[-0.7, 0, 1.9]} rotation={[0, -2.2, 0]}>
            <group scale={0.62}>
              <WeldRobot m={{ id: "M08", name: "Busbar robot", type: "robot", station: "S08", x: 0, z: 0, rot_deg: 0 } as Machine} hero={false} color="#f08a1d" />
            </group>
          </group>

          {/* 4. laser welding cabinet */}
          <group position={[2.0, 0, -1.9]}>
            <RB p={[0, 1.1, 0]} s={[2.2, 2.2, 1.7]} c="#eef1f5" metal={0.2} rough={0.35} r={0.08} />
            <B p={[0.4, 1.4, 0.87]} s={[1.0, 0.7, 0.03]} c="#0f1a2e" />
            <B p={[0.4, 1.4, 0.89]} s={[0.9, 0.6, 0.01]} c="#86efac" emissive="#22c55e" ei={0.6} />
            <mesh position={[0.4, 1.3, 0.9]}><sphereGeometry args={[0.07, 10, 8]} /><meshBasicMaterial color="#7dff9a" toneMapped={false} /></mesh>
            <Cyl p={[-0.5, 2.7, 0]} r={0.2} h={1.2} c="#9aa7b5" metal={0.8} />
            <Cyl p={[-0.5, 3.2, -0.5]} r={0.2} h={1.2} c="#9aa7b5" metal={0.8} rot={[Math.PI / 2, 0, 0]} />
            <B p={[-0.8, 1.2, 0.87]} s={[0.4, 0.5, 0.03]} c="#1f2937" />
          </group>
          <Npc p={[1.4, 0, 0.1]} rotY={Math.PI} color="#e5e7eb" pose="stand" seed={3} />

          {/* 5. module test bench with two operators and a big screen */}
          <group position={[4.4, 0, -0.2]}>
            <RB p={[0, 0.9, 0]} s={[3.0, 0.08, 1.2]} c="#e2e8f0" metal={0.4} />
            <B p={[0, 0.45, 0]} s={[2.9, 0.8, 1.1]} c="#64748b" />
            <RB p={[0.3, 1.9, -0.45]} s={[2.0, 1.1, 0.06]} c="#0b0f19" />
            <Screen p={[0.3, 1.9, -0.41]} s={[1.9, 1.0]} draw={volt} />
            <B p={[0.3, 1.3, -0.45]} s={[0.1, 0.8, 0.08]} c="#475569" />
            <RB p={[-0.9, 1.0, 0.1]} s={[0.9, 0.2, 0.7]} c="#1f2937" metal={0.6} />
            <B p={[-0.9, 1.13, 0.1]} s={[0.8, 0.02, 0.1]} c="#22c55e" emissive="#22c55e" ei={0.7} />
            <B p={[1.2, 1.0, 0.2]} s={[0.12, 0.12, 0.18]} c="#111827" />
          </group>
          <Npc p={[3.7, 0, 0.7]} rotY={Math.PI} color="#e5e7eb" pose="work" seed={5} />
          <Npc p={[5.2, 0, 0.7]} rotY={Math.PI} color="#e5e7eb" pose="work" seed={6} />
          <Npc p={[-4.0, 0, 3.5]} rotY={-0.4} color="#e5e7eb" pose="stand" seed={9} />

          {/* 6. finished-module buffer rack and a module AGV */}
          <group position={[6.6, 0, -3.2]}>
            {[[-0.9, -0.6], [0.9, -0.6], [-0.9, 0.6], [0.9, 0.6]].map(([x, z], i) => <B key={i} p={[x, 1.1, z]} s={[0.08, 2.2, 0.08]} c={BLUE} metal={0.5} />)}
            {[0.6, 1.5].map((y) => <B key={y} p={[0, y, 0]} s={[2.0, 0.06, 1.3]} c={BLUE} />)}
            {[0.6, 1.5].map((y) => [-0.5, 0.5].map((x) => (
              <group key={`${y}${x}`} position={[x, y + 0.04, 0]}>
                <RB p={[0, 0.14, 0]} s={[0.8, 0.26, 1.0]} c="#1f2937" metal={0.6} />
                <B p={[0, 0.28, 0]} s={[0.7, 0.02, 0.12]} c="#22c55e" emissive="#22c55e" ei={0.8} />
              </group>
            )))}
          </group>
          <group position={[6.6, 0, 2.7]}>
            <RB p={[0, 0.16, 0]} s={[1.5, 0.3, 2.3]} c="#facc15" metal={0.4} />
            {[-0.45, 0.45].map((z) => [0].map((x) => (
              <group key={z} position={[x, 0.32, z * 1.1]}>
                <RB p={[0, 0.14, 0]} s={[1.2, 0.26, 0.9]} c="#1f2937" metal={0.6} />
                <B p={[0, 0.28, 0]} s={[1.0, 0.02, 0.1]} c="#22c55e" emissive="#22c55e" ei={0.8} />
              </group>
            )))}
          </group>

          {/* safety kit */}
          <Andon p={[7.3, 0, -4.7]} state={() => "ok"} />
          <Andon p={[-7.3, 0, 5.4]} state={() => "ok"} />
          <TextBoard p={[-7.55, 1.7, 3.2]} s={[1.5, 0.8]} rot={[0, Math.PI / 2, 0]} text="HIGH VOLTAGE" sub="BATTERY AREA" bg="#facc15" fg="#111827" />
          <TextBoard p={[7.55, 1.7, -2.0]} s={[1.5, 0.8]} rot={[0, -Math.PI / 2, 0]} text="HIGH VOLTAGE" sub="BATTERY AREA" bg="#facc15" fg="#111827" />
          <Model name="korean_fire_extinguisher_01" position={[7.2, 0, 4.3]} rotY={2.5} />
          <Cyl p={[6.5, 0.22, 4.4]} r={0.28} h={0.44} c="#dc2626" metal={0.3} rb={0.24} />
          <Model name="korean_fire_extinguisher_01" position={[-7.2, 0, 4.6]} rotY={0.5} />
          {/* empty tray trolley */}
          <group position={[-3.6, 0, 4.2]}>
            <B p={[0, 0.35, 0]} s={[0.9, 0.04, 0.6]} c="#cbd5e1" metal={0.7} />
            <B p={[0, 0.75, 0]} s={[0.9, 0.04, 0.6]} c="#cbd5e1" metal={0.7} />
            {[[-0.4, -0.25], [0.4, -0.25], [-0.4, 0.25], [0.4, 0.25]].map(([x, z], i) => <B key={i} p={[x, 0.45, z]} s={[0.03, 0.9, 0.03]} c="#94a3b8" />)}
            <B p={[0, 0.8, 0]} s={[0.7, 0.05, 0.45]} c="#2f3743" />
          </group>
        </group>
      )}
    </AtStation>
  );
}
