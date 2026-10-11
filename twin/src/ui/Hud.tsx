import { useEffect, useMemo, useState } from "react";
import { camera, clock, fmt, VIEWS } from "../clock";
import { Station } from "../data";
import { useTwin } from "../state";
import { ForecastChart, Gauge, Spark } from "./charts";
import { liveAt, money, rateSeries, seriesName, SHIFT_S } from "./live";

const SPEEDS = [1, 10, 60, 300, 1200];
const hhmm = (t: number, shift: string) => fmt(t, shift).slice(0, 5);

function useTick(ms = 200) {
  const [, set] = useState(0);
  useEffect(() => {
    const id = setInterval(() => set((n) => n + 1), ms);
    return () => clearInterval(id);
  }, [ms]);
}

function TopBar() {
  const { shift, setShift } = useTwin();
  useTick();
  return (
    <div className="topbar">
      <div className="brand">
        <span className="bolt">⚡</span>
        <b>Voltline EV Works</b>
        <i />
        <span className="sub">Talk to Your Plant ▾</span>
      </div>
      <div className="topright">
        {(["A", "B"] as const).map((s) => (
          <button key={s} className={`pill ${s === shift ? "on" : ""}`} onClick={() => { setShift(s); clock.t = 0; }}>Shift {s}</button>
        ))}
        <div className="clockbox">
          <b>{fmt(clock.t, shift)}</b>
          <span>Oct 10, 2026</span>
        </div>
        <div className="live"><i /> LIVE</div>
      </div>
    </div>
  );
}

function StatePanel() {
  const { data, shift } = useTwin();
  useTick();
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  const techActive = shift === "A" && clock.t >= data.hero.t_dispatch_s && clock.t < data.hero.t_repair_end_s;
  const rows = data.layout.stations.map((s: Station) => {
    let status = "Running";
    let cls = "ok";
    let name = `${s.id}  ${s.name}`;
    let sub = "";
    if (s.id === "S06" && L.status === "alert") {
      status = "Alert"; cls = "bad"; name = "M05  Weld robot 2";
      sub = `Bearing wear, RUL ${Math.ceil(L.rulMin ?? 0)} min`;
    } else if (s.id === "S06" && L.status === "repair") {
      status = "Repair"; cls = "warn"; name = "M05  Weld robot 2"; sub = "Technician replacing bearing";
    } else if (s.id === "S10" && techActive) {
      status = "Maintenance"; cls = "warn";
    }
    return { id: s.id, name, sub, status, cls };
  });
  return (
    <div className="card statepanel">
      <div className="card-h"><span>〰 Live plant state</span><span>›</span></div>
      <div className="thead"><span>Machine / Station</span><span>Status</span></div>
      <div className="rows">
        {rows.map((r) => (
          <div key={r.id} className={`srow ${r.cls === "bad" ? "alertrow" : ""}`}>
            <i className={`dot ${r.cls}`} />
            <div className="sname"><div>{r.name}</div>{r.sub && <small>{r.sub}</small>}</div>
            <div className={`stat ${r.cls}`}><i className={`dot ${r.cls}`} /> {r.status}</div>
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
    const s = data.kpi.series[seriesName(shift)];
    const pick = (a: number[]) => a.filter((_, i) => i % 8 === 0);
    return { down: pick(s.cum_down_s), cost: pick(s.cum_cost) };
  }, [data, shift]);
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  const pct = Math.min(L.units / L.planUnits, 1);
  const upto = Math.max(2, Math.floor(clock.t / 480));
  return (
    <div className="card kpipanel">
      <div className="card-h"><span>◎ KPIs</span><span>›</span></div>
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

function CameraChips() {
  const [active, setActive] = useState("Overview");
  return (
    <div className="card chips">
      <div className="card-h"><span>◉ Camera shortcuts</span></div>
      {(Object.keys(VIEWS) as (keyof typeof VIEWS)[]).map((k) => (
        <button key={k} className={`chip ${k === active ? "on" : ""}`} onClick={() => { setActive(k); camera.goal = { pos: [...VIEWS[k].pos], target: [...VIEWS[k].target] }; }}>{k}</button>
      ))}
    </div>
  );
}

function AlertToast() {
  const { data, shift } = useTwin();
  useTick();
  if (!data) return null;
  const L = liveAt(clock.t, shift, data.kpi, data.hero);
  if (L.status === "alert") return <div className="toast bad">⚠ ALERT: weld robot 2 bearing wear detected</div>;
  if (L.status === "repair") return <div className="toast warn">🔧 Technician replacing the joint 1 bearing on weld robot 2</div>;
  return null;
}

function ForecastPanel() {
  const { data, shift } = useTwin();
  useTick(500);
  const actual = useMemo(() => (data ? rateSeries(data.kpi, shift) : []), [data, shift]);
  if (!data) return null;
  const nowIdx = Math.min(Math.floor(clock.t / 600), actual.length - 1);
  const tail = actual.slice(Math.max(nowIdx - 5, 0), nowIdx + 1);
  const mean = tail.reduce((a, b) => a + b, 0) / Math.max(tail.length, 1);
  const sd = Math.sqrt(tail.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(tail.length, 1));
  const forecast = actual.map((v, i) => (i <= nowIdx ? v : mean));
  return (
    <div className="card forecast">
      <div className="card-h"><span>◔ Throughput forecast <small>(rest of shift)</small></span>
        <span className="legendline"><i className="l1" /> Actual <i className="l2" /> Forecast <i className="l3" /> Confidence band</span></div>
      <div className="chart"><ForecastChart actual={actual} forecast={forecast} band={Math.max(sd * 2, 3)} nowIdx={nowIdx} ymax={60} /></div>
    </div>
  );
}

function TimelinePanel() {
  const { data, shift } = useTwin();
  useTick();
  const [playing, setPlaying] = useState(clock.playing);
  const [speed, setSpeed] = useState(clock.speed);
  if (!data) return null;
  const h = data.hero;
  const marks = shift === "A"
    ? [["Fault onset", h.t_onset_s, "#ef4444"], ["Alert", h.t_alert_s, "#f59e0b"], ["Technician dispatched", h.t_dispatch_s, "#38bdf8"], ["Repair", h.t_repair_end_s, "#22c55e"]] as const
    : [];
  return (
    <div className="card timeline">
      <div className="card-h"><span>◷ Simulation timeline</span></div>
      <div className="track">
        {marks.map(([name, t, col], i) => (
          <div key={name} className="mark" style={{ left: `${(t / SHIFT_S) * 100}%`, top: (i % 2) * 0 }}>
            <small style={{ color: col }}>{name}</small>
            <small>{hhmm(t, shift)}</small>
            <i style={{ background: col, height: i % 2 ? 8 : 22 }} />
          </div>
        ))}
        <input type="range" min={0} max={SHIFT_S} step={10} value={clock.t} onChange={(e) => { clock.t = Number(e.target.value); }} />
      </div>
      <div className="transport">
        <button className="play" onClick={() => { clock.playing = !clock.playing; setPlaying(clock.playing); }}>{playing ? "❚❚" : "▶"}</button>
        {SPEEDS.map((v) => (
          <button key={v} className={`spd ${v === speed ? "on" : ""}`} onClick={() => { clock.speed = v; setSpeed(v); }}>{v}x</button>
        ))}
        {shift === "A" && <button className="spd jump" onClick={() => { clock.t = h.t_alert_s - 120; }}>Jump to alert</button>}
        <div className="now"><b>{fmt(clock.t, shift)}</b><small>(current)</small></div>
      </div>
    </div>
  );
}

function WhatIf() {
  const { data } = useTwin();
  const [state, setState] = useState<"idle" | "running" | "done">("done");
  if (!data) return null;
  const base = data.kpi.summary.hero_timely_repair;
  const alt = data.kpi.summary.hero_ignored;
  const run = () => { setState("running"); setTimeout(() => setState("done"), 900); };
  const col = (title: string, s: typeof base, hot = false) => (
    <div className={`wcol ${hot ? "hot" : ""}`}>
      <b>{title}</b>
      <div><span>Units lost</span><em>{Math.round(s.units_lost_vs_ideal)}</em></div>
      <div><span>Downtime</span><em>{Math.round(s.downtime_min)} min</em></div>
      <div><span>Cost</span><em>{money(s.downtime_cost_usd)}</em></div>
    </div>
  );
  return (
    <div className="card whatif">
      <div className="card-h"><span>⚙ What-if</span></div>
      <small>What if we keep running 2 more hours? (whole shift)</small>
      <div className="wgrid">
        {col("Baseline (repair now)", base)}
        {state === "running" ? <div className="wcol hot spin">Simulating…</div> : col("With 2 more hours (M05 seizes)", alt, true)}
      </div>
      <button className="run" onClick={run}>Run scenario →</button>
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
      <TopBar />
      <StatePanel />
      <KpiPanel />
      <CameraChips />
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
