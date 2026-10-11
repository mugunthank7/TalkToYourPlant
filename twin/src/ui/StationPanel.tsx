import { useEffect, useRef, useState } from "react";
import { brainGet, brainPost } from "../brain";
import { camera } from "../clock";
import { anchorsFor, frameFor, type PathNode } from "../graphpath";
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
  intent?: string; suggestions?: string[];
}

function ReportView({ r, onAsk }: { r: Report; onAsk?: (q: string) => void }) {
  const proc = r.intent === "process";
  const sec = (label: string, items: string[] | undefined, open = false, numbered = false) =>
    items && items.length > 0 ? (
      <details open={open}>
        <summary>{label}</summary>
        {numbered ? <ol>{items.map((x, i) => <li key={i}>{x}</li>)}</ol> : <ul>{items.map((x, i) => <li key={i}>{x}</li>)}</ul>}
      </details>
    ) : null;
  return (
    <div>
      <div className={`sev ${r.severity}`}>
        <span className="tag">{r.severity.toUpperCase()}</span><span className="hd">{r.headline}</span>
      </div>
      {sec("Do now", r.do_now, true, true)}
      {sec(proc ? "The flow, station by station" : "What happened", r.what_happened, true, proc)}
      {sec(proc ? "How it runs" : "Impact", r.impact, true)}
      {sec("Who to page", r.contacts)}
      {sec("Part", r.parts)}
      {sec(proc ? "Support areas" : "Procedure", r.procedure, proc)}
      {onAsk && r.suggestions && r.suggestions.length > 0 && (
        <div className="chips3">{r.suggestions.map((s) => <button key={s} onClick={() => onAsk(s)}>{s}</button>)}</div>
      )}
      {r.sources && r.sources.length > 0 && <div className="note" style={{ marginTop: 10 }}>Sources: {r.sources.join(" · ")}</div>}
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

function StationView({ sid }: { sid: string }) {
  const [b, setB] = useState<Briefing | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [plan, setPlan] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    setB(null); setErr(null); setPlan(null); setMsg(null);
    let alive = true;
    const load = async () => {
      try { const d = await brainGet<Briefing>(`/station/${sid}`); if (alive) { setB(d); setErr(null); } }
      catch { if (alive) setErr("The brain is not running on :8100. Start it with brain/scripts/start_all.sh"); }
    };
    void load();
    const id = setInterval(load, 4000);
    return () => { alive = false; clearInterval(id); };
  }, [sid]);

  const askPlan = async () => {
    setBusy(true); setPlan(null);
    try { const r = await brainPost(`/station/${sid}/plan`); setPlan(r.plan ?? r.error ?? "no plan"); }
    catch { setPlan("The local LLM did not answer."); }
    setBusy(false);
  };
  const simulate = async () => {
    setMsg("Injecting…");
    try { const r = await brainPost(`/station/${sid}/simulate`, { repair_minutes: 30 }); setMsg(r.error ?? `Fault injected on ${r.injected?.machine ?? "the machine"}.`); }
    catch { setMsg("Could not reach the brain."); }
  };
  if (err) return <div className="pb"><div className="item bad">{err}</div></div>;
  if (!b) return <div className="pb"><div className="note">Asking the brain…</div></div>;
  if (b.error) return <div className="pb"><div className="item warn">{b.error}</div></div>;
  const bad = b.problem;
  return (
    <div className="pb">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <b style={{ fontSize: 15 }}>{sid} · {b.station.name}</b>
        <span className={`tagp ${bad ? "bad" : "ok"}`}>{b.engine_state ?? (bad ? "problem" : "running")}</span>
      </div>
      <div className="note" style={{ marginTop: 4 }}>{b.station.what_happens.replace(/\*\*/g, "")}</div>
      {b.diagnosis?.report
        ? <ReportView r={b.diagnosis.report} />
        : <><h5>What to do</h5><ol style={{ margin: 0, paddingLeft: 18 }}>{b.steps.map((s, i) => <li key={i}>{s}</li>)}</ol></>}
      <div className="row" style={{ marginTop: 14 }}>
        <button className="btn dng" onClick={simulate}>Simulate failure here</button>
        <button className="btn" onClick={askPlan} disabled={busy}>{busy ? "LLM thinking…" : "Ask the local LLM"}</button>
      </div>
      {msg && <div className="note" style={{ marginTop: 6 }}>{msg}</div>}
      {plan && <pre className="txt">{plan}</pre>}
      <h5>Machines</h5>
      {b.machines.map((m) => (
        <div key={m.id} className={`mach ${m.alert === "critical" || m.machine_state === "fault" ? "crit" : ""}`}>
          <b>{m.id}</b> {m.name} · {m.machine_state ?? m.status}{m.alert ? ` · ${m.alert}` : ""}
          {(m.vib_multiple || m.rul_min) ? <div className="mu">{m.vib_multiple ? `vibration ${m.vib_multiple}× healthy` : ""}{m.vib_multiple && m.rul_min ? " · " : ""}{m.rul_min ? `about ${Math.round(m.rul_min)} min of life left` : ""}</div> : null}
          {m.contributors && m.contributors.length > 0 && <div className="mu">Flagged because of {m.contributors.slice(0, 3).map((c) => c.signal).join(", ")}</div>}
          <div className="mu">{Object.entries(m.readings).slice(0, 4).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(" · ")}</div>
        </div>
      ))}
      {b.diagnosis && !b.diagnosis.report && <><h5>The brain says</h5><pre className="txt">{b.diagnosis.text}</pre></>}
      <details>
        <summary>Failure modes that can be simulated ({b.failure_catalog.length})</summary>
        {b.failure_catalog.map((f, i) => <div key={i} className="note" style={{ marginTop: 6 }}><b>{f.machine_id} {f.mode}</b> ({f.component}): {f.symptom}. Fix: {f.repair}, {f.repair_min} min, part {f.spare_part}.</div>)}
      </details>
    </div>
  );
}

const SUGGEST = ["Explain the production process", "Why is M05 red?", "What should I do?", "Can we keep running M05 2 more hours?", "What happens if the conveyor stops?", "How many cars have we built so far?"];

interface AnswerPath { nodes: PathNode[]; machine: string | null }

/** Light the answer up on the plant: nodes appear one by one, the camera frames the whole chain. */
function playPath(p: AnswerPath) {
  const st = useTwin.getState();
  if (!st.data) return;
  st.setGraphPath({ nodes: p.nodes, machine: p.machine, t0: performance.now() });
  camera.mode = "free";
  camera.goal = frameFor(anchorsFor(st.data.layout, p.nodes, p.machine));
}

function AskView() {
  const { data, selectedStation, selectQuiet } = useTwin();
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [log, setLog] = useState<{ q: string; a: string; report?: Report | null; path?: AnswerPath | null }[]>([]);
  const active = useTwin((s) => s.graphPath);
  const [sid] = useState(() => Math.random().toString(36).slice(2));
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => { end.current?.scrollIntoView({ block: "end" }); }, [log, busy]);
  const ask = async (text: string) => {
    text = text.trim();
    if (!text || busy) return;
    setBusy(true); setQ("");
    setLog((l) => [...l, { q: text, a: "" }]);
    try {
      const r = await brainPost("/chat", { message: text, session_id: sid, station_id: selectedStation });
      const first = r.highlight?.machine_ids?.[0];
      const gpath: PathNode[] = r.highlight?.graph_path?.length ? r.highlight.graph_path : first ? [{ id: first, kind: "machine" }] : [];
      const path: AnswerPath | null = gpath.length ? { nodes: gpath, machine: first ?? null } : null;
      setLog((l) => l.map((m, i) => (i === l.length - 1 ? { q: text, a: r.answer, report: r.report, path } : m)));
      if (path) playPath(path); else useTwin.getState().setGraphPath(null);
      const st = data?.layout.machines.find((m) => m.id === first)?.station;
      if (st) selectQuiet(st);
    } catch { setLog((l) => l.map((m, i) => (i === l.length - 1 ? { q: text, a: "The brain is not running on :8100. Start it with brain/scripts/start_all.sh" } : m))); }
    setBusy(false);
  };
  return (
    <div className="askv">
      <div className="log">
        {log.length === 0 && (
          <div>
            <div className="note">Ask about a machine, a fault, what to do, or what happens if something stops.{selectedStation ? ` Questions are about ${selectedStation}.` : ""}</div>
            <div className="chips3">{SUGGEST.map((s) => <button key={s} onClick={() => void ask(s)}>{s}</button>)}</div>
          </div>
        )}
        {log.map((m, i) => (
          <div key={i} style={{ display: "contents" }}>
            <div className="bub">{m.q}</div>
            <div className="ans">
              {m.report ? <ReportView r={m.report} onAsk={(s) => void ask(s)} /> : m.a ? <pre className="txt" style={{ margin: 0 }}>{m.a}</pre> : <div className="note">Thinking…</div>}
              {m.path && (
                <div className="row" style={{ marginTop: 8 }}>
                  <button className="btn pri" onClick={() => playPath(m.path!)}>{m.path.nodes.length > 1 ? "Show the path on the plant" : "Show on the plant"}</button>
                  {active && <button className="btn" onClick={() => useTwin.getState().setGraphPath(null)}>Hide</button>}
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={end} />
      </div>
      <div className="compose">
        <input type="text" className="inp" value={q} placeholder="Why is M05 red?" onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && void ask(q)} />
        <button className="btn pri" onClick={() => void ask(q)} disabled={busy}>Ask</button>
      </div>
    </div>
  );
}

/** Right dock: station briefing and chat share one panel so nothing overlaps the scene. */
export function SidePanel() {
  const sid = useTwin((s) => s.selectedStation);
  const setSid = useTwin((s) => s.setSelectedStation);
  const askOpen = useTwin((s) => s.askOpen);
  const setAskOpen = useTwin((s) => s.setAskOpen);
  const tab = useTwin((s) => s.sideTab);
  const setTab = useTwin((s) => s.setSideTab);
  useEffect(() => { if (askOpen) setTab("ask"); }, [askOpen, setTab]);
  if (!sid && !askOpen) return null;
  const shown = tab === "station" && !sid ? "ask" : tab;
  const close = () => { setSid(null); setAskOpen(false); useTwin.getState().setGraphPath(null); };
  return (
    <div className={`dock gl ${shown === "ask" ? "fill" : ""}`}>
      <div className="tabs3">
        {sid && <button className={shown === "station" ? "on" : ""} onClick={() => setTab("station")}>{sid}</button>}
        <button className={shown === "ask" ? "on" : ""} onClick={() => { setAskOpen(true); setTab("ask"); }}>Ask</button>
        <button className="x" onClick={close} aria-label="Close">×</button>
      </div>
      {shown === "station" && sid ? <StationView sid={sid} /> : <AskView />}
    </div>
  );
}
