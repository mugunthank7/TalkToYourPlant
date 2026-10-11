import { useEffect, useState } from "react";
import { clock, fmt } from "../clock";
import { useTwin } from "../state";

export function TopBar() {
  const { shift, setShift, view, setView } = useTwin();
  const [, set] = useState(0);
  useEffect(() => {
    const id = setInterval(() => set((n) => n + 1), 250);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="topbar">
      <div className="brand">
        <span className="bolt">⚡</span>
        <b>Voltline EV Works</b>
        <i />
        <nav className="tabs">
          <button className={view === "live" ? "on" : ""} onClick={() => setView("live")}>Live 3D</button>
          <button className={view === "dash" ? "on" : ""} onClick={() => setView("dash")}>Dashboard</button>
        </nav>
      </div>
      <div className="topright">
        {(["A", "B"] as const).map((s) => (
          <button key={s} className={`pill ${s === shift ? "on" : ""}`} onClick={() => { setShift(s); clock.t = 0; }}>Shift {s}</button>
        ))}
        <button className="pill" onClick={() => { clock.playing = !clock.playing; }}>{clock.playing ? "❚❚" : "▶"}</button>
        <div className="clockbox">
          <b>{fmt(clock.t, shift)}</b>
          <span>Oct 10, 2026</span>
        </div>
        <div className="live"><i /> LIVE</div>
      </div>
    </div>
  );
}
