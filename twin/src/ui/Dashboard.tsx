import { useEffect, useMemo, useState, type ReactNode } from "react";
import { clock, ctl } from "../clock";
import type { KpiSeries, ScenarioSummary } from "../data";
import { m05Status } from "../data";
import { injectedStopSeconds, TAKT } from "../plant";
import { useTwin } from "../state";
import { Bar, ColMeta, Columns, ForecastChart2, HBars, LineChart, Series, WithTip } from "./charts";
import { Help, type HelpText } from "./Help";
import { AnomalyScores, ScoreHistory, StationLoad, WhyFlagged, WorkOrders, useAnomaly } from "./EngineCards";
import { simLink } from "../simlink";
import { money, rateSeries, seriesName, SHIFT_S } from "./live";

const SCEN: { key: string; label: string; color: string }[] = [
  { key: "ideal", label: "Ideal", color: "#94a3b8" },
  { key: "healthy_realistic", label: "Healthy (realistic)", color: "#22c55e" },
  { key: "hero_timely_repair", label: "Fault: repaired on alert", color: "#38bdf8" },
  { key: "hero_delayed_repair", label: "Fault: repaired 40 min late", color: "#f59e0b" },
  { key: "hero_ignored", label: "Fault: ignored", color: "#ef4444" },
];

const H: Record<string, HelpText> = {
  oee: { title: "OEE", what: "Overall Equipment Effectiveness: the share of the ideal output the line really delivers.", read: "Availability x Performance x Quality. 85%+ is world class, below 60% is poor. Colour: green > 80%, amber 65-80%, red below.", why: "One number that captures stops, slow cycles and scrap together." },
  avail: { title: "Availability", what: "Share of time the line was actually running.", read: "100% minus the minutes the line was stopped. The caption shows the minutes lost.", why: "Stops are the biggest and most expensive loss in a car plant." },
  perf: { title: "Performance", what: "How fast the line runs compared with the 90 s target cycle (takt).", read: "100% = on takt. Below 100% means machines are slowed, for example a worn robot derating itself.", why: "Slow running quietly costs as much as stopping." },
  qual: { title: "Quality", what: "Share of cars that come out right the first time.", read: "Scrap units are cars rejected at inspection. Worn robots weld worse, so quality drops with wear.", why: "Scrap wastes material, energy and the whole line time already spent." },
  units: { title: "Units", what: "Cars completed so far this shift against the shift plan of 320.", read: "The caption projects the end-of-shift total at the current pace.", why: "The plan is the promise to the customer." },
  cost: { title: "Downtime cost", what: "Money lost to line stops: stopped minutes x $38,000.", read: "Climbs whenever the line is stopped. The figure is from Siemens' 2024 True Cost of Downtime report for a large automotive plant.", why: "Makes the business case for fixing things before they break." },
  anomaly: { title: "Anomaly detector", what: "Score from a machine-learning model (Isolation Forest) trained only on healthy data, per machine, updated every minute.", read: "Each bar is how unlike a healthy machine at the same load this one looks. Amber = watch, red = critical (both must persist several minutes, so noise does not alarm).", why: "Finds wear while vibration is still only 5% above normal, hours before the old 2x rule." },
  scorehist: { title: "Score history", what: "The last hour of anomaly scores for the flagged machine (or M05).", read: "A steady climb through the dashed thresholds is real wear; a single spike is noise.", why: "Shows how early and how clearly the model saw it." },
  why: { title: "Why it was flagged", what: "Shapley values: how much each signal pushed the score up versus a healthy machine.", read: "The longest bar is the main evidence. The interval is the predicted remaining useful life (80% confidence).", why: "An alert the team can check against the machine, not a black box." },
  load: { title: "Station load", what: "Share of time each station has been working, from the engine.", read: "Blue = running, amber = repair, red = fault, yellow = starved or blocked.", why: "Shows where the line is waiting." },
  wos: { title: "Work orders", what: "Maintenance orders raised in the engine and how far they have got.", read: "Predictive orders come from the detector; emergency ones from a breakdown.", why: "Closes the loop from alert to repair." },
  robot: { title: "Weld robot 2", what: "Health of the hero machine from its bearing-wear model.", read: "Healthy, then ALERT with the remaining useful life (RUL) in minutes before it would fail, then Repair.", why: "RUL is the window in which acting is cheap." },
  year: { title: "12-month downtime", what: "Unplanned line-down hours over the last year (estimated).", read: "Hours of line stoppage, and the cost at $38,000 per minute.", why: "The scale of the problem the system addresses." },
  cum: { title: "Cumulative output vs ideal", what: "Cars completed over the shift for each scenario. The dashed grey line is the ideal.", read: "The gap below the ideal is lost output. Toggle scenarios with the chips above. The white dashed line marks the current clock.", why: "Shows what each decision costs in cars, not just in dollars." },
  oeeline: { title: "OEE over the shift", what: "Running OEE for each scenario as the shift progresses.", read: "A dip at a stop that slowly recovers. The ignored fault falls furthest.", why: "Shows how long a single failure keeps hurting the numbers." },
  waterfall: { title: "Where the OEE goes", what: "A loss waterfall: ideal 100% minus availability, performance and quality losses equals actual OEE.", read: "Longest red or amber bar is your biggest loss. Hover a row for its meaning.", why: "Tells you which kind of loss to attack first." },
  forecast: { title: "Throughput forecast", what: "Units per hour: solid = past, dashed = the rest of the shift under two decisions.", read: "Blue = we repair when the alert fires. Red = we ignore it. The shaded gap is the cost of waiting. Hover for exact values.", why: "Turns an alert into a number a manager can act on." },
  whatif: { title: "What-if: acting on the alert", what: "Compares repairing at once against waiting, for the whole shift.", read: "Units, OEE, downtime and cost for each, plus the minutes of life the robot has at the alert.", why: "The question a plant manager asks the copilot." },
  days30: { title: "Last 30 days: units per shift", what: "Cars built in each shift, with OEE as the yellow line and the plan as the dashed line.", read: "Red bars are shifts with a degradation incident, grey is Saturday (slower takt). Hover a bar for that shift.", why: "Shows how incidents and weekends move output over time." },
  months: { title: "Line downtime per month", what: "Hours the line was stopped each month (estimated).", read: "Taller bar = more downtime. Hover for the exact hours and share.", why: "Spots bad months and whether things are improving." },
  causes: { title: "Downtime by cause", what: "A Pareto of unplanned line downtime by cause, in hours over 12 months.", read: "The top few bars usually explain most of the loss. Hover for the share of total.", why: "Focus the fix on the causes that matter." },
  machines: { title: "Downtime by machine", what: "Line-down hours attributed to each machine over 12 months.", read: "The press is the heaviest because a failure there is slow to repair.", why: "Shows where maintenance money has the best return." },
  compare: { title: "Scenario comparison", what: "The five simulated versions of the same shift side by side.", read: "Rows: units, OEE, minutes stopped and cost. The highlighted row is the one running live.", why: "Makes the effect of each decision comparable at a glance." },
  health: { title: "Machine health", what: "Failure history of each machine over 12 months (estimated), with a health bar.", read: "MTBF = mean hours between failures (higher is better). MTTR = mean minutes to repair (lower is better). The health bar combines failures and downtime.", why: "Plans maintenance before breakdowns, not after." },
  incidents: { title: "Degradation incidents", what: "Machines that began to wear out in the last 30 days and how it ended.", read: "timely = fixed in time, late = fixed just before failure, failure = it broke. Margin = minutes between the alert and failure if left.", why: "Shows how much warning the system gives and how often we use it." },
};

function useTick(ms = 300) {
  const [, set] = useState(0);
  useEffect(() => {
    const id = setInterval(() => set((n) => n + 1), ms);
    return () => clearInterval(id);
  }, [ms]);
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;
const hrs = (v: number) => `${v.toFixed(1)} h`;

function Tile({ label, value, sub, tone, help }: { label: string; value: string; sub?: string; tone?: "ok" | "warn" | "bad"; help: HelpText }) {
  return (
    <div className={`tile ${tone ?? ""}`}>
      <div className="tile-h"><small>{label}</small><Help {...help} /></div>
      <b>{value}</b>
      {sub && <span>{sub}</span>}
    </div>
  );
}

function Card({ title, note, children, wide, help }: { title: string; note?: string; children: ReactNode; wide?: boolean; help: HelpText }) {
  return (
    <div className={`dcard ${wide ? "wide" : ""}`}>
      <div className="dcard-h"><b>{title}</b><span className="dnote">{note && <small>{note}</small>}<Help {...help} /></span></div>
      {children}
    </div>
  );
}

export function Dashboard() {
  const { data, shift } = useTwin();
  const [on, setOn] = useState<Record<string, boolean>>({ ideal: true, healthy_realistic: true, hero_timely_repair: true, hero_delayed_repair: false, hero_ignored: true });
  useTick();
  const anom = useAnomaly();
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
  const futures = useMemo(() => {
    if (!kpi) return [];
    return shift === "A"
      ? [{ name: "if repaired on alert", color: "#38bdf8", values: rateSeries(kpi, "hero_timely_repair") }, { name: "if ignored", color: "#ef4444", values: rateSeries(kpi, "hero_ignored") }]
      : [{ name: "expected", color: "#38bdf8", values: rates }];
  }, [kpi, shift, rates]);

  if (!data || !kpi || !s) return <div className="dash"><div className="msg">Loading…</div></div>;
  if (!dash) return <div className="dash"><div className="msg">Run the generator without --skip-history to create dashboard.json</div></div>;

  const status = m05Status(clock.t, shift, data.hero);
  const extra = injectedStopSeconds(clock.t, shift, data.hero);
  const frac = extra / Math.max(clock.t, 60);
  const ek = simLink.on ? simLink.snap?.kpis : undefined;      // engine KPIs replace the precomputed series when connected
  const A = ek ? ek.availability : Math.max(0, s.avail[i] - frac), P = ek ? ek.performance : s.perf[i], Q = ek ? ek.quality : s.qual[i], OEE = ek ? ek.oee : s.oee[i] * Math.max(0, 1 - frac);
  const units = ek ? ek.units : Math.max(0, Math.round(s.cum_units[i] - extra / TAKT));
  const elapsed = Math.max(clock.t, 60);
  const projected = Math.round((units / elapsed) * SHIFT_S);
  const downMin = ek ? ek.downtime_min : s.cum_down_s[i] / 60 + extra / 60;
  const cost = ek ? ek.downtime_cost_usd : s.cum_cost[i] + (extra / 60) * kpi.cost_per_min;
  const sum = kpi.summary;
  const timely = sum.hero_timely_repair, ignored = sum.hero_ignored;
  const eng0 = simLink.on ? simLink.snap?.machines?.M05 : undefined;
  const alertLive = eng0 ? eng0.alert === "critical" : shift === "A" && status === "alert";
  const rul = eng0 ? (eng0.alert && eng0.rul_s != null ? eng0.rul_s / 60 : null) : alertLive ? Math.max(0, ((timely.t_fail_if_ignored_s ?? 0) - clock.t) / 60) : null;
  const nowIdx = Math.min(Math.floor(clock.t / 600), rates.length - 1);

  const causes: Bar[] = Object.entries(dash.downtime_h_by_cause).map(([k, v]) => ({ label: k.replace(/_/g, " "), value: v, tip: "Unplanned line downtime attributed to this cause over 12 months." }));
  const byMachine: Bar[] = Object.entries(dash.downtime_h_by_machine).sort((a, b) => b[1] - a[1]).map(([k, v]) => {
    const m = dash.machines.find((x) => x.id === k);
    return { label: `${k} ${m?.name ?? ""}`, value: v, color: "#f59e0b", tip: `${m?.name ?? k} at ${m?.station ?? ""}: hours the line stood still because of this machine.` };
  });
  const months: Bar[] = Object.entries(dash.downtime_h_by_month).map(([k, v]) => ({ label: k, value: v, color: "#a78bfa", tip: "All line downtime in the month, planned and unplanned." }));

  const sh = dash.shifts;
  const barColors = sh.map((r) => (r.had_incident ? "#ef4444" : r.weekday === 5 ? "#64748b" : "#3b82f6"));
  const meta: ColMeta[] = sh.map((r) => ({
    title: `${r.date} shift ${r.shift}`,
    rows: [
      { label: "Units built", value: `${r.units}` }, { label: "Plan", value: `${r.demand_plan_units}` },
      { label: "OEE", value: pct(r.oee) }, { label: "Downtime", value: `${Math.round(r.downtime_min)} min` },
    ],
    note: r.had_incident ? "A machine began to wear out in this shift." : r.weekday === 5 ? "Saturday: slower takt, lower demand." : undefined,
  }));
  const maint = dash.maintenance;
  const row = (key: string) => sum[key] as ScenarioSummary;

  return (
    <div className="dash">
      <div className="dash-inner">
        <div className="dash-title">
          <h2>Plant KPIs <span>Shift {shift}, clock at {Math.floor(clock.t / 3600)}h {Math.floor((clock.t % 3600) / 60)}m of 8h</span></h2>
          <div className="scrub">
            <input type="range" min={0} max={SHIFT_S} step={30} value={clock.t} onChange={(e) => { ctl.seek(Number(e.target.value)); }} />
            {shift === "A" && <button onClick={() => ctl.seek(data.hero.t_alert_s + 60)}>Jump to alert</button>}
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
          <Tile help={H.oee} label="OEE (so far)" value={pct(OEE)} sub="availability x performance x quality" tone={OEE > 0.8 ? "ok" : OEE > 0.65 ? "warn" : "bad"} />
          <Tile help={H.avail} label="Availability" value={pct(A)} sub={`${downMin.toFixed(0)} min line stopped`} />
          <Tile help={H.perf} label="Performance" value={pct(P)} sub="speed vs 90 s takt" />
          <Tile help={H.qual} label="Quality" value={pct(Q)} sub={`${ek ? ek.units - ek.good_units : s.cum_scrap[i]} scrap units`} />
          <Tile help={H.units} label="Units" value={`${units} / ${kpi.plan_units}`} sub={`projected ${projected} at this pace`} />
          <Tile help={H.cost} label="Downtime cost" value={money(cost)} sub={`$${kpi.cost_per_min.toLocaleString()} per minute`} tone="bad" />
          <Tile help={H.robot} label="Weld robot 2" value={alertLive ? "ALERT" : status === "repair" ? "Repair" : "Healthy"} sub={rul !== null ? `RUL ${Math.ceil(rul)} min to failure` : eng0 ? "ML anomaly detector" : "bearing wear model"} tone={alertLive ? "bad" : status === "repair" ? "warn" : "ok"} />
          <Tile help={H.year} label="12-month downtime" value={hrs(maint.unplanned_line_down_h)} sub={`${money(maint.line_downtime_cost_usd)} line cost`} />
        </div>

        <div className="dgrid">
          <Card help={H.cum} title="Cumulative output vs ideal" note="units, one shift" wide>
            <LineChart series={lines} cursor={cursor} yMax={340} unit=" cars" />
            <div className="lg">{lines.map((l) => <span key={l.name}><i style={{ background: l.color }} />{l.name}</span>)}</div>
          </Card>
          <Card help={H.oeeline} title="OEE over the shift" note="cumulative">
            <LineChart series={oeeLines} cursor={cursor} yMax={1} yFmt={(v) => `${Math.round(v * 100)}%`} />
          </Card>

          <Card help={H.waterfall} title="Where the OEE goes" note="loss waterfall, now">
            <Waterfall A={A} P={P} Q={Q} />
          </Card>
          <Card help={H.forecast} title="Throughput forecast" note="units per hour, rest of shift">
            <div className="chart2"><ForecastChart2 actual={rates} futures={futures} nowIdx={nowIdx} ymax={50} ideal={40} startHour={shift === "A" ? 6 : 14} height={190} /></div>
            <div className="lg">
              <span><i style={{ background: "#3b82f6" }} />actual</span>
              {futures.map((f) => <span key={f.name}><i style={{ background: f.color }} />{f.name}</span>)}
            </div>
          </Card>
          <Card help={H.whatif} title="What-if: acting on the alert" note="whole shift">
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
            <div className="callout">Waiting costs {money(ignored.downtime_cost_usd - timely.downtime_cost_usd)} and {timely.units - ignored.units} units. {eng0?.alert && eng0.rul_s != null && eng0.rul_range_s ? `The detector predicts about ${Math.round(eng0.rul_s / 60)} minutes of life left (80% interval ${Math.round(eng0.rul_range_s[0] / 60)} to ${Math.round(eng0.rul_range_s[1] / 60)}) for weld robot 2.` : `At the alert there are about ${timely.remaining_useful_life_at_alert_min} minutes before weld robot 2 would fail.`}</div>
          </Card>

          <Card help={H.days30} title="Last 30 days: units per shift" note="red = incident, grey = Saturday" wide>
            <Columns bars={sh.map((r) => r.units)} colors={barColors} plan={sh.map((r) => r.demand_plan_units)} line={sh.map((r) => r.oee)} yMax={340} meta={meta} />
            <div className="lg"><span><i style={{ background: "#3b82f6" }} />normal</span><span><i style={{ background: "#ef4444" }} />incident</span><span><i style={{ background: "#fbbf24" }} />OEE (line)</span><span><i style={{ background: "#fff" }} />plan</span></div>
          </Card>
          <Card help={H.months} title="Line downtime per month" note="hours, last 12 months">
            <HBars items={months} fmt={(v) => `${v} h`} unit=" h" />
          </Card>

          <Card help={H.causes} title="Downtime by cause" note="Pareto, unplanned, hours (12 months)">
            <HBars items={causes} fmt={(v) => `${v} h`} unit=" h" />
          </Card>
          <Card help={H.machines} title="Downtime by machine" note="line-down hours (12 months)">
            <HBars items={byMachine} fmt={(v) => `${v} h`} unit=" h" />
          </Card>
          <Card help={H.compare} title="Scenario comparison" note="same shift, different decisions">
            <table className="tbl">
              <thead><tr><th>Scenario</th><th>Units</th><th>OEE</th><th>Down</th><th>Cost</th></tr></thead>
              <tbody>
                {SCEN.map((c) => {
                  const x = row(c.key);
                  return (
                    <tr key={c.key} className={c.key === live ? "hl" : ""} title={x.about}>
                      <td><i style={{ background: c.color }} className="dot2" /> {c.label}</td>
                      <td>{x.units}</td><td>{pct(x.oee)}</td><td>{Math.round(x.downtime_min)} min</td><td>{money(x.downtime_cost_usd)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>

          {anom && (
            <>
              <Card help={H.anomaly} title="Anomaly detector" note="live, per machine, from the engine">
                <AnomalyScores a={anom} />
              </Card>
              <Card help={H.scorehist} title="Score history" note="last hour">
                <ScoreHistory a={anom} />
              </Card>
              <Card help={H.why} title="Why it was flagged" note="Shapley contributions">
                <WhyFlagged a={anom} />
              </Card>
            </>
          )}
          {simLink.on && (
            <>
              <Card help={H.load} title="Station load" note="engine, utilisation">
                <StationLoad />
              </Card>
              <Card help={H.wos} title="Work orders" note="engine, latest" wide>
                <WorkOrders />
              </Card>
            </>
          )}

          <Card help={H.health} title="Machine health" note="12 months, estimated" wide>
            <table className="tbl">
              <thead><tr><th>Machine</th><th>Station</th><th>Now</th><th title="Number of failures in 12 months">Failures</th><th title="Mean operating hours between failures">MTBF (h)</th><th title="Mean minutes to repair">MTTR (min)</th><th title="Hours the line stood still because of this machine">Line down (h)</th><th>Health</th></tr></thead>
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
                      <td><div className="hb" title={`Health score ${h} of 100`}><div style={{ width: `${h}%`, background: h > 66 ? "#22c55e" : h > 40 ? "#f59e0b" : "#ef4444" }} /></div></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Card>
          <Card help={H.incidents} title="Degradation incidents" note="last 30 days">
            <table className="tbl">
              <thead><tr><th>Date</th><th>Machine</th><th>Outcome</th><th title="Minutes between the alert and the failure if nothing had been done">Margin at alert</th></tr></thead>
              <tbody>
                {dash.incidents.map((x) => (
                  <tr key={x.shift_id}>
                    <td>{x.date.slice(5)} {x.shift}</td>
                    <td>{x.machine_id}</td>
                    <td><span className={`badge ${x.outcome === "failure" ? "bad" : x.outcome === "late" ? "warn" : "ok"}`} title={x.outcome === "failure" ? "It broke before anyone acted" : x.outcome === "late" ? "Fixed just in time" : "Fixed with time to spare"}>{x.outcome}</span></td>
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
    { label: "Ideal", from: 0, to: 1, color: "#94a3b8", tip: "The theoretical ceiling: no stops, running at takt, no scrap." },
    { label: "Availability loss", from: 1 - availLoss, to: 1, color: "#ef4444", tip: "Minutes the line stood still (breakdowns, repairs, starving)." },
    { label: "Performance loss", from: 1 - availLoss - perfLoss, to: 1 - availLoss, color: "#f59e0b", tip: "Running slower than the 90 s takt, for example a worn robot derating itself." },
    { label: "Quality loss", from: oee, to: oee + qualLoss, color: "#a78bfa", tip: "Cars rejected or reworked." },
    { label: "Actual OEE", from: 0, to: oee, color: "#22c55e", tip: "What is left after all three losses." },
  ];
  return (
    <div className="wf">
      {steps.map((s) => (
        <WithTip key={s.label} tip={{ title: s.label, rows: [{ label: "Size", value: `${((s.to - s.from) * 100).toFixed(1)} pts` }], note: s.tip }}>
          <div className="wfrow">
            <span>{s.label}</span>
            <div className="wft"><div style={{ left: `${s.from * 100}%`, width: `${Math.max((s.to - s.from) * 100, 0.8)}%`, background: s.color }} /></div>
            <em>{s.label === "Ideal" || s.label === "Actual OEE" ? `${(s.to * 100).toFixed(1)}%` : `-${((s.to - s.from) * 100).toFixed(1)} pts`}</em>
          </div>
        </WithTip>
      ))}
    </div>
  );
}
