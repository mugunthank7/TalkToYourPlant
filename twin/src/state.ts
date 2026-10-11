import { create } from "zustand";
import type { TwinData } from "./data";

interface TwinState {
  data: TwinData | null;
  shift: "A" | "B";
  error: string | null;
  setData: (d: TwinData) => void;
  setShift: (s: "A" | "B") => void;
  setError: (e: string) => void;
}
export const useTwin = create<TwinState>((set) => ({
  data: null,
  shift: "A",
  error: null,
  setData: (data) => set({ data }),
  setShift: (shift) => set({ shift }),
  setError: (error) => set({ error }),
}));
