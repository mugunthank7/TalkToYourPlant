// Dashboard cards fed by the SimPy engine: anomaly detector, station utilisation, work orders.
import { useEffect, useState } from "react";
import { simLink } from "../simlink";
import { HBars, type Bar } from "./charts";

interface Anom {
  thresholds: { watch: number; critical: number };
  machines: Record<string, {
    anomaly?: { score: number; features: Record<string, number>; thresholds: { watch: number; critical: number } } | null;
    alert?: string | null;
    contributors?: { signal: string; shap: number }[] | null;
    rul_s?: number | null;
    rul_range_s?: [number, number] | null;
    history: { t: number; score: number }[];
  }>;
}

/** Polls the engine's /anomaly endpoint while connected. */
export function useAnomaly(ms = 3000): Anom | null {
  const [a, setA] = useState<Anom | null>(null);
  useEffect(() => {
    let alive = true;
    const go = async () => {
      if (!simLink.on) { if (alive) setA(null); return; }
      try {
        const r = await fetch(`${simLink.base}/anomaly`);
        if (r.ok && alive) setA(await r.json());
      } catch { /* engine not reachable */ }
    };
    go();
    const id = setInterval(go, ms);
    return () => { alive = false; clearInterval(id); };
  }, [ms]);
  return a;
}

const LEVEL = { critical: "#ef4444", watch: "#f59e0b", ok: "#22c55e" };

export function AnomalyScores({ a }: { a: Anom }) {
  const { watch, critical } = a.thresholds;
  const items: Bar[] = Object.entries(a.machines)
    .map(([id, m]) => {
      const score = m.anomaly?.score ?? 0;
      const lvl = m.alert === "critical" || score >= critical ? "critical" : m.alert === "watch" || score >= watch ? "watch" : "ok";
      return { label: id, value: Math.round(score * 1000) / 1000, color: LEVEL[lvl], sub: lvl,
        tip: `Anomaly score ${score.toFixed(3)} (watch at ${watch.toFixed(2)}, critical at ${critical.toFixed(2)}). ${m.anomaly ? "Higher means less like a healthy machine at this load." : "Not running, no score."}` } as Bar;
    })
    .sort((x, y) => y.value - x.value);
  return (
    <>
      <HBars items={items} fmt={(v) => v.toFixed(2)} />
      <div className="lg">
        <span><i style={{ background: LEVEL.ok }} />healthy</span>
        <span><i style={{ background: LEVEL.watch }} />watch &ge; {watch.toFixed(2)}</span>
        <span><i style={{ background: LEVEL.critical }} />critical &ge; {critical.toFixed(2)}</span>
      </div>
    </>
  );
}

/** Score history of the machine with the highest score (or M05), with the two thresholds. */
export function ScoreHistory({ a }: { a: Anom }) {
  const ids = Object.keys(a.machines);
  const pick = ids.find((id) => a.machines[id].alert) ?? "M05";
  const m = a.machines[pick];
  const h = m?.history ?? [];
  const W = 560, H = 170, top = 0.9;
  if (h.length < 2) return <div className="msg">Collecting scores from the engine…</div>;
  const x = (i: number) => 40 + (i / (h.length - 1)) * (W - 52);
  const y = (v: number) => H - 22 - (Math.min(v, top) / top) * (H - 34);
  const path = h.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.score).toFixed(1)}`).join(" ");
  const mins = Math.round((h[h.length - 1].t - h[0].t) / 60);
  const fmt = (t: number) => `${String(Math.floor(t / 3600) + 6).padStart(2, "0")}:${String(Math.floor((t % 3600) / 60)).padStart(2, "0")}`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart2" style={{ width: "100%" }}>
      {[a.thresholds.watch, a.thresholds.critical].map((v, k) => (
        <g key={k}>
          <line x1={40} x2={W - 12} y1={y(v)} y2={y(v)} stroke={k ? LEVEL.critical : LEVEL.watch} strokeDasharray="4 4" opacity={0.8} />
          <text x={W - 14} y={y(v) - 3} textAnchor="end" fontSize={10} fill={k ? LEVEL.critical : LEVEL.watch}>{k ? "critical" : "watch"}</text>
        </g>
      ))}
      <path d={path} fill="none" stroke="#38bdf8" strokeWidth={2} />
      <text x={40} y={14} fontSize={11} fill="#94a3b8">{pick} anomaly score, last {mins} min</text>
      <text x={40} y={H - 6} fontSize={10} fill="#94a3b8">{fmt(h[0].t)}</text>
      <text x={W - 12} y={H - 6} fontSize={10} fill="#94a3b8" textAnchor="end">{fmt(h[h.length - 1].t)}</text>
    </svg>
  );
}

/** Why the detector flagged a machine: Shapley contributions and the remaining-life interval. */
export function WhyFlagged({ a }: { a: Anom }) {
  const flagged = Object.entries(a.machines).find(([, m]) => m.alert && m.contributors?.length);
  if (!flagged) return <div className="msg">No machine is flagged. The detector is scoring {Object.keys(a.machines).length} machines every minute.</div>;
  const [id, m] = flagged;
  const items: Bar[] = (m.contributors ?? []).map((c) => ({ label: c.signal, value: Math.max(0, c.shap), color: "#ef4444", tip: `Shapley value ${c.shap.toFixed(3)}: how much this signal pushed the anomaly score up compared with a healthy machine.` }));
  const r = m.rul_range_s;
  return (
    <>
      <HBars items={items} fmt={(v) => v.toFixed(3)} />
      <div className="callout">
        {id} is at <b>{m.alert}</b>.{r ? ` Predicted life left ${Math.round((m.rul_s ?? 0) / 60)} min (80% interval ${Math.round(r[0] / 60)} to ${Math.round(r[1] / 60)} min).` : ""}
      </div>
    </>
  );
}

export function StationLoad() {
  const s = simLink.snap;
  if (!s) return null;
  const items: Bar[] = Object.entries(s.stations)
    .map(([id, st]) => ({ label: id, value: Math.round(st.utilization * 100), color: st.state === "run" ? "#3b82f6" : st.state === "fault" ? "#ef4444" : st.state === "repair" ? "#f59e0b" : "#eab308",
      sub: st.state, tip: `${id}: ${st.state}. ${st.reason || "Running normally."} Utilisation is the share of time this station has been working.` } as Bar));
  return <HBars items={items} fmt={(v) => `${v}%`} />;
}

export function WorkOrders() {
  const s = simLink.snap;
  const rows = s?.work_orders ?? [];
  if (!rows.length) return <div className="msg">No work orders yet.</div>;
  const mm = (v: number | null) => (v == null ? "-" : `${Math.floor(v / 3600) + 6}:${String(Math.floor((v % 3600) / 60)).padStart(2, "0")}`);
  return (
    <table className="tbl">
      <thead><tr><th>ID</th><th>Machine</th><th>Kind</th><th>Status</th><th>Opened</th><th>On site</th><th>Closed</th></tr></thead>
      <tbody>
        {rows.slice(-8).reverse().map((w) => (
          <tr key={w.id}><td>{w.id}</td><td>{w.machine}</td><td>{w.kind}</td><td><span className={`badge ${w.status === "closed" ? "ok" : w.kind === "emergency" ? "bad" : "warn"}`}>{w.status}</span></td><td>{mm(w.opened_at)}</td><td>{mm(w.arrived_at)}</td><td>{mm(w.closed_at)}</td></tr>
        ))}
      </tbody>
    </table>
  );
}
