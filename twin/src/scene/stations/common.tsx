import { WeldRobot } from "../Machines";
import type { Machine } from "../../data";

/** A weld robot placed in a station model. rotY 0 = reaches north (towards -z), PI = reaches south. */
export function Robot({ p, rotY = 0, id, absX, color = "#f08a1d", hero = false, s = 1 }:
  { p: [number, number, number]; rotY?: number; id: string; absX: number; color?: string; hero?: boolean; s?: number }) {
  const m = { id, name: id, type: "weld_robot", station: "", x: absX, z: 0, rot_deg: 0 } as Machine;
  return (
    <group position={p} rotation={[0, rotY, 0]} scale={s}>
      <WeldRobot m={m} hero={hero} color={color} />
    </group>
  );
}
