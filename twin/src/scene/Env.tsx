import { useLayoutEffect, useMemo } from "react";
import { Environment, useTexture } from "@react-three/drei";
import * as THREE from "three";
import { useTwin } from "../state";

const T = "/assets/textures";

/** Load a Poly Haven 1k PBR set (diff / rough / nor) and tile it. repeat = tiles across the surface. */
export function usePBR(name: string, repeatX: number, repeatY: number) {
  const t = useTexture({
    map: `${T}/${name}/${name}_diff_1k.jpg`,
    roughnessMap: `${T}/${name}/${name}_rough_1k.jpg`,
    normalMap: `${T}/${name}/${name}_nor_1k.jpg`,
  });
  useLayoutEffect(() => {
    Object.values(t).forEach((x) => {
      x.wrapS = x.wrapT = THREE.RepeatWrapping;
      x.repeat.set(repeatX, repeatY);
      x.anisotropy = 8;
      x.needsUpdate = true;
    });
    t.map.colorSpace = THREE.SRGBColorSpace;
  }, [t, repeatX, repeatY]);
  return t;
}

export function Env() {
  return <Environment files="/assets/hdri/small_hangar_01_1k.hdr" background backgroundBlurriness={0.45} backgroundIntensity={0.9} environmentIntensity={0.7} />;
}

const C34 = `${T}/concrete034/Concrete034_1K-JPG_`;

/** Sealed, glossy light-grey epoxy-style floor, slightly larger than the plant so the walls sit on it. */
export function ConcreteFloor() {
  const { plant } = useTwin((s) => s.data)!.layout;
  const w = plant.width_m + 8;
  const d = plant.depth_m + 8;
  const t = useTexture({ map: `${C34}Color.jpg`, roughnessMap: `${C34}Roughness.jpg`, normalMap: `${C34}NormalGL.jpg` });
  useLayoutEffect(() => {
    Object.values(t).forEach((x) => {
      x.wrapS = x.wrapT = THREE.RepeatWrapping;
      x.repeat.set(w / 7, d / 7);
      x.anisotropy = 8;
      x.needsUpdate = true;
    });
    t.map.colorSpace = THREE.SRGBColorSpace;
  }, [t, w, d]);
  const normalScale = useMemo(() => new THREE.Vector2(0.3, 0.3), []);
  const tint = useMemo(() => new THREE.Color(1.45, 1.47, 1.52), []);
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[w, d]} />
      <meshPhysicalMaterial {...t} color={tint} roughness={0.7} metalness={0.0} clearcoat={0.5} clearcoatRoughness={0.3} normalScale={normalScale} />
    </mesh>
  );
}
