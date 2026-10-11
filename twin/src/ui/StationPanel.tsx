import { useEffect, useState } from "react";
import { brainGet, brainPost } from "../brain";
import { useTwin } from "../state";

interface Machine {
  id: string; name: string; type: string; status?: string; machine_state?: string; alert?: string | null;
  vib_multiple?: number | null; rul_min?: number | null; readings: Record<string, number>;
  contributors?: { signal: string; shap: number }[] | null; evidence?: string[] | null;
  open_work_orders?: { id: string; status: string }[] | null;
}
interface Report {
  title: string; severity: "critical" | "warning" | "ok" | "info"; headline: string;
  what_happened?: string[]; impact?: string[]; do_now?: string[]; contacts?: string[]; parts?: string[]; procedure?: string[]; sources?: string[];
}

function ReportView({ r }: { r: Report }) {
  const sec = (label: string, items?: string[], numbered = false) =>
    items && items.length > 0 ? (
      <div className="rsec">
        <h5>{label}</h5>
        {numbered ? <ol>{items.map((x, i) => <li key={i}>{x}</li>)}</ol> : <ul>{items.map((x, i) => <li key={i}>{x}</li>)}</ul>}
      </div>
    ) : null;
  return (
    <div className={`report ${r.severity}`}>
      <div className="rhead"><span className="rsev">{r.severity.toUpperCase()}</span> {r.headline}</div>
      {sec("What happened", r.what_happened)}
      {sec("Impact", r.impact)}
      {sec("Do now", r.do_now, true)}
      {sec("Who to page", r.contacts)}
      {sec("Part", r.parts)}
      {sec("Procedure", r.procedure)}
      {r.sources && r.sources.length > 0 && <div className="stmut">Sources: {r.sources.join(" · ")}</div>}
    </div>
  );
}

interface Briefing {
  error?: string;
  station: { id: string; name: string; what_happens: string; upstream: string[]; downstream: string[]; people?: string };
  engine_state?: string; reason?: string; problem: boolean; focus_machine?: string; source?: string;
  machines: Machine[]; steps: string[];
  escalation?: { shift: string; chain: { level: string; name: string; role: string; extension: string; page_after_min?: number }[] };
  diagnosis?: { text: string; report?: Report | null; citations: string[]; latency_s: number };
  failure_catalog: { machine_id: string; mode: string; component: string; symptom: string; cause: string; repair: string; spare_part: string; repair_min: number }[];
}

export function StationPanel() {
  const sid = useTwin((s) => s.selectedStation);
  const close = useTwin((s) => s.setSelectedStation);
  const [b, setB] = useState<Briefing | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [plan, setPlan] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    setB(null); setErr(null); setPlan(null); setMsg(null);
    if (!sid) return;
    let alive = true;
    const load = async () => {
      try { const d = await brainGet<Briefing>(`/station/${sid}`); if (alive) { setB(d); setErr(null); } }
      catch (e) { if (alive) setErr("Brain not reachable on :8100. Start it with brain/scripts/start_all.sh"); }
    };
    void load();
    const id = setInterval(load, 4000);
    return () => { alive = false; clearInterval(id); };
  }, [sid]);

  if (!sid) return null;
  const askPlan = async () => {
    setBusy(true); setPlan(null);
    try { const r = await brainPost(`/station/${sid}/plan`); setPlan(r.plan ?? r.error ?? "no plan"); }
    catch { setPlan("local LLM did not answer"); }
    setBusy(false);
  };
  const simulate = async () => {
    setMsg("injecting...");
    try { const r = await brainPost(`/station/${sid}/simulate`, { repair_minutes: 30 }); setMsg(r.error ?? `fault injected on ${r.injected?.machine ?? "machine"}`); }
    catch { setMsg("failed"); }
  };
  const bad = b?.problem;
  return (
    <div className="card stpanel">
      <div className="card-h">
        <span>{sid} {b?.station.name ?? ""}</span>
        <span>
          {b && <span className={`stpill ${bad ? "bad" : "ok"}`}>{b.engine_state ?? (bad ? "problem" : "running")}</span>}
          <button className="stx" onClick={() => close(null)} aria-label="Close">x</button>
        </span>
      </div>
      {err && <div className="fitem bad">{err}</div>}
      {!b && !err && <div className="stmut">Asking the brain...</div>}
      {b && !b.error && (
        <>
          <div className="stmut">{b.station.what_happens}</div>
          {bad && <div className="fitem bad"><b>Problem</b> {b.reason || b.focus_machine}: see below</div>}
          {b.diagnosis?.report
            ? <ReportView r={b.diagnosis.report} />
            : (<><h4>What to do</h4><ol className="stsub">{b.steps.map((s, i) => <li key={i}>{s}</li>)}</ol></>)}
          <div className="frow">
            <button onClick={askPlan} disabled={busy}>{busy ? "LLM thinking (up to 1 min)..." : "Ask the local LLM for a plan"}</button>
            <button className="danger" onClick={simulate}>Simulate failure here</button>
          </div>
          {msg && <div className="stmut">{msg}</div>}
          {plan && <pre className="stpre">{plan}</pre>}
          <h4>Machines</h4>
          {b.machines.map((m) => (
            <div key={m.id} className={`fitem ${m.alert === "critical" || m.machine_state === "fault" ? "bad" : m.alert ? "warn" : "ok"}`}>
              <b>{m.id}</b> {m.name}: {m.machine_state ?? m.status}{m.alert ? `, ${m.alert} alert` : ""}
              {m.vib_multiple ? `, vibration ${m.vib_multiple}x` : ""}{m.rul_min ? `, RUL ${Math.round(m.rul_min)} min` : ""}
              {m.contributors && m.contributors.length > 0 && (
                <div className="stmut">why flagged: {m.contributors.slice(0, 3).map((c) => `${c.signal} ${c.shap}`).join(", ")}</div>
              )}
              <div className="stmut">{Object.entries(m.readings).slice(0, 5).map(([k, v]) => `${k} ${v}`).join(" · ")}</div>
            </div>
          ))}
          {b.diagnosis && !b.diagnosis.report && (<><h4>Brain says</h4><pre className="stpre">{b.diagnosis.text}</pre></>)}
          <details><summary>Failure modes that can be simulated ({b.failure_catalog.length})</summary>
            {b.failure_catalog.map((f, i) => <div key={i} className="stmut"><b>{f.machine_id} {f.mode}</b> ({f.component}): {f.symptom}; fix: {f.repair}, {f.repair_min} min, part {f.spare_part}</div>)}
          </details>
        </>
      )}
    </div>
  );
}
