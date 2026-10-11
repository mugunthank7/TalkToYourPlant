import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../clock";
import { useTwin } from "../state";
import { usePBR } from "./Env";

const WALL_H = 10;

function Wall({ length, position, rotY = 0, lowOnly = false }: { length: number; position: [number, number, number]; rotY?: number; lowOnly?: boolean }) {
  const lower = usePBR("concrete_wall_004", length / 6, 3 / 6);
  const upper = usePBR("corrugated_iron_03", length / 5, 7 / 5);
  const lowH = lowOnly ? 1.4 : 3;
  return (
    <group position={position} rotation={[0, rotY, 0]}>
      <mesh position={[0, lowH / 2, 0]} receiveShadow castShadow>
        <boxGeometry args={[length, lowH, 0.5]} />
        <meshStandardMaterial {...lower} color="#e5e7eb" />
      </mesh>
      {!lowOnly && (
        <>
          <mesh position={[0, 3 + (WALL_H - 3) / 2, 0]} receiveShadow>
            <boxGeometry args={[length, WALL_H - 3, 0.4]} />
            <meshStandardMaterial {...upper} color="#d6dde6" metalness={0.5} />
          </mesh>
          {/* clerestory window band */}
          <mesh position={[0, 7.2, 0.22]}>
            <boxGeometry args={[length - 2, 1.6, 0.05]} />
            <meshStandardMaterial color="#bfe0ff" emissive="#9fd0ff" emissiveIntensity={0.9} />
          </mesh>
        </>
      )}
      {lowOnly && (
        <mesh position={[0, lowH + 1.2, 0]}>
          <boxGeometry args={[length, 2.4, 0.06]} />
          <meshStandardMaterial color="#9ad0ff" transparent opacity={0.13} />
        </mesh>
      )}
    </group>
  );
}

function Columns({ w, d }: { w: number; d: number }) {
  const cols: [number, number][] = [];
  for (let x = -w / 2; x <= w / 2 + 0.1; x += 16) { cols.push([x, -d / 2]); cols.push([x, d / 2]); }
  for (let z = -d / 2 + 18; z < d / 2 - 1; z += 18) { cols.push([-w / 2, z]); cols.push([w / 2, z]); }
  return (
    <>
      {cols.map(([x, z], i) => (
        <group key={i} position={[x, 0, z]}>
          <mesh position={[0, WALL_H / 2, 0]} castShadow>
            <boxGeometry args={[0.9, WALL_H, 0.9]} />
            <meshStandardMaterial color="#cfd6df" roughness={0.7} />
          </mesh>
          <mesh position={[0, 0.5, 0]}>
            <boxGeometry args={[0.96, 1, 0.96]} />
            <meshStandardMaterial color="#facc15" roughness={0.6} />
          </mesh>
        </group>
      ))}
    </>
  );
}

/** Two crane runway beams and a bridge crane that slowly travels along the hall. */
function Crane({ w, d }: { w: number; d: number }) {
  const bridge = useRef<THREE.Group>(null!);
  const trolley = useRef<THREE.Group>(null!);
  const hook = useRef<THREE.Mesh>(null!);
  useFrame(() => {
    const t = clock.t;
    bridge.current.position.x = Math.sin(t / 55) * (w / 2 - 14);
    trolley.current.position.z = Math.sin(t / 31 + 1) * (d / 2 - 12);
    hook.current.scale.y = 1 + 0.3 * Math.sin(t / 9);
  });
  const H = 9;
  return (
    <group>
      {[-d / 2 + 1.5, d / 2 - 1.5].map((z) => (
        <mesh key={z} position={[0, H, z]} castShadow>
          <boxGeometry args={[w, 0.5, 0.5]} />
          <meshStandardMaterial color="#f59e0b" metalness={0.5} roughness={0.5} />
        </mesh>
      ))}
      <group ref={bridge} position={[0, H + 0.1, 0]}>
        <mesh castShadow>
          <boxGeometry args={[0.7, 0.6, d - 3]} />
          <meshStandardMaterial color="#facc15" metalness={0.4} roughness={0.5} />
        </mesh>
        <group ref={trolley}>
          <mesh position={[0, -0.6, 0]} castShadow>
            <boxGeometry args={[1.4, 0.7, 1.6]} />
            <meshStandardMaterial color="#1f2937" metalness={0.6} roughness={0.4} />
          </mesh>
          <mesh ref={hook} position={[0, -2.2, 0]}>
            <boxGeometry args={[0.06, 3, 0.06]} />
            <meshStandardMaterial color="#cbd5e1" metalness={0.9} roughness={0.3} />
          </mesh>
        </group>
      </group>
    </group>
  );
}

/** Pendant LED fixtures: purely visual (emissive), the real lighting comes from the HDRI and sun. */
function Fixtures({ w, d }: { w: number; d: number }) {
  const spots = useMemo(() => {
    const out: [number, number][] = [];
    for (let x = -w / 2 + 10; x < w / 2; x += 20) for (let z = -d / 2 + 10; z < d / 2; z += 20) out.push([x, z]);
    return out;
  }, [w, d]);
  return (
    <>
      {spots.map(([x, z], i) => (
        <mesh key={i} position={[x, 8.2, z]}>
          <boxGeometry args={[4, 0.12, 0.7]} />
          <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={2.2} toneMapped={false} />
        </mesh>
      ))}
    </>
  );
}

/** Overhead items only show in wide views; close-ups would be blocked by them. */
function Overhead({ children }: { children: React.ReactNode }) {
  const g = useRef<THREE.Group>(null!);
  const { camera } = useThree();
  useFrame(() => { g.current.visible = camera.position.y > 45; });
  return <group ref={g}>{children}</group>;
}

export function Building() {
  const { plant } = useTwin((s) => s.data)!.layout;
  const w = plant.width_m + 8;
  const d = plant.depth_m + 8;
  return (
    <>
      <Wall length={w} position={[0, 0, -d / 2]} />
      <Wall length={d} position={[-w / 2, 0, 0]} rotY={Math.PI / 2} />
      <Wall length={d} position={[w / 2, 0, 0]} rotY={Math.PI / 2} />
      <Wall length={w} position={[0, 0, d / 2]} lowOnly />
      <Columns w={w} d={d} />
      <Overhead>
        <Crane w={w} d={d} />
        <Fixtures w={w} d={d} />
      </Overhead>
    </>
  );
}
