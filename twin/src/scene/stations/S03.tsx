import { AtStation, B, Cyl, Npc, Pad, Screen, TextBoard } from "../kit";
import { Model } from "../Props";

const BLUE = "#1d5fd0";
const ORANGE = "#f08a1d";

function Rack3({ p, len = 8, seed = 0 }: { p: [number, number, number]; len?: number; seed?: number }) {
  const bays = Math.round(len / 2.7);
  return (
    <group position={p}>
      {Array.from({ length: bays + 1 }).map((_, i) => [-0.55, 0.55].map((z) => <B key={`${i}${z}`} p={[-len / 2 + (i * len) / bays, 2.2, z]} s={[0.1, 4.4, 0.1]} c={BLUE} metal={0.5} />))}
      {[0.8, 2.2, 3.6].map((y) => [-0.5, 0.5].map((z) => <B key={`${y}${z}`} p={[0, y, z]} s={[len, 0.14, 0.08]} c={ORANGE} metal={0.4} />))}
      {Array.from({ length: bays }).flatMap((_, b) =>
        [0.88, 2.28, 3.68].map((y, l) => {
          const x = -len / 2 + ((b + 0.5) * len) / bays;
          const kind = (b + l + seed) % 3;
          return (
            <group key={`${b}${l}`} position={[x, y, 0]}>
              <B p={[0, 0.07, 0]} s={[2.3, 0.14, 1.0]} c="#a16207" rough={0.9} metal={0} />
              {kind === 0 && [-0.55, 0.55].map((dx) => [-0.25, 0.25].map((dz) => <Model key={`${dx}${dz}`} name="cardboard_box_01" position={[dx, 0.14, dz]} lift={0.18} rotY={(b + l) % 2 * 1.57} />))}
              {kind === 1 && [0, 1, 2, 3].map((k) => <B key={k} p={[-0.8 + k * 0.5, 0.45, 0]} s={[0.1, 0.62, 0.8]} c="#aeb7c4" metal={0.8} rough={0.3} rot={[0, 0, 0.2]} />)}
              {kind === 2 && <B p={[0, 0.4, 0]} s={[1.8, 0.5, 0.8]} c="#d6c7a1" rough={0.9} metal={0} />}
            </group>
          );
        }),
      )}
    </group>
  );
}

function RackCarrier({ p, rotY = 0 }: { p: [number, number, number]; rotY?: number }) {
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      {[[-0.7, -0.5], [0.7, -0.5], [-0.7, 0.5], [0.7, 0.5]].map(([x, z], i) => <B key={i} p={[x, 0.55, z]} s={[0.07, 1.1, 0.07]} c={BLUE} />)}
      <B p={[0, 0.12, 0]} s={[1.5, 0.1, 1.1]} c={BLUE} />
      {[0, 1, 2, 3, 4].map((k) => <B key={k} p={[-0.55 + k * 0.28, 0.6, 0]} s={[0.08, 0.9, 0.85]} c="#aeb7c4" metal={0.85} rough={0.3} rot={[0, 0, 0.12]} />)}
    </group>
  );
}

function Forklift({ p, rotY }: { p: [number, number, number]; rotY: number }) {
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <B p={[0, 0.55, -0.5]} s={[1.2, 0.8, 1.9]} c="#facc15" metal={0.4} rough={0.4} />
      <B p={[0, 0.3, 0.6]} s={[1.2, 0.5, 0.5]} c="#1f2937" />
      <B p={[0, 1.6, -0.5]} s={[1.05, 0.06, 1.0]} c="#1f2937" />
      {[[-0.5, -1.0], [0.5, -1.0], [-0.5, 0.0], [0.5, 0.0]].map(([x, z], i) => <B key={i} p={[x, 1.1, z + 0.0]} s={[0.05, 1.1, 0.05]} c="#1f2937" />)}
      {[-0.45, 0.45].map((x) => <B key={x} p={[x, 1.2, 0.95]} s={[0.1, 2.4, 0.08]} c="#334155" metal={0.7} />)}
      {[-0.4, 0.4].map((x) => <B key={x} p={[x, 0.35, 1.7]} s={[0.12, 0.07, 1.4]} c="#334155" metal={0.7} />)}
      {[[-0.6, -0.9], [0.6, -0.9], [-0.6, 0.7], [0.6, 0.7]].map(([x, z], i) => <mesh key={i} position={[x, 0.3, z]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.3, 0.3, 0.22, 16]} /><meshStandardMaterial color="#111827" /></mesh>)}
      {/* a pallet on the forks */}
      <B p={[0, 0.5, 1.8]} s={[1.0, 0.12, 1.2]} c="#a16207" rough={0.9} metal={0} />
      {[-0.28, 0.28].map((x) => <Model key={x} name="cardboard_box_01" position={[x, 0.56, 1.8]} lift={0.18} />)}
    </group>
  );
}

export function S03() {
  return (
    <AtStation id="S03">
      {() => (
        <group>
          <Pad w={14} d={12} tone="#eef1f5" />
          <mesh position={[-6.5, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.9, 11]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          {/* two rows of pallet racking, north side */}
          <Rack3 p={[0.6, 0, -4.8]} len={8} seed={0} />
          <Rack3 p={[0.6, 0, -2.4]} len={8} seed={1} />

          {/* floor buffer bays with pallets */}
          {[[-5.0, 1.6], [-3.4, 1.6], [-5.0, 3.4], [-3.4, 3.4], [-5.0, 5.0], [-3.4, 5.0]].map(([x, z], i) => (
            <group key={i} position={[x, 0, z]}>
              <B p={[0, 0.08, 0]} s={[1.3, 0.14, 1.1]} c="#a16207" rough={0.9} metal={0} />
              {[0, 1, 2].map((k) => <Model key={k} name="cardboard_box_01" position={[-0.3, 0.14 + k * 0.34, 0]} lift={0.18} rotY={k * 0.4} />)}
              {[0, 1, 2].map((k) => <Model key={`b${k}`} name="cardboard_box_01" position={[0.3, 0.14 + k * 0.34, 0]} lift={0.18} rotY={-k * 0.3} />)}
            </group>
          ))}
          <TextBoard p={[-4.2, 0.09, 0.2]} s={[3.2, 0.5]} rot={[-Math.PI / 2, 0, 0]} text="FLOOR BUFFER" bg="#e5e7eb" fg="#475569" />

          {/* blue rack carriers full of stamped panels */}
          <RackCarrier p={[0.8, 0, 3.4]} rotY={0.1} />
          <RackCarrier p={[2.4, 0, 3.4]} rotY={-0.05} />
          <RackCarrier p={[0.8, 0, 5.0]} rotY={0.05} />
          <RackCarrier p={[2.4, 0, 5.0]} rotY={0.12} />

          {/* forklift + driver, hand pallet jack */}
          <Forklift p={[3.3, 0, -0.2]} rotY={-0.5} />
          <Npc p={[3.3, 0.55, -0.7]} rotY={-0.5} color="#f97316" pose="sit" seed={3} />
          <group position={[5.4, 0, 2.6]} rotation={[0, 0.8, 0]}>
            <B p={[0, 0.1, 0]} s={[0.5, 0.1, 1.2]} c="#c81e1e" />
            <B p={[0, 0.6, -0.65]} s={[0.04, 1.0, 0.04]} c="#c81e1e" rot={[0.5, 0, 0]} />
          </group>

          {/* kanban board + scanner post, logistics operator */}
          <group position={[-5.8, 0, -1.4]}>
            <B p={[-0.5, 0.6, 0]} s={[0.06, 1.2, 0.06]} c="#64748b" />
            <B p={[0.5, 0.6, 0]} s={[0.06, 1.2, 0.06]} c="#64748b" />
            <B p={[0, 1.3, 0]} s={[1.3, 0.9, 0.06]} c="#e5e7eb" />
            {[0, 1, 2].map((r) => [0, 1, 2, 3].map((c) => <B key={`${r}${c}`} p={[-0.45 + c * 0.3, 1.58 - r * 0.28, 0.04]} s={[0.24, 0.2, 0.02]} c={(r + c) % 3 === 0 ? "#22c55e" : (r + c) % 3 === 1 ? "#facc15" : "#38bdf8"} />))}
            <B p={[1.0, 0.6, 0.3]} s={[0.1, 1.2, 0.1]} c="#475569" />
            <Screen p={[1.0, 1.1, 0.36]} s={[0.4, 0.28]} draw={(ctx, w, h) => { ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h); ctx.fillStyle = "#22c55e"; ctx.font = "700 40px sans-serif"; ctx.fillText("SCAN OK", 20, h / 2 + 12); }} />
          </group>
          <Npc p={[-4.9, 0, -0.8]} rotY={-1.9} color="#f97316" pose="stand" seed={4} />

          {/* barrels, bollards, wheel stops */}
          <Model name="barrel_03" position={[5.8, 0, -3.6]} />
          <Model name="barrel_03" position={[5.2, 0, -4.1]} />
          {[-5.5, 0, 5.5].map((x) => <Cyl key={x} p={[x, 0.55, 5.6]} r={0.12} h={1.1} c="#facc15" metal={0.2} />)}
          {[-2.6, -0.2, 2.2, 4.6].map((x) => <B key={x} p={[x, 0.09, 4.4]} s={[1.4, 0.16, 0.2]} c="#111827" metal={0.1} />)}
        </group>
      )}
    </AtStation>
  );
}
