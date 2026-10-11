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
