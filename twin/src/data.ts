export type Pt = [number, number];

export interface Seg {
  k: string;
  s: number;
  e: number;
  anim: "walk" | "work" | "crouch" | "idle";
  path?: Pt[];
  at?: Pt;
  face?: Pt;
  station?: string;
  task?: string | null;
  to?: string;
}
export interface Person {
  employee_id: string;
  name: string;
  role: string;
  shift: string;
  home_station: string;
  timeline: Seg[];
}
export interface Schedule {
  meta: { shift_seconds: number; takt_s: number };
  shifts: Record<string, Person[]>;
}
export interface Station { id: string; name: string; x: number; z: number; w: number; d: number; access: Pt; machines: string[] }
export interface Machine { id: string; name: string; type: string; station: string; x: number; z: number; rot_deg: number }
export interface Layout {
  plant: { width_m: number; depth_m: number };
  stations: Station[];
  machines: Machine[];
  conveyor_path: Pt[];
  safety_zones: { station: string; x: number; z: number; w: number; d: number }[];
  gate: Pt;
  logistics?: { id: string; name: string; vehicle: string; load: string; period_s: number; speed_mps: number; route: Pt[] }[];
  walk_graph: { nodes: { id: string; x: number; z: number }[]; edges: [string, string][] };
}
export interface Hero {
  fault?: { onset_s: number; ramp_s: number; tau_s: number; vib_gain: number };
  t_onset_s: number;
  t_alert_s: number;
  t_dispatch_s: number;
  t_pickup_s: number;
  t_repair_start_s: number;
  t_repair_end_s: number;
}
export interface KpiSeries { cum_units: number[]; cum_down_s: number[]; cum_cost: number[]; oee: number[]; avail: number[]; perf: number[]; qual: number[]; cum_scrap: number[] }
export interface ScenarioSummary {
  units: number; units_lost_vs_ideal: number; downtime_min: number; downtime_cost_usd: number; oee: number;
  t_fail_if_ignored_s?: number; remaining_useful_life_at_alert_min?: number; about: string;
}
export interface Kpi {
  minutes: number; plan_units: number; cost_per_min: number;
  series: Record<string, KpiSeries>; summary: Record<string, ScenarioSummary>;
}
export interface ShiftRow { shift_id: string; date: string; weekday: number; shift: string; units: number; demand_plan_units: number; oee: number; availability: number; performance: number; quality: number; downtime_min: number; downtime_cost_usd: number; scrap_units: number; had_incident: boolean }
export interface Incident { shift_id: string; date: string; shift: string; machine_id: string; component_id: string; onset_s: number; alert_s: number; failure_s_if_ignored: number; outcome: string; repair_start_s: number | null; repair_end_s: number }
export interface MachineStat { failures: number; mtbf_h_observed: number; mttr_min: number | null; line_down_h: number }
export interface DashboardData {
  machines: { id: string; name: string; type: string; station: string }[];
  scenario_summary: Record<string, ScenarioSummary>;
  shifts: ShiftRow[];
  incidents: Incident[];
  maintenance: { unplanned_line_down_h: number; planned_line_down_h: number; maintenance_cost_usd: number; line_downtime_cost_usd: number; corrective_work_orders: number; emergency_share_of_corrective: number; per_machine: Record<string, MachineStat> };
  downtime_h_by_machine: Record<string, number>;
  downtime_h_by_cause: Record<string, number>;
  downtime_h_by_month: Record<string, number>;
}
export interface TwinData { layout: Layout; schedule: Schedule; hero: Hero; kpi: Kpi; dash: DashboardData | null }

export async function loadAll(): Promise<TwinData> {
  const get = async (f: string) => {
    const r = await fetch(`/data/${f}`);
    if (!r.ok) throw new Error(`Could not load /data/${f}. Run the generator with --copy-to ../twin/public/data`);
    return r.json();
  };
  const [layout, schedule, hero, kpi] = await Promise.all([get("layout.json"), get("schedule.json"), get("events.json"), get("kpi.json")]);
  const dash = await get("dashboard.json").catch(() => null);
  return { layout, schedule, hero, kpi, dash };
}

// The plant origin is its NW corner; scene is centred on the plant middle.
export const CENTER: Pt = [64, 36];
export const toScene = (x: number, z: number): [number, number] => [x - CENTER[0], z - CENTER[1]];

export type Status = "healthy" | "alert" | "repair" | "repaired";
export function m05Status(t: number, shift: string, h: Hero): Status {
  if (shift !== "A") return "healthy";
  if (t < h.t_alert_s) return "healthy";
  if (t < h.t_repair_start_s) return "alert";
  if (t < h.t_repair_end_s) return "repair";
  return "repaired";
}

/** Vibration as a multiple of baseline for the hero bearing (mirrors the generator's degradation model). */
export function vibMultiple(t: number, h: Hero): number {
  const f = h.fault;
  if (!f) return 1;
  const x = Math.min(1, Math.max(0, (t - f.onset_s) / f.ramp_s));
  const k = f.ramp_s / f.tau_s;
  return 1 + f.vib_gain * ((Math.exp(x * k) - 1) / (Math.exp(k) - 1));
}
