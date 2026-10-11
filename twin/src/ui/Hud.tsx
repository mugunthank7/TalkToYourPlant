import { useEffect, useState } from "react";
import { camera, clock, fmt, VIEWS } from "../clock";
import { m05Status } from "../data";
import { useTwin } from "../state";

const SPEEDS = [1, 10, 60, 300, 1200];
const STATUS_TEXT = {
  healthy: ["Weld robot 2: running normally", "ok"],
  alert: ["ALERT: weld robot 2 bearing wear detected", "bad"],
  repair: ["Technician repairing joint 1 bearing", "warn"],
  repaired: ["Weld robot 2 repaired, back to normal", "ok"],
} as const;

export function Hud() {
  const { data, shift, setShift } = useTwin();
  const [, setTick] = useState(0);
  const [speed, setSpeed] = useState(clock.speed);
  const [playing, setPlaying] = useState(clock.playing);

  useEffect(() => {
    const id = setInterval(() => setTick((n) => n + 1), 150);
    return () => clearInterval(id);
  }, []);

  if (!data) return null;
  const st = m05Status(clock.t, shift, data.hero);
  const [text, cls] = STATUS_TEXT[st];
  const jump = (t: number) => { clock.t = Math.max(0, t); };

  return (
    <div className="hud">
      <div className="panel">
        <div className="title">Talk to Your Plant <span>digital twin</span></div>
        <div className="time">{fmt(clock.t, shift)}</div>
        <div className="row">
          <button onClick={() => { clock.playing = !clock.playing; setPlaying(clock.playing); }}>{playing ? "Pause" : "Play"}</button>
          {(["A", "B"] as const).map((s) => (
            <button key={s} className={s === shift ? "on" : ""} onClick={() => { setShift(s); jump(0); }}>Shift {s}</button>
          ))}
        </div>
        <div className="row">
          {SPEEDS.map((v) => (
            <button key={v} className={v === speed ? "on" : ""} onClick={() => { clock.speed = v; setSpeed(v); }}>{v}x</button>
          ))}
        </div>
        <input type="range" min={0} max={clock.max} step={10} value={clock.t} onChange={(e) => jump(Number(e.target.value))} />
        {shift === "A" && (
          <div className="row">
            <button onClick={() => jump(data.hero.t_alert_s - 120)}>Jump to alert</button>
            <button onClick={() => jump(data.hero.t_onset_s)}>Fault onset</button>
          </div>
        )}
        <div className="row">
          {(Object.keys(VIEWS) as (keyof typeof VIEWS)[]).map((k) => (
            <button key={k} onClick={() => { camera.goal = { pos: [...VIEWS[k].pos], target: [...VIEWS[k].target] }; }}>{k}</button>
          ))}
        </div>
        <div className={`status ${cls}`}>{text}</div>
      </div>
      <div className="legend">
        <i style={{ background: "#f97316" }} /> operator <i style={{ background: "#fbbf24" }} /> relief
        <i style={{ background: "#38bdf8" }} /> inspector <i style={{ background: "#22c55e" }} /> supervisor
        <i style={{ background: "#ef4444" }} /> technician
      </div>
    </div>
  );
}
