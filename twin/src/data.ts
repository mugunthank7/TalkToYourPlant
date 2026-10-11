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
  walk_graph: { nodes: { id: string; x: number; z: number }[]; edges: [string, string][] };
}
export interface Hero {
  t_onset_s: number;
  t_alert_s: number;
  t_dispatch_s: number;
  t_pickup_s: number;
  t_repair_start_s: number;
  t_repair_end_s: number;
}
export interface KpiSeries { cum_units: number[]; cum_down_s: number[]; cum_cost: number[]; oee: number[] }
export interface ScenarioSummary {
  units: number; units_lost_vs_ideal: number; downtime_min: number; downtime_cost_usd: number; oee: number;
  t_fail_if_ignored_s?: number; remaining_useful_life_at_alert_min?: number; about: string;
}
export interface Kpi {
  minutes: number; plan_units: number; cost_per_min: number;
  series: Record<string, KpiSeries>; summary: Record<string, ScenarioSummary>;
}
export interface TwinData { layout: Layout; schedule: Schedule; hero: Hero; kpi: Kpi }

export async function loadAll(): Promise<TwinData> {
  const get = async (f: string) => {
    const r = await fetch(`/data/${f}`);
    if (!r.ok) throw new Error(`Could not load /data/${f}. Run the generator with --copy-to ../twin/public/data`);
    return r.json();
  };
  const [layout, schedule, hero, kpi] = await Promise.all([get("layout.json"), get("schedule.json"), get("events.json"), get("kpi.json")]);
  return { layout, schedule, hero, kpi };
}

// The plant origin is its NW corner; scene is centred on the plant middle.
export const CENTER: Pt = [80, 45];
export const toScene = (x: number, z: number): [number, number] => [x - CENTER[0], z - CENTER[1]];

export type Status = "healthy" | "alert" | "repair" | "repaired";
export function m05Status(t: number, shift: string, h: Hero): Status {
  if (shift !== "A") return "healthy";
  if (t < h.t_alert_s) return "healthy";
  if (t < h.t_repair_start_s) return "alert";
  if (t < h.t_repair_end_s) return "repair";
  return "repaired";
}
