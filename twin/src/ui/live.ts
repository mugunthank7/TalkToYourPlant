import { Hero, Kpi, Status, m05Status } from "../data";
import { injectedStopSeconds, TAKT } from "../plant";

export const SHIFT_S = 8 * 3600;

export interface Live {
  units: number;
  planUnits: number;
  downMin: number;
  cost: number;
  oee: number;
  ratePerHr: number;
  status: Status;
  rulMin: number | null;
}

export function seriesName(shift: string) {
  return shift === "A" ? "hero_timely_repair" : "healthy_realistic";
}

export function liveAt(t: number, shift: string, kpi: Kpi, hero: Hero): Live {
  const s = kpi.series[seriesName(shift)];
  const i = Math.min(Math.max(Math.floor(t / 60), 0), kpi.minutes - 1);
  const j = Math.max(i - 60, 0);
  const status = m05Status(t, shift, hero);
  const failAt = kpi.summary.hero_timely_repair.t_fail_if_ignored_s ?? 0;
  const extra = injectedStopSeconds(t, shift, hero);
  const frac = extra / Math.max(t, 60);
  return {
    units: Math.max(0, Math.round(s.cum_units[i] - extra / TAKT)),
    planUnits: kpi.plan_units,
    downMin: s.cum_down_s[i] / 60 + extra / 60,
    cost: s.cum_cost[i] + (extra / 60) * kpi.cost_per_min,
    oee: s.oee[i] * Math.max(0, 1 - frac),
    ratePerHr: i - j > 0 ? ((s.cum_units[i] - s.cum_units[j]) / (i - j)) * 60 : 40,
    status,
    rulMin: shift === "A" && status === "alert" ? Math.max(0, (failAt - t) / 60) : null,
  };
}

/** Rolling units per hour at every 10 minutes, for the forecast chart. */
export function rateSeries(kpi: Kpi, shift: string): number[] {
  const s = kpi.series[seriesName(shift)].cum_units;
  const out: number[] = [];
  for (let m = 10; m <= kpi.minutes; m += 10) {
    const a = Math.max(m - 60, 0);
    out.push(((s[m - 1] - (a > 0 ? s[a - 1] : 0)) / (m - a)) * 60);
  }
  return out;
}

export const money = (v: number) => (v >= 1e6 ? `$${(v / 1e6).toFixed(2)}M` : `$${Math.round(v).toLocaleString()}`);
