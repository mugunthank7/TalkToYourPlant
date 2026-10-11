import { useEffect, useMemo, useState } from "react";
import { camera, clock, ctl, fmt } from "../clock";
import { forecastFor, makeInjected, stationState } from "../plant";
import { useTwin } from "../state";
import { ForecastChart2, Gauge, Spark } from "./charts";
import { Help } from "./Help";
import { heroTimes, liveAt, money, rateSeries, ratesFromCum, SHIFT_S } from "./live";
import { simLink, simPost } from "../simlink";
import { buildShots, goTo } from "./shots";

const SPEEDS = [1, 10, 60, 300, 1200];
const hhmm = (t: number, shift: string) => fmt(t, shift).slice(0, 5);

function useTick(ms = 200) {
  const [, set] = useState(0);
  useEffect(() => {
    const id = setInterval(() => set((n) => n + 1), ms);
    return () => clearInterval(id);
  }, [ms]);
}

type Row = { id: string; name: string; sub: string; cls: "ok" | "warn" | "bad" | "blink" | "amber"; label: string };

function useRows(): Row[] {
  const { data, shift } = useTwin();
  useTick(250);
  if (!data) return [];
  return data.layout.stations.map((s) => {
    const r = stationState(s.id, clock.t, shift, data.hero);
    const f = forecastFor(s.id, clock.t, shift, data.hero);
    const L = liveAt(clock.t, shift, data.kpi, data.hero);
    const hero = s.id === "S06";
    const nm = hero && (L.status === "alert" || L.status === "repair" || f.level !== "ok") ? "M05  Weld robot 2" : `${s.id}  ${s.name}`;
    if (r.state === "fault") return { id: s.id, name: nm, sub: r.reason, cls: "blink", label: "Fault" };
    if (r.state === "repair") return { id: s.id, name: nm, sub: r.reason, cls: "amber", label: "Repair" };
    if (r.state === "micro") return { id: s.id, name: nm, sub: r.reason, cls: "warn", label: "Micro-stop" };
    if (r.state === "starved" || r.state === "blocked") return { id: s.id, name: nm, sub: r.reason, cls: "warn", label: r.state === "starved" ? "Starved" : "Blocked" };
    if (hero && L.status === "alert") return { id: s.id, name: nm, sub: `Bearing wear, RUL ${Math.ceil(L.rulMin ?? 0)} min${detectorNote()}`, cls: "bad", label: "Alert" };
    if (f.level !== "ok") return { id: s.id, name: nm, sub: f.text, cls: "warn", label: f.level === "risk" ? "At risk" : "Watch" };
    return { id: s.id, name: nm, sub: "", cls: "ok", label: "Running" };
  });
}

function StatePanel() {
  const rows = useRows();
  const { data, shift } = useTwin();
  if (!data) return null;
  const risk = rows.filter((r) => r.cls === "warn" || r.cls === "bad").length;
  const down = rows.filter((r) => r.cls === "blink" || r.cls === "amber").length;
  const f6 = forecastFor("S06", clock.t, shift, data.hero);
  const headline = down
    ? "Line stopped: downstream starving, upstream blocking"
    : f6.level !== "ok" && f6.etaMin !== undefined
      ? `Bottleneck forecast: M05 wear will slow the line, failure in ~${f6.etaMin} min`
      : risk
        ? "Watch list: near-capacity stations"
        : "No bottleneck expected in the next hour";
  return (
    <div className="card statepanel">
      <div className="card-h">
        <span>〰 Live plant state</span>
        <Help title="Live plant state" what="Status of every station right now, plus a one-hour forecast."
          read="Green = running. Yellow = forecast risk, or a station that is starved (no input) or blocked (output full). Amber = under repair. Red blinking = fault, the line is stopped."
          why="Shows where the next bottleneck will form before it stops the line." />
      </div>
      <div className={`headline ${down ? "bad" : risk ? "warn" : "ok"}`}>{headline}</div>
      <div className="rows">
        {rows.map((r) => (
          <div key={r.id} className={`srow ${r.cls === "bad" ? "alertrow" : r.cls === "blink" ? "faultrow" : ""}`} title={r.sub || r.label}>
            <i className={`dot ${r.cls}`} />
            <div className="sname"><div>{r.name}</div>{r.sub && <small className={r.cls}>{r.sub}</small>}</div>
            <div className={`stat ${r.cls}`}>{r.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function KpiPanel() {
  const { data, shift } = useTwin();
  useTick();
  const spark = useMemo(() => {
    if (!data) return { down: [] as number[], cost: [] as number[] };
    const s = data.kpi.series[shift === "A" ? "hero_timely_repair" : "healthy_realistic"];
    const pick = (a: number[]) => a.filter((_, i) => i % 8 === 0);
    return { down: pick(s.cum_down_s), cost: pick(s.cum_cost) };
  }, [data, shift]);
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  const pct = Math.min(L.units / L.planUnits, 1);
  const upto = Math.max(2, Math.floor(clock.t / 480));
  return (
    <div className="card kpipanel">
      <div className="card-h">
        <span>◎ KPIs</span>
        <Help title="KPIs" what="Live shift numbers: OEE (how much of the ideal output we really get), throughput, output vs plan, downtime and its cost."
          read="OEE = availability x speed x quality. Cost counts every minute the line is stopped at $38,000 per minute."
          why="These are the numbers a plant manager is judged on; each fault moves them." />
      </div>
      <div className="kpigrid">
        <Gauge value={L.oee} label="OEE" />
        <div className="kcol">
          <small>Throughput</small>
          <div className="big">{Math.round(L.ratePerHr)} <span>units/hr</span></div>
          <small>Units today vs plan</small>
          <div className="big small2">{L.units} / {L.planUnits} <em>{Math.round(pct * 100)}%</em></div>
          <div className="bar"><div style={{ width: `${pct * 100}%` }} /></div>
        </div>
        <div className="kcol2">
          <small>Downtime</small>
          <div className="big">{Math.round(L.downMin)} <span>min</span></div>
          <Spark values={spark.down.slice(0, upto)} />
        </div>
        <div className="kcol2">
          <small>Downtime cost</small>
          <div className="big">{money(L.cost)}</div>
          <Spark values={spark.cost.slice(0, upto)} color="#ef4444" />
        </div>
      </div>
      <div className="foot">$38,000 per minute of line stop (Siemens 2024, large automotive plant)</div>
    </div>
  );
}

function CameraCard() {
  const { data } = useTwin();
  const [active, setActive] = useState("Overview");
  const [mode, setMode] = useState(camera.mode);
  const shots = useMemo(() => (data ? buildShots(data.layout) : []), [data]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT") return;
      const n = Number(e.key);
      if (n >= 1 && n <= 9 && shots[n - 1]) { goTo(shots[n - 1]); setActive(shots[n - 1].name); setMode("free"); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [shots]);
  const setM = (m: typeof camera.mode) => { camera.mode = m; camera.tourIdx = -1; setMode(m); };
  return (
    <div className="card chips">
      <div className="card-h">
        <span>◉ Cameras</span>
        <Help title="Camera shots" what="Ready-made viewpoints for demos. Keys 1 to 9 jump to the first nine shots."
          read="Tour plays a cinematic sequence. Orbit circles the plant. Follow car and Follow tech track the action."
          why="Lets you tell the story without hunting for the right angle." />
      </div>
      <div className="modes">
        {([["tour", "▶ Tour"], ["orbit", "⟳ Orbit"], ["follow-car", "🚗 Follow car"], ["follow-tech", "🔧 Follow tech"]] as const).map(([m, label]) => (
          <button key={m} className={`chip mode ${mode === m ? "on" : ""}`} onClick={() => setM(mode === m ? "free" : m)}>{label}</button>
        ))}
      </div>
      <div className="shots">
        {shots.map((s, i) => (
          <button key={s.name} title={s.note} className={`chip ${mode === "free" && active === s.name ? "on" : ""}`} onClick={() => { goTo(s); setActive(s.name); setMode("free"); }}>
            {i < 9 && <kbd>{i + 1}</kbd>}{s.name}
          </button>
        ))}
      </div>
    </div>
  );
}

function FaultCard() {
  const { data, shift, faults, addFault, clearFaults } = useTwin();
  const [machine, setMachine] = useState("M03");
  useTick(500);
  if (!data) return null;
  const choices = data.layout.machines.filter((m) => m.type !== "agv");
  const inject = () => { if (simLink.on) void simPost("/fault", { machine }); else addFault(makeInjected(data.layout, machine, clock.t)); };
  const clear = () => { if (simLink.on) ctl.send?.({ type: "control", action: "clear_faults" }); else clearFaults(); };
  return (
    <div className="card faultcard">
      <div className="card-h">
        <span>⚡ Simulate a fault</span>
        <Help title="Fault simulator" what="Break any machine right now and watch the plant react."
          read="The machine blinks red, the line stops, stations downstream starve and upstream ones block. An on-call technician walks from the maintenance bay via the spares cage to repair it."
          why="Shows the cost of a surprise breakdown, which is what the copilot is built to prevent." />
      </div>
      <div className="frow">
        <select value={machine} onChange={(e) => setMachine(e.target.value)}>
          {choices.map((m) => <option key={m.id} value={m.id}>{m.id} {m.name} ({m.station})</option>)}
        </select>
        <button className="danger" onClick={inject}>Break it</button>
      </div>
      <div className="frow">
        <button onClick={() => ctl.seek(heroTimes(data.kpi, data.hero).t_alert_s - 120)} disabled={shift !== "A"}>Replay hero alert</button>
        <button onClick={clear} disabled={!faults.length && !simLink.on}>Clear faults</button>
      </div>
      {simLink.on && simLink.snap!.work_orders.filter((w) => w.status !== "closed").map((w) => (
        <div key={w.id} className="fitem bad"><b>{w.machine}</b> {w.kind} work order {w.id}: {w.status === "open" ? "technician being dispatched" : w.status === "dispatched" ? "technician on the way" : "repairing"}</div>
      ))}
      {faults.map((f) => {
        const t = clock.t;
        const stage = t < f.t0 ? "scheduled" : t < f.dispatchAt ? "dispatching technician" : t < f.pickupAt ? "technician fetching part" : t < f.arriveAt ? "technician on the way" : t < f.fixAt ? `repairing, ${Math.ceil((f.fixAt - t) / 60)} min left` : "fixed";
        return <div key={f.id} className={`fitem ${t >= f.fixAt ? "ok" : "bad"}`}><b>{f.machine}</b> {f.machineName} at {hhmm(f.t0, shift)}: {stage}</div>;
      })}
    </div>
  );
}

/** Detector output for the hero machine when the SimPy engine is connected: top SHAP contributors and the RUL interval. */
function detectorNote(): string {
  if (!simLink.on) return "";
  const m = simLink.snap?.machines?.M05;
  if (!m?.contributors?.length) return "";
  const top = m.contributors.slice(0, 3).map((c) => `${c.signal} ${c.shap >= 0 ? "+" : ""}${c.shap.toFixed(2)}`).join(", ");
  const r = m.rul_range_s;
  const rul = r ? ` · RUL ${Math.round(r[0] / 60)} to ${Math.round(r[1] / 60)} min (80%)` : "";
  return ` — driven by ${top}${rul}`;
}

function AlertToast() {
  const { data, shift, faults } = useTwin();
  useTick();
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  const active = faults.find((f) => clock.t >= f.t0 && clock.t < f.fixAt);
  if (active && clock.t < active.arriveAt) return <div className="toast blink">⛔ FAULT: {active.machine} {active.machineName} stopped the line</div>;
  if (active) return <div className="toast warn">🔧 Repairing {active.machine}: line stopped</div>;
  if (L.status === "alert") return <div className="toast bad">⚠ ALERT: weld robot 2 bearing wear detected{detectorNote()}</div>;
  if (L.status === "repair") return <div className="toast warn">🔧 Technician replacing the joint 1 bearing: line stopped</div>;
  return null;
}

function ForecastPanel() {
  const { data, shift, sim } = useTwin();
  useTick(500);
  const [eng, setEng] = useState<null | { actual: number[]; futures: { name: string; color: string; values: number[] }[] }>(null);
  useEffect(() => {
    if (sim !== "on") { setEng(null); return; }
    let alive = true;
    const pull = async () => {
      const [act, wait] = await Promise.all([simPost("/scenario", { changes: [{ op: "dispatch_now" }] }), simPost("/scenario", { changes: [{ op: "keep_running", hours: 2 }] })]);
      if (!alive) return;
      const a = ratesFromCum(act.scenario.cum_units_10min), w = ratesFromCum(wait.scenario.cum_units_10min);
      setEng({ actual: ratesFromCum(act.baseline.cum_units_10min), futures: [{ name: "if repaired on alert", color: "#38bdf8", values: a }, { name: "if ignored", color: "#ef4444", values: w }] });
    };
    void pull();
    const id = setInterval(pull, 15000);
    return () => { alive = false; clearInterval(id); };
  }, [sim]);
  const model = useMemo(() => {
    if (eng) return eng;
    if (!data) return null;
    const live = shift === "A" ? "hero_timely_repair" : "healthy_realistic";
    const actual = rateSeries(data.kpi, live);
    const futures = shift === "A"
      ? [{ name: "if repaired on alert", color: "#38bdf8", values: rateSeries(data.kpi, "hero_timely_repair") },
         { name: "if ignored", color: "#ef4444", values: rateSeries(data.kpi, "hero_ignored") }]
      : [{ name: "expected", color: "#38bdf8", values: actual }];
    return { actual, futures };
  }, [data, shift, eng]);
  if (!data || !model) return null;
  const nowIdx = Math.min(Math.floor(clock.t / 600), model.actual.length - 1);
  return (
    <div className="card forecast">
      <div className="card-h">
        <span>◔ Throughput forecast <small>(units per hour)</small></span>
        <Help title="Throughput forecast" what="Rolling units per hour. Solid line = what has happened. Dashed lines = what the rest of the shift looks like under each decision."
          read="Blue dashed = we fix the weld robot when the alert fires. Red dashed = we ignore it and it seizes. The shaded gap is the cost of waiting. The grey dotted line is the ideal rate."
          why="Turns a vibration alert into a number a manager can act on." />
      </div>
      <div className="chart"><ForecastChart2 actual={model.actual} futures={model.futures} nowIdx={nowIdx} ymax={50} ideal={40} startHour={shift === "A" ? 6 : 14} /></div>
    </div>
  );
}

function TimelinePanel() {
  const { data, shift, faults } = useTwin();
  useTick();
  const [playing, setPlaying] = useState(clock.playing);
  const [speed, setSpeed] = useState(clock.speed);
  if (!data) return null;
  const h = heroTimes(data.kpi, data.hero);
  type Band = { a: number; b: number; color: string; label: string };
  const bands: Band[] = [];
  if (shift === "A") {
    bands.push({ a: h.t_onset_s, b: h.t_alert_s, color: "#f59e0b", label: "Bearing degrading" });
    bands.push({ a: h.t_alert_s, b: h.t_repair_start_s, color: "#ef4444", label: "Alert, technician dispatched" });
    bands.push({ a: h.t_repair_start_s, b: h.t_repair_end_s, color: "#a855f7", label: "Repair, line stopped" });
  }
  faults.forEach((f) => {
    bands.push({ a: f.t0, b: f.arriveAt, color: "#ff2a2a", label: `${f.machine} fault` });
    bands.push({ a: f.arriveAt, b: f.fixAt, color: "#a855f7", label: `${f.machine} repair, line stopped` });
  });
  const jumps: [string, number][] = shift === "A"
    ? [["Start", 0], ["Onset", h.t_onset_s], ["Alert", h.t_alert_s], ["Repair", h.t_repair_start_s], ["Recovered", h.t_repair_end_s + 60]]
    : [["Start", 0]];
  faults.forEach((f) => jumps.push([`${f.machine} fault`, f.t0 - 30], [`${f.machine} fixed`, f.fixAt + 30]));
  const pos = (t: number) => `${(Math.max(0, Math.min(t, SHIFT_S)) / SHIFT_S) * 100}%`;
  return (
    <div className="card timeline">
      <div className="card-h">
        <span>◷ Timeline <small>{fmt(clock.t, shift)}</small></span>
        <Help title="Simulation timeline" what="The 8-hour shift as one bar. Coloured bands are events: yellow = bearing degrading, red = alert, purple = line stopped for repair, bright red = injected fault."
          read="Drag the white marker or click a chip to jump to an event. Speed chips change how fast simulated time runs."
          why="Lets you scrub straight to the moment that matters instead of waiting." />
      </div>
      <div className="tbar">
        {bands.map((b, i) => <div key={i} className="band" title={b.label} style={{ left: pos(b.a), width: `calc(${pos(b.b)} - ${pos(b.a)})`, background: b.color }} />)}
        <div className="cursor" style={{ left: pos(clock.t) }} />
        <input type="range" min={0} max={SHIFT_S} step={10} value={clock.t} onChange={(e) => { ctl.seek(Number(e.target.value)); }} />
        <div className="ticks">{[0, 2, 4, 6, 8].map((k) => <span key={k} style={{ left: `${(k / 8) * 100}%` }}>{hhmm(k * 3600, shift)}</span>)}</div>
      </div>
      <div className="transport">
        <button className="play" onClick={() => { ctl.play(!clock.playing); setPlaying(clock.playing); }}>{playing ? "❚❚" : "▶"}</button>
        {SPEEDS.map((v) => <button key={v} className={`spd ${v === speed ? "on" : ""}`} onClick={() => { ctl.speed(v); setSpeed(v); }}>{v}x</button>)}
        <div className="jumps">
          {jumps.map(([n, t]) => <button key={n + t} className="spd jump" onClick={() => ctl.seek(t)}>{n}</button>)}
        </div>
      </div>
    </div>
  );
}

function WhatIf() {
  const { data, sim } = useTwin();
  const [res, setRes] = useState<null | { act: any; wait: any; at: number }>(null);
  const [busy, setBusy] = useState(false);
  if (!data) return null;
  const base = data.kpi.summary.hero_timely_repair;
  const alt = data.kpi.summary.hero_ignored;
  const run = async () => {
    if (sim !== "on") { setBusy(true); setTimeout(() => setBusy(false), 900); return; }
    setBusy(true);
    const [act, wait] = await Promise.all([simPost("/scenario", { changes: [{ op: "dispatch_now" }] }), simPost("/scenario", { changes: [{ op: "keep_running", hours: 2 }] })]);
    setRes({ act, wait, at: clock.t });
    setBusy(false);
  };
  const col = (title: string, k: { units_lost_vs_ideal: number; downtime_min: number; downtime_cost_usd: number }, hot = false) => (
    <div className={`wcol ${hot ? "hot" : ""}`}>
      <b>{title}</b>
      <div><span>Units lost</span><em>{Math.round(k.units_lost_vs_ideal)}</em></div>
      <div><span>Downtime</span><em>{Math.round(k.downtime_min)} min</em></div>
      <div><span>Cost</span><em>{money(k.downtime_cost_usd)}</em></div>
    </div>
  );
  const live = sim === "on" && res;
  return (
    <div className="card whatif">
      <div className="card-h">
        <span>⚙ What-if {sim === "on" && <small className="simtag">SimPy</small>}</span>
        <Help title="What-if" what="Runs the real simulation forward from now to the end of the shift for two decisions: send the technician now, or keep running 2 more hours."
          read="Units lost, downtime and cost for each. Waiting costs far more because the robot seizes and needs a 90-minute emergency repair."
          why="This is the question a plant manager asks the copilot." />
      </div>
      <small>{live ? (res!.wait.summary as string).slice(0, 110) + "…" : "What if we keep running 2 more hours?"}</small>
      <div className="wgrid">
        {col("Repair now", live ? res!.act.scenario.kpis : base)}
        {busy ? <div className="wcol hot spin">Simulating…</div> : col("Keep running", live ? res!.wait.scenario.kpis : alt, true)}
      </div>
      <button className="run" onClick={run}>{sim === "on" ? "Run on SimPy →" : "Run scenario →"}</button>
    </div>
  );
}

function ChatButton() {
  const [open, setOpen] = useState(false);
  return (
    <>
      {open && <div className="card chat">Chat and voice connect to the LLM side (teammate). Coming soon.</div>}
      <button className="mic" onClick={() => setOpen(!open)}>🎤<small>Ask your plant…</small></button>
    </>
  );
}

export function Hud() {
  return (
    <div className="hud">
      <StatePanel />
      <KpiPanel />
      <div className="rightcol">
        <CameraCard />
        <FaultCard />
      </div>
      <AlertToast />
      <div className="bottom">
        <ForecastPanel />
        <TimelinePanel />
        <WhatIf />
      </div>
      <ChatButton />
    </div>
  );
}
