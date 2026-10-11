// Mutable simulation clock, read every frame by the scene (no React re-renders).
export const clock = { t: 0, speed: 60, playing: true, max: 8 * 3600 };

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
  Overview: { pos: [0, 76, 92], target: [0, 0, 8] },
  "Weld cells": { pos: [42, 24, 30], target: [42, 0, 0] },
  "Maintenance bay": { pos: [-50, 22, 55], target: [-48, 0, 24] },
} as const;
