// Animated knowledge-graph path over the plant: nodes pop up one after another, a line arcs to the next node, and a pulse keeps
// travelling along the chain until it is hidden. Beams and rings make each node visible from the overview camera.
import { useMemo, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import * as THREE from "three";
import { anchorsFor, type Anchor } from "../graphpath";
import { useTwin } from "../state";
import { Label } from "./Label";

const STEP = 1.1;      // seconds between nodes appearing

function arc(a: THREE.Vector3, b: THREE.Vector3): THREE.Vector3[] {
  const d = a.distanceTo(b);
  const h = d < 8 ? 0 : Math.min(26, d * 0.28);
  return Array.from({ length: 41 }, (_, i) => {
    const t = i / 40;
    return new THREE.Vector3().lerpVectors(a, b, t).add(new THREE.Vector3(0, h * Math.sin(Math.PI * t), 0));
  });
}

function NodeMark({ a, revealAt, t0 }: { a: Anchor; revealAt: number; t0: number }) {
  const grp = useRef<THREE.Group>(null!);
  const ring = useRef<THREE.Mesh>(null!);
  const col = useMemo(() => new THREE.Color(a.color), [a.color]);
  useFrame(() => {
    const e = (performance.now() - t0) / 1000 - revealAt;
    const k = THREE.MathUtils.clamp(e / 0.45, 0, 1);
    const pop = k < 1 ? 1 + 0.25 * Math.sin(k * Math.PI) : 1;
    grp.current.visible = e > 0;
    grp.current.scale.setScalar(Math.max(0.001, k * pop));
    ring.current.scale.setScalar(1 + 0.25 * Math.sin(performance.now() / 260));
  });
  const [x, y, z] = a.pos;
  return (
    <group ref={grp} visible={false}>
      {/* ground ring and beam: readable from far away */}
      <mesh ref={ring} position={[x, 0.2, z]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[2.2, 2.9, 40]} />
        <meshBasicMaterial color={col} transparent opacity={0.85} depthWrite={false} toneMapped={false} />
      </mesh>
      <mesh position={[x, y / 2, z]}>
        <cylinderGeometry args={[0.18, 0.18, y, 10, 1, true]} />
        <meshBasicMaterial color={col} transparent opacity={0.35} depthWrite={false} toneMapped={false} side={THREE.DoubleSide} />
      </mesh>
      <mesh position={[x, y, z]}>
        <sphereGeometry args={[0.7, 20, 16]} />
        <meshBasicMaterial color={col} toneMapped={false} />
      </mesh>
      <Label text={`${a.tag}: ${a.label}`} position={[x, y + 1.9, z]} height={3.4} bg={a.color} fg="#0b1220" />
    </group>
  );
}

function Edge({ from, to, color, revealAt, t0 }: { from: THREE.Vector3; to: THREE.Vector3; color: string; revealAt: number; t0: number }) {
  const pts = useMemo(() => arc(from, to), [from, to]);
  const curve = useMemo(() => new THREE.CatmullRomCurve3(pts), [pts]);
  const pulse = useRef<THREE.Mesh>(null!);
  const [shown, setShown] = useState(false);
  useFrame(() => {
    const e = (performance.now() - t0) / 1000 - revealAt;
    if (e > 0 && !shown) setShown(true);
    pulse.current.visible = e > 0;
    if (e > 0) pulse.current.position.copy(curve.getPoint(((e * 0.55) % 1 + 1) % 1));
  });
  return (
    <>
      {shown && <Line points={pts} color={color} lineWidth={3.2} transparent opacity={0.9} toneMapped={false} />}
      <mesh ref={pulse} visible={false}>
        <sphereGeometry args={[0.55, 14, 12]} />
        <meshBasicMaterial color="#ffffff" toneMapped={false} />
      </mesh>
    </>
  );
}

export function GraphPath() {
  const gp = useTwin((s) => s.graphPath);
  const layout = useTwin((s) => s.data)!.layout;
  const anchors = useMemo(() => (gp ? anchorsFor(layout, gp.nodes, gp.machine) : []), [gp, layout]);
  if (!gp || anchors.length === 0) return null;
  const vec = (a: Anchor) => new THREE.Vector3(...a.pos);
  return (
    <group key={gp.t0}>
      {anchors.map((a, i) => <NodeMark key={a.node.id + i} a={a} revealAt={i * STEP} t0={gp.t0} />)}
      {anchors.slice(1).map((a, i) => (
        <Edge key={a.node.id + "e" + i} from={vec(anchors[i])} to={vec(a)} color={a.color} revealAt={i * STEP + 0.35} t0={gp.t0} />
      ))}
    </group>
  );
}
