import type { Hero, Layout, Person, Pt, Seg } from "./data";
import { length, route } from "./pathfind";
import { clock } from "./clock";
import { simAnim, simLink } from "./simlink";
import { useTwin } from "./state";

// ---- which station is where in the process --------------------------------------------------------
export const MAIN = ["S01", "S02", "S03", "S04", "S05", "S06", "S07", "S09"];
export const BELT = ["S04", "S05", "S06", "S07"];
const BUFFER_S = 600; // upstream/downstream buffers absorb this long
const BELT_SPEED = 0.25;
export const TAKT = 90;

export type SState = "run" | "fault" | "repair" | "starved" | "blocked" | "micro";
export interface Interval { a: number; b: number; state: SState; reason: string; machine: string }

export interface Injected {
  id: string; machine: string; machineName: string; station: string;
  t0: number; dispatchAt: number; pickupAt: number; arriveAt: number; fixAt: number; person: Person;
}

/** Repair minutes per machine type (estimates). */
const REPAIR_MIN: Record<string, number> = { weld_robot: 25, robot: 30, press: 60, fixture: 20, vision_gate: 15, gantry: 30, sealer: 30, decoiler: 40, conveyor: 30, agv: 15 };

const idx = (s: string) => MAIN.indexOf(s);

function scripted(shift: string, hero: Hero) {
  if (shift !== "A") return [];
  return [{ a: hero.t_repair_start_s, b: hero.t_repair_end_s, station: "S06", machine: "M05", arrive: hero.t_repair_start_s }];
}

function windows(shift: string, hero: Hero) {
  const inj = useTwin.getState().faults.map((f) => ({ a: f.t0, b: f.fixAt, station: f.station, machine: f.machine, arrive: f.arriveAt }));
  return [...scripted(shift, hero), ...inj];
}

/** Idle intervals (not producing) for one station, with the reason. */
export function idleIntervals(sid: string, shift: string, hero: Hero): Interval[] {
  const out: Interval[] = [];
  for (const w of windows(shift, hero)) {
    const F = w.station;
    const label = `${w.machine}`;
    if (sid === F) {
      if (w.arrive > w.a) out.push({ a: w.a, b: w.arrive, state: "fault", reason: `${label} fault`, machine: w.machine });
      out.push({ a: w.arrive, b: w.b, state: "repair", reason: `${label} under repair`, machine: w.machine });
      continue;
    }
    const iF = idx(F);
    const iS = idx(sid);
    const inBelt = BELT.includes(F);
    // when does the belt actually stop?
    let beltFrom: number | null = null;
    if (inBelt) beltFrom = w.a;
    else if (iF >= 0 && iF < idx("S04")) beltFrom = w.a + BUFFER_S + 300; // feeders starve the line after the buffer
    else if (F === "S09") beltFrom = w.a + 300;
    else if (F === "S08") beltFrom = null;
    if (beltFrom !== null && beltFrom < w.b) {
      if (BELT.includes(sid)) out.push({ a: beltFrom, b: w.b, state: iS < iF ? "blocked" : "starved", reason: `waiting on ${label}`, machine: w.machine });
      else if (sid === "S09" && F !== "S09") out.push({ a: beltFrom, b: w.b, state: "starved", reason: `starved by ${label}`, machine: w.machine });
      else if (iS >= 0 && iS < idx("S04") && iF >= idx("S04")) out.push({ a: Math.min(beltFrom + BUFFER_S, w.b), b: w.b, state: "blocked", reason: `blocked by ${label}`, machine: w.machine });
      else if (iS >= 0 && iS < idx("S04") && iF < idx("S04") && iS > iF) out.push({ a: w.a + 60, b: w.b, state: "starved", reason: `starved by ${label}`, machine: w.machine });
      else if (iS >= 0 && iS < idx("S04") && iF < idx("S04") && iS < iF) out.push({ a: beltFrom + BUFFER_S, b: w.b, state: "blocked", reason: `blocked by ${label}`, machine: w.machine });
    }
    if (F === "S09" && sid === "S08") out.push({ a: w.a + BUFFER_S, b: w.b, state: "blocked", reason: `blocked by ${label}`, machine: w.machine });
    if (F === "S09" && iS >= 0 && iS < idx("S04")) out.push({ a: w.a + BUFFER_S + 300, b: w.b, state: "blocked", reason: `blocked by ${label}`, machine: w.machine });
    if (F === "S08" && sid === "S09") out.push({ a: w.a + BUFFER_S, b: w.b, state: "starved", reason: `no battery packs (${label})`, machine: w.machine });
  }
  return out;
}

const PRIORITY: Record<SState, number> = { run: 0, micro: 1, blocked: 1, starved: 1, repair: 2, fault: 3 };

export function stationState(sid: string, t: number, shift: string, hero: Hero): { state: SState; reason: string; machine: string } {
  if (simLink.on) {
    const s = simLink.snap!.stations[sid];
    if (!s) return { state: "run", reason: "", machine: "" };
    return { state: s.state as SState, reason: s.reason, machine: s.machine ?? "" };
  }
  let best: { state: SState; reason: string; machine: string } = { state: "run", reason: "", machine: "" };
  for (const iv of idleIntervals(sid, shift, hero)) {
    if (t >= iv.a && t < iv.b && PRIORITY[iv.state] >= PRIORITY[best.state]) best = { state: iv.state, reason: iv.reason, machine: iv.machine };
  }
  return best;
}

/** Time this station has actually been running up to t (animations use this so they freeze when the station is idle). */
export function animT(sid: string, t: number, shift: string, hero: Hero): number {
  if (simLink.on) return simAnim(sid);
  let lost = 0;
  const ivs = idleIntervals(sid, shift, hero).sort((x, y) => x.a - y.a);
  let cursor = 0;
  for (const iv of ivs) {
    const a = Math.max(iv.a, cursor);
    const b = Math.min(iv.b, t);
    if (b > a) { lost += b - a; cursor = b; }
  }
  return t - lost;
}

/** Belt time: the conveyor and the cars on it stand still while any belt-stopping fault is active. */
export function beltTime(t: number, shift: string, hero: Hero): number {
  if (simLink.on) return simLink.beltT + (simLink.snap!.belt.moving ? Math.min(2, Math.max(0, t - simLink.snap!.t)) : 0);
  const stops: [number, number][] = [];
  for (const w of windows(shift, hero)) {
    const iF = idx(w.station);
    let from: number | null = null;
    if (BELT.includes(w.station)) from = w.a;
    else if (iF >= 0 && iF < idx("S04")) from = w.a + BUFFER_S + 300;
    else if (w.station === "S09") from = w.a + 300;
    if (from !== null && from < w.b) stops.push([from, w.b]);
  }
  stops.sort((x, y) => x[0] - y[0]);
  let lost = 0, cursor = 0;
  for (const [a0, b0] of stops) {
    const a = Math.max(a0, cursor), b = Math.min(b0, t);
    if (b > a) { lost += b - a; cursor = b; }
  }
  return t - lost;
}

/** Total seconds the line was stopped by injected faults up to t (for KPI adjustments). */
export function injectedStopSeconds(t: number, shift: string, hero: Hero): number {
  const saved = useTwin.getState().faults;
  if (!saved.length) return 0;
  let lost = 0, cursor = 0;
  const stops: [number, number][] = saved.map((f) => {
    const iF = idx(f.station);
    const from = BELT.includes(f.station) ? f.t0 : iF >= 0 && iF < idx("S04") ? f.t0 + BUFFER_S + 300 : f.station === "S09" ? f.t0 + 300 : f.fixAt;
    return [from, f.fixAt] as [number, number];
  }).sort((x, y) => x[0] - y[0]);
  for (const [a0, b0] of stops) {
    const a = Math.max(a0, cursor), b = Math.min(b0, t);
    if (b > a) { lost += b - a; cursor = b; }
  }
  void shift; void hero;
  return lost;
}

export type Andon = "ok" | "warn" | "bad";
export function andonOf(sid: string, t: number, shift: string, hero: Hero): Andon {
  if (simLink.on && sid === "S06" && simLink.snap!.machines.M05?.alert === "critical" && simLink.snap!.stations.S06.state === "run") return "bad";
  const s = stationState(sid, t, shift, hero).state;
  if (s === "fault") return "bad";
  if (s === "repair" || s === "starved" || s === "blocked" || s === "micro") return "warn";
  if (sid === "S06" && shift === "A" && t >= hero.t_alert_s && t < hero.t_repair_start_s) return "bad";
  return "ok";
}

// ---- forecast ---------------------------------------------------------------------------------------
export interface Forecast { level: "ok" | "watch" | "risk"; text: string; etaMin?: number }

const PACE_UTIL: Record<string, number> = { S04: 85 / TAKT, S05: 70 / TAKT, S06: 70 / TAKT, S07: 55 / TAKT, S08: 80 / TAKT, S09: 75 / TAKT, S02: 70 / TAKT };

export function forecastFor(sid: string, t: number, shift: string, hero: Hero): Forecast {
  if (simLink.on && sid === "S06") {
    const m = simLink.snap!.machines.M05;
    if (m?.reset) return { level: "ok", text: "Bearing replaced, wear reset" };
    if (m?.alert === "critical") return { level: "risk", etaMin: Math.round((m.rul_s ?? 0) / 60), text: `Bearing wear: failure in ~${Math.round((m.rul_s ?? 0) / 60)} min if left, line will slow first` };
    if (m?.alert === "watch") return { level: "watch", text: "Vibration trending up, bottleneck risk soon" };
  }
  const f = hero.fault;
  if (sid === "S06" && shift === "A" && f) {
    const progress = (tt: number) => Math.min(1, Math.max(0, (tt - f.onset_s) / f.ramp_s));
    const failAt = f.onset_s + f.ramp_s;
    if (t >= hero.t_repair_end_s) return { level: "ok", text: "Bearing replaced, wear reset" };
    if (t >= hero.t_repair_start_s) return { level: "ok", text: "Under repair" };
    if (t >= f.onset_s) {
      const slow = Math.round(0.3 * progress(t + 3600) * 100);
      const eta = Math.max(0, Math.round((failAt - t) / 60));
      return { level: t >= hero.t_alert_s ? "risk" : "watch", etaMin: eta, text: `Bearing wear: line slows ~${slow}% within 1 h, failure in ~${eta} min if left` };
    }
    if (t >= f.onset_s - 1800) return { level: "watch", text: "Vibration trending up, bottleneck risk soon" };
  }
  const u = PACE_UTIL[sid];
  if (u !== undefined && u >= 0.9) return { level: "watch", text: `Pacing station: ${Math.round(u * 100)}% of takt, any slowdown stops the line` };
  return { level: "ok", text: "" };
}

// ---- injecting faults -------------------------------------------------------------------------------
export function makeInjected(layout: Layout, machineId: string, t0: number): Injected {
  const m = layout.machines.find((x) => x.id === machineId)!;
  const speed = 1.3;
  const dispatchAt = t0 + 300;
  const toSpares = route(layout, "S10.in", "S12.in");
  const toStation = route(layout, "S12.in", `${m.station}.in`);
  const back = route(layout, `${m.station}.in`, "S10.in");
  const pickupAt = dispatchAt + length(toSpares) / speed;
  const arriveAt = pickupAt + 90 + length(toStation) / speed;
  const repairS = (REPAIR_MIN[m.type] ?? 30) * 60;
  const fixAt = arriveAt + repairS;
  const st = layout.stations.find((s) => s.id === m.station)!;
  const home = layout.stations.find((s) => s.id === "S10")!;
  const mk = (kind: string, s: number, e: number, anim: Seg["anim"], extra: Partial<Seg> = {}): Seg => ({ k: kind, s, e, anim, ...extra });
  const walkSeg = (s: number, p: Pt[], to: string): Seg => mk("walk", s, s + length(p) / speed, "walk", { path: p, to });
  const tl: Seg[] = [];
  tl.push(mk("desk", 0, dispatchAt, "idle", { station: "S10", at: home.access, face: [home.x, home.z] }));
  tl.push(walkSeg(dispatchAt, toSpares, "S12"));
  const spares = layout.stations.find((s) => s.id === "S12")!;
  tl.push(mk("pickup", pickupAt - 0, pickupAt + 90, "work", { station: "S12", at: spares.access, face: [spares.x, spares.z] }));
  tl.push(walkSeg(pickupAt + 90, toStation, m.station));
  tl.push(mk("repair", arriveAt, fixAt, "crouch", { station: m.station, at: st.access, face: [st.x, st.z] }));
  tl.push(walkSeg(fixAt, back, "S10"));
  const backEnd = tl[tl.length - 1].e;
  tl.push(mk("desk", backEnd, 1e9, "idle", { station: "S10", at: home.access, face: [home.x, home.z] }));
  const person: Person = { employee_id: `ON-CALL-${machineId}`, name: "On-call technician", role: "technician", shift: "A", home_station: "S10", timeline: tl };
  return { id: `F-${machineId}-${Math.round(t0)}`, machine: machineId, machineName: m.name, station: m.station, t0, dispatchAt, pickupAt, arriveAt, fixAt, person };
}

export const andonFor = (sid: string) => () => {
  const st = useTwin.getState();
  return andonOf(sid, clock.t, st.shift, st.data!.hero);
};
/** Whole-plant andon (control room): worst state of any station. */
export const andonPlant = () => {
  const st = useTwin.getState();
  let worst: Andon = "ok";
  for (const s of st.data!.layout.stations) {
    const a = andonOf(s.id, clock.t, st.shift, st.data!.hero);
    if (a === "bad") return "bad" as Andon;
    if (a === "warn") worst = "warn";
  }
  return worst;
};

/** A technician walking for an engine work order: desk -> spares -> machine -> repair -> desk. */
export function responderFromWO(layout: Layout, wo: { id: string; machine: string; station: string; dispatch_at: number; arrived_at: number | null; closed_at: number | null; repair_s: number }): Person {
  const speed = 1.3;
  const toSpares = route(layout, "S10.in", "S12.in");
  const toStation = route(layout, "S12.in", `${wo.station}.in`);
  const back = route(layout, `${wo.station}.in`, "S10.in");
  const home = layout.stations.find((s) => s.id === "S10")!;
  const spares = layout.stations.find((s) => s.id === "S12")!;
  const st = layout.stations.find((s) => s.id === wo.station)!;
  const d0 = wo.dispatch_at;
  const pick = d0 + length(toSpares) / speed;
  const arrive = wo.arrived_at ?? pick + 90 + length(toStation) / speed;
  const fix = wo.closed_at ?? arrive + wo.repair_s;
  const mk = (kind: string, s: number, e: number, anim: Seg["anim"], extra: Partial<Seg> = {}): Seg => ({ k: kind, s, e, anim, ...extra });
  const walk = (s: number, p: Pt[], to: string): Seg => mk("walk", s, s + length(p) / speed, "walk", { path: p, to });
  const tl: Seg[] = [mk("desk", 0, d0, "idle", { station: "S10", at: home.access, face: [home.x, home.z] }), walk(d0, toSpares, "S12"),
    mk("pickup", pick, pick + 90, "work", { station: "S12", at: spares.access, face: [spares.x, spares.z] }), walk(pick + 90, toStation, wo.station),
    mk("repair", arrive, fix, "crouch", { station: wo.station, at: st.access, face: [st.x, st.z] }), walk(fix, back, "S10")];
  tl.push(mk("desk", tl[tl.length - 1].e, 1e9, "idle", { station: "S10", at: home.access, face: [home.x, home.z] }));
  // make the first segments contiguous even if the walk to spares ends before the pickup start
  for (let i = 1; i < tl.length; i++) tl[i].s = tl[i - 1].e;
  tl[tl.length - 1].e = 1e9;
  return { employee_id: `ON-CALL-${wo.id}`, name: "On-call technician", role: "technician", shift: "A", home_station: "S10", timeline: tl };
}
