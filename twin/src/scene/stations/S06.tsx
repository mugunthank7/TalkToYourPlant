import { Billboard } from "@react-three/drei";
import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { clock } from "../../clock";
import { m05Status, vibMultiple } from "../../data";
import { useTwin } from "../../state";
import { Andon, AtStation, B, CellFence, Cyl, Hazard, Npc, Pad, RB, Screen, TextBoard } from "../kit";
import { Robot } from "./common";

export function S06() {
  const data = useTwin((s) => s.data)!;
  const status = () => m05Status(clock.t, useTwin.getState().shift, data.hero);
  const alertGroup = useRef<THREE.Group>(null!);
  const halo = useRef<THREE.MeshBasicMaterial>(null!);
  useFrame(() => {
    const st = status();
    const on = st === "alert";
    alertGroup.current.visible = on || st === "repair";
    if (halo.current) halo.current.opacity = on ? 0.1 + 0.07 * Math.sin(performance.now() / 160) : 0.06;
  });

  const trend = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#b91c1c"; ctx.font = "700 22px sans-serif"; ctx.fillText("M05 vibration", 14, 30);
    ctx.strokeStyle = "#ef4444"; ctx.lineWidth = 4; ctx.beginPath();
    const t0 = Math.max(0, clock.t - 3600);
    for (let i = 0; i <= 40; i++) {
      const t = t0 + (i / 40) * Math.max(clock.t - t0, 1);
      const v = (vibMultiple(t, data.hero) - 1) / 2.6;
      const x = 18 + (i / 40) * (w - 36), y = h - 18 - v * (h - 70);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.fillStyle = "#475569"; ctx.font = "18px sans-serif"; ctx.fillText(`${vibMultiple(clock.t, data.hero).toFixed(1)}x baseline`, 14, h - 2);
  };

  return (
    <AtStation id="S06">
      {() => (
        <group>
          <Pad w={12} d={11} tone="#eef1f5" />
          <mesh position={[-5.7, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.6, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <mesh position={[5.7, 0.075, 0]} rotation={[-Math.PI / 2, 0, 0]}><planeGeometry args={[0.6, 10.4]} /><meshStandardMaterial color="#22c55e" roughness={0.6} /></mesh>
          <Hazard p={[0, 0.0, 5.1]} s={[10, 0.4]} />

          <CellFence w={12} d={11} gate={[1.2, 1.8]} />

          {/* hero: white M05 on the south side, two orange robots north */}
          <Robot p={[0.4, 0, 2.9]} id="M05" absX={100} color="#f1f5f9" hero />
          <Robot p={[-2.8, 0, -3.0]} rotY={Math.PI} id="M05b" absX={100} />
          <Robot p={[2.8, 0, -3.0]} rotY={Math.PI} id="M05c" absX={100} />

          {/* labels that follow the camera */}
          <Billboard position={[0.4, 3.7, 2.9]}>
            <TextBoard p={[0, 0.34, 0]} s={[1.5, 0.42]} text="M05 Weld robot 2" bg="#f8fafc" fg="#0f172a" />
            <TextBoard p={[0, -0.12, 0]} s={[1.5, 0.38]} text="joint 1 bearing" bg="#f8fafc" fg="#475569" />
          </Billboard>

          {/* alert effects: halo, banner, callout, trend panel */}
          <group ref={alertGroup} visible={false}>
            <mesh position={[0.4, 1.8, 2.9]}>
              <sphereGeometry args={[2.6, 24, 16]} />
              <meshBasicMaterial ref={halo} color="#ff2a2a" transparent opacity={0.12} depthWrite={false} blending={THREE.AdditiveBlending} />
            </mesh>
            <Billboard position={[0.4, 6.4, 0.5]}>
              <TextBoard p={[0, 0, 0]} s={[5.6, 0.7]} text="ALERT: weld robot 2 bearing wear detected" bg="#b91c1c" fg="#ffffff" emissive />
            </Billboard>
            <Billboard position={[2.9, 3.6, 3.3]}>
              <TextBoard p={[0, 0, 0]} s={[1.7, 0.4]} text="m05_joint1_bearing" bg="#fef2f2" fg="#b91c1c" />
            </Billboard>
            <Billboard position={[-2.2, 4.3, 3.6]}>
              <B p={[0, 0, -0.03]} s={[2.5, 1.5, 0.04]} c="#ffffff" />
              <Screen p={[0, 0, 0]} s={[2.4, 1.4]} draw={trend} bright={1.0} />
            </Billboard>
          </group>

          {/* controller cabinet, monitor, operator, supervisor look-out */}
          <group position={[-4.6, 0, 3.8]}>
            <RB p={[0, 1.0, 0]} s={[1.1, 2.0, 0.7]} c="#eef1f5" metal={0.2} rough={0.4} />
            <B p={[0.3, 1.2, 0.36]} s={[0.35, 0.5, 0.03]} c="#0f172a" />
          </group>
          <group position={[3.6, 0, 3.6]}>
            <B p={[-0.5, 0.6, 0]} s={[0.08, 1.2, 0.08]} c="#1d5fd0" />
            <B p={[0.5, 0.6, 0]} s={[0.08, 1.2, 0.08]} c="#1d5fd0" />
            <RB p={[0, 1.5, 0]} s={[1.5, 0.9, 0.06]} c="#0b0f19" r={0.03} />
            <Screen p={[0, 1.5, 0.035]} s={[1.4, 0.8]} draw={(ctx, w, h) => {
              ctx.fillStyle = "#f8fafc"; ctx.fillRect(0, 0, w, h);
              ctx.fillStyle = "#334155"; ctx.font = "700 22px sans-serif"; ctx.fillText("WELD MONITOR  CELL B", 14, 32);
              for (let i = 0; i < 12; i++) { ctx.fillStyle = "#22c55e"; ctx.fillRect(18 + i * 36, h - 30 - (30 + ((i * 29) % 80)), 24, 30 + ((i * 29) % 80)); }
            }} />
          </group>
          <Npc p={[2.2, 0, 4.7]} rotY={Math.PI} color="#f97316" pose="stand" seed={4} />

          <Andon p={[5.2, 0, -4.8]} state={() => { const s = status(); return s === "alert" ? "bad" : s === "repair" ? "warn" : "ok"; }} />
          <Andon p={[-5.2, 0, 4.8]} state={() => { const s = status(); return s === "alert" ? "bad" : s === "repair" ? "warn" : "ok"; }} />
          <Cyl p={[-5.4, 0.5, -5.2]} r={0.1} h={1.0} c="#facc15" metal={0.2} />
        </group>
      )}
    </AtStation>
  );
}
