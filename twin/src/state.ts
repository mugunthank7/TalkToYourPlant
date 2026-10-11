import { create } from "zustand";
import type { TwinData } from "./data";
import type { Injected } from "./plant";

interface TwinState {
  data: TwinData | null;
  shift: "A" | "B";
  faults: Injected[];
  addFault: (f: Injected) => void;
  clearFaults: () => void;
  view: "live" | "dash";
  setView: (v: "live" | "dash") => void;
  error: string | null;
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
  view: "live",
  setView: (view) => set({ view }),
  error: null,
  setData: (data) => set({ data }),
  setShift: (shift) => set({ shift }),
  setError: (error) => set({ error }),
}));
