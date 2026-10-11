import type { ReactElement } from "react";
import { S01 } from "./S01";
import { S02 } from "./S02";
import { S03 } from "./S03";
import { S08 } from "./S08";
import { S09 } from "./S09";
import { S10 } from "./S10";
import { S11 } from "./S11";
import { S12 } from "./S12";

/** Stations that have a detailed model. The generic pad, props and machines are skipped for these. */
export const DETAILED: Record<string, () => ReactElement> = { S01, S02, S03, S08, S09, S10, S11, S12 };
export const DETAILED_IDS = new Set(Object.keys(DETAILED));
/** Machine ids drawn inside a detailed station model. */
export const MACHINES_IN_MODELS = new Set<string>(["M09", "M01", "M02", "M10", "M11", "M08"]);

export function StationModels() {
  return (
    <>
      {Object.entries(DETAILED).map(([id, C]) => (
        <C key={id} />
      ))}
    </>
  );
}
