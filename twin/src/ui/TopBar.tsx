import { useEffect, useState } from "react";
import { clock, ctl, fmt } from "../clock";
import { connectSim, disconnectSim } from "../simlink";
import { useTwin } from "../state";

export function TopBar() {
  const { shift, setShift, view, setView, sim } = useTwin();
  useEffect(() => { if (new URLSearchParams(location.search).get("sim") !== null) connectSim(new URLSearchParams(location.search).get("sim") || undefined); }, []);
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
        <button className="pill" onClick={() => ctl.play(!clock.playing)}>{clock.playing ? "❚❚" : "▶"}</button>
        <button className={`pill simbtn ${sim}`} title="Connect to the SimPy engine (cd sim && .venv/bin/uvicorn plantsim.api:app --port 8000)" onClick={() => (sim === "off" ? connectSim() : disconnectSim())}>{sim === "on" ? "● SimPy live" : sim === "connecting" ? "SimPy…" : "SimPy off"}</button>
        <div className="clockbox">
          <b>{fmt(clock.t, shift)}</b>
          <span>Oct 10, 2026</span>
        </div>
        <div className="live"><i /> LIVE</div>
      </div>
    </div>
  );
}
