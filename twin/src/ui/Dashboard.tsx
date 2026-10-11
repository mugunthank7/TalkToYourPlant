import { useEffect, useMemo, useState } from "react";
import { clock } from "../clock";
import type { KpiSeries, ScenarioSummary } from "../data";
import { m05Status } from "../data";
import { useTwin } from "../state";
import { Bar, Columns, ForecastChart, Gauge, HBars, LineChart, Series } from "./charts";
import { money, rateSeries, seriesName, SHIFT_S } from "./live";

const SCEN: { key: string; label: string; color: string }[] = [
  { key: "ideal", label: "Ideal", color: "#94a3b8" },
  { key: "healthy_realistic", label: "Healthy (realistic)", color: "#22c55e" },
  { key: "hero_timely_repair", label: "Fault: repaired on alert", color: "#38bdf8" },
  { key: "hero_delayed_repair", label: "Fault: repaired 40 min late", color: "#f59e0b" },
  { key: "hero_ignored", label: "Fault: ignored", color: "#ef4444" },
];

function useTick(ms = 300) {
  const [, set] = useState(0);
  useEffect(() => {
    const id = setInterval(() => set((n) => n + 1), ms);
    return () => clearInterval(id);
  }, [ms]);
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;
const hrs = (v: number) => `${v.toFixed(1)} h`;

function Tile({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone?: "ok" | "warn" | "bad" }) {
  return (
    <div className={`tile ${tone ?? ""}`}>
      <small>{label}</small>
      <b>{value}</b>
      {sub && <span>{sub}</span>}
    </div>
  );
}

function Card({ title, note, children, wide }: { title: string; note?: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <div className={`dcard ${wide ? "wide" : ""}`}>
      <div className="dcard-h"><b>{title}</b>{note && <small>{note}</small>}</div>
      {children}
    </div>
  );
}

export function Dashboard() {
  const { data, shift } = useTwin();
  const [on, setOn] = useState<Record<string, boolean>>({ ideal: true, healthy_realistic: true, hero_timely_repair: true, hero_delayed_repair: false, hero_ignored: true });
  useTick();
  const dash = data?.dash;
  const kpi = data?.kpi;

  const live = shift === "A" ? "hero_timely_repair" : "healthy_realistic";
  const s: KpiSeries | undefined = kpi?.series[seriesName(shift)];
  const i = Math.min(Math.floor(clock.t / 60), (kpi?.minutes ?? 480) - 1);
  const cursor = clock.t / SHIFT_S;

  const lines: Series[] = useMemo(() => {
    if (!kpi) return [];
    return SCEN.filter((c) => on[c.key]).map((c) => ({ name: c.label, color: c.color, values: kpi.series[c.key].cum_units.filter((_, k) => k % 4 === 0), dashed: c.key === "ideal" }));
  }, [kpi, on]);
  const oeeLines: Series[] = useMemo(() => {
    if (!kpi) return [];
    return SCEN.filter((c) => on[c.key] && c.key !== "ideal").map((c) => ({ name: c.label, color: c.color, values: kpi.series[c.key].oee.filter((_, k) => k % 4 === 0) }));
  }, [kpi, on]);

  const rates = useMemo(() => (kpi ? rateSeries(kpi, shift) : []), [kpi, shift]);

  if (!data || !kpi || !s) return <div className="dash"><div className="msg">Loading…</div></div>;
  if (!dash) return <div className="dash"><div className="msg">Run the generator without --skip-history to create dashboard.json</div></div>;

  const status = m05Status(clock.t, shift, data.hero);
  const A = s.avail[i], P = s.perf[i], Q = s.qual[i], OEE = s.oee[i];
  const units = s.cum_units[i];
  const elapsed = Math.max(clock.t, 60);
  const projected = Math.round((units / elapsed) * SHIFT_S);
  const sum = kpi.summary;
  const timely = sum.hero_timely_repair, ignored = sum.hero_ignored;
  const alertLive = shift === "A" && status === "alert";
  const rul = alertLive ? Math.max(0, ((timely.t_fail_if_ignored_s ?? 0) - clock.t) / 60) : null;

  const nowIdx = Math.min(Math.floor(clock.t / 600), rates.length - 1);
  const tail = rates.slice(Math.max(nowIdx - 5, 0), nowIdx + 1);
  const mean = tail.reduce((a, b) => a + b, 0) / Math.max(tail.length, 1);
  const sd = Math.sqrt(tail.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(tail.length, 1));
  const fc = rates.map((v, k) => (k <= nowIdx ? v : mean));

  const causes: Bar[] = Object.entries(dash.downtime_h_by_cause).map(([k, v]) => ({ label: k.replace(/_/g, " "), value: v }));
  const byMachine: Bar[] = Object.entries(dash.downtime_h_by_machine).sort((a, b) => b[1] - a[1]).map(([k, v]) => {
    const m = dash.machines.find((x) => x.id === k);
    return { label: `${k} ${m?.name ?? ""}`, value: v, color: "#f59e0b" };
  });
  const months: Bar[] = Object.entries(dash.downtime_h_by_month).map(([k, v]) => ({ label: k, value: v, color: "#a78bfa" }));

  const sh = dash.shifts;
  const barColors = sh.map((r) => (r.had_incident ? "#ef4444" : r.weekday === 5 ? "#64748b" : "#3b82f6"));
  const maint = dash.maintenance;

  const row = (key: string) => {
    const x = sum[key] as ScenarioSummary;
    return x;
  };

  return (
    <div className="dash">
      <div className="dash-inner">
        <div className="dash-title">
          <h2>Plant KPIs <span>Shift {shift}, clock at {Math.floor(clock.t / 3600)}h {Math.floor((clock.t % 3600) / 60)}m of 8h</span></h2>
          <div className="scrub">
            <input type="range" min={0} max={SHIFT_S} step={30} value={clock.t} onChange={(e) => { clock.t = Number(e.target.value); }} />
            {shift === "A" && <button onClick={() => { clock.t = data.hero.t_alert_s + 60; }}>Jump to alert</button>}
          </div>
          <div className="chips2">
            {SCEN.map((c) => (
              <button key={c.key} className={on[c.key] ? "on" : ""} style={{ borderColor: on[c.key] ? c.color : undefined }} onClick={() => setOn({ ...on, [c.key]: !on[c.key] })}>
                <i style={{ background: c.color }} /> {c.label}
              </button>
            ))}
          </div>
        </div>

        <div className="tiles">
          <Tile label="OEE (so far)" value={pct(OEE)} sub="availability x performance x quality" tone={OEE > 0.8 ? "ok" : OEE > 0.65 ? "warn" : "bad"} />
          <Tile label="Availability" value={pct(A)} sub={`${(s.cum_down_s[i] / 60).toFixed(0)} min line stopped`} />
          <Tile label="Performance" value={pct(P)} sub="speed vs 90 s takt" />
          <Tile label="Quality" value={pct(Q)} sub={`${s.cum_scrap[i]} scrap units`} />
          <Tile label="Units" value={`${units} / ${kpi.plan_units}`} sub={`projected ${projected} at this pace`} />
          <Tile label="Downtime cost" value={money(s.cum_cost[i])} sub={`$${kpi.cost_per_min.toLocaleString()} per minute`} tone="bad" />
          <Tile label="Weld robot 2" value={alertLive ? "ALERT" : status === "repair" ? "Repair" : "Healthy"} sub={rul !== null ? `RUL ${Math.ceil(rul)} min to failure` : "bearing wear model"} tone={alertLive ? "bad" : status === "repair" ? "warn" : "ok"} />
          <Tile label="12-month downtime" value={hrs(maint.unplanned_line_down_h)} sub={`${money(maint.line_downtime_cost_usd)} line cost`} />
        </div>

        <div className="dgrid">
          <Card title="Cumulative output vs ideal" note="units, one shift" wide>
            <LineChart series={lines} cursor={cursor} yMax={340} />
            <div className="lg">{lines.map((l) => <span key={l.name}><i style={{ background: l.color }} />{l.name}</span>)}</div>
          </Card>
          <Card title="OEE over the shift" note="cumulative">
            <LineChart series={oeeLines} cursor={cursor} yMax={1} yFmt={(v) => `${Math.round(v * 100)}%`} />
          </Card>

          <Card title="Where the OEE goes" note="loss waterfall, now">
            <Waterfall A={A} P={P} Q={Q} />
          </Card>
          <Card title="Throughput forecast" note="units per hour, rest of shift">
            <div className="chart2"><ForecastChart actual={rates} forecast={fc} band={Math.max(sd * 2, 3)} nowIdx={nowIdx} ymax={60} /></div>
          </Card>
          <Card title="What-if: acting on the alert" note="whole shift">
            <div className="cmp">
              {([["Repair on alert", timely, "#38bdf8"], ["Ignore it", ignored, "#ef4444"]] as const).map(([name, x, col]) => (
                <div key={name} className="cmpcol" style={{ borderColor: col }}>
                  <b>{name}</b>
                  <div><span>Units</span><em>{x.units}</em></div>
                  <div><span>OEE</span><em>{pct(x.oee)}</em></div>
                  <div><span>Downtime</span><em>{Math.round(x.downtime_min)} min</em></div>
                  <div><span>Cost</span><em>{money(x.downtime_cost_usd)}</em></div>
                </div>
              ))}
            </div>
            <div className="callout">Waiting costs {money(ignored.downtime_cost_usd - timely.downtime_cost_usd)} and {timely.units - ignored.units} units. At the alert there are about {timely.remaining_useful_life_at_alert_min} minutes before weld robot 2 would fail.</div>
          </Card>

          <Card title="Last 30 days: units per shift" note="red = shift with a degradation incident, grey = Saturday" wide>
            <Columns bars={sh.map((r) => r.units)} colors={barColors} plan={sh.map((r) => r.demand_plan_units)} line={sh.map((r) => r.oee)} yMax={340} />
            <div className="lg"><span><i style={{ background: "#3b82f6" }} />normal</span><span><i style={{ background: "#ef4444" }} />incident</span><span><i style={{ background: "#fbbf24" }} />OEE (line)</span><span><i style={{ background: "#fff" }} />plan</span></div>
          </Card>
          <Card title="Line downtime per month" note="hours, last 12 months">
            <HBars items={months} fmt={(v) => `${v} h`} />
          </Card>

          <Card title="Downtime by cause" note="Pareto, unplanned, hours (12 months)">
            <HBars items={causes} fmt={(v) => `${v} h`} />
          </Card>
          <Card title="Downtime by machine" note="line-down hours (12 months)">
            <HBars items={byMachine} fmt={(v) => `${v} h`} />
          </Card>
          <Card title="Scenario comparison" note="same shift, different decisions">
            <table className="tbl">
              <thead><tr><th>Scenario</th><th>Units</th><th>OEE</th><th>Down</th><th>Cost</th></tr></thead>
              <tbody>
                {SCEN.map((c) => {
                  const x = row(c.key);
                  return (
                    <tr key={c.key} className={c.key === live ? "hl" : ""}>
                      <td><i style={{ background: c.color }} className="dot2" /> {c.label}</td>
                      <td>{x.units}</td><td>{pct(x.oee)}</td><td>{Math.round(x.downtime_min)} min</td><td>{money(x.downtime_cost_usd)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          <Card title="Machine health" note="12 months, estimated" wide>
            <table className="tbl">
              <thead><tr><th>Machine</th><th>Station</th><th>Now</th><th>Failures</th><th>MTBF (h)</th><th>MTTR (min)</th><th>Line down (h)</th><th>Health</th></tr></thead>
              <tbody>
                {dash.machines.filter((m) => dash.maintenance.per_machine[m.id]).map((m) => {
                  const st = dash.maintenance.per_machine[m.id];
                  const hot = m.id === "M05" && alertLive;
                  const rep = m.id === "M05" && status === "repair";
                  const health = Math.max(5, Math.min(100, Math.round(100 - st.failures * 7 - st.line_down_h * 1.2)));
                  const h = hot ? Math.max(8, Math.round((rul ?? 0) / 0.6)) : health;
                  return (
                    <tr key={m.id} className={hot ? "alertrow" : ""}>
                      <td><b>{m.id}</b> {m.name}</td>
                      <td>{m.station}</td>
                      <td><span className={`badge ${hot ? "bad" : rep ? "warn" : "ok"}`}>{hot ? "Alert" : rep ? "Repair" : "Running"}</span></td>
                      <td>{st.failures}</td><td>{st.mtbf_h_observed}</td><td>{st.mttr_min ?? "-"}</td><td>{st.line_down_h}</td>
                      <td><div className="hb"><div style={{ width: `${h}%`, background: h > 66 ? "#22c55e" : h > 40 ? "#f59e0b" : "#ef4444" }} /></div></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
          <Card title="Degradation incidents" note="last 30 days">
            <table className="tbl">
              <thead><tr><th>Date</th><th>Machine</th><th>Outcome</th><th>Margin at alert</th></tr></thead>
              <tbody>
                {dash.incidents.map((x) => (
                  <tr key={x.shift_id}>
                    <td>{x.date.slice(5)} {x.shift}</td>
                    <td>{x.machine_id}</td>
                    <td><span className={`badge ${x.outcome === "failure" ? "bad" : x.outcome === "late" ? "warn" : "ok"}`}>{x.outcome}</span></td>
                    <td>{Math.round((x.failure_s_if_ignored - x.alert_s) / 60)} min</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="callout">Emergency share of repairs (12 months): {Math.round(maint.emergency_share_of_corrective * 100)}%. Planned repairs after an alert are about 4x cheaper in line time.</div>
          </Card>
        </div>
        <div className="dash-foot">All numbers are synthetic. Downtime cost: Siemens, The True Cost of Downtime 2024 ($2.3M per hour for a large automotive plant). See docs/SOURCES.md.</div>
      </div>
    </div>
  );
}

function Waterfall({ A, P, Q }: { A: number; P: number; Q: number }) {
  const availLoss = 1 - A;
  const perfLoss = A * (1 - P);
  const qualLoss = A * P * (1 - Q);
  const oee = A * P * Q;
  const steps = [
    { label: "Ideal", from: 0, to: 1, color: "#94a3b8" },
    { label: "Availability loss", from: 1 - availLoss, to: 1, color: "#ef4444" },
    { label: "Performance loss", from: 1 - availLoss - perfLoss, to: 1 - availLoss, color: "#f59e0b" },
    { label: "Quality loss", from: oee, to: oee + qualLoss, color: "#a78bfa" },
    { label: "Actual OEE", from: 0, to: oee, color: "#22c55e" },
  ];
  return (
    <div className="wf">
      {steps.map((s) => (
        <div key={s.label} className="wfrow">
          <span>{s.label}</span>
          <div className="wft"><div style={{ left: `${s.from * 100}%`, width: `${Math.max((s.to - s.from) * 100, 0.8)}%`, background: s.color }} /></div>
          <em>{s.label === "Ideal" || s.label === "Actual OEE" ? `${(s.to * 100).toFixed(1)}%` : `-${((s.to - s.from) * 100).toFixed(1)} pts`}</em>
        </div>
      ))}
    </div>
  );
}
