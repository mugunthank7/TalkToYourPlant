import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../../clock";
import { animT } from "../../plant";
import { useTwin } from "../../state";
import { AtStation, B, Cyl, Hazard, Npc, Pad, RB, Screen } from "../kit";
import { WeldRobot } from "../Machines";
import type { Machine } from "../../data";
import { Model } from "../Props";

const BLUE = "#1d5fd0";
const STEEL = "#8e99a8";

function Press() {
  const ram = useRef<THREE.Group>(null!);
  const bar = useRef<THREE.MeshStandardMaterial>(null!);
  useFrame(() => {
    const st = useTwin.getState();
    const ta = animT("S02", clock.t, st.shift, st.data!.hero);
    const cyc = (ta % 6) / 6; // 6 s stroke cycle, down fast, up slow
    const down = cyc < 0.25 ? cyc / 0.25 : cyc < 0.35 ? 1 : 1 - (cyc - 0.35) / 0.65;
    ram.current.position.y = 4.2 - Math.max(0, down) * 2.2;
    bar.current.emissive.setHSL((clock.t * 0.05) % 1, 0.9, 0.5);
  });
  return (
    <group>
      {/* side frames */}
      {[-2.6, 2.6].map((x) => (
        <group key={x}>
          <RB p={[x, 3.2, 0]} s={[1.0, 6.4, 3.8]} c={BLUE} metal={0.45} rough={0.4} r={0.08} />
          <B p={[x, 3.2, 1.93]} s={[0.7, 5.8, 0.04]} c="#174a9e" />
        </group>
      ))}
      <RB p={[0, 6.1, 0]} s={[6.2, 1.2, 3.8]} c={BLUE} metal={0.45} rough={0.4} r={0.1} />
      <RB p={[0, 0.55, 0]} s={[5.6, 1.1, 3.4]} c="#2b3a52" metal={0.6} rough={0.4} r={0.06} />
      <B p={[0, 1.15, 0]} s={[4.6, 0.12, 3.0]} c="#9aa5b4" metal={0.8} rough={0.3} />
      {/* ram */}
      <group ref={ram} position={[0, 4.2, 0]}>
        <RB p={[0, 0, 0]} s={[4.4, 1.3, 3.0]} c={STEEL} metal={0.7} rough={0.3} r={0.08} />
        <B p={[0, -0.7, 0]} s={[3.8, 0.12, 2.6]} c="#566173" metal={0.8} />
      </group>
      {/* light bar */}
      <mesh position={[0, 6.85, 1.95]}>
        <boxGeometry args={[5.2, 0.16, 0.06]} />
        <meshStandardMaterial ref={bar} color="#ffffff" emissive="#ff0000" emissiveIntensity={1.8} toneMapped={false} />
      </mesh>
      {/* control box on the column */}
      <B p={[3.25, 1.8, 1.0]} s={[0.12, 0.8, 0.5]} c="#334155" />
    </group>
  );
}

function RollerConveyor({ from, to }: { from: [number, number]; to: [number, number] }) {
  const len = Math.hypot(to[0] - from[0], to[1] - from[1]);
  const a = -Math.atan2(to[1] - from[1], to[0] - from[0]);
  const panels = useRef<THREE.Group[]>([]);
  useFrame(() => {
    panels.current.forEach((g, i) => {
      if (!g) return;
      const st = useTwin.getState();
      const u = (((animT("S02", clock.t, st.shift, st.data!.hero) * 0.35 + i * (len / 4)) % len) + len) % len;
      g.position.x = -len / 2 + u;
    });
  });
  return (
    <group position={[(from[0] + to[0]) / 2, 0, (from[1] + to[1]) / 2]} rotation={[0, a, 0]}>
      {[-0.7, 0.7].map((z) => <B key={z} p={[0, 0.65, z]} s={[len, 0.1, 0.08]} c={BLUE} metal={0.5} />)}
      {Array.from({ length: Math.floor(len / 0.25) }).map((_, i) => (
        <Cyl key={i} p={[-len / 2 + 0.15 + i * 0.25, 0.7, 0]} r={0.05} h={1.3} c="#cbd5e1" rot={[Math.PI / 2, 0, 0]} seg={10} />
      ))}
      {[-len / 2 + 0.3, 0, len / 2 - 0.3].map((x) => [-0.65, 0.65].map((z) => <B key={`${x}${z}`} p={[x, 0.3, z]} s={[0.08, 0.6, 0.08]} c={BLUE} />))}
      {Array.from({ length: 4 }).map((_, i) => (
        <group key={i} ref={(g) => { if (g) panels.current[i] = g; }}>
          <RB p={[0, 0.85, 0]} s={[0.9, 0.05, 0.7]} c="#aeb7c4" metal={0.8} rough={0.3} rot={[0.05, 0, 0.1]} />
        </group>
      ))}
    </group>
  );
}

function PartRack({ p }: { p: [number, number, number] }) {
  return (
    <group position={p}>
      {[[-1.0, -0.6], [1.0, -0.6], [-1.0, 0.6], [1.0, 0.6]].map(([x, z], i) => <B key={i} p={[x, 0.9, z]} s={[0.08, 1.8, 0.08]} c={BLUE} metal={0.5} />)}
      {[0.35, 0.8, 1.25, 1.7].map((y) => <B key={y} p={[0, y, 0]} s={[2.0, 0.05, 1.2]} c={BLUE} />)}
      {[0.4, 0.85, 1.3].map((y) => <B key={y} p={[0, y + 0.07, 0]} s={[1.7, 0.07, 0.9]} c="#b8c0cc" metal={0.8} rough={0.3} rot={[0, 0, 0.05]} />)}
    </group>
  );
}

export function S02() {
  return (
    <AtStation id="S02">
      {() => (
        <group>
          <Pad w={22} d={16} tone="#eef1f5" />
          {/* green painted aisle along the south and east edges, like the reference */}
          <mesh position={[0, 0.075, 7.2]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[21, 1.2]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[10.1, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1.2, 15]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          {/* press with hazard-stripe surround */}
          <group position={[-1.5, 0, -1.2]}>
            <Press />
          </group>
          <Hazard p={[-1.5, 0, -1.2]} s={[8.4, 0.9]} />
          <Hazard p={[-1.5, 0, 1.6]} s={[8.4, 0.9]} />
          <Hazard p={[-5.6, 0, 0.2]} s={[0.9, 2.2]} />
          <Hazard p={[2.6, 0, 0.2]} s={[0.9, 2.2]} />

          {/* transfer robot at the press exit (orange), reaching west into the press */}
          <group position={[4.4, 0, -1.0]} rotation={[0, Math.PI / 2, 0]}>
            <WeldRobot m={{ id: "M02", name: "Transfer robot", type: "robot", station: "S02", x: 0, z: 0, rot_deg: 0 } as Machine} hero={false} color="#f08a1d" />
          </group>

          {/* part conveyor to the racks */}
          <RollerConveyor from={[5.2, 1.4]} to={[9.0, 3.6]} />
          <PartRack p={[7.0, 0, -4.4]} />
          <PartRack p={[9.1, 0, -4.4]} />

          {/* die cart with a heavy die */}
          <group position={[5.6, 0, -6.0]}>
            <B p={[0, 0.3, 0]} s={[2.5, 0.3, 1.6]} c="#374151" metal={0.6} />
            <RB p={[0, 0.65, 0]} s={[2.1, 0.45, 1.3]} c="#58616e" metal={0.85} rough={0.35} />
            <B p={[0, 0.9, 0]} s={[1.9, 0.1, 1.1]} c="#7b8696" metal={0.9} />
            {[[-1.0, 0.6], [1.0, 0.6], [-1.0, -0.6], [1.0, -0.6]].map(([x, z], i) => <mesh key={i} position={[x, 0.12, z]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.12, 0.12, 0.1, 12]} /><meshStandardMaterial color="#111827" /></mesh>)}
          </group>
          <Npc p={[3.9, 0, -6.4]} rotY={1.5} color="#ef4444" pose="work" seed={2} />
          <Npc p={[7.6, 0, -6.4]} rotY={-1.5} color="#ef4444" pose="stand" seed={6} />

          {/* hydraulic power unit behind a yellow guard fence */}
          <group position={[-8.6, 0, -4.6]}>
            <RB p={[0, 0.8, 0]} s={[2.4, 1.6, 1.6]} c="#1d4ed8" metal={0.5} />
            <Cyl p={[-0.5, 1.9, 0]} r={0.35} h={0.7} c="#94a3b8" metal={0.8} />
            <Cyl p={[0.6, 1.9, 0]} r={0.3} h={0.5} c="#1f2937" />
            <Cyl p={[1.4, 1.4, 1.0]} r={0.06} h={4.2} c="#94a3b8" rot={[0, 0, Math.PI / 2]} />
            <Cyl p={[3.0, 1.4, 1.5]} r={0.06} h={3.0} c="#94a3b8" rot={[Math.PI / 2, 0, 0]} />
            {[[-1.8, -1.3], [1.8, -1.3], [-1.8, 1.3], [1.8, 1.3]].map(([x, z], i) => <B key={i} p={[x, 0.55, z]} s={[0.08, 1.1, 0.08]} c="#facc15" />)}
            <B p={[0, 1.0, 1.3]} s={[3.6, 0.07, 0.07]} c="#facc15" />
            <B p={[0, 1.0, -1.3]} s={[3.6, 0.07, 0.07]} c="#facc15" />
            <B p={[-1.8, 1.0, 0]} s={[0.07, 0.07, 2.6]} c="#facc15" />
          </group>

          {/* operator HMI console */}
          <group position={[-4.3, 0, 5.2]}>
            <B p={[0, 0.5, 0]} s={[0.12, 1.0, 0.12]} c="#475569" />
            <RB p={[0, 1.15, 0]} s={[0.8, 0.55, 0.08]} c="#1d5fd0" r={0.03} rot={[-0.2, 0, 0]} />
            <Screen p={[0, 1.15, 0.045]} s={[0.7, 0.45]} rot={[-0.2, 0, 0]} draw={(ctx, w, h) => {
              ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
              ctx.fillStyle = "#38bdf8"; ctx.font = "700 26px sans-serif"; ctx.fillText("PRESS 1  AUTO", 14, 38);
              ctx.fillStyle = "#e2e8f0"; ctx.font = "22px sans-serif"; ctx.fillText(`strokes ${Math.floor(clock.t / 6)}`, 14, 82);
              ctx.fillStyle = "#22c55e"; ctx.fillText("tonnage 2410 t", 14, 118);
            }} />
          </group>
          <Npc p={[-4.3, 0, 6.2]} rotY={Math.PI} color="#ef4444" pose="stand" seed={1} />
          {/* oil drip tray */}
          <B p={[-6.4, 0.08, 4.2]} s={[2.1, 0.06, 1.2]} c="#1f2937" rough={0.9} metal={0.1} shadow={false} />
          <Model name="barrel_03" position={[-9.6, 0, 3.4]} />
        </group>
      )}
    </AtStation>
  );
}
