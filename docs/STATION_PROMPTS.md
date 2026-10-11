# Station reference prompts (for ChatGPT image generation)

How to use: paste the **shared header** once at the start of a new chat, then paste one **station prompt** at a time. Ask for the image, then send it to Claude with the station ID in the filename (e.g. `S11_control_room.png`). Every image must show the station ID and name as a floating label so nothing gets mixed up.

## Shared header (paste once)

```text
You are a senior industrial designer and 3D environment artist. I am building a realistic 3D digital twin of a fictional EV car factory called "Voltline EV Works". I will send you one station at a time. For every station produce TWO images, 16:9, high resolution, no watermark:
IMAGE A: an isometric 3/4 aerial hero view of that station only, on its floor pad, clean modern factory look with soft shadows, light glossy grey epoxy floor, yellow and green painted safety lanes, hi-vis workers in hard hats, realistic machines and props. Style: Unreal Engine / NVIDIA Omniverse factory twin, slightly stylised, clean.
IMAGE B: a top-down orthographic plan of the same station with the footprint dimensions written in metres and every major object labelled.
RULES: 1) Show a clear floating label chip in the image reading exactly "<STATION ID>  <STATION NAME>" as I give it. 2) Use only the footprint size I give. 3) No real brands, logos or car-maker names; invent generic ones. 4) Colour code: orange or white robots, blue steel racks and frames, yellow safety rails and bollards, green walkway lanes, red for alerts. 5) Keep objects modelable (simple solid forms, no tiny clutter) because I will rebuild them as low-poly-to-medium 3D models. 6) Include 2 to 4 people and any vehicles listed, doing their work. 7) Reply with only the two images and a short bulleted list of the objects you drew with approximate sizes in metres.
Reply "ready" and wait for the first station.
```

## S01  Coil yard (footprint 18 m x 14 m)

```text
Station: "S01  Coil yard". Footprint 18 m x 14 m.
Objects: a steel coil decoiler with a large silver steel coil on a mandrel (coil about 1.5 m wide, 1.6 m diameter), a coil storage rack with 4 coils lying in V-cradles, a straightener and cut-to-length feed table that ends in a stack of flat steel blanks, a floor-level coil car/AGV (yellow low platform) carrying a coil, a short overhead crane hook above the storage rack, a banding and wrapping area, safety bollards and a light curtain at the feed table, a small operator HMI stand.
People: a crane/AGV operator and a material handler checking a tag.
```

## S02  Casting and press (footprint 22 m x 16 m)

```text
Station: "S02  Casting and press". Footprint 22 m x 16 m.
Objects: one large tall servo press (about 6 m high, blue steel frame, grey moving ram, light bar on top), a die cart with a heavy die beside it, a 6-axis transfer robot (orange) at the press exit, a conveyor of stamped panels leading to two blue part racks, a hydraulic power unit with pipes, safety light curtains and a yellow guard fence with a door, an operator HMI console on a stand, oil drip tray, hi-vis floor hatching around the press.
People: a press operator at the console and a maintenance worker checking the die.
Vehicle: a small AGV carrying a rack of stamped parts out to the next station.
```

## S03  Parts buffer (footprint 14 m x 12 m)

```text
Station: "S03  Parts buffer". Footprint 14 m x 12 m.
Objects: floor-marked bays holding pallets with cardboard boxes, blue rack carriers full of stamped body panels, 2 rows of steel pallet racking (3 levels), a kanban board and barcode scanner post, barrels, a yellow forklift moving a pallet, an AGV (yellow low platform) carrying a body underbody pan, hand pallet jack, wheel stops and yellow bollards.
People: a logistics operator scanning a pallet and a forklift driver.
```

## S04  Framing (footprint 11 m x 11 m)

```text
Station: "S04  Framing". Footprint 11 m x 11 m, at the start of the main conveyor.
Objects: the start of the main conveyor with a car underbody floor pan arriving on a skid, a framing jig/fixture with 4 clamp towers (blue) and locating pins, 2 tack-weld robots (orange) on either side of the jig, light curtains and yellow fence with a gap for the conveyor, a parts presentation rack, tool cabinet, andon light stack, an operator loading station with an HMI.
People: two operators loading floor parts into the jig.
```

## S05  Weld cell A (footprint 12 m x 11 m)

```text
Station: "S05  Weld cell A". Footprint 12 m x 11 m, healthy normal state.
Objects: main conveyor passing through the middle carrying a partly built unpainted steel car body shell, TWO orange 6-axis spot-welding robots on either side of the body with welding guns and small orange sparks, yellow safety fence with clear polycarbonate panels and a person gate on one side, light curtains where the conveyor enters and leaves, an electrode tip-dressing station, a controller cabinet, a green-lit andon tower, a weld quality monitor screen.
People: an operator at the pendant panel outside the fence.
```

## S06  Weld cell B (hero, alert state) (footprint 12 m x 11 m)

```text
Station: "S06  Weld cell B". Footprint 12 m x 11 m. This is the HERO station and it is in ALERT state.
Objects: same layout as a weld cell (conveyor with an unpainted car body, yellow fence with clear panels, light curtains, controller cabinet) but the main robot is WHITE and glowing RED with a pulsing red halo and a red ring around its first joint (joint 1 bearing). Red-lit andon tower on top of the fence. A floating red alert banner above reading "ALERT: weld robot 2 bearing wear detected" and a small callout arrow pointing at the joint-1 bearing ring reading "m05_joint1_bearing". A second smaller panel showing a vibration trend rising.
People: a technician in a red vest arriving with a toolbox and a new bearing box, and the supervisor in green looking at the robot.
```

## S07  Inspection gate (footprint 10 m x 11 m)

```text
Station: "S07  Inspection gate". Footprint 10 m x 11 m, end of the main conveyor.
Objects: a grey-framed camera arch / gantry spanning the conveyor with 6 downward cameras and glowing blue laser scan lines sweeping a now-painted white car body, a bright LED inspection tunnel, a QA booth with a monitor showing a defect heat map, a reject/rework bay with yellow floor outline, a tablet stand, a small gauge table, andon light stack.
People: a quality inspector with a tablet looking at the body.
```

## S08  Battery module line (footprint 16 m x 11 m)

```text
Station: "S08  Battery module line". Footprint 16 m x 11 m.
Objects: a green-painted ESD (anti-static) floor zone, an overhead gantry robot stacking rectangular battery cells into module trays, two input conveyors carrying cell trays, a finished-module buffer rack, a glass partition on one side, a module test bench with a screen, a battery pack on an AGV leaving the station, fire extinguisher and caution signage for high-voltage batteries.
People: two operators in ESD smocks and gloves at the bench.
```

## S09  Pack closing and EOL test (footprint 16 m x 11 m)

```text
Station: "S09  Pack closing and EOL test". Footprint 16 m x 11 m.
Objects: a pack sealing press (box-like machine with a heated seal head), a leak-test chamber with a clear door and pressure gauge, an end-of-line test cell with a large screen and a diagnostic cable on a reel, a marriage station where a flat battery pack is lifted up into a white car body held on a skid, an AGV arriving with a finished car body, an AGV carrying a battery pack, a final-pass green light tower, a rework bay.
People: a test technician at the screen and an operator guiding the pack lift.
```

## S10  Maintenance bay (footprint 18 m x 11 m)

```text
Station: "S10  Maintenance bay". Footprint 18 m x 11 m.
Objects: two heavy workbenches with vices and a monitor showing the maintenance system, a red tool chest and rolling tool trolley, a parts washer, a robot-arm spare joint on a stand, a storage cart with bearings in boxes, a small overhead jib crane with a hoist, a wall board with lockout-tagout padlocks, a wall-mounted fire extinguisher, a technician locker row, a tablet charging dock, floor drip trays, safety signage.
People: a maintenance technician in a red vest loading a bearing box and tools onto a trolley, and a second technician at the bench.
```

## S11  Control room and break room (footprint 16 m x 10 m)

```text
Station: "S11  Control room and break room". Footprint 16 m x 10 m.
Objects: on the left a glass-walled control room with a curved desk, 6 monitors, and a big wall-mounted video wall showing a 3D factory twin, KPI gauges and alerts (red alert tile), an andon status board with 12 station tiles (green with one red), a supervisor desk; on the right an open break area with 3 round tables and chairs, a coffee machine, vending machine, lockers and a whiteboard. A tall andon light stack outside the glass.
People: the supervisor (green vest) at the control desk, two operators on a break at a table.
```

## S12  Spare parts cage (footprint 12 m x 8 m)

```text
Station: "S12  Spare parts cage". Footprint 12 m x 8 m.
Objects: a wire-mesh security cage with a lockable door, inside 2 rows of blue steel shelving (3 levels) holding labelled boxes and bins: bearing boxes, servo motors, gearboxes, cable harnesses, electrode tips; a scanning kiosk with a screen showing "bearing_6208: in stock", a hand truck, a parts-pick trolley, a floor-marked pick zone, a hanging sign "SPARE PARTS", a fire extinguisher.
People: a stores clerk scanning a box and the technician collecting a bearing.
Vehicle: a small purple spares cart (tugger) loaded with boxes leaving the cage.
```

## Bonus images (optional)
- Whole plant: "all 12 stations laid out as in the layout reference" (send them `docs/img/layout-compact.png`).
- Characters: "hi-vis factory worker in 5 role colours: orange operator, yellow relief, blue inspector, green supervisor, red technician, front/side/back turnaround".
