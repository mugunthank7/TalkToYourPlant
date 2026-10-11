import type { GraphPath } from "./graphpath";
import { create } from "zustand";

export type BotState = "idle" | "listening" | "thinking" | "answering" | "happy" | "searching" | "pointing" | "warning" | "danger" | "sleeping";
let botTimer: ReturnType<typeof setTimeout> | undefined;
import type { TwinData } from "./data";
import type { Injected } from "./plant";

interface TwinState {
  data: TwinData | null;
  shift: "A" | "B";
  faults: Injected[];
  addFault: (f: Injected) => void;
  clearFaults: () => void;
  sim: "off" | "connecting" | "on";
  setSim: (s: "off" | "connecting" | "on") => void;
  view: "live" | "dash";
  setView: (v: "live" | "dash") => void;
  error: string | null;
  selectedStation: string | null;
  bot: BotState;
  setBot: (s: BotState, holdMs?: number) => void;       // after holdMs the bot goes back to idle
  graphPath: GraphPath | null;
  setGraphPath: (p: GraphPath | null) => void;
  askOpen: boolean;
  setAskOpen: (v: boolean) => void;
  setSelectedStation: (id: string | null) => void;
  selectQuiet: (id: string | null) => void;     // highlight a station without switching the side panel to its tab (used by chat answers)
  sideTab: "station" | "ask";
  setSideTab: (t: "station" | "ask") => void;
  setData: (d: TwinData) => void;
  setShift: (s: "A" | "B") => void;
  setError: (e: string) => void;
}
export const useTwin = create<TwinState>((set) => ({
  data: null,
  shift: "A",
  faults: [],
  addFault: (f) => set((s) => ({ faults: [...s.faults, f] })),
  clearFaults: () => set({ faults: [] }),
  sim: "off",
  setSim: (sim) => set({ sim }),
  view: "live",
  setView: (view) => set({ view }),
  error: null,
  selectedStation: null,
  bot: "idle",
  setBot: (bot, holdMs) => { clearTimeout(botTimer); set({ bot }); if (holdMs) botTimer = setTimeout(() => set({ bot: "idle" }), holdMs); },
  graphPath: null,
  setGraphPath: (graphPath) => set({ graphPath }),
  askOpen: false,
  setAskOpen: (askOpen) => set({ askOpen }),
  setSelectedStation: (selectedStation) => set((st) => ({ selectedStation, sideTab: selectedStation ? "station" : st.sideTab })),
  selectQuiet: (selectedStation) => set({ selectedStation }),
  sideTab: "station",
  setSideTab: (sideTab) => set({ sideTab }),
  setData: (data) => set({ data }),
  setShift: (shift) => set({ shift }),
  setError: (error) => set({ error }),
}));
