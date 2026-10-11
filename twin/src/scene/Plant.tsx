import { Line } from "@react-three/drei";
import { Label } from "./Label";
import { toScene } from "../data";
import { ConcreteFloor } from "./Env";
import { useTwin } from "../state";
import { DETAILED_IDS } from "./stations";

const PAD: Record<string, string> = {
  S01: "#cbd5e1", S02: "#cbd5e1", S03: "#e2e8f0", S04: "#bfdbfe", S05: "#bfdbfe", S06: "#bfdbfe",
  S07: "#bfdbfe", S08: "#d9f99d", S09: "#d9f99d", S10: "#fde68a", S11: "#e9d5ff", S12: "#fde68a",
};

export function Floor() {
  const { plant } = useTwin((s) => s.data)!.layout;
  const hw = plant.width_m / 2 + 3.4;
  const hd = plant.depth_m / 2 + 3.4;
  return (
    <>
      <ConcreteFloor />
      {/* painted safety border just inside the walls */}
      {[
        [0, -hd, plant.width_m + 6.8, 0.3], [0, hd, plant.width_m + 6.8, 0.3],
        [-hw, 0, 0.3, plant.depth_m + 6.8], [hw, 0, 0.3, plant.depth_m + 6.8],
      ].map(([x, z, w, d], i) => (
        <mesh key={i} position={[x, 0.02, z]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[w, d]} />
          <meshStandardMaterial color="#facc15" roughness={0.6} />
        </mesh>
      ))}
    </>
  );
}

export function Stations() {
  const layout = useTwin((s) => s.data)!.layout;
  const selected = useTwin((s) => s.selectedStation);
  const select = useTwin((s) => s.setSelectedStation);
  return (
    <>
      {layout.stations.map((s) => {
        const [x, z] = toScene(s.x, s.z);
        const withBuilding = false;
        const detailed = DETAILED_IDS.has(s.id);
        const on = selected === s.id;
        const hw = s.w / 2, hd = s.d / 2;
        return (
          <group key={s.id} position={[x, 0, z]}
            onClick={(e) => { e.stopPropagation(); select(on ? null : s.id); }}
            onPointerOver={() => { document.body.style.cursor = "pointer"; }}
            onPointerOut={() => { document.body.style.cursor = ""; }}>
            {/* click target covering the whole station footprint */}
            <mesh position={[0, 1.2, 0]}>
              <boxGeometry args={[s.w, 2.4, s.d]} />
              <meshBasicMaterial transparent opacity={0} depthWrite={false} />
            </mesh>
            {on && (
              <Line points={[[-hw, 0.14, -hd], [hw, 0.14, -hd], [hw, 0.14, hd], [-hw, 0.14, hd], [-hw, 0.14, -hd]]}
                color="#22d3ee" lineWidth={4} />
            )}
            {!detailed && (
              <mesh position={[0, 0.06, 0]} receiveShadow>
                <boxGeometry args={[s.w, 0.12, s.d]} />
                <meshStandardMaterial color={PAD[s.id] ?? "#cbd5e1"} roughness={0.9} />
              </mesh>
            )}
            <Label text={`${s.id}  ${s.name}`} position={[0, detailed ? 4.4 : 1.2, s.d / 2 + 0.5]} height={1.5} />
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
        const rot: [number, number, number] = [-Math.PI / 2, 0, -Math.atan2(bz - az, bx - ax)];
        const mid: [number, number, number] = [(ax + bx) / 2, 0.025, (az + bz) / 2];
        const edge = (off: number) => {
          const nx = -(bz - az) / len;
          const nz = (bx - ax) / len;
          return (
            <mesh key={off} position={[mid[0] + nx * off, 0.03, mid[2] + nz * off]} rotation={rot}>
              <planeGeometry args={[len, 0.12]} />
              <meshStandardMaterial color="#facc15" roughness={0.5} />
            </mesh>
          );
        };
        return (
          <group key={a + b}>
            <mesh position={mid} rotation={rot}>
              <planeGeometry args={[len, 1.5]} />
              <meshStandardMaterial color="#22c55e" roughness={0.6} transparent opacity={0.38} />
            </mesh>
            {edge(0.75)}
            {edge(-0.75)}
          </group>
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
