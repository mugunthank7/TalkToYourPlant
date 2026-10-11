import { create } from "zustand";

export type BotState = "idle" | "listening" | "thinking" | "answering" | "happy" | "searching" | "pointing" | "warning" | "danger" | "sleeping";
let botTimer: ReturnType<typeof setTimeout> | undefined;
import type { TwinData } from "./data";
import type { Injected } from "./plant";
import { focusStation } from "./ui/shots";

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
  askOpen: false,
  setAskOpen: (askOpen) => set({ askOpen }),
  setSelectedStation: (selectedStation) => {
    set((st) => ({ selectedStation, sideTab: selectedStation ? "station" : st.sideTab }));
    const d = useTwin.getState().data;
    if (selectedStation && d) focusStation(d.layout, selectedStation);      // clicking a station also flies the camera to it
  },
  selectQuiet: (selectedStation) => set({ selectedStation }),
  sideTab: "station",
  setSideTab: (sideTab) => set({ sideTab }),
  setData: (data) => set({ data }),
  setShift: (shift) => set({ shift }),
  setError: (error) => set({ error }),
}));
