// Live connection to the SimPy engine (sim/). When connected, station states, the belt, KPIs, work orders and
// fault injection come from the engine instead of the client-side approximation in plant.ts.
import { clock, ctl } from "./clock";
import { useTwin } from "./state";

export interface SimSnap {
  t: number;
  stations: Record<string, { state: string; reason: string; machine: string | null; mode: string; utilization: number }>;
  machines: Record<string, { state: string; alert?: string | null; rul_s?: number; rul_range_s?: [number, number]; contributors?: { signal: string; shap: number }[]; anomaly?: { score: number; thresholds: { watch: number; critical: number } }; vib_multiple?: number; reset?: boolean; sensors: Record<string, number> }>;
  belt: { moving: boolean; cars: { k: number; stage: string; d_m?: number; progress?: number; build?: number; exit?: number; loc: string }[]; speed_mult: number };
  kpis: { units: number; good_units: number; oee: number; availability: number; performance: number; quality: number; downtime_min: number; downtime_cost_usd: number; throughput_per_hour: number; plan_units: number };
  alerts: { t: number; severity: string; text: string; machine: string; rul_s?: number }[];
  work_orders: { id: string; machine: string; station: string; kind: string; status: string; opened_at: number; dispatch_at: number; arrived_at: number | null; closed_at: number | null; repair_s: number }[];
  buffers: Record<string, number>;
}

export const simLink = {
  snap: null as SimSnap | null,
  base: "http://localhost:8000",
  anim: {} as Record<string, number>,
  beltT: 0,
  lastT: 0,
  lastMsgClock: 0,
  ws: null as WebSocket | null,
  get on() { return this.snap !== null && useTwin.getState().sim === "on"; },
};

export function connectSim(url = "ws://localhost:8000/ws") {
  const set = useTwin.getState().setSim;
  if (simLink.ws) return;
  set("connecting");
  const ws = new WebSocket(url);
  simLink.ws = ws;
  simLink.base = url.replace(/^ws/, "http").replace(/\/ws$/, "");
  ws.onopen = () => {
    clock.linked = true;
    ctl.send = (m) => ws.readyState === 1 && ws.send(JSON.stringify(m));
    ctl.send({ type: "control", action: clock.playing ? "play" : "pause", speed: clock.speed });   // the engine starts paused: adopt what the UI shows
    set("on");
  };
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.type === "state") {
      if (typeof m.playing === "boolean") clock.playing = m.playing;     // the engine is the source of truth for play and speed
      if (typeof m.speed === "number") clock.speed = m.speed;
      const prev = simLink.snap;
      const dt = prev ? m.t - prev.t : 0;
      if (prev && dt > 0 && dt < 300) {
        for (const [sid, st] of Object.entries(prev.stations)) if (st.state === "run") simLink.anim[sid] = (simLink.anim[sid] ?? 0) + dt;
        if (prev.belt.moving) simLink.beltT += dt;
      } else if (!prev || dt < 0) {
        simLink.anim = {}; simLink.beltT = m.t;
        for (const sid of Object.keys(m.stations)) simLink.anim[sid] = m.t;
      }
      simLink.snap = m as SimSnap;
      simLink.lastT = m.t;
      simLink.lastMsgClock = performance.now();
      // keep the twin clock locked to the engine, smoothly
      const drift = m.t - clock.t;
      if (Math.abs(drift) > Math.max(3, clock.speed * 0.5)) clock.t = m.t;
      else clock.t += drift * 0.25;
    }
  };
  ws.onclose = () => { simLink.ws = null; simLink.snap = null; clock.linked = false; ctl.send = null; set("off"); };
  ws.onerror = () => ws.close();
}

export function disconnectSim() {
  simLink.ws?.close();
}

export async function simPost(path: string, body: unknown) {
  const r = await fetch(`${simLink.base}${path}`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}

/** Animation time of a station: seconds it has actually been running (freezes while it is not). */
export function simAnim(sid: string): number {
  const s = simLink.snap;
  if (!s) return clock.t;
  const base = simLink.anim[sid] ?? s.t;
  const running = s.stations[sid]?.state === "run";
  return base + (running ? Math.min(2, Math.max(0, clock.t - s.t)) : 0);
}

(globalThis as unknown as { __sim: () => SimSnap | null }).__sim = () => (simLink.on ? simLink.snap : null);
