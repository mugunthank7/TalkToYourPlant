import { andonFor, andonPlant } from "../../plant";
import { AtStation, Andon, B, CellFence, Cyl, Hazard, Npc, Pad, RB, Screen } from "../kit";
import { Robot } from "./common";

export function S05() {
  return (
    <AtStation id="S05">
      {() => (
        <group>
          <Pad w={12} d={11} tone="#eef1f5" />
          {/* green lane frame, as in the reference */}
          <mesh position={[-5.7, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.6, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[5.7, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.6, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <B p={[0, 0.085, 4.6]} s={[10, 0.02, 0.5]} c="#1f2937" rough={0.95} metal={0} shadow={false} />
          <Hazard p={[0, 0.0, 5.1]} s={[10, 0.4]} />

          <CellFence w={12} d={11} gate={[0.6, 1.8]} />

          {/* two robots south, one north, all welding the body */}
          <Robot p={[-2.6, 0, 2.9]} id="M04" absX={84}  station="S05" />
          <Robot p={[2.6, 0, 2.9]} id="M04b" absX={84}  station="S05" />
          <Robot p={[0.2, 0, -3.0]} rotY={Math.PI} id="M04c" absX={84}  station="S05" />

          {/* electrode tip dresser */}
          <group position={[-4.6, 0, 2.0]}>
            <RB p={[0, 0.5, 0]} s={[0.8, 1.0, 0.7]} c="#cbd5e1" metal={0.6} />
            <Cyl p={[0, 1.1, 0]} r={0.2} h={0.25} c="#475569" />
            <B p={[0.25, 0.7, 0.36]} s={[0.2, 0.2, 0.02]} c="#22c55e" emissive="#22c55e" ei={0.6} />
          </group>

          {/* controller cabinet with teach pendant, operator */}
          <group position={[4.6, 0, 3.9]}>
            <RB p={[0, 1.0, 0]} s={[1.1, 2.0, 0.7]} c="#eef1f5" metal={0.2} rough={0.4} />
            <B p={[0.3, 1.2, 0.36]} s={[0.35, 0.5, 0.03]} c="#0f172a" />
            <B p={[-0.5, 1.2, 0.4]} s={[0.1, 0.35, 0.06]} c="#facc15" />
          </group>
          <Npc p={[3.6, 0, 4.5]} rotY={Math.PI} color="#f97316" pose="work" seed={3} />

          {/* weld quality monitor on a stand */}
          <group position={[5.0, 0, 1.4]}>
            <B p={[0, 0.5, 0]} s={[0.1, 1.0, 0.1]} c="#475569" />
            <RB p={[0, 1.4, 0]} s={[1.3, 0.8, 0.06]} c="#0b0f19" r={0.03} rot={[0, -1.2, 0]} />
            <Screen p={[-0.02, 1.4, 0.03]} s={[1.2, 0.7]} rot={[0, -1.2, 0]} draw={(ctx, w, h) => {
              ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
              ctx.fillStyle = "#38bdf8"; ctx.font = "700 24px sans-serif"; ctx.fillText("WELD QUALITY  CELL A", 14, 34);
              for (let i = 0; i < 12; i++) { ctx.fillStyle = i === 7 ? "#f59e0b" : "#22c55e"; ctx.fillRect(18 + i * 38, h - 40 - (40 + ((i * 37) % 70)), 26, 40 + ((i * 37) % 70)); }
            }} />
          </group>

          <Andon p={[5.2, 0, -4.8]} state={andonFor("S05")} />
          <Cyl p={[-5.4, 0.5, 5.2]} r={0.1} h={1.0} c="#facc15" metal={0.2} />
          <Cyl p={[5.4, 0.5, 5.2]} r={0.1} h={1.0} c="#facc15" metal={0.2} />
        </group>
      )}
    </AtStation>
  );
}
