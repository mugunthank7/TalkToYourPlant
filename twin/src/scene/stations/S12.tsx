import { useMemo } from "react";
import { AtStation, B, Cyl, Hazard, Npc, Pad, RB, Screen, TextBoard, WireMesh, type V3 } from "../kit";
import { Model } from "../Props";

const BLUE = "#1d5fd0";
const ORANGE = "#f97316";

/** Deterministic pseudo random, so the shelves look the same on every load. */
function rng(seed: number) {
  let s = seed * 9301 + 49297;
  return () => ((s = (s * 9301 + 49297) % 233280) / 233280);
}

/** Back-to-back blue steel shelving unit, runs along z. Local origin = floor centre. */
function Shelving({ p, len = 5.6, seed = 1 }: { p: V3; len?: number; seed?: number }) {
  const levels = 3;
  const h = 2.4;
  const items = useMemo(() => {
    const r = rng(seed);
    const out: { kind: "box" | "bin" | "bearing" | "sack"; z: number; y: number; x: number; rot: number; c: string }[] = [];
    for (let l = 0; l < levels; l++) {
      for (let i = 0; i < Math.floor(len / 0.62); i++) {
        if (r() < 0.12) continue;
        const k = r();
        out.push({
          kind: k < 0.45 ? "box" : k < 0.7 ? "bin" : k < 0.9 ? "bearing" : "sack",
          z: -len / 2 + 0.4 + i * 0.62, y: 0.22 + (l * h) / levels + 0.05, x: (r() - 0.5) * 0.12, rot: (r() - 0.5) * 0.25,
          c: ["#2563eb", "#f59e0b", "#22c55e", "#ef4444"][Math.floor(r() * 4)],
        });
      }
    }
    return out;
  }, [len, seed]);
  return (
    <group position={p}>
      {[-len / 2, len / 2].flatMap((z) => [-0.45, 0.45].map((x) => <B key={`${x}${z}`} p={[x, h / 2, z]} s={[0.08, h, 0.08]} c={BLUE} metal={0.5} />))}
      {Array.from({ length: levels }).map((_, l) => <B key={l} p={[0, 0.2 + (l * h) / levels, 0]} s={[1.0, 0.06, len]} c={ORANGE} metal={0.4} />)}
      {items.map((it, i) =>
        it.kind === "box" ? (
          <Model key={i} name="cardboard_box_01" position={[it.x, it.y, it.z]} rotY={it.rot + 1.57} lift={0.18} />
        ) : it.kind === "bin" ? (
          <group key={i} position={[it.x, it.y, it.z]} rotation={[0, it.rot, 0]}>
            <B p={[0, 0.14, 0]} s={[0.7, 0.28, 0.5]} c={it.c} rough={0.6} metal={0.05} />
            <B p={[0.36, 0.14, 0]} s={[0.02, 0.2, 0.3]} c="#f8fafc" />
          </group>
        ) : it.kind === "bearing" ? (
          <group key={i} position={[it.x, it.y, it.z]} rotation={[0, it.rot, 0]}>
            <B p={[0, 0.1, 0]} s={[0.34, 0.2, 0.34]} c="#f1f5f9" rough={0.5} metal={0.05} />
            <B p={[0.18, 0.12, 0]} s={[0.01, 0.1, 0.2]} c="#dc2626" />
            <B p={[0, 0.1, 0.4 - 0.4]} s={[0.36, 0.02, 0.36]} c="#dc2626" />
          </group>
        ) : (
          <B key={i} p={[it.x, it.y + 0.12, it.z]} s={[0.5, 0.24, 0.4]} c="#d6c7a1" rough={0.9} metal={0} rot={[0, it.rot, 0]} />
        ),
      )}
    </group>
  );
}

export function S12() {
  return (
    <AtStation id="S12">
      {() => (
        <group>
          <Pad w={12} d={8} tone="#eef1f5" />
          {/* green pedestrian strip along the north edge, like the reference */}
          <mesh position={[0, 0.075, -3.75]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[11.6, 0.5]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>

          {/* ---- wire mesh cage, door in the north wall ---- */}
          <WireMesh p={[-3.4, 0, -3.3]} s={[4.1, 2.4]} />
          <WireMesh p={[3.4, 0, -3.3]} s={[4.1, 2.4]} />
          <B p={[0, 2.35, -3.3]} s={[2.6, 0.1, 0.08]} c="#1d4ed8" />
          <WireMesh p={[0, 0, 3.4]} s={[10.8, 2.4]} />
          <WireMesh p={[-5.4, 0, 0]} s={[6.8, 2.4]} axis="z" />
          <WireMesh p={[5.4, 0, 0]} s={[6.8, 2.4]} axis="z" />
          {/* open door leaf */}
          <group position={[-1.25, 0, -3.3]} rotation={[0, -1.2, 0]}>
            <WireMesh p={[0.6, 0, 0]} s={[1.2, 2.2]} />
          </group>
          <B p={[0.9, 1.1, -3.3]} s={[0.06, 2.2, 0.08]} c="#1d4ed8" />

          {/* hanging sign */}
          <B p={[-0.4, 2.8, -3.3]} s={[0.02, 0.5, 0.02]} c="#94a3b8" />
          <B p={[0.4, 2.8, -3.3]} s={[0.02, 0.5, 0.02]} c="#94a3b8" />
          <TextBoard p={[0, 2.35, -3.3]} s={[1.9, 0.5]} text="SPARE PARTS" bg="#f8fafc" fg="#0f172a" />

          {/* ---- shelving rows (east side, back to back) ---- */}
          <Shelving p={[4.6, 0, 0.1]} seed={4} />
          <Shelving p={[3.2, 0, 0.1]} seed={9} />

          {/* ---- scanning kiosk ---- */}
          <group position={[-4.0, 0, -1.6]}>
            <B p={[0, 0.5, 0]} s={[0.12, 1.0, 0.12]} c="#475569" />
            <B p={[0, 0.08, 0]} s={[0.7, 0.16, 0.5]} c="#334155" />
            <RB p={[0, 1.2, 0]} s={[0.92, 0.64, 0.08]} c="#0b0f19" r={0.03} />
            <Screen p={[0, 1.2, 0.045]} s={[0.84, 0.56]} draw={(ctx, w, h) => {
              ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
              ctx.fillStyle = "#38bdf8"; ctx.font = "600 22px sans-serif"; ctx.fillText("SPARES  SCAN", 18, 34);
              ctx.fillStyle = "#e2e8f0"; ctx.font = "700 34px sans-serif"; ctx.fillText("bearing_6208", 18, 88);
              ctx.fillStyle = "#22c55e"; ctx.font = "700 40px sans-serif"; ctx.fillText("IN STOCK", 18, 136);
              ctx.fillStyle = "#94a3b8"; ctx.font = "20px sans-serif"; ctx.fillText("bin B-12 · qty 14", 18, 168);
            }} />
          </group>
          <Npc p={[-3.2, 0, -1.5]} rotY={-Math.PI / 2} color="#facc15" pose="stand" seed={5} />

          {/* hand truck and pick trolley */}
          <Model name="hand_truck" position={[-4.7, 0, 2.2]} rotY={0.5} />
          <group position={[-1.6, 0, 2.2]}>
            <B p={[0, 0.35, 0]} s={[1.2, 0.05, 0.7]} c="#2563eb" />
            <B p={[0, 0.85, 0]} s={[1.2, 0.05, 0.7]} c="#2563eb" />
            {[[-0.55, -0.3], [0.55, -0.3], [-0.55, 0.3], [0.55, 0.3]].map(([x, z], i) => <B key={i} p={[x, 0.55, z]} s={[0.04, 1.1, 0.04]} c="#94a3b8" />)}
            <Model name="cardboard_box_01" position={[-0.25, 0.38, 0]} lift={0.18} rotY={0.2} />
            <Model name="cardboard_box_01" position={[0.3, 0.88, 0]} lift={0.18} rotY={1.7} />
            {[[-0.5, 0.3], [0.5, 0.3], [-0.5, -0.3], [0.5, -0.3]].map(([x, z], i) => (
              <mesh key={i} position={[x, 0.08, z]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.08, 0.08, 0.05, 12]} /><meshStandardMaterial color="#111827" /></mesh>
            ))}
          </group>

          {/* pick zone */}
          <Hazard p={[-1.2, 0, 0.6]} s={[3.2, 2.0]} />
          <B p={[-1.2, 0.09, -0.42]} s={[3.2, 0.03, 0.06]} c="#111827" shadow={false} />
          <B p={[-1.2, 0.09, 1.62]} s={[3.2, 0.03, 0.06]} c="#111827" shadow={false} />

          {/* extinguishers on the cage posts */}
          <Model name="korean_fire_extinguisher_01" position={[-5.2, 0.9, -3.1]} rotY={0} />
          <Model name="korean_fire_extinguisher_01" position={[5.2, 0.9, 3.2]} rotY={Math.PI} />
          <Cyl p={[-5.2, 0.9, -3.3]} r={0.015} h={0.01} c="#94a3b8" />
        </group>
      )}
    </AtStation>
  );
}
