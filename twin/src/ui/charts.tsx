import { useRef, useState, type ReactNode } from "react";

// ---- tooltip plumbing -------------------------------------------------------------------------------
export interface TipRow { color?: string; label: string; value: string }
export interface Tip { title: string; rows: TipRow[]; note?: string }

function TipBox({ tip, x, y }: { tip: Tip; x: number; y: number }) {
  return (
    <div className="tip" style={{ left: `${Math.min(Math.max(x, 8), 92)}%`, top: y }}>
      <b>{tip.title}</b>
      {tip.rows.map((r, i) => (
        <div key={i}><span>{r.color && <i style={{ background: r.color }} />}{r.label}</span><em>{r.value}</em></div>
      ))}
      {tip.note && <small>{tip.note}</small>}
    </div>
  );
}

/** Wrapper that turns mouse position into a fraction (0..1) and shows a tooltip. */
function Hoverable({ children, tipAt }: { children: ReactNode; tipAt: (frac: number) => Tip | null }) {
  const ref = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<{ tip: Tip; x: number; y: number } | null>(null);
  return (
    <div className="hover" ref={ref}
      onMouseMove={(e) => {
        const r = ref.current!.getBoundingClientRect();
        const frac = (e.clientX - r.left) / r.width;
        const tip = tipAt(frac);
        setState(tip ? { tip, x: frac * 100, y: Math.max(4, e.clientY - r.top - 70) } : null);
      }}
      onMouseLeave={() => setState(null)}>
      {children}
      {state && <TipBox tip={state.tip} x={state.x} y={state.y} />}
    </div>
  );
}

// ---- gauge & spark ----------------------------------------------------------------------------------
export function Gauge({ value, label }: { value: number; label: string }) {
  const r = 44;
  const c = 2 * Math.PI * r;
  const col = value > 0.8 ? "#22c55e" : value > 0.6 ? "#f59e0b" : "#ef4444";
  return (
    <svg viewBox="0 0 110 110" width="104" height="104">
      <title>{`${label}: ${Math.round(value * 100)}%. Green above 80%, amber 60-80%, red below 60%.`}</title>
      <circle cx="55" cy="55" r={r} fill="none" stroke="rgba(148,163,184,.25)" strokeWidth="9" />
      <circle cx="55" cy="55" r={r} fill="none" stroke={col} strokeWidth="9" strokeLinecap="round"
        strokeDasharray={`${c * value} ${c}`} transform="rotate(-90 55 55)" />
      <text x="55" y="50" textAnchor="middle" fill="#94a3b8" fontSize="11">{label}</text>
      <text x="55" y="70" textAnchor="middle" fill="#fff" fontSize="22" fontWeight="700">{Math.round(value * 100)}%</text>
    </svg>
  );
}

export function Spark({ values, color = "#38bdf8" }: { values: number[]; color?: string }) {
  if (values.length < 2) return <svg width="100%" height="28" />;
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const pts = values.map((v, i) => `${(i / (values.length - 1)) * 100},${26 - ((v - lo) / (hi - lo || 1)) * 24}`).join(" ");
  return (
    <svg viewBox="0 0 100 28" preserveAspectRatio="none" width="100%" height="28">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

// ---- throughput forecast ------------------------------------------------------------------------------
export interface Future { name: string; color: string; values: number[] }
interface ForecastProps { actual: number[]; futures: Future[]; nowIdx: number; ymax: number; ideal?: number; startHour: number; height?: number }

/** Rolling units/hour. Solid = what happened. Dashed = what the rest of the shift looks like under each decision. */
export function ForecastChart2({ actual, futures, nowIdx, ymax, ideal, startHour, height = 130 }: ForecastProps) {
  const W = 420;
  const H = height;
  const n = actual.length;
  const x = (i: number) => 34 + (i / (n - 1)) * (W - 44);
  const y = (v: number) => H - 20 - (Math.min(Math.max(v, 0), ymax) / ymax) * (H - 32);
  const pts = (vals: number[], from: number, to: number) => vals.slice(from, to + 1).map((v, k) => `${x(from + k)},${y(v)}`).join(" ");
  const a = futures[0]?.values, b = futures[1]?.values;
  const band = a && b ? [...a.slice(nowIdx).map((v, k) => `${x(nowIdx + k)},${y(v)}`), ...b.slice(nowIdx).map((v, k) => `${x(nowIdx + k)},${y(v)}`).reverse()].join(" ") : "";
  const clock = (i: number) => { const m = Math.round(((i + 1) * 10) + startHour * 60); return `${String(Math.floor(m / 60) % 24).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`; };
  const tipAt = (f: number): Tip | null => {
    const i = Math.round(((f * W - 34) / (W - 44)) * (n - 1));
    if (i < 0 || i >= n) return null;
    const rows: TipRow[] = [];
    if (i <= nowIdx) rows.push({ color: "#3b82f6", label: "Actual", value: `${actual[i].toFixed(1)} /h` });
    else futures.forEach((fu) => rows.push({ color: fu.color, label: fu.name, value: `${fu.values[i].toFixed(1)} /h` }));
    if (ideal) rows.push({ color: "#94a3b8", label: "Ideal", value: `${ideal} /h` });
    return { title: `${clock(i)}  ${i <= nowIdx ? "(past)" : "(forecast)"}`, rows };
  };
  return (
    <Hoverable tipAt={tipAt}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1="34" x2={W - 10} y1={y(ymax * f)} y2={y(ymax * f)} stroke="rgba(148,163,184,.2)" />
            <text x="28" y={y(ymax * f) + 3} textAnchor="end" fill="#94a3b8" fontSize="9">{Math.round(ymax * f)}</text>
          </g>
        ))}
        {[0, 2, 4, 6, 8].map((h) => <text key={h} x={34 + (h / 8) * (W - 44)} y={H - 6} textAnchor="middle" fill="#94a3b8" fontSize="9">{`${(startHour + h) % 24}:00`}</text>)}
        {ideal && <line x1="34" x2={W - 10} y1={y(ideal)} y2={y(ideal)} stroke="rgba(203,213,225,.55)" strokeDasharray="2 3" />}
        {band && <polygon points={band} fill="rgba(239,68,68,.16)" />}
        {futures.map((fu) => <polyline key={fu.name} points={pts(fu.values, nowIdx, n - 1)} fill="none" stroke={fu.color} strokeWidth="1.8" strokeDasharray="5 3" />)}
        <polyline points={pts(actual, 0, Math.max(nowIdx, 1))} fill="none" stroke="#3b82f6" strokeWidth="2.2" />
        <line x1={x(nowIdx)} x2={x(nowIdx)} y1="6" y2={H - 20} stroke="rgba(255,255,255,.4)" strokeDasharray="2 3" />
      </svg>
    </Hoverable>
  );
}

// ---- dashboard charts -----------------------------------------------------------------------------------
export interface Series { name: string; color: string; values: number[]; dashed?: boolean }

export function LineChart({ series, yMax, yFmt = (v: number) => String(Math.round(v)), cursor, startHour = 6, hours = 8, height = 190, unit = "" }:
  { series: Series[]; yMax?: number; yFmt?: (v: number) => string; cursor?: number; startHour?: number; hours?: number; height?: number; unit?: string }) {
  const W = 560;
  const H = height;
  const n = Math.max(...series.map((s) => s.values.length), 2);
  const top = yMax ?? Math.max(...series.flatMap((s) => s.values), 1) * 1.05;
  const x = (i: number) => 40 + (i / (n - 1)) * (W - 52);
  const y = (v: number) => H - 22 - (Math.min(v, top) / top) * (H - 34);
  const tipAt = (f: number): Tip | null => {
    const i = Math.round(((f * W - 40) / (W - 52)) * (n - 1));
    if (i < 0 || i >= n) return null;
    const m = Math.round(startHour * 60 + (i / (n - 1)) * hours * 60);
    return { title: `${String(Math.floor(m / 60) % 24).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`, rows: series.map((s) => ({ color: s.color, label: s.name, value: `${yFmt(s.values[Math.min(i, s.values.length - 1)])}${unit}` })) };
  };
  return (
    <Hoverable tipAt={tipAt}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H}>
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line x1="40" x2={W - 12} y1={y(top * f)} y2={y(top * f)} stroke="rgba(148,163,184,.18)" />
            <text x="34" y={y(top * f) + 3} textAnchor="end" fill="#94a3b8" fontSize="9">{yFmt(top * f)}</text>
          </g>
        ))}
        {Array.from({ length: hours + 1 }).map((_, h) => (
          <text key={h} x={40 + (h / hours) * (W - 52)} y={H - 6} textAnchor="middle" fill="#94a3b8" fontSize="9">{`${(startHour + h) % 24}:00`}</text>
        ))}
        {series.map((s) => (
          <polyline key={s.name} fill="none" stroke={s.color} strokeWidth={s.dashed ? 1.4 : 2} strokeDasharray={s.dashed ? "5 4" : undefined}
            points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(" ")} />
        ))}
        {cursor !== undefined && <line x1={40 + cursor * (W - 52)} x2={40 + cursor * (W - 52)} y1="6" y2={H - 22} stroke="rgba(255,255,255,.5)" strokeDasharray="3 3" />}
      </svg>
    </Hoverable>
  );
}

export interface Bar { label: string; value: number; color?: string; sub?: string; tip?: string }

/** Horizontal bar chart (Pareto style) with a hover explanation per bar. */
export function HBars({ items, fmt = (v: number) => String(v), color = "#3b82f6", unit = "" }: { items: Bar[]; fmt?: (v: number) => string; color?: string; unit?: string }) {
  const max = Math.max(...items.map((i) => i.value), 1);
  const total = items.reduce((s, i) => s + i.value, 0) || 1;
  const [hover, setHover] = useState<number | null>(null);
  return (
    <div className="hbars">
      {items.map((i, k) => (
        <div key={i.label} className={`hbar ${hover === k ? "hot" : ""}`} onMouseEnter={() => setHover(k)} onMouseLeave={() => setHover(null)}>
          <span className="hl">{i.label}</span>
          <div className="ht"><div style={{ width: `${(i.value / max) * 100}%`, background: i.color ?? color }} /></div>
          <span className="hv">{fmt(i.value)}</span>
          {hover === k && <div className="tip hbtip"><b>{i.label}</b><div><span>Value</span><em>{fmt(i.value)}{unit}</em></div><div><span>Share of total</span><em>{Math.round((i.value / total) * 100)}%</em></div>{i.tip && <small>{i.tip}</small>}</div>}
        </div>
      ))}
    </div>
  );
}

export interface ColMeta { title: string; rows: TipRow[]; note?: string }

/** Columns with an optional OEE line and plan line; hover shows the shift behind each bar. */
export function Columns({ bars, colors, line, lineColor = "#fbbf24", plan, height = 190, yMax, meta }:
  { bars: number[]; colors: string[]; line?: number[]; lineColor?: string; plan?: number[]; height?: number; yMax?: number; meta?: ColMeta[] }) {
  const W = 560;
  const H = height;
  const n = bars.length;
  const top = yMax ?? Math.max(...bars, ...(plan ?? [0]), 1) * 1.1;
  const bw = (W - 52) / n;
  const y = (v: number) => H - 20 - (v / top) * (H - 32);
  const tipAt = (f: number): Tip | null => {
    const i = Math.floor(((f * W - 40) / (W - 52)) * n);
    if (i < 0 || i >= n || !meta) return null;
    return meta[i];
  };
  return (
    <Hoverable tipAt={tipAt}>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H}>
        {[0, 0.5, 1].map((f) => (
          <g key={f}>
            <line x1="40" x2={W - 8} y1={y(top * f)} y2={y(top * f)} stroke="rgba(148,163,184,.18)" />
            <text x="34" y={y(top * f) + 3} textAnchor="end" fill="#94a3b8" fontSize="9">{Math.round(top * f)}</text>
          </g>
        ))}
        {bars.map((v, i) => <rect key={i} x={40 + i * bw + bw * 0.12} y={y(v)} width={bw * 0.76} height={H - 20 - y(v)} rx="2" fill={colors[i]} />)}
        {plan && <polyline fill="none" stroke="rgba(255,255,255,.55)" strokeDasharray="4 3" points={plan.map((v, i) => `${40 + i * bw + bw / 2},${y(v)}`).join(" ")} />}
        {line && <polyline fill="none" stroke={lineColor} strokeWidth="1.8" points={line.map((v, i) => `${40 + i * bw + bw / 2},${y(v * top)}`).join(" ")} />}
      </svg>
    </Hoverable>
  );
}

/** Reusable hover wrapper for custom blocks (waterfall rows etc.). */
export function WithTip({ tip, children }: { tip: Tip; children: ReactNode }) {
  const [on, setOn] = useState(false);
  return (
    <div className="hover" onMouseEnter={() => setOn(true)} onMouseLeave={() => setOn(false)}>
      {children}
      {on && <div className="tip hbtip" style={{ left: "50%" }}><b>{tip.title}</b>{tip.rows.map((r, i) => <div key={i}><span>{r.label}</span><em>{r.value}</em></div>)}{tip.note && <small>{tip.note}</small>}</div>}
    </div>
  );
}
