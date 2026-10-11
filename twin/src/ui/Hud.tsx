// Live 3D HUD v3: the scene stays visible. Top: KPI strip + one status banner. Left: station dots + tool rail with one drawer.
// Right: station briefing / ask (SidePanel). Bottom: time dock. Styles in hud.css (all under .h3).
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { camera, clock, ctl, fmt } from "../clock";
import { forecastFor, makeInjected, stationState } from "../plant";
import { useTwin } from "../state";
import { ForecastChart2 } from "./charts";
import { Help } from "./Help";
import { heroTimes, liveAt, money, rateSeries, ratesFromCum, SHIFT_S } from "./live";
import { simLink, simPost } from "../simlink";
import { buildShots, goTo } from "./shots";
import { SidePanel } from "./StationPanel";

const SPEEDS = [1, 10, 60, 300, 1200];
const hhmm = (t: number, shift: string) => fmt(t, shift).slice(0, 5);

function useTick(ms = 200) {
  const [, set] = useState(0);
  useEffect(() => {
    const id = setInterval(() => set((n) => n + 1), ms);
    return () => clearInterval(id);
  }, [ms]);
}

const I = {
  stations: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"><path d="M4 6h16M4 12h16M4 18h10" /></svg>,
  camera: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"><path d="M3 8h4l2-3h6l2 3h4v11H3z" /><circle cx="12" cy="13" r="3.5" /></svg>,
  bolt: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"><path d="M13 3 5 14h6l-1 7 8-11h-6z" /></svg>,
  plan: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19V5M4 19h16M8 15l4-5 3 3 5-7" /></svg>,
  chat: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"><path d="M4 5h16v11H9l-5 4z" /></svg>,
};

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
    const nm = hero && (L.status === "alert" || L.status === "repair" || f.level !== "ok") ? "Weld cell B (M05)" : s.name;
    if (r.state === "fault") return { id: s.id, name: nm, sub: r.reason, cls: "blink", label: "Fault" };
    if (r.state === "repair") return { id: s.id, name: nm, sub: r.reason, cls: "amber", label: "Repair" };
    if (r.state === "micro") return { id: s.id, name: nm, sub: r.reason, cls: "warn", label: "Micro-stop" };
    if (r.state === "starved" || r.state === "blocked") return { id: s.id, name: nm, sub: r.reason, cls: "warn", label: r.state === "starved" ? "Starved" : "Blocked" };
    if (hero && L.status === "alert") return { id: s.id, name: nm, sub: `Bearing wear, RUL ${Math.ceil(L.rulMin ?? 0)} min`, cls: "bad", label: "Alert" };
    if (f.level !== "ok") return { id: s.id, name: nm, sub: f.text, cls: "warn", label: f.level === "risk" ? "At risk" : "Watch" };
    return { id: s.id, name: nm, sub: "", cls: "ok", label: "Running" };
  });
}

/** Detector output for the hero machine when the SimPy engine is connected. */
function detectorNote(): string {
  if (!simLink.on) return "";
  const m = simLink.snap?.machines?.M05;
  if (!m?.contributors?.length) return "";
  const top = m.contributors.slice(0, 2).map((c) => c.signal).join(" and ");
  const r = m.rul_range_s;
  return ` · flagged by ${top}${r ? ` · ${Math.round(r[0] / 60)} to ${Math.round(r[1] / 60)} min left` : ""}`;
}

// ---- top: KPI strip and status banner --------------------------------------------------------------
function Ring({ v }: { v: number }) {
  const r = 15, c = 2 * Math.PI * r, col = v > 0.8 ? "#34d399" : v > 0.65 ? "#fbbf24" : "#fb5a5a";
  return (
    <svg width="38" height="38" viewBox="0 0 38 38">
      <circle cx="19" cy="19" r={r} fill="none" stroke="rgba(255,255,255,.1)" strokeWidth="4" />
      <circle cx="19" cy="19" r={r} fill="none" stroke={col} strokeWidth="4" strokeLinecap="round" strokeDasharray={`${c * v} ${c}`} transform="rotate(-90 19 19)" />
    </svg>
  );
}

function KpiStrip() {
  const { data, shift } = useTwin();
  useTick();
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  const pct = Math.min(L.units / L.planUnits, 1);
  return (
    <div className="kpis gl">
      <div className="kpi"><Ring v={L.oee} /><div><small>OEE</small><b className="num">{Math.round(L.oee * 100)}%</b></div></div>
      <div className="kpi"><div><small>Output vs plan</small><b className="num">{L.units}<span>/ {L.planUnits}</span></b><div className="meter"><i style={{ width: `${pct * 100}%` }} /></div></div></div>
      <div className="kpi"><div><small>Throughput</small><b className="num">{Math.round(L.ratePerHr)}<span>/ hr</span></b></div></div>
      <div className="kpi"><div><small>Downtime</small><b className="num">{Math.round(L.downMin)}<span>min</span></b></div></div>
      <div className="kpi cost"><div><small>Downtime cost</small><b className="num">{money(L.cost)}</b></div></div>
    </div>
  );
}

function Banner() {
  const { data, shift, faults, setSelectedStation } = useTwin();
  const rows = useRows();
  useTick();
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  const active = faults.find((f) => clock.t >= f.t0 && clock.t < f.fixAt);
  const stOf = (mid: string) => data.layout.machines.find((m) => m.id === mid)?.station ?? null;
  let tone = "ok", text = "All stations running", go: string | null = null;
  if (active && clock.t < active.arriveAt) { tone = "bad"; text = `Fault: ${active.machine} ${active.machineName}. The line is stopped.`; go = stOf(active.machine); }
  else if (active) { tone = "amber"; text = `Repairing ${active.machine}. The line is stopped.`; go = stOf(active.machine); }
  else if (L.status === "alert") { tone = "bad"; text = `M05 weld robot 2: bearing wear${detectorNote()}`; go = "S06"; }
  else if (L.status === "repair") { tone = "amber"; text = "Technician replacing the M05 joint bearing. The line is stopped."; go = "S06"; }
  else {
    const down = rows.find((r) => r.cls === "blink" || r.cls === "amber");
    const risk = rows.find((r) => r.cls === "warn" || r.cls === "bad");
    const f6 = forecastFor("S06", clock.t, shift, data.hero);
    if (down) { tone = "amber"; text = `${down.id} ${down.name}: ${down.label.toLowerCase()}. Line affected.`; go = down.id; }
    else if (f6.level !== "ok" && f6.etaMin !== undefined) { tone = "warn"; text = `Watch: M05 wear will slow the line, failure in about ${f6.etaMin} min`; go = "S06"; }
    else if (risk) { tone = "warn"; text = `Watch: ${risk.id} ${risk.sub || risk.label}`; go = risk.id; }
  }
  return (
    <div className={`banner gl ${tone}`}>
      <i /><span>{text}</span>
      {go && <button onClick={() => setSelectedStation(go)}>Open {go}</button>}
    </div>
  );
}

// ---- left rail: station dots + tools -----------------------------------------------------------------
type Tool = "stations" | "cameras" | "faults" | "plan";
const TOOLS: [Tool, string, ReactNode][] = [["stations", "Stations", I.stations], ["cameras", "Cameras", I.camera], ["faults", "Simulate a fault", I.bolt], ["plan", "Forecast and what-if", I.plan]];

function Rail({ tool, setTool }: { tool: Tool | null; setTool: (t: Tool | null) => void }) {
  const rows = useRows();
  const sel = useTwin((s) => s.selectedStation);
  const pick = useTwin((s) => s.setSelectedStation);
  return (
    <div className="rail gl">
      {rows.map((r) => (
        <button key={r.id} className={`sdot ${sel === r.id ? "sel" : ""}`} data-tip={`${r.id} ${r.name}: ${r.label}`} onClick={() => pick(sel === r.id ? null : r.id)}>
          <i className={r.cls} />{r.id.slice(1)}
        </button>
      ))}
      <hr />
      {TOOLS.map(([k, label, icon]) => (
        <button key={k} className={`tool ${tool === k ? "on" : ""}`} data-tip={label} aria-label={label} onClick={() => setTool(tool === k ? null : k)}>{icon}</button>
      ))}
    </div>
  );
}

function Drawer({ title, help, onClose, children }: { title: string; help?: { title: string; what: string; read: string; why: string }; onClose: () => void; children: ReactNode }) {
  return (
    <div className="drawer gl">
      <div className="ph"><span>{title} {help && <Help {...help} />}</span><button className="x" onClick={onClose} aria-label="Close">×</button></div>
      <div className="pb">{children}</div>
    </div>
  );
}

function StationsDrawer({ onClose }: { onClose: () => void }) {
  const rows = useRows();
  const pick = useTwin((s) => s.setSelectedStation);
  return (
    <Drawer title="Stations" onClose={onClose} help={{ title: "Stations", what: "Status of every station right now.", read: "Green = running. Yellow = forecast risk, starved (no input) or blocked (output full). Orange = under repair. Red = fault, the line is stopped.", why: "Shows where the next bottleneck will form before it stops the line." }}>
      {rows.map((r) => (
        <div key={r.id} className="srw" onClick={() => pick(r.id)}>
          <i className={r.cls} />
          <div className="nm">{r.id} · {r.name}{r.sub && <small>{r.sub}</small>}</div>
          <span className={`st ${r.cls}`}>{r.label}</span>
        </div>
      ))}
    </Drawer>
  );
}

function CamerasDrawer({ onClose }: { onClose: () => void }) {
  const { data } = useTwin();
  const [active, setActive] = useState("Overview");
  const [mode, setMode] = useState(camera.mode);
  const shots = useMemo(() => (data ? buildShots(data.layout) : []), [data]);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
      const n = Number(e.key);
      if (n >= 1 && n <= 9 && shots[n - 1]) { goTo(shots[n - 1]); setActive(shots[n - 1].name); setMode("free"); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [shots]);
  const setM = (m: typeof camera.mode) => { camera.mode = m; camera.tourIdx = -1; setMode(m); };
  return (
    <Drawer title="Cameras" onClose={onClose} help={{ title: "Camera shots", what: "Ready-made viewpoints. Keys 1 to 9 jump to the first nine shots.", read: "Tour plays a cinematic sequence, Orbit circles the plant, Follow car and Follow tech track the action.", why: "Tell the story without hunting for the right angle." }}>
      <h5>Motion</h5>
      <div className="grid2">
        {([["tour", "Tour"], ["orbit", "Orbit"], ["follow-car", "Follow car"], ["follow-tech", "Follow technician"]] as const).map(([m, label]) => (
          <button key={m} className={`shot ${mode === m ? "on" : ""}`} onClick={() => setM(mode === m ? "free" : m)}>{label}</button>
        ))}
      </div>
      <h5>Viewpoints</h5>
      <div className="grid2">
        {shots.map((s, i) => (
          <button key={s.name} title={s.note} className={`shot ${mode === "free" && active === s.name ? "on" : ""}`} onClick={() => { goTo(s); setActive(s.name); setMode("free"); }}>
            {i < 9 && <kbd>{i + 1}</kbd>}{s.name}
          </button>
        ))}
      </div>
    </Drawer>
  );
}

function FaultsDrawer({ onClose }: { onClose: () => void }) {
  const { data, shift, faults, addFault, clearFaults } = useTwin();
  const [machine, setMachine] = useState("M03");
  useTick(500);
  if (!data) return null;
  const choices = data.layout.machines.filter((m) => m.type !== "agv");
  const inject = () => { if (simLink.on) void simPost("/fault", { machine }); else addFault(makeInjected(data.layout, machine, clock.t)); };
  const clear = () => { if (simLink.on) ctl.send?.({ type: "control", action: "clear_faults" }); else clearFaults(); };
  return (
    <Drawer title="Simulate a fault" onClose={onClose} help={{ title: "Fault simulator", what: "Break any machine right now and watch the plant react.", read: "The machine blinks red, the line stops, downstream stations starve and upstream ones block. A technician walks from the maintenance bay via the spares cage.", why: "Shows the cost of a surprise breakdown, which is what the copilot is built to prevent." }}>
      <h5>Break a machine</h5>
      <div className="row">
        <select className="grow" value={machine} onChange={(e) => setMachine(e.target.value)}>
          {choices.map((m) => <option key={m.id} value={m.id}>{m.id} {m.name} ({m.station})</option>)}
        </select>
        <button className="btn dng" onClick={inject}>Break it</button>
      </div>
      <h5>Scenario</h5>
      <div className="row">
        <button className="btn" onClick={() => ctl.seek(heroTimes(data.kpi, data.hero).t_alert_s - 120)} disabled={shift !== "A"}>Replay hero alert</button>
        <button className="btn" onClick={clear} disabled={!faults.length && !simLink.on}>Clear faults</button>
      </div>
      <h5>Now</h5>
      {simLink.on && simLink.snap!.work_orders.filter((w) => w.status !== "closed").map((w) => (
        <div key={w.id} className="item bad"><b>{w.machine}</b> {w.kind} order {w.id}: {w.status === "open" ? "technician being dispatched" : w.status === "dispatched" ? "technician on the way" : "repairing"}</div>
      ))}
      {faults.map((f) => {
        const t = clock.t;
        const stage = t < f.t0 ? "scheduled" : t < f.dispatchAt ? "dispatching technician" : t < f.pickupAt ? "technician fetching part" : t < f.arriveAt ? "technician on the way" : t < f.fixAt ? `repairing, ${Math.ceil((f.fixAt - t) / 60)} min left` : "fixed";
        return <div key={f.id} className={`item ${t >= f.fixAt ? "ok" : "bad"}`}><b>{f.machine}</b> {f.machineName} at {hhmm(f.t0, shift)}: {stage}</div>;
      })}
      {!faults.length && !(simLink.on && simLink.snap!.work_orders.some((w) => w.status !== "closed")) && <div className="note">Nothing broken right now.</div>}
    </Drawer>
  );
}

function PlanDrawer({ onClose }: { onClose: () => void }) {
  const { data, shift, sim } = useTwin();
  useTick(500);
  const [eng, setEng] = useState<null | { actual: number[]; futures: { name: string; color: string; values: number[] }[] }>(null);
  const [res, setRes] = useState<null | { act: any; wait: any }>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (sim !== "on") { setEng(null); return; }
    let alive = true;
    const pull = async () => {
      const [act, wait] = await Promise.all([simPost("/scenario", { changes: [{ op: "dispatch_now" }] }), simPost("/scenario", { changes: [{ op: "keep_running", hours: 2 }] })]);
      if (!alive) return;
      setRes({ act, wait });
      setEng({ actual: ratesFromCum(act.baseline.cum_units_10min), futures: [{ name: "repair on alert", color: "#4cc2ff", values: ratesFromCum(act.scenario.cum_units_10min) }, { name: "ignore it", color: "#fb5a5a", values: ratesFromCum(wait.scenario.cum_units_10min) }] });
    };
    void pull();
    const id = setInterval(pull, 20000);
    return () => { alive = false; clearInterval(id); };
  }, [sim]);
  const model = useMemo(() => {
    if (eng) return eng;
    if (!data) return null;
    const live = shift === "A" ? "hero_timely_repair" : "healthy_realistic";
    const actual = rateSeries(data.kpi, live);
    const futures = shift === "A"
      ? [{ name: "repair on alert", color: "#4cc2ff", values: rateSeries(data.kpi, "hero_timely_repair") }, { name: "ignore it", color: "#fb5a5a", values: rateSeries(data.kpi, "hero_ignored") }]
      : [{ name: "expected", color: "#4cc2ff", values: actual }];
    return { actual, futures };
  }, [data, shift, eng]);
  if (!data || !model) return null;
  const nowIdx = Math.min(Math.floor(clock.t / 600), model.actual.length - 1);
  const base = data.kpi.summary.hero_timely_repair, alt = data.kpi.summary.hero_ignored;
  const live = sim === "on" && res;
  const col = (title: string, k: { units_lost_vs_ideal: number; downtime_min: number; downtime_cost_usd: number }, hot = false) => (
    <div className={hot ? "hot" : ""}>
      <b>{title}</b>
      <div><span>Units lost</span><em className="num">{Math.round(k.units_lost_vs_ideal)}</em></div>
      <div><span>Downtime</span><em className="num">{Math.round(k.downtime_min)} min</em></div>
      <div><span>Cost</span><em className="num">{money(k.downtime_cost_usd)}</em></div>
    </div>
  );
  const run = async () => {
    if (sim !== "on") return;
    setBusy(true);
    const [act, wait] = await Promise.all([simPost("/scenario", { changes: [{ op: "dispatch_now" }] }), simPost("/scenario", { changes: [{ op: "keep_running", hours: 2 }] })]);
    setRes({ act, wait });
    setBusy(false);
  };
  return (
    <Drawer title="Forecast and what-if" onClose={onClose} help={{ title: "Forecast and what-if", what: "Rolling units per hour (solid = so far, dashed = rest of the shift under each decision), and the real simulation run forward for two choices.", read: "Blue = repair when the alert fires. Red = keep running and let the robot seize. The gap is the cost of waiting.", why: "Turns an alert into a number a manager can act on." }}>
      <h5>Units per hour</h5>
      <ForecastChart2 actual={model.actual} futures={model.futures} nowIdx={nowIdx} ymax={50} ideal={40} startHour={shift === "A" ? 6 : 14} />
      <div className="legend"><span><i style={{ background: "#fff" }} />so far</span>{model.futures.map((f) => <span key={f.name}><i style={{ background: f.color }} />{f.name}</span>)}</div>
      <h5>What if we keep running 2 more hours?</h5>
      <div className="note">{live ? (res!.wait.summary as string) : "Compares sending the technician now with waiting, to the end of the shift."}</div>
      <div className="scen">
        {col("Repair now", live ? res!.act.scenario.kpis : base)}
        {busy ? <div className="hot note">Simulating…</div> : col("Keep running", live ? res!.wait.scenario.kpis : alt, true)}
      </div>
      <div className="row" style={{ marginTop: 10 }}>
        <button className="btn pri" onClick={run} disabled={sim !== "on" || busy}>{busy ? "Running…" : "Run again on SimPy"}</button>
      </div>
    </Drawer>
  );
}

// ---- bottom: time dock -------------------------------------------------------------------------------
function TimeDock() {
  const { data, shift, faults } = useTwin();
  useTick();
  const [speed, setSpeed] = useState(clock.speed);
  const [playing, setPlaying] = useState(clock.playing);
  if (!data) return null;
  const h = heroTimes(data.kpi, data.hero);
  type Band = { a: number; b: number; color: string; label: string };
  const bands: Band[] = [];
  if (shift === "A") {
    bands.push({ a: h.t_onset_s, b: h.t_alert_s, color: "#fbbf24", label: "Bearing degrading" });
    bands.push({ a: h.t_alert_s, b: h.t_repair_start_s, color: "#fb5a5a", label: "Alert, technician dispatched" });
    bands.push({ a: h.t_repair_start_s, b: h.t_repair_end_s, color: "#a78bfa", label: "Repair, line stopped" });
  }
  faults.forEach((f) => {
    bands.push({ a: f.t0, b: f.arriveAt, color: "#ff3b3b", label: `${f.machine} fault` });
    bands.push({ a: f.arriveAt, b: f.fixAt, color: "#a78bfa", label: `${f.machine} repair` });
  });
  const jumps: [string, number, boolean?][] = shift === "A"
    ? [["Start", 0], ["Onset", h.t_onset_s], ["Alert", h.t_alert_s, true], ["Repair", h.t_repair_start_s], ["Recovered", h.t_repair_end_s + 60]]
    : [["Start", 0]];
  faults.forEach((f) => jumps.push([`${f.machine} fault`, f.t0 - 30, true], [`${f.machine} fixed`, f.fixAt + 30]));
  const pct = (t: number) => `${(Math.max(0, Math.min(t, SHIFT_S)) / SHIFT_S) * 100}%`;
  const toggle = () => { ctl.play(!clock.playing); setPlaying(clock.playing); };
  return (
    <div className="time gl">
      <div className="top">
        <button className="playbtn" onClick={toggle} aria-label={playing ? "Pause" : "Play"}>{playing ? "❚❚" : "▶"}</button>
        <div className="tl">
          <div className="trk">{bands.map((b, i) => <div key={i} className="band" title={b.label} style={{ left: pct(b.a), width: `calc(${pct(b.b)} - ${pct(b.a)})`, background: b.color }} />)}</div>
          <div className="fill" style={{ width: pct(clock.t) }} />
          <div className="head" style={{ left: pct(clock.t) }} />
          <input type="range" min={0} max={SHIFT_S} step={10} value={clock.t} aria-label="Shift time" onChange={(e) => ctl.seek(Number(e.target.value))} />
        </div>
        <div className="clk num">{fmt(clock.t, shift)}</div>
        <div className="seg">{SPEEDS.map((v) => <button key={v} className={v === speed ? "on" : ""} onClick={() => { ctl.speed(v); setSpeed(v); }}>{v}×</button>)}</div>
      </div>
      <div className="bot">
        <div className="jumps3">{jumps.map(([n, t, hot]) => <button key={n + t} className={hot ? "hot" : ""} onClick={() => ctl.seek(t)}>{n}</button>)}</div>
        <span className="hint">{hhmm(0, shift)} to {hhmm(SHIFT_S, shift)} · drag the bar to scrub</span>
      </div>
    </div>
  );
}

function AskButton() {
  const { askOpen, setAskOpen, selectedStation } = useTwin();
  if (askOpen || selectedStation) return null;
  return <button className="askfab" onClick={() => setAskOpen(true)}>{I.chat}Ask your plant</button>;
}

export function Hud() {
  const [tool, setTool] = useState<Tool | null>(null);
  const close = () => setTool(null);
  return (
    <div className="h3">
      <KpiStrip />
      <Banner />
      <Rail tool={tool} setTool={setTool} />
      {tool === "stations" && <StationsDrawer onClose={close} />}
      {tool === "cameras" && <CamerasDrawer onClose={close} />}
      {tool === "faults" && <FaultsDrawer onClose={close} />}
      {tool === "plan" && <PlanDrawer onClose={close} />}
      <SidePanel />
      <AskButton />
      <TimeDock />
    </div>
  );
}
