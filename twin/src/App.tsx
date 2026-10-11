import { Suspense, useEffect, useMemo, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { camera as camGoal, clock } from "./clock";
import { beltTime } from "./plant";
import { CAR_SLOTS, carDistance } from "./flow";
import { buildShots } from "./ui/shots";
import { TOUR } from "./ui/shots";
import { poseAt } from "./scene/People";
import { loadAll, toScene } from "./data";
import { useTwin } from "./state";
import { Floor, SafetyZones, Stations, Walkways } from "./scene/Plant";
import { Conveyor, Logistics } from "./scene/Flow";
import { Machines } from "./scene/Machines";
import { People } from "./scene/People";
import { Hud } from "./ui/Hud";
import { TopBar } from "./ui/TopBar";
import { Dashboard } from "./ui/Dashboard";
import { Env } from "./scene/Env";
import { Building } from "./scene/Building";
import { Cells } from "./scene/Cells";
import { Props } from "./scene/Props";
import { StationModels } from "./scene/stations";
import { Bloom, EffectComposer } from "@react-three/postprocessing";

/** Shift the render so the plant sits in the free area between the HUD panels. */
function ViewFit() {
  const { camera, size } = useThree();
  useEffect(() => {
    const L = 276, R = 352, T = 52, B = 150;
    const cx = (L + size.width - R) / 2;
    const cy = (T + size.height - B) / 2;
    const cam = camera as THREE.PerspectiveCamera;
    cam.setViewOffset(size.width, size.height, size.width / 2 - cx, size.height / 2 - cy, size.width, size.height);
    return () => cam.clearViewOffset();
  }, [camera, size]);
  return null;
}

/** ?station=S11 starts zoomed on that station; &clean=1 hides the HUD for clean screenshots. */
function UrlView() {
  const { camera, controls } = useThree();
  const data = useTwin((s) => s.data)!;
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    if (q.get("clean")) document.body.classList.add("clean");
    const id = q.get("station");
    const st = data.layout.stations.find((s) => s.id === id);
    if (!st || !controls) return;
    const [x, z] = toScene(st.x, st.z);
    const k = Math.max(st.w, st.d) * 0.95;
    camera.position.set(x + (Number(q.get("dx")) || 0), k * 0.85, z + k * 0.95);
    (controls as unknown as OrbitControlsImpl).target.set(x, 0.5, z);
    (controls as unknown as OrbitControlsImpl).update();
    camera.clearViewOffset();
  }, [camera, controls, data]);
  return null;
}

const goalPos = new THREE.Vector3();
const goalTarget = new THREE.Vector3();
const tmpPos = new THREE.Vector3();
const tmpTarget = new THREE.Vector3();

function CameraRig() {
  const { camera, controls } = useThree();
  const data = useTwin((s) => s.data)!;
  const shots = useMemo(() => buildShots(data.layout), [data]);
  useFrame(() => {
    if (!controls) return;
    const oc = controls as unknown as OrbitControlsImpl;
    const st = useTwin.getState();
    const mode = camGoal.mode;
    let desiredPos: THREE.Vector3 | null = null;
    let desiredTarget: THREE.Vector3 | null = null;
    let k = 0.08;

    if (mode === "orbit") {
      const ang = performance.now() / 24000;
      desiredPos = tmpPos.set(Math.sin(ang) * 100, 58, Math.cos(ang) * 96 + 4);
      desiredTarget = tmpTarget.set(0, 0, 4);
      k = 0.04;
    } else if (mode === "tour") {
      const idx = Math.floor(performance.now() / 8000) % TOUR.length;
      if (idx !== camGoal.tourIdx) {
        camGoal.tourIdx = idx;
        const shot = shots.find((s) => s.name === TOUR[idx]);
        if (shot) camGoal.goal = { pos: [...shot.pos], target: [...shot.target] };
      }
      k = 0.035;
    } else if (mode === "follow-car") {
      const cp = data.layout.conveyor_path;
      const [x0, z0] = toScene(cp[0][0], cp[0][1]);
      const len = cp[1][0] - cp[0][0];
      const bt = beltTime(clock.t, st.shift, data.hero);
      let best = -1, bd = -1;
      for (let s = 0; s < CAR_SLOTS; s++) {
        const { d } = carDistance(s, bt);
        if (d >= 0 && d <= len - 4 && d > bd) { bd = d; best = s; }
      }
      if (best >= 0) {
        desiredTarget = tmpTarget.set(x0 + bd, 1.4, z0);
        desiredPos = tmpPos.set(x0 + bd - 7, 5.5, z0 + 10);
        k = 0.1;
      }
    } else if (mode === "follow-tech") {
      const resp = st.faults.find((f) => clock.t >= f.t0 - 5 && clock.t < f.fixAt + 240);
      const person = resp ? resp.person : st.data!.schedule.shifts[st.shift].find((p) => p.role === "technician");
      if (person) {
        const ps = poseAt(person, clock.t);
        const [sx, sz] = toScene(ps.x, ps.z);
        desiredTarget = tmpTarget.set(sx, 1.2, sz);
        desiredPos = tmpPos.set(sx + 6, 5, sz + 9);
        k = 0.12;
      }
    }

    if (desiredPos && desiredTarget) {
      camera.position.lerp(desiredPos, k);
      oc.target.lerp(desiredTarget, k);
      oc.update();
      return;
    }
    const g = camGoal.goal;
    if (!g) return;
    goalPos.set(...g.pos);
    goalTarget.set(...g.target);
    camera.position.lerp(goalPos, k);
    oc.target.lerp(goalTarget, k);
    oc.update();
    if (mode !== "tour" && camera.position.distanceTo(goalPos) < 0.3) camGoal.goal = null;
  });
  return null;
}

function Scene({ low }: { low: boolean }) {
  return (
    <>

      <hemisphereLight args={["#ffffff", "#8a94a0", 0.9]} />
      <directionalLight
        position={[60, 90, 40]}
        intensity={1.6}
        castShadow
        shadow-mapSize={low ? [1024, 1024] : [2048, 2048]}
        shadow-camera-left={-100}
        shadow-camera-right={100}
        shadow-camera-top={70}
        shadow-camera-bottom={-70}
        shadow-camera-far={300}
      />
      <Suspense fallback={null}>
        <Env />
        <Floor />
        <Props />
        <StationModels />
        <Building />
      </Suspense>
      <Walkways />
      <Stations />
      <Conveyor />
      <Logistics />
      <Machines />
      <People />
      {!low && (
        <EffectComposer multisampling={0}>
          <Bloom intensity={0.9} luminanceThreshold={0.9} luminanceSmoothing={0.2} mipmapBlur />
        </EffectComposer>
      )}
      {new URLSearchParams(location.search).get("station") ? <UrlView /> : <ViewFit />}
      <CameraRig />
      <OrbitControls makeDefault target={[0, 0, 4]} maxPolarAngle={Math.PI / 2.1} minDistance={15} maxDistance={220} />
    </>
  );
}

export default function App() {
  const { data, error, setData, setError, view } = useTwin();
  const low = new URLSearchParams(location.search).get("q") === "low";      // only when asked for in the URL; never switched on automatically

  useEffect(() => {
    loadAll().then(setData).catch((e) => setError(String(e.message ?? e)));
  }, [setData, setError]);

  if (error) return <div className="msg">{error}</div>;
  if (!data) return <div className="msg">Loading plant data...</div>;

  return (
    <>
      <TopBar />
      <div style={{ position: "fixed", inset: 0, display: view === "live" ? "block" : "none" }}>
      <Canvas frameloop={view === "live" ? "always" : "never"} shadows camera={{ position: [0, 92, 104], fov: 45, near: 0.5, far: 600 }} dpr={low ? 1 : [1, 1.75]}>
        <Scene low={low} />
      </Canvas>
      <Hud />
      </div>
      {view === "dash" && <Dashboard />}
    </>
  );
}
