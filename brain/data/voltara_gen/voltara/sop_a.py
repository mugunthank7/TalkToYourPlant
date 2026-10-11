"""Procedures & protocols, part A: safety, maintenance management, robotics.
All content is synthetic (modeled on common industrial practice and public standards references)."""

SOPS_A = []


def sop(sid, title, area, owner, body, revision="C", effective="2025-03-01", refs=None):
    SOPS_A.append(dict(id=sid, title=title, area=area, owner=owner, revision=revision, effective=effective,
                       references=refs or [], body=body.strip()))


sop("SOP-SAF-01", "Lockout/Tagout (Control of Hazardous Energy)", "ALL", "EHS Officer", """
## Purpose
Prevent unexpected energization, start-up or release of stored energy while servicing machinery. Applies to every
machine in the plant: electrical, hydraulic, pneumatic, gravitational, thermal, chemical and stored (accumulators, capacitors, springs, counterbalances).

## Scope and authority
Only **Authorized Employees** (cert code LOTO) may apply locks. Affected employees (operators) must be notified. Contractors and vendor engineers must follow this procedure or be escorted by an authorized employee and apply their own personal lock.

## Procedure
1. **Prepare.** Identify all energy sources on the machine energy-source card (posted at each machine). Review the machine-specific lockout procedure. Collect locks, tags and a multi-lock hasp.
2. **Notify.** Tell the Line Lead and operator(s) that the machine will be locked out and why. Press the area Andon so production is aware.
3. **Shut down** the machine using the normal stop sequence (do not use E-stop as a stop).
4. **Isolate.** Open and lock each energy-isolating device: main disconnect, hydraulic pump motor starter, pneumatic dump valve, and individual shutoff valves. For robots, lock the controller main switch and the cell mains disconnect.
5. **Apply locks and tags.** Each authorized person applies a personal lock and a tag with name, date and shift. One person = one lock.
6. **Release stored energy.** Bleed hydraulic accumulators via the manual dump valve, vent pneumatics, block or lower suspended loads (die, cushion, robot arm on its mechanical stops), discharge capacitors/drives (wait for DC link discharge time on the drive label, minimum 5 minutes for servo amplifiers).
7. **Verify zero energy (Try-out).** Attempt a start from the HMI/control panel and confirm nothing moves. Verify electrical zero energy with a rated meter (live-dead-live) where exposed conductors are involved. Return controls to OFF.
8. **Perform the work.** If a lock-holder leaves the work, their lock stays on. Shift change: use the group lockout board and handover per SOP-MNT-03.
9. **Release.** Clear tools and people, reinstall guards, remove locks (each person removes their own), notify affected employees, re-energize, and run a test cycle with the operator.

## Special cases
- **Hydraulic presses / Giga Press:** accumulator pre-charge gas (nitrogen) is stored energy: use the accumulator dump valve and confirm gauge reads zero before any hose or valve work. Die must be blocked with the safety blocks when working between platens.
- **Robot cells:** lock out controller and the weld transformer/servo gun supply; the arm can drop when brakes release; use mechanical stops/blocking for axes 2 and 3.
- **HV battery equipment:** follow SOP-SAF-02 in addition to this procedure.

## Lock removal when the owner is unavailable
Only the Maintenance Manager (or delegate) after documented attempt to contact the owner, a physical check of the machine, and notification of the employee upon return.

## Records
LOTO permit stored in CMMS attached to the work order. Annual periodic inspection by EHS for each machine-specific procedure.
""", refs=["OSHA 29 CFR 1910.147"])

sop("SOP-SAF-02", "High-Voltage (EV Battery) Safe Work Procedure", "BAT", "HV Safety Engineer", """
## Purpose
Control electrical shock, arc-flash and thermal risks when working on EV battery modules, packs and HV test equipment (typically 400 V to 800 V nominal; a pack with ~198 cells in series can operate from roughly 610 to 835 V).

## Qualification
- **NFPA 70E qualified person (cert HV):** may work on or near exposed energized parts only with an approved energized work permit.
- **HVB (non-electrical HV awareness):** may handle sealed, isolated packs and use galvanically isolated fastening tools; may not open HV enclosures.

## Rules
1. Treat every pack as energized. A pack is NOT safe until the **service disconnect** is pulled, the pack is verified at zero volts with a CAT III/IV rated meter on both poles to chassis, and the insulation resistance measurement is recorded.
2. PPE for qualified persons: Class 0 (1000 V) rubber insulating gloves with leather protectors (air-tested before shift), arc-rated face shield and clothing, insulated tools (1000 V rated). Non-qualified persons wear cut-resistant gloves and safety glasses and keep a 1 m exclusion distance from open HV.
3. Fastening tools used near HV busbars must have **galvanically isolated chucks**; never substitute a standard bit or socket.
4. Remove all metal jewelry. No conductive tools on top of open packs. Use dissipative mats.
5. Two-person rule for all HV work; one is the safety observer with the E-stop in hand and trained in rescue (non-conductive hook).
6. Cells outside spec (swelling, odor, leakage, surface temperature > 60 C): STOP, move people out, follow SOP-SAF-03.

## HV test equipment (pack EOL, HV tester)
- Verify interlock loop and warning beacons each shift (daily check PM-BE).
- Discharge and verify zero before connecting/disconnecting leads. Insulation test voltage is applied only when cell door is closed and interlock confirmed.
- A **HV insulation fault** alarm (TST-HV-ISO) stops the test; do not retry more than once without a qualified person inspecting cables for moisture or damage.

## Escalation
Any HV incident or suspected fault is **Level 6 immediately**: page HV Safety Engineer and EHS. Quarantine the pack in the marked battery quarantine bay (outdoors cage, 3 m separation).

## Records
Energized work permits, insulation resistance logs, PPE glove test log, and incident reports.
""", refs=["NFPA 70E", "OSHA 29 CFR 1910.147"])

sop("SOP-SAF-03", "Battery Thermal Event & Fire Emergency Response", "BAT", "EHS Officer", """
## Purpose
Respond safely to cell venting, smoke, swelling, fire or thermal runaway of battery cells, modules or packs.

## Recognition
Hissing/venting, white or grey smoke, sweet solvent odor, unexpected heat, swelling, voltage collapse flagged by the test system, or flames.

## Immediate actions (first 60 seconds)
1. **Alarm and evacuate**: hit the nearest fire pull station and shout "battery fire". Evacuate everyone at least 15 m upwind; do not fight a pack fire beyond incipient stage.
2. Cut power to the station using the E-stop if it is safe to do so.
3. Call the on-site emergency team (radio channel EMERG) and 911 from the control room.
4. Page EHS and the HV Safety Engineer (Level 6).

## If incipient (a single cell venting, no flame)
Trained responders may isolate by moving the module using insulated tools into the quarantine cage if the surface temperature is below 80 C. Otherwise wait for fire service.

## Fire suppression notes
Large volumes of water are the recommended agent for lithium-ion fire cooling when applied by fire service; Class D and dry chemical agents are not effective on thermal runaway. The plant's sprinkler system covers the battery bay.

## After the event
Keep the area closed for at least 24 h. Monitor surface temperature of nearby packs with the thermal camera for re-ignition. Preserve evidence. Notify Quality and file an incident report. A Level 6 RCA is required.
""", refs=["NFPA 855", "NFPA 70E"])

sop("SOP-SAF-04", "Robot Cell Entry, Teaching and Safeguarding", "ALL", "Robotics Supervisor", """
## Purpose
Protect personnel who enter robot cells for maintenance, teaching or troubleshooting. Applies to all FANUC, KUKA, ABB, Duerr and cobot cells.

## Safeguards
Fence with interlocked gate, trapped-key or safety-rated door switch, light curtains at material windows, safety scanners at open cells, E-stops on each operator station and on the teach pendant. Safety circuit validation is part of the annual PM (ISO 10218 requires verification at defined intervals).

## Entry procedure
1. Request entry through the cell operator; stop the cell in a safe state (arm at home).
2. Switch the controller to **T1 (manual reduced speed)**. Take the teach pendant with you and keep the enabling (deadman) switch accessible.
3. If work is not required with power on, **lock out** per SOP-SAF-01. For work inside the envelope with robot power ON (teaching, collision recovery), only a trained person may enter and must carry the pendant; nobody else may operate the cell controls (use the trapped key / personal lock on the gate).
4. Never rely on a stopped robot: stored program waits, servo-gun closes and weld current can start unexpectedly. Check the position of other robots in a shared cell.
5. Leaving: remove all tools and personal items, close and lock the gate, reset the safety circuit, check that people are clear, restore AUTO mode only from outside the fence.

## Typical alarms seen on entry
- SRVO-007 (external E-stop) / KSS emergency stop active: identify which device opened the chain before resetting.
- SRVO-230 chain abnormal: do not bypass; call controls.

## Records
Entries logged on the cell entry sheet; teach changes logged per SOP-MNT-06.
""", refs=["ISO 10218-1/-2", "ANSI/RIA R15.06"])

sop("SOP-MNT-01", "Fault Escalation and Paging Protocol", "ALL", "Maintenance Manager", """
## Purpose
Ensure the right person is engaged at the right time when equipment faults, defining who to page, when, and how quickly they must acknowledge.

## Roles
- **Operator:** first responder. Pull the Andon, note time and fault code, tell the Line Lead.
- **Line Lead (L0):** confirms the stop, tries a safe reset (once), calls the on-shift Primary Technician for the machine (radio channel MAINT or pager).
- **L1 Primary Technician:** the on-shift technician assigned to the machine in the trade matching the fault (mechanical, electrical, hydraulics, robotics, controls, process).
- **L2 Backup Technician:** same trade, same shift; paged if no ack within 5 minutes or if a second person is required (two-person work).
- **L3 Maintenance Supervisor (shift):** for the zone; paged on thresholds below, any severity-3+ fault, or any safety concern.
- **L4 Area Engineer (on-call):** reliability, controls or process engineer for the area, selected by fault trade.
- **L5 Vendor support:** OEM emergency line per machine (see machine record for contract and SLA).
- **L6 Plant management:** Maintenance Manager, Operations Director, Plant Manager; always engaged immediately for safety events.

## Escalation timers (minutes of line-impacting downtime)
| Machine criticality | L1 tech | L2 backup | L3 supervisor | L4 engineer | L5 vendor | L6 plant mgmt |
|---|---|---|---|---|---|---|
| A (line-stopping) | 2 | 8 | 15 | 30 | 90 | 180 |
| B (buffered) | 5 | 15 | 30 | 60 | 180 | 360 |
| C (non-critical) | 10 | 30 | 60 | 120 | 360 | 720 |

Timers run from the Andon. A repeat of the same fault within 24 hours moves the escalation straight to L4.

## Acknowledgement
Pages must be acknowledged within 3 minutes (A), 5 minutes (B), 10 minutes (C). If no ack, the sender pages the next level and calls the radio/phone. The Maintenance Supervisor can reassign technicians across trades.

## Fault-trade routing
- Robot alarm (SRVO-/KSS-/ABB-): ROBO tech; controls engineer for DCS/safety parameter issues.
- Hydraulic pressure/temperature/leak: HYD tech.
- Drive overload, breakers, motors: ELEC tech.
- PLC/MES comms, AGV navigation: CTRL tech.
- Torque NOK, calibration, process drift, laser power: PROC tech with process engineer.
- Mechanical wear/jam: MECH tech.

## Safety overrides
Injury, fire/smoke, HV event, paint Ex-purge fault, molten metal or die water leak: **Level 6 immediately**, follow SOP-SAF-03 / SOP-CAS-02 / SOP-PNT-01.

## Communication
Use the area channel for status every 15 minutes during Level 3+ events. The Maintenance Supervisor posts the event summary into the shift handover (SOP-MNT-03). After vendor engagement the Planner opens a service ticket in CMMS.

## Who to page when information is incomplete
Page the **Maintenance Supervisor** for the zone; they know the on-call rota. The on-call rota (weekly) lists primary and secondary engineers per discipline.
""")

sop("SOP-MNT-02", "Work Order Management, Priorities and Failure Coding", "ALL", "Maintenance Planner", """
## Priority definitions
- **P1 (emergency):** safety risk or line stop at a criticality-A machine, response immediately.
- **P2 (urgent):** major fault or risk of line stop within the shift, response < 30 min.
- **P3 (normal):** degraded operation, planned PM, inspections; scheduled within 7 days.
- **P4 (minor):** nuisance faults and improvements; scheduled within 30 days.

## Closure requirements (CM work orders)
Technician must record: fault code, symptom, diagnosis, action taken, root cause (free text) and category, parts used with part numbers, downtime minutes, and any follow-up needed. For P1/P2 events with downtime above 4 hours an RCA is raised within 3 days.

## Root-cause categories
Wear/aging, Lubrication, Contamination, Electrical/instrumentation, Operator/material handling, Software/configuration, Thermal/cooling, Leak/sealing, Process drift, Unknown. "Unknown" must be re-reviewed by the area engineer within 7 days.

## PM execution
PM work orders are generated by interval (operating hours, from machine runtime counters, or calendar days). Technicians complete the checklist, record findings and close. Deferred PMs require supervisor approval and rescheduling within 14 days. PMs more than 14 days overdue on criticality-A machines are escalated to the Maintenance Manager.

## Repeat failures
Same machine and fault code within 14 days triggers an automatic review (4M: man, machine, method, material). Three occurrences in 90 days opens a reliability project.
""")

sop("SOP-MNT-03", "Shift Handover Protocol", "ALL", "Production Supervisor", """
## Purpose
Preserve continuity of equipment status, open issues and safety information between shifts A (06:00-14:00), B (14:00-22:00) and C (22:00-06:00).

## Overlap and format
15-minute overlap at the area board. Outgoing supervisor and maintenance supervisor brief the incoming pair using the handover sheet.

## Handover content
1. Safety events and near misses.
2. Output vs plan, scrap and quality holds.
3. Downtime events with work order numbers, status (repaired/temporary fix/waiting parts).
4. Machines under watch (trending sensors, recently repaired).
5. Equipment under LOTO or in bypass (list each lock and owner).
6. PMs and inspections planned for the next shift.
7. Vendor activity and open service tickets.

## Rules
- A temporary fix must state exit criteria and a time limit.
- No machine in bypass may be handed over without supervisor approval.
- The notes are saved in the CMMS shift log and are searchable for the next 12 months.
""")

sop("SOP-MNT-04", "Spare Parts, Critical Spares and Emergency Purchasing", "ALL", "Storekeeper", """
## Spare classification
- **Critical spares** (unit cost > $1,500 or lead time > 5 weeks, or single point of failure): minimum one on site for criticality-A machines.
- **Consumables** (filters, tips, glass, batteries, gaskets): min/max kanban in the maintenance store and line-side lockers.

## Issue process
Technicians scan the part number against the work order. Part number must be entered on the WO; unlisted parts need the planner's approval.

## Emergency purchasing
If a critical spare is not in stock: 1) Planner calls the OEM emergency desk; 2) request air freight with tracking; 3) check sister plant stock; 4) engineer assesses a temporary repair or redeploying parts from a lower-criticality machine; 5) record expected arrival in the WO notes.

## Reorder
Reorder point = annual usage x lead time (days) / 365 x 1.5 safety factor, rounded up, minimum 1.

## Batteries and lubricants
Robot backup batteries (e.g. FANUC A02B-0200-K102) are stocked for each controller type and rotated first-in first-out; lubricant and gear oil are stored sealed and labeled with date opened.
""")

sop("SOP-MNT-05", "Condition Monitoring, Oil Analysis and Alert Thresholds", "ALL", "Reliability Engineer", """
## Purpose
Detect developing failures from sensor trends, oil analysis and thermography so work is planned before breakdown.

## Sensors and thresholds
Each machine publishes channels (vibration mm/s RMS, motor current A, motor temperature C, hydraulic pressure bar, oil temperature C, filter differential pressure bar, battery voltage V, laser power %, etc.). Each channel has a **nominal**, **warn** and **alarm** value defined in the machine record. Actions:
- **Warn:** raise a PdM work order, inspect within 5 working days, increase sampling frequency.
- **Alarm:** treat as imminent failure; supervisor decides whether to continue production using SOP-OPS-02 (run-extension decisions).
- Trends crossing 70% of the nominal-to-warn distance for more than 7 days also trigger a PdM work order.

## Oil analysis
- Gearbox and hydraulic oil sampled quarterly (robot gearboxes at annual PM).
- Iron (Fe) > 200 ppm triggers a work order for oil change and internal inspection.
- Hydraulic fluid cleanliness target ISO 4406 18/16/13 for servo valves (17/15/12 for presses with proportional valves); particle count above target triggers filtration/flush.
- Water > 0.1% in hydraulic oil triggers cooler leak check.

## Thermography
Quarterly on switchgear, VFDs, motor terminal boxes and compressor motors. Hot spots > 15 C over reference or > 40 C over ambient raise a P2 work order.

## Anomaly detection
The plant's anomaly detection model (shared with the digital twin) scores sensor windows and attaches SHAP feature contributions to alerts. Engineers review alerts daily; confirmed true positives are logged as PdM work orders and used to retrain the model.
""")

sop("SOP-MNT-06", "Management of Change and Robot Program Backup", "ALL", "Controls Engineer", """
## Purpose
Prevent unplanned behavior after software, parameter or hardware changes.

## Rules
1. All robot, PLC, CNC and test-system programs are backed up to the plant version control server **before and after** any change. Robots: full controller backup (all programs, system variables, DCS/safety parameters, mastering data).
2. Changes to safety parameters (FANUC DCS, KUKA SafeOperation, ABB SafeMove) require controls engineer approval and a documented safety verification report.
3. After any mastering/calibration event: validate TCP, run the accuracy check and record results.
4. Firmware updates only during planned downtime with vendor support and rollback plan.
5. A DCS checksum mismatch alarm (e.g. SRVO-402) after a program change must be resolved by re-applying approved parameters, not by editing the checksum.
""")

sop("SOP-ROB-01", "General Robot Alarm Recovery", "ALL", "Robotics Supervisor", """
## Purpose
Standard approach to clear robot alarms safely and restore production.

## Steps
1. Read the alarm on the pendant and note code, axis/group, and time. Take a photo of the alarm history.
2. If the alarm is safety related (E-stop, chain abnormal, DCS), identify and fix the cause before reset; never bypass interlocks.
3. If the robot stopped mid-process (weld, glue, paint), check part status and quarantine suspect parts.
4. **Collision / disturbance alarms (e.g. SRVO-050, ABB 50026):** enter the cell per SOP-SAF-04, jog the robot clear in T1 using the collision release, inspect tool, fixture, and part for damage, check payload settings, and look for reducer wear if the alarm repeats on the same axis (rising motor current on J2/J3 is an early sign).
5. **Overtemperature / OVC alarms:** let the motor cool, check duty cycle, cooling surfaces and cabinet fans.
6. **Brake alarms:** run the brake test; failure means stop the robot and call the robotics supervisor (axis may drop).
7. After repair, run the program at reduced override, then full speed with an empty cell, and finally in production with first-part inspection.

## Documentation
Record fault code, cause and action on the work order. Repeating alarms are discussed in the weekly reliability meeting.
""")

sop("SOP-ROB-02", "FANUC Backup Battery Alarms (SRVO-062 BZAL / SRVO-065 BLAL) and Re-mastering", "ALL", "Robotics Supervisor", """
## Background
FANUC controllers keep absolute position (mastering) data in pulse coders powered by backup batteries. Two alarms matter:
- **SRVO-065 BLAL:** battery voltage is low, data is still intact. Warning, replace soon.
- **SRVO-062 BZAL:** battery voltage is zero, encoder data lost. Critical, the axis must be re-mastered.

Batteries (lithium A02B-0200-K102 in the controller and robot base on many models) typically last 1-2 years. Replace on a schedule or at the first BLAL.

## SRVO-065 BLAL (low battery) - do this the same shift
1. Keep the controller **powered ON** during replacement so data stays alive.
2. Replace the controller battery and the robot-base battery one at a time, checking polarity.
3. Record the date on the robot tag; clear the alarm.

## SRVO-062 BZAL (battery dead) - re-mastering
1. Replace batteries (check polarity and connector contact; verify the battery cable inside the base is not unplugged or broken).
2. On the pendant, clear the pulse coder alarm with **RES_PCA** (position capture reset) and power cycle (FCTN > 0 > 8 or controller restart).
3. Set **$MASTER_ENB = 1** and select Master/Cal, in T1 mode.
4. Jog the robot to the zero position by the **witness marks** (or use the calibration fixture/quick-master reference stored in the last backup).
5. Master (zero position master) all affected axes, then Calibrate. Cycle power.
6. Verify the zero position and TCP; run the weld/path accuracy check and obtain controls/robotics sign-off. If it still fails after battery replacement check battery installation polarity, contact cleanliness, and the encoder or cable (FANUC service).

## Notes
Typical downtime for BZAL is 90-300 minutes. Keep a controller backup current so that mastering data can be compared to the backup (positional accuracy is lost if the physical position differs from the backed-up mastering).
""", refs=["Public FANUC knowledge-base articles (alarm definitions)"])

sop("SOP-ROB-03", "KUKA Maintenance Reminders and Gear Oil Change", "ALL", "Robotics Supervisor", """
## Background
KUKA KRC4/KR C5 controllers raise maintenance reminder messages based on operating hours or calendar time. Typical OEM intervals: gearbox oil replacement every 10,000-20,000 hours or 3-4 years for main axes (A1-A3), inline-wrist belt inspection/tension at 8,000-10,000 h (6-axis inline wrist only), electrical cabinet inspection by calendar. Newer KR QUANTEC PA palletizers specify an oil change at 20,000 operating hours; some models list "20,000 hourly / 5 yearly gear oil change".
Approved lubricant: KUKA-approved synthetic gear oil, ISO VG 150 (for example Shell Tivela S150 on QUANTEC primary axes; about 8 L per primary axis, confirm the exact quantity in the model manual).

## Oil change procedure (summary)
1. **Burn hazard:** if the robot has just stopped, oil and surfaces may be very hot. Let it cool to a safe temperature but drain while still warm for best flow.
2. Lock out the robot (SOP-SAF-01) and block axis 2/3 against falling.
3. Pull out the oil drain hose; place a suitable receptacle under it; unscrew the union nut of the drain hose.
4. Drain completely; inspect the drained oil for metal particles (indicator of internal wear); photograph and record.
5. Refit the hose, refill through the filler port with approved oil to the level mark, replace sealing washers.
6. Run the robot through the warm-up program (axes 1-3 at 50% for 15 minutes), re-check level and leaks.
7. **Reset the maintenance counter** from the SmartPAD (Maintenance > Resets) and record the service date and hours on the WO.

## Related checks
Inspect robot arm housing for oil leakage at the gearbox seals (A1-A3 primary, A4-A6 secondary). A leak that returns within one shift indicates seal wear or an over-filled/blocked-vent gearbox. Brake test on all axes after oil changes.
""", refs=["Public KUKA maintenance information (industrialmonitordirect.com, kuka.com press release 2021, MaintainX asset library)"])

sop("SOP-ROB-04", "Spot Weld Tip Dressing, Weld Quality Verification and Weld Gun Care", "BIW", "Process Engineer", """
## Tip care
- Dress or change electrode caps at the programmed stepper count (typically every 16-100 welds depending on coating and schedule).
- Cooling water flow at each gun must be at least 4 l/min; low flow causes tip overheating and sticking (fault codes WG-TIP-WEAR, KSS-SPOT-STICK).
- If a tip sticks (robot motion blocked), break the tip free using the manual release, replace the cap, and check the weld schedule and flow before resuming.

## Verification
- Peel test (chisel/destructive) at start of each shift per weld group; nugget diameter at least 4 x sqrt(t) where t is thinnest sheet thickness.
- Ultrasonic nugget testing for critical structural welds weekly.
- Any gun with low-current alerts (weld current falling below warn) is inspected for cable/shunt wear and transformer cooling.

## Weld transformer overtemperature (WG-TRANSF-TEMP)
Check coolant flow and temperature; verify duty cycle; check thermal switch; do not defeat the switch. Replace the transformer if windings are suspect.

## Records
Peel test log, tip dress logs (auto), weld controller logs.
""")
