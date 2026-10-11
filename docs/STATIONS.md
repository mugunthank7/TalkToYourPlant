# Stations: fictional EV plant ("Voltline EV Works")

The plant is fictional (per the project brief). Do not use real automaker or robot-vendor names, logos, or livery anywhere.

**Station IDs and machine IDs below are the contract with the GraphRAG/data side.** Neo4j `Machine.id` must equal the `machine_id` used here and in the sensor stream. Change an ID only via a DECISIONS.md entry and tell the data owner.

## Process flow

```
 [S01 Coil yard] -> [S02 Casting & press] -> [S03 Parts buffer] -> [S04 Framing]
        -> [S05 Weld cell A] -> [S06 Weld cell B (HERO)] -> [S07 Inspection gate]
        -> [S08 Battery module line] -> [S09 Pack closing & EOL test]
 
 Support: [S10 Maintenance bay]   [S11 Control room / andon]   [S12 Spare parts cage]
```

The main conveyor (M06) runs through S04 to S07 and carries the body-in-white (BIW).

## Station list

| ID | Station | What happens | Machines (id) | Priority |
|----|---------|--------------|---------------|----------|
| S01 | Coil yard | Steel/aluminium coils arrive, are decoiled and cut to blanks | Decoiler `M10` | P2 |
| S02 | Casting & press | Large casting press forms underbody parts; a transfer robot moves parts out | Casting press `M01`, Transfer robot `M02` | P0 |
| S03 | Parts buffer | Racks of stamped parts wait for the line; forklift/AGV moves racks | Rack AGV `M11` (optional) | P2 |
| S04 | Framing | Underbody parts are clamped into a fixture and tack-welded | Framing fixture `M03` | P0 |
| S05 | Weld cell A | Robot spot-welds the side panels | Weld robot 1 `M04` | P0 |
| S06 | Weld cell B | **Hero scenario:** robot with joint bearing wear | Weld robot 2 `M05` | P0 |
| S07 | Inspection gate | Camera arch checks weld quality and gaps | Vision gate `M07` | P1 |
| S08 | Battery module line | Cells are stacked into modules | Module stacker `M08` | P2 |
| S09 | Pack closing & EOL test | Pack is sealed, leak/electrical tested | Pack sealer `M09` | P2 |
| S10 | Maintenance bay | Technician workbench, tool cart, tablet | none | P0 (people destination) |
| S11 | Control room / andon | Screens, andon light stack, supervisor desk | none | P1 |
| S12 | Spare parts cage | Shelving with bearings, gearboxes, motors (the "spare part in stock?" beat) | none | P1 |

Cross-cutting: the main conveyor `M06` spans S04 to S07 (P0).

P0 = must exist for the demo. P1 = demo polish. P2 = only if time allows, or as a cheap placeholder.

## Machine list (10 machines, matches the brief's 8 to 10)

| ID | Machine | Station | Notes |
|----|---------|---------|-------|
| M01 | Casting press | S02 | Big, slow stroke animation |
| M02 | Press transfer robot | S02 | 6-axis arm, reuse the weld-robot rig with a gripper |
| M03 | Framing fixture | S04 | Clamps open/close |
| M04 | Weld robot 1 | S05 | Healthy reference robot, sparks |
| M05 | Weld robot 2 | S06 | **Hero.** Faults, glows red, heatmap |
| M06 | Main conveyor | S04 to S07 | Carries BIW along a spline |
| M07 | Vision inspection gate | S07 | Optional scan beam |
| M08 | Battery module stacker | S08 | Simple gantry |
| M09 | Pack sealer | S09 | Simple press/sealer |
| M10 | Decoiler | S01 | Rotating coil |

## Hero machine: Weld robot 2 (`M05`) component breakdown

Each component below must be a separately named mesh/node in the GLB so the twin can glow it and the graph path can highlight it. Names must be snake_case and match Neo4j `Component.id`.

| Node name | Component |
|-----------|-----------|
| `m05_base` | Base plinth |
| `m05_joint1_bearing` | Axis 1 joint bearing (the **faulty** one) |
| `m05_joint2_bearing` | Axis 2 joint bearing |
| `m05_joint3_bearing` | Axis 3 joint bearing |
| `m05_servo_motor` | Servo motor |
| `m05_gearbox` | Gearbox |
| `m05_wrist` | Wrist |
| `m05_weld_gun` | Spot-weld gun |
| `m05_cable_harness` | Cable harness |
| `m05_controller_cabinet` | Controller cabinet |

## People (animated)

| Role | Count | Behaviour |
|------|-------|-----------|
| Line operator | 3 to 4 | Loop at stations S04, S05, S06 (work animation), walk short patrol between them |
| Quality inspector | 1 | Walks to S07, looks at a tablet |
| Line supervisor | 1 | Walks between S11 and the line, reacts to the andon |
| Maintenance technician | 1 | Idle at S10. **On work-order creation, walks S10 -> S12 (pick bearing) -> S06**, crouches at the robot |

Rules: people stay on marked walkways. Anyone inside a robot cell's safety zone makes that robot pause (visual only). This is a cheap realism win and a good "digital twin" talking point.

## Walkways and zones

- Yellow-painted pedestrian lanes along both sides of the conveyor.
- Cell fencing with light curtains at S05 and S06.
- Waypoint graph for pedestrian pathfinding is defined in `twin/src/data/waypoints.json` (to be created in the scene-layout step).
