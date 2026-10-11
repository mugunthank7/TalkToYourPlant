import { useRef, type ReactElement } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../clock";
import { m05Status, toScene } from "../data";
import { useTwin } from "../state";

/** Andon light stack: green / amber / red, one lit at a time. */
export function Andon({ position, state }: { position: [number, number, number]; state: () => "ok" | "warn" | "bad" }) {
  const mats = useRef<THREE.MeshStandardMaterial[]>([]);
  useFrame(() => {
    const s = state();
    const on = s === "bad" ? 0 : s === "warn" ? 1 : 2; // red, amber, green indices
    const pulse = s === "bad" ? 0.6 + 0.4 * Math.sin(performance.now() / 160) : 1;
    mats.current.forEach((m, i) => {
      if (m) m.emissiveIntensity = i === on ? 2.2 * pulse : 0.05;
    });
  });
  const cols = ["#ef4444", "#f59e0b", "#22c55e"];
  return (
    <group position={position}>
      <mesh position={[0, 1.4, 0]} castShadow>
        <cylinderGeometry args={[0.06, 0.06, 2.8, 8]} />
        <meshStandardMaterial color="#334155" />
      </mesh>
      {cols.map((c, i) => (
        <mesh key={c} position={[0, 2.95 + i * 0.32, 0]}>
          <cylinderGeometry args={[0.2, 0.2, 0.28, 16]} />
          <meshStandardMaterial ref={(m) => { if (m) mats.current[i] = m; }} color={c} emissive={c} emissiveIntensity={0.05} />
        </mesh>
      ))}
    </group>
  );
}

function Fence({ w, d, gapSouth = 3, gapSides = 4.2 }: { w: number; d: number; gapSouth?: number; gapSides?: number }) {
  const h = 2;
  const post = (x: number, z: number, k = "") => (
    <mesh key={`${k}${x},${z}`} position={[x, h / 2, z]} castShadow>
      <boxGeometry args={[0.12, h, 0.12]} />
      <meshStandardMaterial color="#facc15" metalness={0.2} roughness={0.5} />
    </mesh>
  );
  const panel = (x0: number, x1: number, z: number, key: string) => (
    <group key={key}>
      <mesh position={[(x0 + x1) / 2, h / 2 + 0.1, z]}>
        <boxGeometry args={[Math.abs(x1 - x0), h - 0.3, 0.03]} />
        <meshStandardMaterial color="#38bdf8" transparent opacity={0.16} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[(x0 + x1) / 2, h - 0.02, z]}>
        <boxGeometry args={[Math.abs(x1 - x0), 0.08, 0.1]} />
        <meshStandardMaterial color="#facc15" />
      </mesh>
      <mesh position={[(x0 + x1) / 2, 0.25, z]}>
        <boxGeometry args={[Math.abs(x1 - x0), 0.08, 0.1]} />
        <meshStandardMaterial color="#facc15" />
      </mesh>
    </group>
  );
  const hw = w / 2;
  const hd = d / 2;
  const posts: ReactElement[] = [];
  for (let x = -hw; x <= hw + 0.01; x += 3) posts.push(post(x, -hd, "n"), post(x, hd, "s"));
  for (let z = -hd + 3; z < hd; z += 3) {
    if (Math.abs(z) > gapSides / 2) { posts.push(post(-hw, z, "w"), post(hw, z, "e")); }
  }
  return (
    <>
      {posts}
      {panel(-hw, hw, -hd, "n")}
      {panel(-hw, -gapSouth / 2, hd, "sa")}
      {panel(gapSouth / 2, hw, hd, "sb")}
      {/* east/west sides are open where the conveyor passes; panels beside the opening */}
      {[-hw, hw].map((x) => (
        <group key={x}>
          <mesh position={[x, h / 2 + 0.1, -(gapSides / 2 + (hd - gapSides / 2) / 2)]}>
            <boxGeometry args={[0.03, h - 0.3, hd - gapSides / 2]} />
            <meshStandardMaterial color="#38bdf8" transparent opacity={0.16} side={THREE.DoubleSide} />
          </mesh>
          <mesh position={[x, h / 2 + 0.1, gapSides / 2 + (hd - gapSides / 2) / 2]}>
            <boxGeometry args={[0.03, h - 0.3, hd - gapSides / 2]} />
            <meshStandardMaterial color="#38bdf8" transparent opacity={0.16} side={THREE.DoubleSide} />
          </mesh>
        </group>
      ))}
    </>
  );
}

export function Cells() {
  const data = useTwin((s) => s.data)!;
  const shift = useTwin((s) => s.shift);
  const ctrl = toScene(60, 71);
  return (
    <>
      {data.layout.safety_zones.map((z) => {
        const [x, zz] = toScene(z.x, z.z);
        const isHero = z.station === "S06";
        return (
          <group key={z.station} position={[x, 0, zz]}>
            <Fence w={z.w - 1} d={z.d - 3} />
            <Andon
              position={[z.w / 2 - 1, 0, -(z.d - 3) / 2]}
              state={() => {
                if (!isHero) return "ok";
                const st = m05Status(clock.t, shift, data.hero);
                return st === "alert" ? "bad" : st === "repair" ? "warn" : "ok";
              }}
            />
          </group>
        );
      })}
      {/* andon at the control room */}
      <Andon position={[ctrl[0], 0, ctrl[1]]} state={() => "ok"} />
    </>
  );
}
