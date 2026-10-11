// Mutable simulation clock, read every frame by the scene (no React re-renders).
export const clock = { t: 0, speed: 60, playing: true, max: 8 * 3600, linked: false };

// When the SimPy engine is connected, these controls go to the engine; otherwise they are local.
export const ctl = {
  send: null as null | ((msg: Record<string, unknown>) => void),
  play(v: boolean) { clock.playing = v; this.send?.({ type: "control", action: v ? "play" : "pause" }); },
  speed(v: number) { clock.speed = v; this.send?.({ type: "control", speed: v }); },
  seek(t: number) { clock.t = Math.max(0, t); this.send?.({ type: "control", action: "seek", t: Math.max(0, t) }); },
};

let started = false;
/** Advance the sim clock from a plain timer so the dashboard tab keeps time while the 3D canvas is paused. */
export function startClock() {
  if (started) return;
  started = true;
  let last = performance.now();
  setInterval(() => {
    const now = performance.now();
    const dt = Math.min((now - last) / 1000, 0.25);
    last = now;
    if (clock.playing) {
      clock.t += dt * clock.speed;
      if (clock.t >= clock.max) { if (clock.linked) clock.t = clock.max; else clock.t = 0; }
    }
  }, 33);
}

export function fmt(t: number, shift: string): string {
  const start = shift === "A" ? 6 : 14;
  const s = Math.floor(t);
  const h = Math.floor(s / 3600) + start;
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

// Camera: shots are scene coordinates (plant coordinates minus the plant centre).
export type Shot = { name: string; pos: [number, number, number]; target: [number, number, number]; note: string };
export const camera = {
  goal: null as null | { pos: [number, number, number]; target: [number, number, number] },
  mode: "free" as "free" | "tour" | "orbit" | "follow-car" | "follow-tech",
  tourIdx: -1,
};
export const stationShot = (cx: number, cz: number, size: number, k = 0.95): { pos: [number, number, number]; target: [number, number, number] } =>
  ({ pos: [cx, size * k * 0.85, cz + size * k], target: [cx, 0.5, cz] });
