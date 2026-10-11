export function Gauge({ value, label }: { value: number; label: string }) {
  const r = 44;
  const c = 2 * Math.PI * r;
  const col = value > 0.8 ? "#22c55e" : value > 0.6 ? "#f59e0b" : "#ef4444";
  return (
    <svg viewBox="0 0 110 110" width="104" height="104">
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

interface ForecastProps { actual: number[]; forecast: number[]; band: number; nowIdx: number; ymax: number }
/** Rolling units/hour: solid actual, dashed forecast with confidence band. x = shift hours. */
export function ForecastChart({ actual, forecast, band, nowIdx, ymax }: ForecastProps) {
  const W = 420;
  const H = 130;
  const n = actual.length;
  const x = (i: number) => 34 + (i / (n - 1)) * (W - 44);
  const y = (v: number) => H - 20 - (Math.min(v, ymax) / ymax) * (H - 32);
  const line = (vals: (number | null)[], from: number, to: number) =>
    vals.slice(from, to + 1).map((v, k) => `${x(from + k)},${y(v ?? 0)}`).join(" ");
  const bandPts = [
    ...forecast.slice(nowIdx).map((v, k) => `${x(nowIdx + k)},${y(v + band)}`),
    ...forecast.slice(nowIdx).map((v, k) => `${x(nowIdx + k)},${y(Math.max(v - band, 0))}`).reverse(),
  ].join(" ");
  const ticks = [0, 1, 2, 3, 4, 5, 6, 7, 8];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line x1="34" x2={W - 10} y1={y(ymax * f)} y2={y(ymax * f)} stroke="rgba(148,163,184,.2)" />
          <text x="28" y={y(ymax * f) + 3} textAnchor="end" fill="#94a3b8" fontSize="9">{Math.round(ymax * f)}</text>
        </g>
      ))}
      {ticks.map((h) => (
        <text key={h} x={34 + (h / 8) * (W - 44)} y={H - 6} textAnchor="middle" fill="#94a3b8" fontSize="9">{`${(6 + h) % 24}:00`}</text>
      ))}
      <polygon points={bandPts} fill="rgba(56,189,248,.18)" />
      <polyline points={line(forecast, nowIdx, n - 1)} fill="none" stroke="#7dd3fc" strokeWidth="1.5" strokeDasharray="4 3" />
      <polyline points={line(actual, 0, Math.max(nowIdx, 1))} fill="none" stroke="#3b82f6" strokeWidth="2" />
      <line x1={x(nowIdx)} x2={x(nowIdx)} y1="6" y2={H - 20} stroke="rgba(255,255,255,.35)" strokeDasharray="2 3" />
    </svg>
  );
}

export interface Series { name: string; color: string; values: number[]; dashed?: boolean }

/** Multi-series line chart over a shift. x labels are hours; `cursor` is 0..1 (the sim clock). */
export function LineChart({ series, yMax, yFmt = (v: number) => String(Math.round(v)), cursor, startHour = 6, hours = 8, height = 190 }:
  { series: Series[]; yMax?: number; yFmt?: (v: number) => string; cursor?: number; startHour?: number; hours?: number; height?: number }) {
  const W = 560;
  const H = height;
  const n = Math.max(...series.map((s) => s.values.length), 2);
  const top = yMax ?? Math.max(...series.flatMap((s) => s.values), 1) * 1.05;
  const x = (i: number) => 40 + (i / (n - 1)) * (W - 52);
  const y = (v: number) => H - 22 - (Math.min(v, top) / top) * (H - 34);
  return (
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
  );
}

export interface Bar { label: string; value: number; color?: string; sub?: string }

/** Horizontal bar chart (Pareto style). */
export function HBars({ items, fmt = (v: number) => String(v), color = "#3b82f6" }: { items: Bar[]; fmt?: (v: number) => string; color?: string }) {
  const max = Math.max(...items.map((i) => i.value), 1);
  return (
    <div className="hbars">
      {items.map((i) => (
        <div key={i.label} className="hbar">
          <span className="hl">{i.label}</span>
          <div className="ht"><div style={{ width: `${(i.value / max) * 100}%`, background: i.color ?? color }} /></div>
          <span className="hv">{fmt(i.value)}</span>
        </div>
      ))}
    </div>
  );
}

/** Columns with an optional line overlay (e.g. units per shift and OEE). */
export function Columns({ bars, colors, line, lineColor = "#fbbf24", plan, height = 190, yMax }:
  { bars: number[]; colors: string[]; line?: number[]; lineColor?: string; plan?: number[]; height?: number; yMax?: number }) {
  const W = 560;
  const H = height;
  const n = bars.length;
  const top = yMax ?? Math.max(...bars, ...(plan ?? [0]), 1) * 1.1;
  const bw = (W - 52) / n;
  const y = (v: number) => H - 20 - (v / top) * (H - 32);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H}>
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line x1="40" x2={W - 8} y1={y(top * f)} y2={y(top * f)} stroke="rgba(148,163,184,.18)" />
          <text x="34" y={y(top * f) + 3} textAnchor="end" fill="#94a3b8" fontSize="9">{Math.round(top * f)}</text>
        </g>
      ))}
      {bars.map((v, i) => (
        <rect key={i} x={40 + i * bw + bw * 0.12} y={y(v)} width={bw * 0.76} height={H - 20 - y(v)} rx="2" fill={colors[i]} />
      ))}
      {plan && <polyline fill="none" stroke="rgba(255,255,255,.55)" strokeDasharray="4 3" points={plan.map((v, i) => `${40 + i * bw + bw / 2},${y(v)}`).join(" ")} />}
      {line && <polyline fill="none" stroke={lineColor} strokeWidth="1.8" points={line.map((v, i) => `${40 + i * bw + bw / 2},${y(v * top)}`).join(" ")} />}
    </svg>
  );
}
