// Shared material-flow timing. Everything is a pure function of the sim clock, so scrubbing,
// jumping and speed changes always show a consistent line.
export const TAKT = 90;            // seconds between car bodies
export const BELT_SPEED = 0.25;    // m/s on the main conveyor
export const CAR_SLOTS = 5;

/** Distance (m) along the conveyor for the car in a given slot at time t. May be negative or past the end. */
export function carDistance(slot: number, t: number): { k: number; d: number } {
  // Car k enters the conveyor at k * TAKT. Slot i handles k = i, i+N, i+2N ...
  const k = slot + CAR_SLOTS * Math.floor((t / TAKT - slot) / CAR_SLOTS);
  return { k, d: (t - k * TAKT) * BELT_SPEED };
}

/** True when any car is within `r` metres of distance `at` along the belt (robot cells use this to spark). */
export function carNear(at: number, t: number, r = 4): boolean {
  for (let s = 0; s < CAR_SLOTS; s++) {
    const { d } = carDistance(s, t);
    if (Math.abs(d - at) < r) return true;
  }
  return false;
}

export const smooth = (a: number, b: number, x: number) => {
  const u = Math.min(1, Math.max(0, (x - a) / (b - a)));
  return u * u * (3 - 2 * u);
};
