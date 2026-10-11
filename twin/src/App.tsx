import { Suspense, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, PerformanceMonitor } from "@react-three/drei";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { camera as camGoal, clock } from "./clock";
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
    const L = 276, R = 352, T = 52, B = 184;
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

function CameraRig() {
  const { camera, controls } = useThree();
  useFrame(() => {
    const g = camGoal.goal;
    if (!g || !controls) return;
    const oc = controls as unknown as OrbitControlsImpl;
    goalPos.set(...g.pos);
    goalTarget.set(...g.target);
    camera.position.lerp(goalPos, 0.08);
    oc.target.lerp(goalTarget, 0.08);
    oc.update();
    if (camera.position.distanceTo(goalPos) < 0.3) camGoal.goal = null;
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
      <SafetyZones />
      <Cells />
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
  const [low, setLow] = useState(new URLSearchParams(location.search).get("q") === "low");

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
        <PerformanceMonitor onDecline={() => setLow(true)} flipflops={0} />
        <Scene low={low} />
      </Canvas>
      <Hud />
      </div>
      {view === "dash" && <Dashboard />}
    </>
  );
}
