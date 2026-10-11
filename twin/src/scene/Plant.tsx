import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { Label } from "./Label";
import * as THREE from "three";
import { clock } from "../clock";
import { toScene } from "../data";
import { useTwin } from "../state";

const PAD: Record<string, string> = {
  S01: "#cbd5e1", S02: "#cbd5e1", S03: "#e2e8f0", S04: "#bfdbfe", S05: "#bfdbfe", S06: "#bfdbfe",
  S07: "#bfdbfe", S08: "#d9f99d", S09: "#d9f99d", S10: "#fde68a", S11: "#e9d5ff", S12: "#fde68a",
};

export function Floor() {
  const { plant } = useTwin((s) => s.data)!.layout;
  return (
    <>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[plant.width_m, plant.depth_m]} />
        <meshStandardMaterial color="#9ca3af" roughness={0.95} />
      </mesh>
      {/* perimeter wall */}
      {[
        { p: [0, 2, -plant.depth_m / 2], s: [plant.width_m, 4, 0.4] },
        { p: [0, 2, plant.depth_m / 2], s: [plant.width_m, 4, 0.4] },
        { p: [-plant.width_m / 2, 2, 0], s: [0.4, 4, plant.depth_m] },
        { p: [plant.width_m / 2, 2, 0], s: [0.4, 4, plant.depth_m] },
      ].map((w, i) => (
        <mesh key={i} position={w.p as [number, number, number]} receiveShadow>
          <boxGeometry args={w.s as [number, number, number]} />
          <meshStandardMaterial color="#d1d5db" transparent opacity={0.28} />
        </mesh>
      ))}
    </>
  );
}

export function Stations() {
  const layout = useTwin((s) => s.data)!.layout;
  return (
    <>
      {layout.stations.map((s) => {
        const [x, z] = toScene(s.x, s.z);
        const withBuilding = ["S10", "S11", "S12"].includes(s.id);
        return (
          <group key={s.id} position={[x, 0, z]}>
            <mesh position={[0, 0.06, 0]} receiveShadow>
              <boxGeometry args={[s.w, 0.12, s.d]} />
              <meshStandardMaterial color={PAD[s.id] ?? "#cbd5e1"} roughness={0.9} />
            </mesh>
            {withBuilding && (
              <mesh position={[0, 1.4, 0]} castShadow>
                <boxGeometry args={[s.w * 0.9, 2.8, s.d * 0.9]} />
                <meshStandardMaterial color={PAD[s.id]} transparent opacity={0.55} />
              </mesh>
            )}
            <Label text={`${s.id}  ${s.name}`} position={[0, withBuilding ? 4.2 : 1.2, s.d / 2 + 0.5]} height={1.5} />
          </group>
        );
      })}
    </>
  );
}

export function Walkways() {
  const { walk_graph } = useTwin((s) => s.data)!.layout;
  const pos = new Map(walk_graph.nodes.map((n) => [n.id, toScene(n.x, n.z)] as const));
  return (
    <>
      {walk_graph.edges.map(([a, b]) => {
        const [ax, az] = pos.get(a)!;
        const [bx, bz] = pos.get(b)!;
        const len = Math.hypot(bx - ax, bz - az);
        return (
          <mesh key={a + b} position={[(ax + bx) / 2, 0.025, (az + bz) / 2]} rotation={[-Math.PI / 2, 0, -Math.atan2(bz - az, bx - ax)]}>
            <planeGeometry args={[len, 1.2]} />
            <meshStandardMaterial color="#facc15" roughness={0.9} transparent opacity={0.55} />
          </mesh>
        );
      })}
    </>
  );
}

export function SafetyZones() {
  const { safety_zones } = useTwin((s) => s.data)!.layout;
  return (
    <>
      {safety_zones.map((z) => {
        const [x, zz] = toScene(z.x, z.z);
        const hw = z.w / 2;
        const hd = z.d / 2;
        const pts: [number, number, number][] = [
          [x - hw, 0.08, zz - hd], [x + hw, 0.08, zz - hd], [x + hw, 0.08, zz + hd], [x - hw, 0.08, zz + hd], [x - hw, 0.08, zz - hd],
        ];
        return <Line key={z.station} points={pts} color="#ef4444" lineWidth={2} dashed dashSize={1} gapSize={0.6} />;
      })}
    </>
  );
}

export function Conveyor() {
  const { conveyor_path, } = useTwin((s) => s.data)!.layout;
  const [x0, z0] = toScene(conveyor_path[0][0], conveyor_path[0][1]);
  const [x1] = toScene(conveyor_path[1][0], conveyor_path[1][1]);
  const len = x1 - x0;
  const cars = useRef<THREE.Group[]>([]);
  const SPEED = 0.25;
  const SPACING = 22.5;
  const N = Math.ceil(len / SPACING) + 1;

  useFrame(() => {
    cars.current.forEach((c, i) => {
      if (!c) return;
      const d = (clock.t * SPEED + i * SPACING) % (N * SPACING);
      c.position.x = x0 + d;
      c.visible = d < len;
    });
  });

  return (
    <group position={[0, 0, z0]}>
      <mesh position={[x0 + len / 2, 0.35, 0]} receiveShadow castShadow>
        <boxGeometry args={[len, 0.5, 2.6]} />
        <meshStandardMaterial color="#475569" roughness={0.6} metalness={0.4} />
      </mesh>
      <mesh position={[x0 + len / 2, 0.62, 0]}>
        <boxGeometry args={[len, 0.04, 2.0]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      {Array.from({ length: N }).map((_, i) => (
        <group key={i} ref={(g) => { if (g) cars.current[i] = g; }}>
          <mesh position={[0, 1.15, 0]} castShadow>
            <boxGeometry args={[4.6, 1.1, 1.9]} />
            <meshStandardMaterial color="#9ca3af" metalness={0.5} roughness={0.45} />
          </mesh>
          <mesh position={[-0.2, 1.9, 0]} castShadow>
            <boxGeometry args={[2.4, 0.6, 1.7]} />
            <meshStandardMaterial color="#94a3b8" metalness={0.5} roughness={0.45} />
          </mesh>
        </group>
      ))}
    </group>
  );
}
