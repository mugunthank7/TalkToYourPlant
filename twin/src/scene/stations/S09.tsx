import { andonFor, andonPlant } from "../../plant";
import { clock } from "../../clock";
import { Andon, AtStation, B, Cyl, Hazard, Npc, Pad, RB, Screen, TextBoard } from "../kit";
import { StaticCar } from "../Flow";
import { useTwin } from "../../state";

const ORANGE = "#f08a1d";
const BLUE = "#1d5fd0";

function Rail({ x0, z0, x1, z1 }: { x0: number; z0: number; x1: number; z1: number }) {
  const len = Math.hypot(x1 - x0, z1 - z0);
  const a = -Math.atan2(z1 - z0, x1 - x0);
  return (
    <group>
      <B p={[(x0 + x1) / 2, 1.0, (z0 + z1) / 2]} s={[len, 0.07, 0.07]} c="#facc15" rot={[0, a, 0]} />
      <B p={[(x0 + x1) / 2, 0.55, (z0 + z1) / 2]} s={[len, 0.07, 0.07]} c="#facc15" rot={[0, a, 0]} />
      {[0, 1].map((k) => <B key={k} p={[x0 + (x1 - x0) * k, 0.5, z0 + (z1 - z0) * k]} s={[0.08, 1.0, 0.08]} c="#facc15" />)}
    </group>
  );
}

function PackModule({ p, rot }: { p: [number, number, number]; rot?: [number, number, number] }) {
  return (
    <group position={p} rotation={rot}>
      <RB p={[0, 0.12, 0]} s={[2.4, 0.24, 1.5]} c="#1f2937" metal={0.6} />
      {Array.from({ length: 6 }).map((_, i) => <B key={i} p={[-1.0 + i * 0.4, 0.26, 0]} s={[0.34, 0.06, 1.3]} c="#334155" metal={0.5} />)}
      <B p={[0, 0.27, 0]} s={[2.2, 0.02, 0.14]} c="#22c55e" emissive="#22c55e" ei={0.7} />
    </group>
  );
}

export function S09() {
  const shift = useTwin((s) => s.shift);
  void shift;
  return (
    <AtStation id="S09">
      {() => (
        <group>
          <Pad w={16} d={11} tone="#eef1f5" />
          {/* green lane through the station like the reference */}
          <mesh position={[1.0, 0.075, -1.0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1.3, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          {/* ---- pack sealing press (orange) with a pack on the infeed bench ---- */}
          <group position={[-5.6, 0, -0.8]}>
            <B p={[0, 0.2, 0]} s={[2.4, 0.4, 2.6]} c="#374151" />
            {[[-1.0, -1.1], [1.0, -1.1], [-1.0, 1.1], [1.0, 1.1]].map(([x, z], i) => <B key={i} p={[x, 1.45, z]} s={[0.22, 2.1, 0.22]} c={ORANGE} metal={0.4} />)}
            <RB p={[0, 2.6, 0]} s={[2.5, 0.5, 2.6]} c={ORANGE} metal={0.4} />
            <RB p={[0, 3.0, 0]} s={[1.5, 0.5, 1.6]} c="#2f3743" metal={0.6} />
            <B p={[0, 1.65, 0]} s={[1.7, 0.4, 1.7]} c="#9aa7b5" metal={0.7} />
          </group>
          <group position={[-5.4, 0, 2.1]}>
            <RB p={[0, 0.78, 0]} s={[3.0, 0.1, 1.5]} c="#9aa7b5" metal={0.5} />
            {[[-1.4, -0.65], [1.4, -0.65], [-1.4, 0.65], [1.4, 0.65]].map(([x, z], i) => <B key={i} p={[x, 0.38, z]} s={[0.1, 0.76, 0.1]} c={BLUE} metal={0.5} />)}
            <B p={[0, 0.32, 0]} s={[2.9, 0.06, 1.4]} c={BLUE} />
            <PackModule p={[0, 0.84, 0]} />
          </group>

          {/* ---- leak test chamber + cable reel ---- */}
          <group position={[-2.5, 0, -2.4]}>
            <RB p={[0, 0.95, 0]} s={[2.2, 1.9, 1.8]} c="#e7ebf0" metal={0.2} rough={0.4} />
            <B p={[0.4, 1.05, 0.92]} s={[1.2, 0.9, 0.03]} c="#0f1a2e" metal={0.2} />
            <B p={[0.4, 1.05, 0.935]} s={[1.1, 0.8, 0.01]} c="#7dd3fc" emissive="#38bdf8" ei={0.35} />
            <Cyl p={[-0.6, 2.2, 0.2]} r={0.28} h={0.1} c="#e5e7eb" rot={[Math.PI / 2, 0, 0]} />
            <B p={[-0.6, 2.2, 0.26]} s={[0.04, 0.2, 0.01]} c="#ef4444" rot={[0, 0, 0.6]} />
            <B p={[-0.6, 1.95, 0.2]} s={[0.1, 0.35, 0.1]} c="#94a3b8" />
          </group>
          <group position={[-2.9, 0, -0.3]}>
            <Cyl p={[0, 0.55, 0]} r={0.5} h={0.18} c="#16a34a" rot={[Math.PI / 2, 0, 0]} />
            <Cyl p={[0, 0.55, 0]} r={0.14} h={0.3} c="#334155" rot={[Math.PI / 2, 0, 0]} />
            <B p={[0, 0.28, 0]} s={[0.15, 0.56, 0.5]} c="#475569" />
          </group>

          {/* ---- EOL test cell (blue frame, big screen, operator) ---- */}
          <group position={[0.2, 0, -3.0]}>
            {[[-1.7, -1.4], [1.7, -1.4], [-1.7, 1.4], [1.7, 1.4]].map(([x, z], i) => <B key={i} p={[x, 1.6, z]} s={[0.14, 3.2, 0.14]} c={BLUE} metal={0.5} />)}
            {[-1.4, 1.4].map((z) => <B key={z} p={[0, 3.2, z]} s={[3.5, 0.14, 0.14]} c={BLUE} metal={0.5} />)}
            {[-1.7, 1.7].map((x) => <B key={x} p={[x, 3.2, 0]} s={[0.14, 0.14, 2.9]} c={BLUE} metal={0.5} />)}
            <B p={[0, 0.2, 0]} s={[3.2, 0.4, 2.2]} c="#cbd5e1" metal={0.5} />
            <PackModule p={[0, 0.4, 0]} />
            <RB p={[0.3, 2.3, 1.3]} s={[2.2, 1.25, 0.08]} c="#0b0f19" r={0.03} rot={[-0.12, 0, 0]} />
            <Screen p={[0.3, 2.3, 1.345]} s={[2.1, 1.15]} rot={[-0.12, 0, 0]} draw={(ctx, w, h) => {
              ctx.fillStyle = "#06121a"; ctx.fillRect(0, 0, w, h);
              ctx.fillStyle = "#22c55e"; ctx.font = "700 24px sans-serif"; ctx.fillText("EOL TEST  PACK 4471", 16, 36);
              ctx.font = "18px monospace"; ctx.fillStyle = "#86efac";
              ["insulation  ok  >500 Mohm", "leak rate   ok  0.4 cc/min", "cell balance ok  12 mV", "BMS comms   ok", "thermal     ok  24.1 C"].forEach((t, i) => ctx.fillText(t, 16, 80 + i * 30));
              ctx.fillStyle = "#22c55e"; ctx.fillRect(16, h - 50, 150, 34); ctx.fillStyle = "#06121a"; ctx.font = "700 20px sans-serif"; ctx.fillText("PASS", 52, h - 25);
              const f = (clock.t * 8) % w; ctx.fillStyle = "rgba(56,189,248,.5)"; ctx.fillRect(f, 50, 3, h - 100);
            }} />
          </group>
          <Npc p={[1.5, 0, -1.4]} rotY={Math.PI} color="#22c55e" pose="work" seed={4} />

          {/* ---- marriage station: scissor lift, pack below, body above ---- */}
          <group position={[3.6, 0, 1.2]}>
            <B p={[0, 0.1, 0]} s={[4.6, 0.2, 3.2]} c="#374151" />
            {[-1, 1].map((s) => (
              <group key={s}>
                <B p={[0, 0.8, s * 1.2]} s={[3.2, 0.12, 0.12]} c={ORANGE} rot={[0, 0, 0.45]} />
                <B p={[0, 0.8, s * 1.2]} s={[3.2, 0.12, 0.12]} c={ORANGE} rot={[0, 0, -0.45]} />
              </group>
            ))}
            <B p={[0, 1.45, 0]} s={[4.4, 0.16, 2.8]} c="#475569" />
            <PackModule p={[0, 1.55, 0]} />
            <group position={[0, 2.3, 0]}><StaticCar color="#f8fafc" /></group>
          </group>
          <Hazard p={[3.6, 0, 1.2]} s={[5.4, 0.4]} />
          <Npc p={[1.0, 0, 2.7]} rotY={0.5} color="#f97316" pose="stand" seed={9} />

          {/* ---- rework bay ---- */}
          {[[5.4, -4.4], [5.4, -2.9]].map(([x, z], i) => (
            <group key={i} position={[x, 0, z]}>
              {[[-0.7, -0.35], [0.7, -0.35], [-0.7, 0.35], [0.7, 0.35]].map(([a, b], k) => <B key={k} p={[a, 0.9, b]} s={[0.06, 1.8, 0.06]} c={ORANGE} />)}
              {[0.3, 0.9, 1.5].map((y) => <B key={y} p={[0, y, 0]} s={[1.5, 0.05, 0.8]} c={ORANGE} />)}
              <B p={[0.2, 0.42, 0]} s={[0.5, 0.25, 0.4]} c="#cbd5e1" />
              <B p={[-0.3, 1.02, 0]} s={[0.4, 0.25, 0.4]} c="#64748b" />
            </group>
          ))}
          <TextBoard p={[5.4, 2.1, -5.2]} s={[1.6, 0.4]} text="REWORK BAY" bg="#f8fafc" fg="#0f172a" />

          {/* guard rails, green go tower */}
          <Rail x0={-7.6} z0={4.9} x1={-3.0} z1={4.9} />
          <Rail x0={7.4} z0={-5.0} x1={7.4} z1={1.0} />
          <Andon p={[2.9, 0, -4.8]} state={andonFor("S09")} />
        </group>
      )}
    </AtStation>
  );
}
