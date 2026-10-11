import { useEffect, useState } from "react";
import { clock, ctl, fmt } from "../clock";
import { connectSim } from "../simlink";
import { useTwin } from "../state";

export function TopBar() {
  const { shift, setShift, view, setView, sim } = useTwin();
  // The engine is always the source of truth: connect on load and keep retrying (the client-side model in plant.ts covers the gap).
  useEffect(() => {
    const url = new URLSearchParams(location.search).get("sim") || undefined;
    connectSim(url);
    const id = setInterval(() => { if (useTwin.getState().sim === "off") connectSim(url); }, 3000);
    return () => clearInterval(id);
  }, []);
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
          <button key={s} className={`pill ${s === shift ? "on" : ""}`} onClick={() => { setShift(s); if (sim === "on") ctl.send?.({ type: "control", action: "reset", shift: s }); else clock.t = 0; }}>Shift {s}</button>
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
