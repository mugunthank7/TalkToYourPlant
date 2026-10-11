import { Suspense, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, PerformanceMonitor } from "@react-three/drei";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { camera as camGoal, clock } from "./clock";
import { loadAll } from "./data";
import { useTwin } from "./state";
import { Conveyor, Floor, SafetyZones, Stations, Walkways } from "./scene/Plant";
import { Machines } from "./scene/Machines";
import { People } from "./scene/People";
import { Hud } from "./ui/Hud";
import { Env } from "./scene/Env";
import { Cells } from "./scene/Cells";
import { Props } from "./scene/Props";
import { Bloom, EffectComposer } from "@react-three/postprocessing";

function Clock() {
  useFrame((_, dt) => {
    if (clock.playing) {
      clock.t += Math.min(dt, 0.1) * clock.speed;
      if (clock.t >= clock.max) clock.t = 0;
    }
  });
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
      <color attach="background" args={["#cfd8e3"]} />
      <fog attach="fog" args={["#cfd8e3", 160, 340]} />
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
      </Suspense>
      <Walkways />
      <SafetyZones />
      <Cells />
      <Stations />
      <Conveyor />
      <Machines />
      <People />
      {!low && (
        <EffectComposer multisampling={0}>
          <Bloom intensity={0.9} luminanceThreshold={0.9} luminanceSmoothing={0.2} mipmapBlur />
        </EffectComposer>
      )}
      <CameraRig />
      <OrbitControls makeDefault target={[0, 0, 8]} maxPolarAngle={Math.PI / 2.1} minDistance={15} maxDistance={220} />
    </>
  );
}

export default function App() {
  const { data, error, setData, setError } = useTwin();
  const [low, setLow] = useState(new URLSearchParams(location.search).get("q") === "low");

  useEffect(() => {
    loadAll().then(setData).catch((e) => setError(String(e.message ?? e)));
  }, [setData, setError]);

  if (error) return <div className="msg">{error}</div>;
  if (!data) return <div className="msg">Loading plant data...</div>;

  return (
    <>
      <Canvas shadows camera={{ position: [0, 76, 92], fov: 45, near: 0.5, far: 600 }} dpr={low ? 1 : [1, 1.75]}>
        <PerformanceMonitor onDecline={() => setLow(true)} flipflops={0} />
        <Clock />
        <Scene low={low} />
      </Canvas>
      <Hud />
    </>
  );
}
