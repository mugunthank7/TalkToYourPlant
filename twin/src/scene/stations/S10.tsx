import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../../clock";
import { AtStation, B, Cyl, Hazard, Npc, Pad, RB, Screen, TextBoard } from "../kit";
import { Model } from "../Props";

const RED = "#c81e1e";
const BLUE = "#1d5fd0";
const YELLOW = "#facc15";

function ToolChest({ p, rotY = 0 }: { p: [number, number, number]; rotY?: number }) {
  return (
    <group position={p} rotation={[0, rotY, 0]}>
      <RB p={[0, 0.5, 0]} s={[1.3, 1.0, 0.65]} c={RED} metal={0.4} rough={0.4} r={0.04} />
      {[0.18, 0.4, 0.62, 0.84].map((y) => (
        <group key={y}>
          <B p={[0, y, 0.335]} s={[1.24, 0.17, 0.02]} c="#a31616" metal={0.5} />
          <B p={[0, y, 0.35]} s={[0.4, 0.03, 0.03]} c="#d1d5db" metal={0.9} />
        </group>
      ))}
      <B p={[0, 1.02, 0]} s={[1.34, 0.05, 0.69]} c="#374151" />
    </group>
  );
}

function JibCrane() {
  const arm = useRef<THREE.Group>(null!);
  const hoist = useRef<THREE.Group>(null!);
  useFrame(() => {
    arm.current.rotation.y = -0.6 + Math.sin(clock.t / 40) * 0.45;
    hoist.current.position.x = 2.2 + Math.sin(clock.t / 23) * 0.8;
  });
  return (
    <group>
      <Cyl p={[0, 0.1, 0]} r={0.55} h={0.2} c="#475569" />
      <Cyl p={[0, 2.1, 0]} r={0.16} h={4.2} c="#9aa7b5" metal={0.7} />
      <group ref={arm} position={[0, 4.0, 0]}>
        <B p={[1.9, 0, 0]} s={[3.8, 0.28, 0.22]} c={YELLOW} metal={0.4} />
        <B p={[1.3, -0.45, 0]} s={[2.5, 0.06, 0.06]} c={YELLOW} rot={[0, 0, 0.18]} />
        <group ref={hoist} position={[2.2, -0.28, 0]}>
          <RB p={[0, -0.12, 0]} s={[0.4, 0.3, 0.3]} c={YELLOW} />
          <Cyl p={[0, -0.9, 0]} r={0.012} h={1.4} c="#475569" />
          <B p={[0, -1.65, 0]} s={[0.12, 0.16, 0.08]} c="#475569" metal={0.8} />
        </group>
      </group>
    </group>
  );
}

function Bench({ p }: { p: [number, number, number] }) {
  return (
    <group position={p}>
      <RB p={[0, 0.92, 0]} s={[3.6, 0.08, 1.1]} c="#c9a070" metal={0.05} rough={0.7} />
      <B p={[0, 0.78, 0]} s={[3.5, 0.2, 1.0]} c="#475569" />
      {[-1.7, 1.7].flatMap((x) => [-0.45, 0.45].map((z) => <B key={`${x}${z}`} p={[x, 0.45, z]} s={[0.07, 0.9, 0.07]} c={BLUE} metal={0.5} />))}
      <B p={[0, 0.3, 0]} s={[3.4, 0.05, 0.9]} c={BLUE} metal={0.4} />
      {/* vice */}
      <B p={[-1.2, 1.02, 0.2]} s={[0.3, 0.14, 0.26]} c="#1f2937" metal={0.8} />
      <B p={[-1.2, 1.12, 0.36]} s={[0.26, 0.2, 0.05]} c="#374151" metal={0.8} />
      {/* monitor */}
      <B p={[0.9, 1.16, -0.2]} s={[0.06, 0.28, 0.06]} c="#1f2937" />
      <RB p={[0.9, 1.5, -0.2]} s={[0.9, 0.55, 0.05]} c="#0b0f19" />
      <Screen p={[0.9, 1.5, -0.17]} s={[0.84, 0.5]} draw={(ctx, w, h) => {
        ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
        ctx.fillStyle = "#38bdf8"; ctx.font = "600 22px sans-serif"; ctx.fillText("CMMS  WORK ORDER", 16, 34);
        ctx.fillStyle = "#e2e8f0"; ctx.font = "26px sans-serif"; ctx.fillText("M05 joint 1 bearing", 16, 82);
        ctx.fillStyle = "#fbbf24"; ctx.fillText("part: bearing_6208", 16, 122);
        ctx.fillStyle = "#22c55e"; ctx.fillText("tools ready", 16, 162);
      }} />
      <B p={[0.1, 0.96, 0.15]} s={[0.5, 0.02, 0.3]} c="#e5e7eb" />
      <B p={[-0.2, 0.97, 0.3]} s={[0.12, 0.03, 0.03]} c="#ef4444" />
    </group>
  );
}

export function S10() {
  return (
    <AtStation id="S10">
      {() => (
        <group>
          <Pad w={18} d={11} tone="#eef1f5" />
          {/* green lane through the bay */}
          <mesh position={[-2.2, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1.4, 10.6]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[-2.2, 0.076, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[1.6, 10.6]} /><meshStandardMaterial color="#facc15" roughness={0.6} transparent opacity={0.5} /></mesh>

          {/* walls: north (with a wide roller door gap) and west */}
          <B p={[-6.2, 1.75, -5.5]} s={[5.6, 3.5, 0.25]} c="#eef1f4" rough={0.8} metal={0.05} />
          <B p={[4.2, 1.75, -5.5]} s={[9.6, 3.5, 0.25]} c="#eef1f4" rough={0.8} metal={0.05} />
          <B p={[-2.2, 3.1, -5.5]} s={[3.6, 0.8, 0.25]} c="#eef1f4" rough={0.8} metal={0.05} />
          <B p={[-9, 1.75, 0]} s={[0.25, 3.5, 11]} c="#e6eaef" rough={0.8} metal={0.05} />
          <B p={[0, 0.06, -5.5]} s={[18, 0.12, 0.27]} c="#9aa7b5" />
          {/* ceiling strip light */}
          <B p={[4, 3.3, -5.3]} s={[4.5, 0.08, 0.1]} c="#ffffff" emissive="#ffffff" ei={2} shadow={false} />

          {/* lockers (west wall) */}
          {Array.from({ length: 7 }).map((_, k) => (
            <group key={k}>
              <B p={[-8.5, 1.0, -3.4 + k * 0.62]} s={[0.55, 2.0, 0.6]} c="#4f7fb8" metal={0.4} />
              <B p={[-8.21, 1.4, -3.4 + k * 0.62]} s={[0.02, 0.5, 0.48]} c="#3b6a9d" />
              <B p={[-8.21, 0.6, -3.4 + k * 0.62]} s={[0.02, 0.5, 0.48]} c="#3b6a9d" />
            </group>
          ))}
          <B p={[-8.2, 1.2, 1.4]} s={[0.04, 0.34, 0.26]} c="#22c55e" emissive="#22c55e" ei={0.3} />

          {/* tool chests, parts washer on the north wall */}
          <ToolChest p={[-6.6, 0, -4.9]} />
          <ToolChest p={[-5.2, 0, -4.9]} />
          <group position={[-3.6, 0, -4.9]}>
            <RB p={[0, 0.5, 0]} s={[1.4, 1.0, 0.8]} c="#6b7686" metal={0.5} />
            <RB p={[0, 1.05, 0]} s={[1.3, 0.14, 0.75]} c="#475569" metal={0.5} />
            <RB p={[0, 1.25, -0.25]} s={[1.3, 0.3, 0.2]} c="#6b7686" metal={0.5} rot={[-0.5, 0, 0]} />
          </group>

          {/* wall signs and lockout board */}
          <TextBoard p={[2.4, 2.45, -5.36]} s={[0.9, 0.6]} text="SAFETY FIRST" bg="#16a34a" fg="#ffffff" />
          <TextBoard p={[3.5, 2.45, -5.36]} s={[0.9, 0.6]} text="CAUTION" bg="#facc15" fg="#111827" />
          <TextBoard p={[-7.2, 2.4, -5.36]} s={[1.4, 0.9]} text="LOCK OUT" sub="TAG OUT" bg="#b91c1c" fg="#ffffff" />
          <Model name="korean_fire_extinguisher_01" position={[1.2, 0.9, -5.2]} />

          {/* workbench + technician (the scheduled technician stands at the bench front) */}
          <Bench p={[5.6, 0, -4.7]} />
          <Hazard p={[5.6, 0, -2.4]} s={[4.2, 0.5]} />
          <B p={[5.6, 0.085, -3.0]} s={[3.6, 0.02, 1.4]} c="#1f2937" rough={0.95} metal={0} shadow={false} />
          <Npc p={[5.0, 0, -3.1]} rotY={Math.PI} color="#ef4444" pose="work" seed={3} />

          {/* jib crane in the middle of the bay */}
          <group position={[1.0, 0, 0.2]}><JibCrane /></group>

          {/* spare robot joint on a blue stand */}
          <group position={[4.0, 0, 1.2]}>
            <B p={[0, 0.06, 0]} s={[2.6, 0.12, 2.0]} c="#1f2937" rough={0.95} metal={0} />
            {[[-0.8, -0.6], [0.8, -0.6], [-0.8, 0.6], [0.8, 0.6]].map(([x, z], i) => (
              <B key={i} p={[x * 0.9, 0.55, z * 0.9]} s={[0.12, 1.0, 0.12]} c={BLUE} metal={0.5} rot={[z * 0.2, 0, -x * 0.2]} />
            ))}
            <B p={[0, 1.05, 0]} s={[1.7, 0.12, 1.2]} c={BLUE} metal={0.5} />
            <Cyl p={[0, 1.5, 0]} r={0.45} h={0.7} c="#d1d5db" metal={0.7} rough={0.3} />
            <Cyl p={[0, 1.9, 0]} r={0.38} h={0.22} c="#9aa7b5" metal={0.8} rough={0.3} />
            <mesh position={[0, 1.2, 0]} rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.46, 0.05, 10, 28]} /><meshStandardMaterial color="#475569" metalness={0.8} roughness={0.3} /></mesh>
          </group>
          {/* yellow guard rails around crane and joint stand */}
          {[[2.6, -1.2, 2.6, 3.4], [2.6, 3.4, 7.0, 3.4], [7.0, 3.4, 7.0, 0.2]].map(([x0, z0, x1, z1], i) => {
            const len = Math.hypot(x1 - x0, z1 - z0);
            return (
              <group key={i}>
                <B p={[(x0 + x1) / 2, 1.0, (z0 + z1) / 2]} s={[len, 0.07, 0.07]} c={YELLOW} rot={[0, -Math.atan2(z1 - z0, x1 - x0), 0]} />
                <B p={[(x0 + x1) / 2, 0.55, (z0 + z1) / 2]} s={[len, 0.07, 0.07]} c={YELLOW} rot={[0, -Math.atan2(z1 - z0, x1 - x0), 0]} />
                {[0, 1].map((k) => <B key={k} p={[x0 + (x1 - x0) * k, 0.5, z0 + (z1 - z0) * k]} s={[0.08, 1.0, 0.08]} c={YELLOW} />)}
              </group>
            );
          })}

          {/* storage cart with bearings, rolling tool trolley, mats */}
          <Model name="industrial_storage_cart" position={[-5.2, 0, 2.4]} rotY={0.35} />
          {[[-5.6, 1.6], [-4.9, 2.6], [-4.7, 1.4]].map(([x, z], i) => (
            <Model key={i} name="cardboard_box_01" position={[x, 1.25, z]} lift={0.18} rotY={i} scale={0.8} />
          ))}
          <Npc p={[-3.7, 0, 3.2]} rotY={-2.2} color="#ef4444" pose="carry" seed={7} />
          <group position={[-1.5, 0, 3.4]}>
            <ToolChest p={[0, 0.2, 0]} />
            {[[-0.5, 0.25], [0.5, 0.25], [-0.5, -0.25], [0.5, -0.25]].map(([x, z], i) => (
              <mesh key={i} position={[x, 0.08, z]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.1, 0.1, 0.06, 12]} /><meshStandardMaterial color="#111827" /></mesh>
            ))}
          </group>
          <B p={[-4.6, 0.085, 2.2]} s={[3.2, 0.02, 2.4]} c="#1f2937" rough={0.95} metal={0} shadow={false} />
          {/* tablet charging dock */}
          <B p={[-8.5, 1.1, 2.2]} s={[0.08, 0.5, 0.4]} c="#334155" />
        </group>
      )}
    </AtStation>
  );
}
