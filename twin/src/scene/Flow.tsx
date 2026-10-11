import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../clock";
import { BELT_SPEED, CAR_SLOTS, TAKT, carDistance, smooth } from "../flow";
import { toScene } from "../data";
import { useTwin } from "../state";
import { beltTime } from "../plant";
import { simLink } from "../simlink";

const STEEL = new THREE.Color("#8b95a3");
const PAINTS = ["#f8fafc", "#cbd5e1", "#1d4ed8", "#e2e8f0", "#b91c1c"].map((c) => new THREE.Color(c));

// ---- car body: floor pan -> underbody frame -> shell rises -> paint -> wheels --------------------------
const profile = (() => {
  const sh = new THREE.Shape();
  sh.moveTo(-2.3, 0); sh.lineTo(2.3, 0); sh.lineTo(2.3, 0.5); sh.lineTo(1.55, 0.62); sh.lineTo(0.75, 1.14);
  sh.lineTo(-0.85, 1.17); sh.lineTo(-1.7, 0.7); sh.lineTo(-2.3, 0.62); sh.closePath();
  return sh;
})();
const shellGeo = new THREE.ExtrudeGeometry(profile, { depth: 1.7, bevelEnabled: true, bevelSize: 0.07, bevelThickness: 0.07, bevelSegments: 2 });
shellGeo.translate(0, 0, -0.85);

const LIVE_SLOTS = 12;      // engine cars are mapped to slots by id; a full line with queues holds up to 8 bodies

// ---- conveyor with cars that are built as they travel ------------------------------------------------
export function Conveyor() {
  const { conveyor_path } = useTwin((s) => s.data)!.layout;
  const [x0, z0] = toScene(conveyor_path[0][0], conveyor_path[0][1]);
  const [x1] = toScene(conveyor_path[1][0], conveyor_path[1][1]);
  const len = x1 - x0;
  const groups = useRef<THREE.Group[]>([]);
  const prog = useMemo(() => Array.from({ length: LIVE_SLOTS }, () => ({ current: 0 })), []);

  useFrame(() => {
    if (simLink.on) {
      const by = new Map<number, { d_m: number }>();
      for (const c of simLink.snap!.belt.cars) by.set(c.k % LIVE_SLOTS, c);
      for (let s = 0; s < LIVE_SLOTS; s++) {
        const g = groups.current[s];
        const c = by.get(s);
        if (!g) continue;
        g.visible = !!c;
        if (c) {
          const tx = x0 + Math.min(c.d_m * (len / 59), len + 2);
          g.position.x = Math.abs(tx - g.position.x) > 4 ? tx : g.position.x + (tx - g.position.x) * 0.25;
          prog[s].current = Math.min(1, Math.max(0, c.d_m / 59));
        }
      }
      return;
    }
    for (let s = 0; s < LIVE_SLOTS; s++) {
      const g = groups.current[s];
      if (!g) continue;
      if (s >= CAR_SLOTS) { g.visible = false; continue; }      // offline model only uses the first slots
      const st = useTwin.getState();
      const { k, d } = carDistance(s, beltTime(clock.t, st.shift, st.data!.hero));
      const onBelt = d >= 0 && d <= len + 2;
      g.visible = onBelt;
      g.position.x = x0 + Math.min(d, len + 2);
      prog[s].current = Math.min(1, Math.max(0, d / len));
      g.userData.k = k;
    }
  });

  return (
    <group position={[0, 0, z0]}>
      <mesh position={[x0 + len / 2, 0.3, 0]} receiveShadow castShadow>
        <boxGeometry args={[len, 0.5, 2.6]} />
        <meshStandardMaterial color="#3f4a5a" roughness={0.5} metalness={0.5} />
      </mesh>
      <mesh position={[x0 + len / 2, 0.57, 0]}>
        <boxGeometry args={[len, 0.04, 2.1]} />
        <meshStandardMaterial color="#0f172a" roughness={0.6} />
      </mesh>
      {[-1.25, 1.25].map((z) => (
        <mesh key={z} position={[x0 + len / 2, 0.62, z]}>
          <boxGeometry args={[len, 0.1, 0.1]} />
          <meshStandardMaterial color="#facc15" />
        </mesh>
      ))}
      {Array.from({ length: LIVE_SLOTS }).map((_, s) => (
        <group key={s} ref={(g) => { if (g) groups.current[s] = g; }}>
          <group position={[0, 0.6, 0]}>
            <LiveCar progressRef={prog[s]} paint={PAINTS[s % PAINTS.length]} />
          </group>
        </group>
      ))}
    </group>
  );
}

function LiveCar({ progressRef, paint }: { progressRef: React.MutableRefObject<number>; paint: THREE.Color }) {
  // CarBody takes a plain number; wrap it so it re-reads the ref each frame.
  const frame = useRef<THREE.Group>(null!);
  const shell = useRef<THREE.Mesh>(null!);
  const glassM = useRef<THREE.Mesh>(null!);
  const wh = useRef<THREE.Group>(null!);
  const shellMat = useRef<THREE.MeshPhysicalMaterial>(null!);
  useFrame(() => {
    const p = progressRef.current;
    frame.current.visible = p > 0.05;
    frame.current.scale.set(1, Math.max(smooth(0.05, 0.22, p), 0.001), 1);
    const rise = smooth(0.24, 0.72, p);
    shell.current.visible = rise > 0.01;
    shell.current.scale.set(1, Math.max(rise, 0.001), 1);
    glassM.current.visible = p > 0.75;
    glassM.current.scale.set(1, Math.max(smooth(0.75, 0.84, p), 0.001), 1);
    const paintT = smooth(0.8, 0.93, p);
    shellMat.current.color.lerpColors(STEEL, paint, paintT);
    shellMat.current.metalness = 0.55 + 0.1 * paintT;
    shellMat.current.roughness = 0.5 - 0.28 * paintT;
    shellMat.current.clearcoat = paintT;
    wh.current.visible = p > 0.93;
  });
  return (
    <group>
      <mesh position={[0, 0.34, 0]} castShadow>
        <boxGeometry args={[4.5, 0.08, 1.7]} />
        <meshStandardMaterial color="#59616d" metalness={0.7} roughness={0.5} />
      </mesh>
      <group ref={frame} position={[0, 0.34, 0]}>
        {[-0.7, 0.7].map((z) => (
          <mesh key={z} position={[0, 0.13, z]} castShadow><boxGeometry args={[4.4, 0.18, 0.1]} /><meshStandardMaterial color="#7b8593" metalness={0.7} roughness={0.4} /></mesh>
        ))}
        {[-1.6, -0.2, 1.2].map((x) => (
          <mesh key={x} position={[x, 0.13, 0]} castShadow><boxGeometry args={[0.1, 0.18, 1.5]} /><meshStandardMaterial color="#7b8593" metalness={0.7} roughness={0.4} /></mesh>
        ))}
      </group>
      <group position={[0, 0.38, 0]}>
        <mesh ref={shell} geometry={shellGeo} castShadow>
          <meshPhysicalMaterial ref={shellMat} color="#8b95a3" metalness={0.6} roughness={0.5} clearcoatRoughness={0.1} />
        </mesh>
        <mesh ref={glassM} position={[0, 0.92, 0]}>
          <boxGeometry args={[1.95, 0.4, 1.74]} />
          <meshStandardMaterial color="#0b1220" metalness={0.9} roughness={0.08} />
        </mesh>
      </group>
      <group ref={wh}>
        {[[-1.4, 0.82], [1.4, 0.82], [-1.4, -0.82], [1.4, -0.82]].map(([x, z], i) => (
          <mesh key={i} position={[x, 0.36, z]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[0.36, 0.36, 0.26, 18]} />
            <meshStandardMaterial color="#111827" roughness={0.8} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

// ---- logistics vehicles ---------------------------------------------------------------------------------
type Pt = [number, number];
interface Route { pts: Pt[]; cum: number[]; len: number }

function makeRoute(route: Pt[]): Route {
  const pts = route.map(([x, z]) => toScene(x, z) as Pt);
  const cum = [0];
  for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return { pts, cum, len: cum[cum.length - 1] };
}

function along(r: Route, d: number, out: { x: number; z: number; h: number }) {
  const dd = Math.min(Math.max(d, 0), r.len);
  let i = 1;
  while (i < r.pts.length - 1 && r.cum[i] < dd) i++;
  const [x0, z0] = r.pts[i - 1];
  const [x1, z1] = r.pts[i];
  const f = r.cum[i] > r.cum[i - 1] ? (dd - r.cum[i - 1]) / (r.cum[i] - r.cum[i - 1]) : 0;
  out.x = x0 + (x1 - x0) * f;
  out.z = z0 + (z1 - z0) * f;
  out.h = Math.atan2(x1 - x0, z1 - z0);
}

function LoadMesh({ kind }: { kind: string }) {
  switch (kind) {
    case "coil":
      return (
        <mesh position={[0, 0.9, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.75, 0.75, 0.9, 28]} />
          <meshStandardMaterial color="#cbd5e1" metalness={0.9} roughness={0.25} />
        </mesh>
      );
    case "rack":
      return (
        <group position={[0, 0.2, 0]}>
          <mesh position={[0, 0.55, 0]} castShadow><boxGeometry args={[1.3, 1.0, 0.9]} /><meshStandardMaterial color="#2563eb" metalness={0.5} roughness={0.5} /></mesh>
          {[0.25, 0.55, 0.85].map((y) => (
            <mesh key={y} position={[0, y, 0]} castShadow><boxGeometry args={[1.15, 0.12, 0.8]} /><meshStandardMaterial color="#9aa5b4" metalness={0.8} roughness={0.35} /></mesh>
          ))}
        </group>
      );
    case "pan":
      return (
        <mesh position={[0, 0.38, 0]} castShadow>
          <boxGeometry args={[4.5, 0.08, 1.7]} />
          <meshStandardMaterial color="#59616d" metalness={0.7} roughness={0.5} />
        </mesh>
      );
    case "pack":
      return (
        <group position={[0, 0.4, 0]}>
          <mesh castShadow><boxGeometry args={[2.0, 0.3, 1.3]} /><meshStandardMaterial color="#1f2937" metalness={0.6} roughness={0.45} /></mesh>
          <mesh position={[0, 0.17, 0]}><boxGeometry args={[1.8, 0.02, 0.2]} /><meshStandardMaterial color="#22c55e" emissive="#22c55e" emissiveIntensity={0.6} /></mesh>
        </group>
      );
    case "pallet":
      return (
        <group position={[0, 0.3, 0]}>
          <mesh position={[0, 0.08, 0]} castShadow><boxGeometry args={[1.2, 0.16, 1.0]} /><meshStandardMaterial color="#a16207" roughness={0.9} /></mesh>
          {[0, 1, 2].map((k) => (
            <mesh key={k} position={[0, 0.4 + k * 0.5, 0]} castShadow><boxGeometry args={[1.0, 0.45, 0.85]} /><meshStandardMaterial color="#b98b52" roughness={0.9} /></mesh>
          ))}
        </group>
      );
    default:
      return (
        <group position={[0, 0.45, 0]}>
          {[[-0.25, 0, 0], [0.25, 0, 0.1], [0, 0.4, 0]].map((p, i) => (
            <mesh key={i} position={p as [number, number, number]} castShadow><boxGeometry args={[0.5, 0.4, 0.5]} /><meshStandardMaterial color="#b98b52" roughness={0.9} /></mesh>
          ))}
        </group>
      );
  }
}

function VehicleBody({ kind }: { kind: string }) {
  if (kind === "forklift")
    return (
      <group>
        <mesh position={[0, 0.65, -0.4]} castShadow><boxGeometry args={[1.1, 0.9, 1.6]} /><meshStandardMaterial color="#f59e0b" metalness={0.4} roughness={0.5} /></mesh>
        <mesh position={[0, 1.6, -0.5]} castShadow><boxGeometry args={[1.0, 0.08, 1.0]} /><meshStandardMaterial color="#1f2937" /></mesh>
        {[-0.45, 0.45].map((x) => (<mesh key={x} position={[x, 0.9, 0.5]} castShadow><boxGeometry args={[0.08, 1.8, 0.08]} /><meshStandardMaterial color="#334155" /></mesh>))}
        {[-0.35, 0.35].map((x) => (<mesh key={x} position={[x, 0.1, 1.1]} castShadow><boxGeometry args={[0.12, 0.08, 1.2]} /><meshStandardMaterial color="#334155" /></mesh>))}
      </group>
    );
  const col = kind === "cart" ? "#7c3aed" : "#facc15";
  return (
    <group>
      <mesh position={[0, 0.14, 0]} castShadow>
        <boxGeometry args={[kind === "cart" ? 1.0 : 1.7, 0.24, kind === "cart" ? 0.7 : 1.05]} />
        <meshStandardMaterial color={col} metalness={0.4} roughness={0.5} />
      </mesh>
      <mesh position={[0.75, 0.3, 0]}><boxGeometry args={[0.12, 0.06, 0.3]} /><meshStandardMaterial color="#22c55e" emissive="#22c55e" emissiveIntensity={1.2} /></mesh>
    </group>
  );
}

interface Logi { id: string; vehicle: string; load: string; period_s: number; speed_mps: number; route: Pt[] }

function Shuttle({ l, index, beltLen }: { l: Logi; index: number; beltLen: number }) {
  const route = useMemo(() => makeRoute(l.route), [l]);
  const g = useRef<THREE.Group>(null!);
  const load = useRef<THREE.Group>(null!);
  const out = useMemo(() => ({ x: 0, z: 0, h: 0 }), []);
  const timing = useMemo(() => {
    const travel = route.len / l.speed_mps;
    const dwell = 4;
    const period = Math.max(l.period_s, 2 * travel + 2 * dwell + 4);
    // When does the forward leg START inside each period?
    let start = (index * 37) % period;
    if (l.id === "L3") start = (((TAKT - travel) % TAKT) + TAKT) % TAKT;                    // arrives exactly as a new body enters the belt
    if (l.id === "L4") start = ((((beltLen + 2) / BELT_SPEED) % TAKT) + TAKT) % TAKT;     // leaves when the finished body reaches the end
    return { travel, dwell, period, start };
  }, [route, l, index, beltLen]);

  useFrame(() => {
    const { travel, dwell, period, start } = timing;
    const st = useTwin.getState();
    const tt = l.id === "L3" || l.id === "L4" ? beltTime(clock.t, st.shift, st.data!.hero) : clock.t;
    const u = ((((tt - start) % period) + period) % period);
    let d = 0;
    let carrying = true;
    if (u < travel) d = (u / travel) * route.len;
    else if (u < travel + dwell) { d = route.len; carrying = !(l.id === "L3" || l.id === "L4") && u < travel + 1.5; }
    else if (u < 2 * travel + dwell) { d = route.len * (1 - (u - travel - dwell) / travel); carrying = false; }
    else { d = 0; carrying = l.id !== "L4"; }          // parked at origin, next load waiting
    along(route, d, out);
    g.current.position.set(out.x, 0, out.z);
    const back = u >= travel + dwell && u < 2 * travel + dwell;
    g.current.rotation.y = out.h + (back ? Math.PI : 0);
    load.current.visible = carrying;
  });

  return (
    <group ref={g}>
      <VehicleBody kind={l.vehicle} />
      <group ref={load} position={[0, l.vehicle === "forklift" ? 0.25 : 0.26, l.vehicle === "forklift" ? 1.1 : 0]}>
        {l.load === "car" ? <FinishedCar /> : <LoadMesh kind={l.load} />}
      </group>
    </group>
  );
}

function FinishedCar() {
  return (
    <group position={[0, 0.0, 0]}>
      <ProgressCarFixed />
    </group>
  );
}

function ProgressCarFixed() {
  const p = useRef(1);
  return <LiveCar progressRef={p} paint={PAINTS[0]} />;
}

export function Logistics() {
  const layout = useTwin((s) => s.data)!.layout;
  const logi = (layout as unknown as { logistics?: Logi[] }).logistics;
  if (!logi) return null;
  const beltLen = layout.conveyor_path[1][0] - layout.conveyor_path[0][0];
  return (
    <>
      {logi.map((l, i) => (
        <Shuttle key={l.id} l={l} index={i} beltLen={beltLen} />
      ))}
    </>
  );
}

/** A finished body, for station models (marriage station etc.). */
export function StaticCar({ color = "#f8fafc" }: { color?: string }) {
  const p = { current: 1 };
  return <LiveCar progressRef={p} paint={new THREE.Color(color)} />;
}
