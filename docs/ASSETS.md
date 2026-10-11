# Asset list and sourcing plan

Format: **glTF binary (`.glb`)**, Y-up, 1 unit = 1 metre, Draco/meshopt compressed for the web, target under 25 MB total for the whole scene.
Pipeline: source -> Blender (cleanup, naming, rig) -> export GLB -> `assets/models/` -> Three.js via `useGLTF`.

## Sourcing strategy (hybrid, see DECISIONS.md D-004)

| Method | Use for | Why |
|--------|---------|-----|
| **A. Blender + Claude (procedural bpy scripts)** | Hero assets: weld robot (`M05`, `M04`, `M02`), conveyor, fixtures, cell fencing | We control mesh names, pivots and rigging; each component is a separate node the twin can glow; no licence risk; consistent look |
| **B. Free CC0 / CC-BY models from the web** | Generic props: shelving, pallets, tool cart, crates, light fixtures, barriers, forklift, floor markings | Fast, good looking, no need to model |
| **C. Mixamo (or Quaternius) rigged characters + animations** | People: walk, idle, work, crouch, inspect | Rigged and animated already, FBX -> GLB conversion in Blender |

Rule: anything the system must **highlight, animate per part, or attach a sensor to** goes in bucket A. Pure set dressing goes in bucket B.

## Where to look (web)

| Source | Licence | Good for |
|--------|---------|----------|
| [Poly Pizza](https://poly.pizza) | CC0 / CC-BY | Low-poly props, GLB downloads |
| [Quaternius](https://quaternius.com) | CC0 | Characters, props, rigged animated packs |
| [Kenney](https://kenney.nl/assets) | CC0 | Props, factory/industrial kits |
| [Sketchfab](https://sketchfab.com) (filter: downloadable, CC) | CC-BY / CC0 | Robot arms, presses, industrial props |
| [Mixamo](https://www.mixamo.com) | Free for projects (Adobe account) | Humanoid animations |
| [Poly Haven](https://polyhaven.com) | CC0 | HDRIs, PBR textures (concrete floor, metal) |
| [ambientCG](https://ambientcg.com) | CC0 | PBR textures |

**Licence log:** every downloaded asset gets a row in the table at the bottom of this file (name, URL, author, licence). CC-BY needs attribution in the README credits. No real-brand models (no recognisable KUKA/FANUC/ABB livery or logos); re-skin or avoid.

## Asset list

Status: `todo` / `sourcing` / `done`. Bucket: A = Blender+Claude, B = web, C = characters.

### Machines

| # | Asset | For | Bucket | Priority | Status | Notes |
|---|-------|-----|--------|----------|--------|-------|
| 1 | Weld robot, 6-axis, rigged | M05, M04 | A | P0 | todo | Hero. 10 named components (see STATIONS.md). Separate pivots per axis so it can animate. Instance for M04 |
| 2 | Spot-weld gun + spark particles | M04, M05 | A | P0 | todo | Sparks via Three.js particles, not mesh |
| 3 | Transfer robot (robot + gripper) | M02 | A | P1 | todo | Reuse #1 rig, swap end effector |
| 4 | Casting press | M01 | A | P0 | todo | Frame + moving ram, big and recognisable |
| 5 | Main conveyor (modular segments) | M06 | A | P0 | todo | Rollers/skids, a curve spline for BIW |
| 6 | Body-in-white (car shell) | carried on M06 | B then A | P0 | todo | Generic EV shell, no brand. Try Sketchfab/Poly Pizza; else block out in Blender |
| 7 | Framing fixture | M03 | A | P1 | todo | Clamp arms that open/close |
| 8 | Vision inspection gate | M07 | A | P1 | todo | Arch with camera heads |
| 9 | Battery module stacker | M08 | A | P2 | todo | Simple gantry + module blocks |
| 10 | Pack sealer | M09 | A | P2 | todo | Box + press |
| 11 | Decoiler + coil | M10 | A | P2 | todo | Rotating cylinder |
| 12 | Rack AGV | M11 | B | P2 | todo | Optional |

### People (bucket C)

| # | Asset | Animations needed | Priority | Status |
|---|-------|-------------------|----------|--------|
| 13 | Operator character x2 skins (hi-vis vest, hard hat) | idle, walk, work (use tool), look-around | P0 | todo |
| 14 | Maintenance technician | idle, walk, pick up, crouch/repair, tablet | P0 | todo |
| 15 | Quality inspector | idle, walk, tablet inspect | P1 | todo |
| 16 | Supervisor | idle, walk, point/react | P1 | todo |

Animation sources: Mixamo clips retargeted in Blender; export one GLB per character with all clips in one file. Use `SkeletonUtils.clone` to spawn extra crew from one load.

### Environment and props (bucket B unless noted)

| # | Asset | Priority | Notes |
|---|-------|----------|-------|
| 17 | Factory shell (floor, walls, roof trusses, skylights) | P0 | Build in code/Blender, cheap |
| 18 | Floor texture + yellow lane markings | P0 | ambientCG/Poly Haven concrete + decals |
| 19 | Safety fencing and light curtains | P1 | A (simple boxes + emissive strip) |
| 20 | Andon light stack (green/yellow/red) | P0 | A, emissive; tied to alert state |
| 21 | Control room desk + monitors | P1 | B |
| 22 | Maintenance workbench, tool cart, tablet | P0 | B |
| 23 | Spare parts shelving + bearing boxes | P0 | B; "in stock?" beat |
| 24 | Pallets, crates, part racks | P1 | B |
| 25 | Overhead cranes / cable trays / pipes | P2 | B |
| 26 | Forklift | P2 | B |
| 27 | Signage (station labels, safety signs) | P1 | Three.js text/sprites, no models |
| 28 | HDRI lighting | P0 | Poly Haven indoor industrial HDRI |

## Blender + Claude workflow (bucket A)

1. Claude writes a `bpy` script per asset in `assets/source/blender/<asset>.py` (parametric: sizes and counts as variables).
2. Run headless: `blender --background --python assets/source/blender/<asset>.py` to produce `assets/models/<asset>.glb`.
3. Naming contract: node names exactly as in STATIONS.md; pivots at joint axes; origin at floor level.
4. Check in the browser (`twin/` viewer), fix, regenerate. Scripts are the source of truth, so models are reproducible and reviewable in git.
5. If an asset needs hand-sculpting, download from the web instead (bucket B) rather than burn time.

Prerequisite: install Blender (`brew install --cask blender`) and confirm `blender --version` works from the shell.

## Licence log

| Asset | Source URL | Author | Licence | Attribution needed |
|-------|------------|--------|---------|--------------------|
| (none yet) | | | | |
