import { useMemo } from "react";
import { useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { toScene } from "../data";

type V3 = [number, number, number];

export function Model({ name, position, rotY = 0, scale = 1, lift = 0 }: { name: string; position: V3; rotY?: number; scale?: number; lift?: number }) {
  const { scene } = useGLTF(`/assets/models/${name}/${name}_1k.gltf`);
  const obj = useMemo(() => {
    const c = scene.clone(true);
    c.traverse((o) => {
      if ((o as THREE.Mesh).isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
    return c;
  }, [scene]);
  return <primitive object={obj} position={[position[0], position[1] + lift, position[2]]} rotation={[0, rotY, 0]} scale={scale} />;
}

const BOX_LIFT = 0.18; // cardboard_box_01 origin is at its middle

/** Steel rack with cardboard boxes on the shelves. Local origin = rack floor centre, rack runs along x. */
export function Rack({ position, rotY = 0, len = 4, levels = 3, seed = 1 }: { position: V3; rotY?: number; len?: number; levels?: number; seed?: number }) {
  const h = 2.4;
  const boxes: { p: V3; r: number }[] = [];
  let s = seed * 9301;
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  for (let l = 0; l < levels; l++)
    for (let i = 0; i < Math.floor(len / 0.6); i++) {
      if (rnd() < 0.2) continue;
      boxes.push({ p: [-len / 2 + 0.4 + i * 0.6, 0.2 + (l * h) / levels + 0.08, (rnd() - 0.5) * 0.15], r: (rnd() - 0.5) * 0.2 });
    }
  return (
    <group position={position} rotation={[0, rotY, 0]}>
      {[-len / 2, len / 2].flatMap((x) => [-0.4, 0.4].map((z) => (
        <mesh key={`${x}${z}`} position={[x, h / 2, z]} castShadow>
          <boxGeometry args={[0.08, h, 0.08]} />
          <meshStandardMaterial color="#2563eb" metalness={0.4} roughness={0.5} />
        </mesh>
      )))}
      {Array.from({ length: levels }).map((_, l) => (
        <mesh key={l} position={[0, 0.2 + (l * h) / levels, 0]} castShadow receiveShadow>
          <boxGeometry args={[len, 0.06, 0.9]} />
          <meshStandardMaterial color="#f97316" metalness={0.3} roughness={0.5} />
        </mesh>
      ))}
      {boxes.map((b, i) => (
        <Model key={i} name="cardboard_box_01" position={b.p} rotY={b.r} lift={BOX_LIFT} />
      ))}
    </group>
  );
}

function Pallet({ position, stack = 3, rotY = 0 }: { position: V3; stack?: number; rotY?: number }) {
  return (
    <group position={position} rotation={[0, rotY, 0]}>
      <mesh position={[0, 0.08, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.2, 0.16, 1.0]} />
        <meshStandardMaterial color="#a16207" roughness={0.9} />
      </mesh>
      {Array.from({ length: stack }).map((_, k) =>
        [-0.3, 0.3].flatMap((x) => [-0.2, 0.2].map((z) => (
          <Model key={`${k}${x}${z}`} name="cardboard_box_01" position={[x, 0.16 + k * 0.34, z]} rotY={(k % 2) * 1.57} lift={BOX_LIFT} />
        ))),
      )}
    </group>
  );
}

function Bench({ position, rotY = 0 }: { position: V3; rotY?: number }) {
  return (
    <group position={position} rotation={[0, rotY, 0]}>
      <mesh position={[0, 0.9, 0]} castShadow receiveShadow>
        <boxGeometry args={[3, 0.1, 1.1]} />
        <meshStandardMaterial color="#64748b" metalness={0.5} roughness={0.4} />
      </mesh>
      {[-1.4, 1.4].flatMap((x) => [-0.45, 0.45].map((z) => (
        <mesh key={`${x}${z}`} position={[x, 0.45, z]} castShadow>
          <boxGeometry args={[0.08, 0.9, 0.08]} />
          <meshStandardMaterial color="#1e293b" />
        </mesh>
      )))}
      <mesh position={[0.5, 1.35, -0.3]} castShadow>
        <boxGeometry args={[0.8, 0.5, 0.05]} />
        <meshStandardMaterial color="#0f172a" emissive="#38bdf8" emissiveIntensity={0.5} />
      </mesh>
    </group>
  );
}

/** Set-dressing for the support stations, placed in plant coordinates. */
export function Props() {
  const at = (x: number, z: number): V3 => {
    const [sx, sz] = toScene(x, z);
    return [sx, 0, sz];
  };
  return (
    <>
      {/* S12 spare parts cage: two racks of boxes, a hand truck */}
      <Rack position={at(58, 57.4)} len={5} seed={3} />
      <Rack position={at(58, 60.8)} len={5} seed={7} />
      <Model name="hand_truck" position={at(63.8, 55)} rotY={0.6} />
      {/* S03 parts buffer: pallets of boxes, barrels */}
      <Pallet position={at(48, 11)} stack={3} />
      <Pallet position={at(51, 11)} stack={4} rotY={0.1} />
      <Pallet position={at(54, 11)} stack={2} />
      <Pallet position={at(57, 11)} stack={3} rotY={-0.1} />
      <Model name="barrel_03" position={at(58.5, 17)} />
      <Model name="barrel_03" position={at(57.6, 18)} />
      {/* S10 maintenance bay */}
      <Bench position={at(12, 57.5)} />
      <Model name="industrial_storage_cart" position={at(19, 59)} rotY={-0.4} />
      <Model name="barrel_03" position={at(8.5, 63)} />
      {/* S01 / S02 */}
      <Model name="barrel_03" position={at(23.5, 21.5)} />
      <Model name="barrel_03" position={at(2.8, 21)} />
      <Pallet position={at(16, 17)} stack={3} />
      {/* S08 / S09 */}
      <Pallet position={at(82.5, 64)} stack={3} />
      <Pallet position={at(85, 64)} stack={2} />
      <Pallet position={at(118, 64)} stack={2} />
      {/* safety: extinguishers at the weld-cell fences and the control room */}
      {[[77, 44.5], [93, 44.5], [109, 44.5], [46.5, 56]].map(([x, z], i) => (
        <Model key={i} name="korean_fire_extinguisher_01" position={at(x, z)} rotY={i} />
      ))}
    </>
  );
}

["cardboard_box_01", "hand_truck", "industrial_storage_cart", "barrel_03", "korean_fire_extinguisher_01"].forEach((n) =>
  useGLTF.preload(`/assets/models/${n}/${n}_1k.gltf`));
