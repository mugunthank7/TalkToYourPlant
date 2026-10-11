import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

function paint(canvas: HTMLCanvasElement, text: string, bg: string, fg: string, font: number) {
  const ctx = canvas.getContext("2d")!;
  const f = `600 ${font}px Inter, Helvetica, Arial, sans-serif`;
  ctx.font = f;
  canvas.width = Math.ceil(ctx.measureText(text).width) + 28;
  canvas.height = font + 22;
  ctx.font = f;
  ctx.fillStyle = bg;
  ctx.beginPath();
  ctx.roundRect(0, 0, canvas.width, canvas.height, 12);
  ctx.fill();
  ctx.fillStyle = fg;
  ctx.textBaseline = "middle";
  ctx.fillText(text, 14, canvas.height / 2 + 2);
}

interface Props {
  text: string;
  position: [number, number, number];
  height?: number;
  bg?: string;
  fg?: string;
}

export function Label({ text, position, height = 1.4, bg = "rgba(255,255,255,0.9)", fg = "#0f172a" }: Props) {
  const { tex, aspect } = useMemo(() => {
    const c = document.createElement("canvas");
    paint(c, text, bg, fg, 40);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return { tex: t, aspect: c.width / c.height };
  }, [text, bg, fg]);
  const ref = useRef<THREE.Sprite>(null!);
  const { camera } = useThree();
  const tmp = useMemo(() => new THREE.Vector3(), []);
  useFrame(() => {
    ref.current.getWorldPosition(tmp);
    const k = Math.min(1, Math.max(0.28, camera.position.distanceTo(tmp) / 85));
    ref.current.scale.set(height * k * aspect, height * k, 1);
  });
  return (
    <sprite ref={ref} position={position} scale={[height * aspect, height, 1]} renderOrder={10}>
      <spriteMaterial map={tex} depthTest={false} transparent />
    </sprite>
  );
}

/** A label whose text changes at runtime (people's current activity). */
export function LiveLabel({ getText, position, height = 0.8, near = 24 }: { getText: () => string; position: [number, number, number]; height?: number; near?: number }) {
  const { camera } = useThree();
  const tmp = useMemo(() => new THREE.Vector3(), []);
  const sprite = useRef<THREE.Sprite>(null!);
  const state = useMemo(() => {
    const canvas = document.createElement("canvas");
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    return { canvas, tex, last: "" };
  }, []);
  useFrame(() => {
    sprite.current.getWorldPosition(tmp);
    const near_ = camera.position.distanceTo(tmp) < near;
    sprite.current.visible = near_;
    if (!near_) return;
    const text = getText();
    if (text === state.last) return;
    state.last = text;
    paint(state.canvas, text, "rgba(15,23,42,0.8)", "#ffffff", 36);
    state.tex.needsUpdate = true;
    sprite.current.scale.set((height * state.canvas.width) / state.canvas.height, height, 1);
  });
  return (
    <sprite ref={sprite} position={position} renderOrder={11}>
      <spriteMaterial map={state.tex} depthTest={false} transparent />
    </sprite>
  );
}
