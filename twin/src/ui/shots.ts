import { camera as cam, stationShot, type Shot } from "../clock";
import { toScene, type Layout } from "../data";

/** Named camera shots, built from the layout so they follow any layout change. */
export function buildShots(layout: Layout): Shot[] {
  const st = (id: string) => layout.stations.find((s) => s.id === id)!;
  const at = (id: string, k = 0.95) => {
    const s = st(id);
    const [x, z] = toScene(s.x, s.z);
    return stationShot(x, z, Math.max(s.w, s.d), k);
  };
  const [hx, hz] = toScene(st("S06").x, st("S06").z);
  return [
    { name: "Overview", pos: [0, 92, 104], target: [0, 0, 4], note: "Whole plant at a glance" },
    { name: "Top-down", pos: [0, 128, 8], target: [0, 0, 2], note: "Layout and flow from above" },
    { name: "Line, low angle", pos: [-34, 5, 12], target: [18, 1.6, -2], note: "Cinematic view along the conveyor" },
    { name: "Line, from the end", pos: [76, 9, -12], target: [-10, 2, -2], note: "Looking back up the line" },
    { name: "Hero cell S06", pos: [hx + 2, 8, hz + 11], target: [hx, 1.2, hz - 0.5], note: "Weld robot 2, the fault story" },
    { name: "Robot close-up", pos: [hx - 0.5, 3.6, hz + 5.5], target: [hx + 0.4, 1.3, hz + 2.6], note: "The joint-1 bearing ring" },
    { name: "Weld cells", pos: [30, 20, 30], target: [30, 0, -4], note: "S05 and S06 together" },
    { name: "Control room S11", ...at("S11") as { pos: [number, number, number]; target: [number, number, number] }, note: "Video wall, andon board" },
    { name: "Press S02", ...at("S02", 0.8) as { pos: [number, number, number]; target: [number, number, number] }, note: "Press, transfer robot, racks" },
    { name: "Battery line S08", ...at("S08") as { pos: [number, number, number]; target: [number, number, number] }, note: "Cell infeed to module rack" },
    { name: "Pack and EOL S09", ...at("S09") as { pos: [number, number, number]; target: [number, number, number] }, note: "Marriage station and EOL test" },
    { name: "Maintenance S10", ...at("S10") as { pos: [number, number, number]; target: [number, number, number] }, note: "Where the technician starts" },
    { name: "Spares S12", ...at("S12", 1.2) as { pos: [number, number, number]; target: [number, number, number] }, note: "Where the bearing is picked" },
    { name: "Coil yard S01", ...at("S01") as { pos: [number, number, number]; target: [number, number, number] }, note: "Raw material in" },
    { name: "Parts buffer S03", ...at("S03") as { pos: [number, number, number]; target: [number, number, number] }, note: "Racks, pallets, forklift" },
    { name: "Framing S04", ...at("S04", 1.1) as { pos: [number, number, number]; target: [number, number, number] }, note: "Where each car starts" },
    { name: "Inspection S07", ...at("S07", 1.1) as { pos: [number, number, number]; target: [number, number, number] }, note: "Scan arch, finished body" },
  ];
}

export const TOUR = ["Overview", "Line, low angle", "Press S02", "Battery line S08", "Control room S11", "Hero cell S06", "Robot close-up", "Maintenance S10", "Line, from the end", "Overview"];

export function goTo(shot: Shot) {
  cam.mode = "free";
  cam.goal = { pos: [...shot.pos], target: [...shot.target] };
}
