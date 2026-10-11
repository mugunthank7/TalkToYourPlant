import { clock } from "../../clock";
import { m05Status } from "../../data";
import { useTwin } from "../../state";
import { liveAt } from "../../ui/live";
import { AtStation, Andon, B, Chair, Cyl, GlassWall, Npc, Pad, Plant, RB, Screen, TextBoard, type V3 } from "../kit";

/** Seats / standing spots for scheduled people, relative to the station centre: [x, z, faceX, faceZ]. Mirrored in data/plantdata/layout.py. */
export const S11_TABLES: [number, number][] = [[3.6, -1.0], [5.8, 0.4], [4.2, 2.4]];

function useAlert() {
  const data = useTwin.getState().data!;
  return () => m05Status(clock.t, useTwin.getState().shift, data.hero) === "alert";
}

const GREEN = "#22c55e";
const RED = "#ef4444";

export function S11() {
  const alert = useAlert();
  const data = useTwin((s) => s.data)!;

  // ---- video wall: station map, machine list, OEE gauge and an alarm tile --------------------------
  const drawWall = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    const st = useTwin.getState();
    const a = alert();
    ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
    // left list
    ctx.fillStyle = "#111c33"; ctx.fillRect(6, 6, 150, h - 12);
    ctx.font = "600 11px sans-serif"; ctx.fillStyle = "#94a3b8"; ctx.fillText("MACHINE STATUS", 14, 22);
    data.layout.machines.filter((m) => m.type !== "conveyor").slice(0, 10).forEach((m, i) => {
      const bad = a && m.id === "M05";
      ctx.fillStyle = bad ? RED : GREEN; ctx.beginPath(); ctx.arc(20, 40 + i * 20, 4, 0, 7); ctx.fill();
      ctx.fillStyle = bad ? "#fecaca" : "#cbd5e1"; ctx.font = "11px sans-serif"; ctx.fillText(`${m.id} ${m.name.slice(0, 16)}`, 30, 44 + i * 20);
    });
    // centre minimap
    ctx.fillStyle = "#0f1a2e"; ctx.fillRect(162, 6, 210, h - 12);
    const { width_m, depth_m } = data.layout.plant;
    const sx = 198 / width_m, sz = 150 / depth_m;
    data.layout.stations.forEach((s) => {
      const hot = a && s.id === "S06";
      ctx.fillStyle = hot ? "#7f1d1d" : "#1e3a5f"; ctx.strokeStyle = hot ? RED : "#38bdf8"; ctx.lineWidth = hot ? 2 : 1;
      ctx.fillRect(168 + (s.x - s.w / 2) * sx, 30 + (s.z - s.d / 2) * sz, s.w * sx, s.d * sz);
      ctx.strokeRect(168 + (s.x - s.w / 2) * sx, 30 + (s.z - s.d / 2) * sz, s.w * sx, s.d * sz);
    });
    ctx.fillStyle = "#94a3b8"; ctx.font = "600 11px sans-serif"; ctx.fillText("LIVE PLANT MAP", 170, 22);
    // right: gauge + alarm
    const L = liveAt(clock.t, st.shift, data.kpi, data.hero);
    ctx.strokeStyle = "rgba(148,163,184,.3)"; ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(440, 60, 30, 0, 7); ctx.stroke();
    ctx.strokeStyle = L.oee > 0.8 ? GREEN : "#f59e0b"; ctx.beginPath(); ctx.arc(440, 60, 30, -Math.PI / 2, -Math.PI / 2 + L.oee * 6.283); ctx.stroke();
    ctx.fillStyle = "#fff"; ctx.font = "700 16px sans-serif"; ctx.textAlign = "center"; ctx.fillText(`${Math.round(L.oee * 100)}%`, 440, 66);
    ctx.fillStyle = "#94a3b8"; ctx.font = "10px sans-serif"; ctx.fillText("OEE", 440, 104);
    ctx.fillStyle = a ? RED : "#14532d"; ctx.fillRect(386, 124, 120, 110);
    ctx.fillStyle = "#fff"; ctx.font = "700 13px sans-serif";
    ctx.fillText(a ? "ALARM" : "ALL CLEAR", 446, 160);
    ctx.font = "11px sans-serif"; ctx.fillText(a ? "M05 BEARING WEAR" : "LINE RUNNING", 446, 182);
    if (a) ctx.fillText(`RUL ${Math.ceil(L.rulMin ?? 0)} MIN`, 446, 202);
    ctx.textAlign = "left";
  };

  const drawBoard = (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    const a = alert();
    ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
    ctx.fillStyle = "#94a3b8"; ctx.font = "600 13px sans-serif"; ctx.fillText("ANDON BOARD", 12, 20);
    data.layout.stations.forEach((s, i) => {
      const col = i % 4, row = Math.floor(i / 4);
      const bad = a && s.id === "S06";
      ctx.fillStyle = bad ? RED : "#16a34a"; ctx.fillRect(12 + col * 62, 32 + row * 50, 54, 42);
      ctx.fillStyle = "#fff"; ctx.font = "700 14px sans-serif"; ctx.fillText(s.id, 20 + col * 62, 59 + row * 50);
    });
  };

  const trend = (seed: number) => (ctx: CanvasRenderingContext2D, w: number, h: number) => {
    ctx.fillStyle = "#07101f"; ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = "#1e3a5f"; ctx.lineWidth = 1;
    for (let i = 1; i < 4; i++) { ctx.beginPath(); ctx.moveTo(0, (h * i) / 4); ctx.lineTo(w, (h * i) / 4); ctx.stroke(); }
    ctx.strokeStyle = seed % 2 ? "#38bdf8" : "#22c55e"; ctx.lineWidth = 2.5; ctx.beginPath();
    for (let x = 0; x < w; x += 8) {
      const y = h / 2 + Math.sin((x + clock.t * 3 + seed * 40) / 28) * h * 0.22 + Math.sin((x + seed * 9) / 9) * h * 0.06;
      x === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.stroke();
  };

  const tableSeats = (tx: number, tz: number): [number, number, number][] =>
    [0, 1, 2, 3].map((i) => [tx + Math.cos((i * Math.PI) / 2 + 0.4) * 1.05, tz + Math.sin((i * Math.PI) / 2 + 0.4) * 1.05, (i * Math.PI) / 2 + 0.4]);

  return (
    <AtStation id="S11">
      {() => (
        <group>
          <Pad w={16} d={10} tone="#eef1f5" />

          {/* ---- walls ---- */}
          <B p={[-3.9, 1.6, -5]} s={[8.2, 3.2, 0.25]} c="#f1f3f6" rough={0.8} metal={0.05} />
          <B p={[4.9, 1.6, -5]} s={[6.4, 3.2, 0.25]} c="#f1f3f6" rough={0.8} metal={0.05} />
          <B p={[0.9, 2.9, -5]} s={[1.4, 0.6, 0.25]} c="#f1f3f6" rough={0.8} metal={0.05} />
          <B p={[8, 1.6, 0]} s={[0.25, 3.2, 10]} c="#eceff3" rough={0.8} metal={0.05} />
          <B p={[0, 0.06, -5]} s={[16, 0.12, 0.27]} c="#9aa7b5" />
          {/* glass: west + south of the control room, partition to the break area */}
          <GlassWall p={[-8, 0, 0]} len={10} axis="z" />
          <GlassWall p={[-3.5, 0, 5]} len={9} axis="x" />
          <GlassWall p={[1, 0, 0.6]} len={8.8} axis="z" />
          {/* door frame */}
          <B p={[0.2, 1.4, -5]} s={[0.1, 2.8, 0.3]} c="#64748b" metal={0.6} />
          <B p={[1.6, 1.4, -5]} s={[0.1, 2.8, 0.3]} c="#64748b" metal={0.6} />

          {/* ---- control room ---- */}
          {/* video wall (3 x 2 look: one big canvas in a black frame) */}
          <B p={[-5, 2.05, -4.82]} s={[5.0, 2.5, 0.12]} c="#0a0e18" metal={0.6} />
          <Screen p={[-5, 2.05, -4.74]} s={[4.8, 2.3]} draw={drawWall} bright={1.15} />
          <B p={[-1.3, 1.9, -4.86]} s={[2.1, 1.7, 0.08]} c="#0a0e18" />
          <Screen p={[-1.3, 1.9, -4.8]} s={[1.95, 1.55]} draw={drawBoard} />

          {/* curved console: centre + two angled wings */}
          <RB p={[-4.8, 0.74, -2.7]} s={[3.8, 0.1, 1.0]} c="#d9b98f" rough={0.6} metal={0.05} r={0.05} />
          <B p={[-4.8, 0.37, -2.7]} s={[3.6, 0.7, 0.9]} c="#475569" />
          <RB p={[-6.95, 0.74, -1.95]} s={[2.0, 0.1, 0.95]} c="#d9b98f" rough={0.6} metal={0.05} rot={[0, 0.55, 0]} r={0.05} />
          <B p={[-6.95, 0.37, -1.95]} s={[1.8, 0.7, 0.8]} c="#475569" rot={[0, 0.55, 0]} />
          <RB p={[-2.65, 0.74, -1.95]} s={[2.0, 0.1, 0.95]} c="#d9b98f" rough={0.6} metal={0.05} rot={[0, -0.55, 0]} r={0.05} />
          <B p={[-2.65, 0.37, -1.95]} s={[1.8, 0.7, 0.8]} c="#475569" rot={[0, -0.55, 0]} />
          {[[-5.9, -2.95, 0], [-4.8, -2.95, 1], [-3.7, -2.95, 2]].map(([x, z, k]) => (
            <group key={k} position={[x, 0, z]}>
              <B p={[0, 1.18, -0.05]} s={[0.98, 0.58, 0.04]} c="#0b0f19" />
              <Screen p={[0, 1.18, -0.027]} s={[0.92, 0.52]} draw={trend(k)} />
              <B p={[0, 0.88, 0.02]} s={[0.06, 0.28, 0.06]} c="#1f2937" />
            </group>
          ))}
          {[[-7.2, -2.1, 0.55, 3], [-2.4, -2.1, -0.55, 4]].map(([x, z, r, k]) => (
            <group key={k} position={[x, 0, z]} rotation={[0, r, 0]}>
              <B p={[0, 1.14, 0]} s={[0.84, 0.5, 0.04]} c="#0b0f19" />
              <Screen p={[0, 1.14, 0.023]} s={[0.78, 0.44]} draw={trend(k)} />
              <B p={[0, 0.88, -0.02]} s={[0.06, 0.28, 0.06]} c="#1f2937" />
            </group>
          ))}
          <B p={[-4.8, 0.8, -2.35]} s={[0.6, 0.03, 0.2]} c="#111827" />
          {/* console operator (seated, faces the wall) */}
          <Chair p={[-4.8, 0, -1.2]} rotY={Math.PI} c="#334155" />
          <Npc p={[-4.8, 0, -1.25]} rotY={Math.PI} color="#22c55e" pose="sit" seed={1} />

          {/* supervisor desk (scheduled supervisor stands here) */}
          <RB p={[-4.5, 0.74, 3.0]} s={[3.0, 0.08, 1.1]} c="#d9b98f" rough={0.6} metal={0.05} />
          <B p={[-5.7, 0.37, 3.0]} s={[0.08, 0.74, 1.0]} c="#475569" />
          <B p={[-3.3, 0.37, 3.0]} s={[0.08, 0.74, 1.0]} c="#475569" />
          <B p={[-4.2, 0.79, 3.1]} s={[0.55, 0.02, 0.38]} c="#e5e7eb" />
          <B p={[-4.2, 0.95, 2.92]} s={[0.55, 0.34, 0.02]} c="#1f2937" rot={[-0.2, 0, 0]} />
          <B p={[-5.1, 0.45, 3.45]} s={[0.4, 0.5, 0.4]} c="#1f2937" />
          <Plant p={[-7.3, 0, 4.2]} s={1.1} />
          <Plant p={[0.5, 0, 4.3]} />
          <Cyl p={[-0.5, 0.25, 4.3]} r={0.2} h={0.5} c="#64748b" metal={0.4} />

          {/* ---- break area ---- */}
          {S11_TABLES.map(([tx, tz], i) => (
            <group key={i}>
              <Cyl p={[tx, 0.74, tz]} r={0.9} h={0.06} c="#e8d7b8" metal={0.05} rough={0.6} />
              <Cyl p={[tx, 0.37, tz]} r={0.07} h={0.74} c="#64748b" />
              <Cyl p={[tx, 0.02, tz]} r={0.35} h={0.04} c="#475569" />
              {tableSeats(tx, tz).map(([x, z, a], k) => (
                <Chair key={k} p={[x, 0, z]} rotY={-a + Math.PI / 2} c="#a8b0bb" />
              ))}
              <Cyl p={[tx + 0.2, 0.8, tz]} r={0.05} h={0.08} c="#ffffff" rough={0.3} />
            </group>
          ))}
          {/* coffee table + machine, vending machine */}
          <B p={[3.4, 0.82, -4.3]} s={[1.9, 0.06, 0.8]} c="#d9b98f" rough={0.6} metal={0.05} />
          {[[2.55, -4.0], [4.25, -4.0], [2.55, -4.6], [4.25, -4.6]].map(([x, z], i) => <B key={i} p={[x, 0.4, z]} s={[0.06, 0.8, 0.06]} c="#1d4ed8" />)}
          <RB p={[3.2, 1.1, -4.4]} s={[0.5, 0.5, 0.45]} c="#111827" metal={0.5} />
          <B p={[3.2, 1.15, -4.17]} s={[0.3, 0.2, 0.02]} c="#38bdf8" emissive="#38bdf8" ei={0.6} />
          <RB p={[5.7, 0.95, -4.3]} s={[1.0, 1.9, 0.8]} c="#4b5563" metal={0.5} />
          <B p={[5.55, 1.05, -3.9]} s={[0.62, 1.3, 0.03]} c="#fef3c7" emissive="#fde68a" ei={0.7} shadow={false} />
          <B p={[6.1, 1.05, -3.9]} s={[0.2, 1.3, 0.03]} c="#1f2937" />
          <Cyl p={[7.1, 0.35, -4.2]} r={0.25} h={0.7} c="#64748b" metal={0.4} rb={0.22} />
          {/* whiteboard + lockers on the east wall */}
          <B p={[7.88, 1.8, -2.2]} s={[0.05, 1.4, 2.5]} c="#94a3b8" metal={0.6} />
          <TextBoard p={[7.84, 1.8, -2.2]} s={[2.3, 1.2]} rot={[0, -Math.PI / 2, 0]} text="FACTORY NOTES" bg="#f8fafc" fg="#334155" />
          {[0, 1, 2, 3, 4, 5].map((k) => (
            <group key={k}>
              <B p={[7.6, 0.95, 0.5 + k * 0.62]} s={[0.55, 1.9, 0.58]} c="#4f7fb8" metal={0.4} rough={0.5} />
              <B p={[7.32, 1.35, 0.5 + k * 0.62]} s={[0.02, 0.5, 0.45]} c="#3b6a9d" />
              <B p={[7.32, 0.6, 0.5 + k * 0.62]} s={[0.02, 0.5, 0.45]} c="#3b6a9d" />
            </group>
          ))}
          <Cyl p={[7.3, 0.3, 4.6]} r={0.28} h={0.6} c="#64748b" metal={0.4} rb={0.24} />

          {/* ---- andon towers outside the glass ---- */}
          <Andon p={[-8.6, 0, 4.6]} state={() => (alert() ? "bad" : "ok")} />
          <Andon p={[1.4, 0, 5.6]} state={() => (alert() ? "bad" : "ok")} />

          {/* people not on the schedule: two colleagues having coffee */}
          <Npc p={[2.3, 0, -3.5] as V3} rotY={Math.PI} color="#f97316" pose="stand" seed={2} />
        </group>
      )}
    </AtStation>
  );
}
