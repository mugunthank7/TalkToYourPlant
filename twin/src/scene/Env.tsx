import { useLayoutEffect } from "react";
import { Environment, useTexture } from "@react-three/drei";
import * as THREE from "three";
import { useTwin } from "../state";

const C = "/assets/textures/concrete034/Concrete034_1K-JPG_";

export function Env() {
  return <Environment files="/assets/hdri/small_hangar_01_1k.hdr" environmentIntensity={0.5} />;
}

export function ConcreteFloor() {
  const { plant } = useTwin((s) => s.data)!.layout;
  const t = useTexture({ map: `${C}Color.jpg`, normalMap: `${C}NormalGL.jpg`, roughnessMap: `${C}Roughness.jpg` });
  useLayoutEffect(() => {
    Object.values(t).forEach((x) => {
      x.wrapS = x.wrapT = THREE.RepeatWrapping;
      x.repeat.set(plant.width_m / 4, plant.depth_m / 4);
      x.anisotropy = 8;
    });
    t.map.colorSpace = THREE.SRGBColorSpace;
    t.map.needsUpdate = true;
  }, [t, plant]);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[plant.width_m, plant.depth_m]} />
      <meshStandardMaterial {...t} color="#d4d8de" roughness={0.9} normalScale={new THREE.Vector2(0.6, 0.6)} />
    </mesh>
  );
}
