import { useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { camera as camGoal, clock } from "./clock";
import { loadAll } from "./data";
import { useTwin } from "./state";
import { Conveyor, Floor, SafetyZones, Stations, Walkways } from "./scene/Plant";
import { Machines } from "./scene/Machines";
import { People } from "./scene/People";
import { Hud } from "./ui/Hud";

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

function Scene() {
  return (
    <>
      <color attach="background" args={["#cfd8e3"]} />
      <fog attach="fog" args={["#cfd8e3", 160, 340]} />
      <hemisphereLight args={["#ffffff", "#8a94a0", 0.9]} />
      <directionalLight
        position={[60, 90, 40]}
        intensity={1.6}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-100}
        shadow-camera-right={100}
        shadow-camera-top={70}
        shadow-camera-bottom={-70}
        shadow-camera-far={300}
      />
      <Floor />
      <Walkways />
      <SafetyZones />
      <Stations />
      <Conveyor />
      <Machines />
      <People />
      <CameraRig />
      <OrbitControls makeDefault target={[0, 0, 4]} maxPolarAngle={Math.PI / 2.1} minDistance={15} maxDistance={220} />
    </>
  );
}

export default function App() {
  const { data, error, setData, setError } = useTwin();

  useEffect(() => {
    loadAll().then(setData).catch((e) => setError(String(e.message ?? e)));
  }, [setData, setError]);

  if (error) return <div className="msg">{error}</div>;
  if (!data) return <div className="msg">Loading plant data...</div>;

  return (
    <>
      <Canvas shadows camera={{ position: [0, 62, 74], fov: 45, near: 0.5, far: 600 }} dpr={[1, 2]}>
        <Clock />
        <Scene />
      </Canvas>
      <Hud />
    </>
  );
}
