import { andonFor, andonPlant } from "../../plant";
import { AtStation, Andon, B, CellFence, Cyl, Npc, Pad, RB, Screen } from "../kit";
import { Robot } from "./common";

const BLUE = "#1d5fd0";

function Portal({ x }: { x: number }) {
  return (
    <group position={[x, 0, 0]}>
      {[-2.2, 2.2].map((z) => <RB key={z} p={[0, 1.8, z]} s={[0.5, 3.6, 0.5]} c={BLUE} metal={0.5} r={0.06} />)}
      <RB p={[0, 3.55, 0]} s={[0.45, 0.45, 4.9]} c={BLUE} metal={0.5} r={0.06} />
      {/* clamp arms reaching in to the underbody */}
      {[-1.25, 1.25].map((z) => (
        <group key={z}>
          <B p={[0, 2.6, z]} s={[0.18, 1.6, 0.18]} c="#94a3b8" metal={0.8} />
          <B p={[0, 1.7, z * 0.85]} s={[0.35, 0.18, 0.5]} c="#475569" metal={0.7} />
          <Cyl p={[0, 1.2, z * 0.8]} r={0.07} h={0.7} c="#cbd5e1" metal={0.9} />
        </group>
      ))}
    </group>
  );
}

export function S04() {
  return (
    <AtStation id="S04">
      {() => (
        <group>
          <Pad w={11} d={11} tone="#eef1f5" />
          <mesh position={[-5.0, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.8, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[0, 0.075, 5.0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[10.4, 0.8]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          <CellFence w={11} d={11} gate={[1.4, 1.8]} />

          {/* framing jig: two portals straddling the conveyor */}
          <Portal x={-1.8} />
          <Portal x={1.8} />

          {/* tack-welding robots */}
          <Robot p={[-3.0, 0, 3.1]} id="M03a" absX={68}  station="S04" />
          <Robot p={[3.2, 0, 3.1]} id="M03b" absX={68}  station="S04" />
          <Robot p={[3.4, 0, -3.1]} rotY={Math.PI} id="M03c" absX={68}  station="S04" />

          {/* parts presentation racks with stamped panels */}
          {[[-4.2, -3.2], [-4.2, -4.6]].map(([x, z], i) => (
            <group key={i} position={[x, 0, z]}>
              {[[-0.7, -0.5], [0.7, -0.5], [-0.7, 0.5], [0.7, 0.5]].map(([a, b], k) => <B key={k} p={[a, 0.9, b]} s={[0.07, 1.8, 0.07]} c={BLUE} />)}
              {[0.3, 0.9, 1.5].map((y) => <B key={y} p={[0, y, 0]} s={[1.5, 0.05, 1.1]} c={BLUE} />)}
              {[0.35, 0.95, 1.55].map((y) => <B key={y} p={[0, y + 0.06, 0]} s={[1.3, 0.06, 0.9]} c="#b8c0cc" metal={0.85} rough={0.3} />)}
            </group>
          ))}

          {/* operator loading station with HMI and scanner */}
          <group position={[-3.6, 0, 3.8]}>
            <B p={[0, 0.5, 0]} s={[0.1, 1.0, 0.1]} c="#475569" />
            <RB p={[0, 1.15, 0]} s={[0.75, 0.5, 0.08]} c="#1d5fd0" r={0.03} rot={[-0.2, 0, 0]} />
            <Screen p={[0, 1.15, 0.045]} s={[0.66, 0.42]} rot={[-0.2, 0, 0]} draw={(ctx, w, h) => { ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h); ctx.fillStyle = "#38bdf8"; ctx.font = "700 28px sans-serif"; ctx.fillText("FRAMING 1", 14, 42); ctx.fillStyle = "#22c55e"; ctx.fillText("LOAD PAN OK", 14, 90); }} />
          </group>
          <Npc p={[-3.6, 0, 4.7]} rotY={Math.PI} color="#f97316" pose="work" seed={1} />
          <Npc p={[-0.2, 0, 2.2]} rotY={0.3} color="#f97316" pose="stand" seed={2} />

          {/* tool cabinet + andon */}
          <group position={[3.8, 0, 4.7]}>
            <RB p={[0, 0.7, 0]} s={[1.0, 1.4, 0.6]} c="#1d5fd0" metal={0.4} />
            <B p={[0, 0.7, 0.31]} s={[0.9, 1.2, 0.02]} c="#174a9e" />
          </group>
          <Andon p={[-4.9, 0, -4.9]} state={andonFor("S04")} />
          <Andon p={[4.9, 0, -4.9]} state={andonFor("S04")} />
        </group>
      )}
    </AtStation>
  );
}
