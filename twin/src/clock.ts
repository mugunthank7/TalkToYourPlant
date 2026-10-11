// Mutable simulation clock, read every frame by the scene (no React re-renders).
export const clock = { t: 0, speed: 60, playing: true, max: 8 * 3600 };

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
      if (clock.t >= clock.max) clock.t = 0;
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

// Camera shortcuts: scene coordinates (plant coords minus plant centre).
export const camera = {
  goal: null as null | { pos: [number, number, number]; target: [number, number, number] },
};
export const VIEWS = {
  Overview: { pos: [0, 92, 104], target: [0, 0, 4] },
  "Weld cells": { pos: [30, 20, 26], target: [30, 0, -4] },
  "Maintenance bay": { pos: [-44, 18, 44], target: [-42, 0, 22] },
} as const;
