import { create } from "zustand";
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
  setSelectedStation: (id: string | null) => void;
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
  setSelectedStation: (selectedStation) => set({ selectedStation }),
  setData: (data) => set({ data }),
  setShift: (shift) => set({ shift }),
  setError: (error) => set({ error }),
}));
