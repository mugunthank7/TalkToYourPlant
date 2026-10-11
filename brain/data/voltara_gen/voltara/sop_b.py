"""Procedures & protocols, part B: area-specific, quality, utilities, operations decisions (synthetic)."""

SOPS_B = []


def sop(sid, title, area, owner, body, revision="B", effective="2025-06-01", refs=None):
    SOPS_B.append(dict(id=sid, title=title, area=area, owner=owner, revision=revision, effective=effective,
                       references=refs or [], body=body.strip()))


sop("SOP-CAS-01", "Giga Press Start-up, Shutdown and Daily Hydraulic Checks", "CAS", "Casting Area Manager", """
## Machine overview
IDRA GIGAPRESS NEO 6100 class: 6,100 t (about 60,000 kN) clamping force, die height 2,400 mm, ~430 t, with accumulator-based injection (fill time roughly 120 ms for a 6,000 t class machine), Block-Control tie-bar monitoring with automatic clamping-force adjustment, automatic toggle lubrication and servo-driven guarding.

## Start-up
1. Verify LOTO released and the machine area clear. Check the die is locked and cooling circuits are connected.
2. Hydraulic walk-down: reservoir level at least 85%, oil temperature between 35 and 50 C, no leaks, filter dP indicators green, accumulator pre-charge gauges within the setpoint on the machine card.
3. Start hydraulic pumps, wait for pressure to stabilize at setpoint (nominal ~280 bar on the main circuit). If pressure fails to build or is more than 10% low, stop (fault GP-PRESS-LOW).
4. Warm up die with the die thermal control units to the die temperature recipe before first shot. Run 3 dry cycles and check clamping force distribution across the four tie bars; investigate a deviation > 3% (fault GP-TIEBAR, run tie-bar calibration).
5. Start the dosing furnace transfer and inject the first shots at reduced speed; verify fill time and shot curve against the golden profile before full speed.

## During production
- Check the shot profile each shift: a slow fill or low accumulator recovery points to accumulator pre-charge loss, valve response issues or sleeve wear (GP-SHOT-SLOW).
- Record hydraulic temperature; above 58 C is a warn. Clean oil cooler and check water flow; above 65 C is an alarm: stop at end of shot.
- Trim, X-ray and machining cells downstream depend on this machine (criticality A).

## Shutdown
Run last shot, retract plunger, close die with low force, switch off pumps, vent accumulators only for maintenance (LOTO). Record the shot counter and any parameter changes.
""", refs=["IDRA public Giga Press catalog data"])

sop("SOP-CAS-02", "Die Change and Die Cooling Leak / Molten Metal Safety", "CAS", "Casting Area Manager", """
## Die change
1. Cool the die to the permitted handling temperature; remove die spray and cooling hoses.
2. LOTO the press and apply the die-safety blocks between platens (SOP-SAF-01).
3. Use the overhead crane (certified operator, cert CRANE) and the die cart; verify die weight vs crane rating. Follow lift plan.
4. Install the new die, connect cooling circuits, pressure-test the circuits at working pressure for 5 minutes, and verify zero leak before heating.
5. Run the die warm-up and first-off qualification.

## Die cooling leak (GP-DIE-LEAK) - Level 6 notification
Water entering a molten-aluminum cavity can cause a violent steam explosion. If a leak is suspected (steam, popping, water at parting line, moisture on casting): stop the cycle, clear the area by 10 m, do not open the press until the die surface temperature and cooling circuits have been checked, notify the Casting Area Manager and EHS, and pull the die under SOP-CAS-02 with the Maintenance Manager's approval.

## Molten metal PPE
Aluminized coat and hood, face shield, heat-resistant gloves, safety boots with metatarsal protection. No wet tools or moist alloy ingots near the furnace.
""")

sop("SOP-CAS-03", "Shot Sleeve and Plunger Tip Inspection", "CAS", "Reliability Engineer", """
Inspect the plunger tip and shot sleeve every 400 operating hours or after any GP-SHOT-SLOW event.
- Measure plunger tip outside diameter and sleeve inside diameter; replace the tip when clearance exceeds the OEM limit or when scoring is visible.
- Check lubricant spray quality and plunger lubrication; check for aluminum buildup.
- Verify shot speed profile after replacement; record the first 20 shots.
- A worn tip raises fill time variation, increases porosity and can show as lower accumulator pressure drop.
Typical downtime for a planned tip change is 2-3 hours; unplanned replacement 2-8 hours.
""")

sop("SOP-HYD-01", "Hydraulic System Fault Response: Low Pressure, High Temperature, Leaks, Filter dP", "ALL", "Hydraulics Technician Lead", """
## General
Hydraulic systems on presses, the Giga Press and trim press store energy in accumulators. Always depressurize and LOTO before opening any hose, fitting, filter or valve.

## Low pressure
1. Confirm gauge vs transducer; check reservoir level and pump motor current.
2. Check accumulator nitrogen pre-charge (should be 60-70% of minimum operating pressure); recharge or replace bladder/piston seals.
3. Check pump delivery vs baseline and case-drain flow (a rising drain flow indicates pump wear).
4. Inspect valve block cartridges for internal leakage; swap in a known good cartridge if available.
5. Replace suction strainer if clogged; check oil viscosity.

## High oil temperature
Check cooling water flow and inlet temperature, clean the cooler, verify the thermostatic valve, and trend temperature versus cycle count. A steady rise at constant load often indicates pump internal leakage (energy converting to heat).

## Hose/fitting leaks
Isolate and depressurize per LOTO; replace hose with the same part number and date code, torque fitting to spec, clean up spills (SOP-ENV-01), top up reservoir with the correct oil grade; run and inspect under pressure from a safe distance.

## Filters
Replace return and pressure filters at amber dP indicator or at the PM interval; take an oil sample if the filter loaded abnormally fast. Target cleanliness ISO 4406 17/15/12 or better for proportional/servo valves.

## Escalation
Pressure or temperature in alarm, oil fire risk, or a leak larger than 5 gallons: page the Maintenance Supervisor and EHS.
""", refs=["ISO 4406"])

sop("SOP-STP-01", "Servo Press: Double Blank, Die Cushion and Transfer Misfeed Response", "STP", "Stamping Area Manager", """
- **Double blank (PRS-DOUBLE-BLANK):** stop the line, LOTO, remove both blanks, check destacker magnets and fanner; check double-blank sensor sensitivity (target thickness reading 0.7-0.8 mm for outer panels) and clean the sensor head. Inspect die for damage before restart.
- **Die cushion pressure loss:** check cushion cylinder seals and valve; run cushion calibration after repair.
- **Transfer misfeed (PRS-TRANSFER):** inspect fingers for wear; re-sync the transfer servo; verify part presence sensors.
- Always run the first 5 panels slowly after a die change and perform a visual/gauge check before releasing the batch.
""")

sop("SOP-PNT-01", "Paint Booth: Ex-Zone Safety, Purge Faults, Atomizer and Color Changer", "PNT", "Paint Area Manager", """
## Hazard
Paint robots operate in explosion-protected zones; purged enclosures must maintain positive pressure before power is applied.

## Purge fault (PR-EXPL-INTERLOCK) - Level 6 notification
1. **Do not start or reset the robot repeatedly.** Shut down the booth segment via the booth control.
2. Verify purge air supply pressure and flow; check the purge pressure sensor and tubing for kinks/leaks.
3. Only a person with ATEX competence (cert ATEX) may restore; document readings before restart.

## Atomizer (PR-BELL-SPEED)
- Bell speed nominal ~45 krpm; warn at 42, alarm at 38. Check turbine air pressure and filter, bearing air quality, and contamination on the cup.
- Replace the turbine at alarm or when speed fluctuates > 3%.
- Verify film build on test panel after replacement.

## Color changer
Flush with solvent per color change; stuck valves are common after long idle periods. Replace valve seats and run a purge test.

## Film build defects (PR-FILM-DEFECT)
Calibrate flow meters, check shaping air, and run test panels; confirm thickness with the thickness gauge before releasing production.

## Housekeeping
Overspray and booth filters are replaced per PM; keep walkways clear.
""", refs=["NFPA 33"])

sop("SOP-PNT-02", "Cure Oven Start-up, Purge and Temperature Profiling", "PNT", "Paint Area Manager", """
1. Start the exhaust fans and verify flow switches (OVN-EXH-LOW interlock prevents burner start).
2. Complete the pre-ignition purge cycle per NFPA 86 timing; confirm the purge timer completes.
3. Ramp the oven zones per recipe (nominal 165 C for cure zones; allowed deviation +/- 5 C).
4. Run a temperature profile with a data logger weekly (and after any burner/fan repair).
5. Alarms: zone temperature deviation (OVN-ZONE-TEMP) - compare with reference thermocouple; fan vibration high (OVN-FAN-VIB) - stop at alarm (vibration > 7.1 mm/s equivalent) and inspect bearings; chain drive faults inside the oven (OVN-CHAIN) - check chain tension hot and relubricate with high-temperature lubricant.
6. Annual: safety interlock test and thermocouple calibration.
""", refs=["NFPA 86"])

sop("SOP-BAT-01", "Pack Fastening, Torque Traceability and Isolated Tooling", "BAT", "Process Engineer", """
## Equipment
Synchronous four-spindle fastening stations (Desoutter) apply up to 20 Nm to fix the pack at four points simultaneously; the spindles are galvanically isolated to protect workers near HV busbars. Corded isolated angle drivers are used for busbar rework.

## Procedure
1. Daily torque verification on the test joint (record in the daily check). Reject the station if the verification falls outside +/- 5%.
2. All tightening results are recorded against the VIN/pack serial. NOK results are not re-tightened without quality approval.
3. A **missed-bolt (TQ-BATCH-MISS)** event quarantines the pack, and requires re-inspection by a quality inspector before release.
4. Inspect isolation of chucks and cables at each PM; replace damaged cables (TQ-CBL-FAULT).
5. Transducer calibration yearly (or every 500k cycles); station without valid certificate must not run.

## Typical torque faults
- TQ-NOK: out-of-window torque - check cross-threading, socket wear, transducer drift and fastener lot friction.
- TQ-MOTOR-TEMP: tool temperature rising - verify duty cycle, replace gear head if abnormal.
""", refs=["Public Desoutter/Assembly magazine information on EV pack fastening"])

sop("SOP-BAT-02", "Laser Safety and Protective Glass Replacement", "BAT", "Process Engineer", """
Class 4 lasers (TruDisk disk lasers for busbar welding and laser brazing) require a Laser Safety Officer (cert LASER) for any enclosure access.
- Interlocks and shutter checks daily; fume extraction verified before use.
- **Protective cover glass** is the most common consumable: contamination leads to power loss (LSR-PWR-LOW). Replace when the measured power at the workpiece falls below 94% of nominal (alarm 90%) or when the cleaning cycle no longer restores power. Inspect glass at the start of each shift in BAT-BL cells (daily PM) and weekly in brazing cells.
- After replacing the glass, run a power measurement and a seam test; record readings.
- Chiller outlet temperature must stay within 20-25 C; above 27 C triggers inspection of chiller filters/condenser.
- Never defeat interlocks; the shutter must confirm open before beam on.
""")

sop("SOP-BAT-03", "Pack End-of-Line: Helium Leak Test and HV Test Fail Handling", "BAT", "Quality Engineer", """
## Helium leak test
- Run reference leak check weekly and at the start of each shift on A criticality; reject threshold typically 5 x 10^-6 mbar l/s (warn) and 1 x 10^-5 (alarm) for the plant recipe.
- Failed packs are quarantined, retested once, and sent to rework if still failing. Check seal/gasket, fastening torque history and glue bead record in MES.

## HV / insulation / functional test
- Insulation resistance or functional failure: quarantine the pack in the marked area, inform the HV Safety Engineer if there is any voltage anomaly or swelling.
- False-fail trends (TST-FALSE-FAIL) are investigated for contact wear in the fixture (pogo pins) and threshold drift before touching packs.
- Packs that fail twice go to teardown with Quality; keep the data trace.
""")

sop("SOP-QA-01", "Torque NOK Handling and Tool Calibration (General Assembly)", "GA", "Quality Engineer", """
- Atlas Copco Power Focus controllers log each tightening with VIN, torque, angle and status.
- NOK actions: stop the station, inspect fastener and joint, **do not re-tighten** without quality approval, and check the daily test joint verification.
- Three NOKs in a row, or 2% NOK rate in a shift, triggers a containment: check tool calibration, socket wear, and fastener batch; quarantine suspect lots; audit the last 20 vehicles.
- Calibration: transducer calibration every 12 months or 500k cycles; overdue tools are tagged out (TQ-CAL-DUE).
- Cable faults (TQ-CBL-FAULT) and tool overtemperature (TQ-MOTOR-TEMP) are handled by process technicians.
""")

sop("SOP-QA-02", "Containment and Quarantine of Suspect Vehicles/Parts", "ALL", "Quality Manager", """
1. Stop shipping affected units; apply a Quality hold tag in MES.
2. Identify scope using shift, machine, time window, and VIN range from the CMMS and MES.
3. Segregate parts physically in the red-tag area.
4. Perform 100% re-inspection until the root cause is fixed and 3 consecutive good lots verified.
5. Record disposition (rework, scrap, release) and customer-impact assessment.
Large downtime events with possible quality impact (e.g. weld parameter drift, paint film defect, laser power drop) always trigger containment for units made since the last verified good check.
""")

sop("SOP-GA-01", "Conveyor, AGV and AMR Fault Response", "GA", "General Assembly Area Manager", """
- **Conveyor jam (CNV-JAM):** LOTO before clearing; check carrier alignment, photo-eye cleanliness and chain tension.
- **Drive overload (CNV-DRV-OVL):** check for mechanical resistance, motor current vs nameplate; replace gearmotor if abnormal; vibration above 5 mm/s is a warn.
- **Chain elongation:** measure elongation, replace the chain section above 3%.
- **AGV/AMR localization lost (AGV-NAV-LOST):** re-localize at a charging station; update map if layout changed.
- **Safety scanner fault (AGV-LIDAR):** clean lens, verify protective field with test object; never bypass.
- **Low battery or charge contact failure:** replace contact set; verify charger.
- Decking AGVs carrying battery packs: a stopped AGV in the marriage station blocks the line (criticality A). Notify the supervisor immediately.
""")

sop("SOP-UTL-01", "Compressed Air System: Compressor Trip and Low Pressure Response", "UTL", "Utilities Supervisor", """
- Plant air header normal 7.5 bar; if pressure falls below 6.0 bar start the standby compressor and prepare to shed non-critical loads (blow-off, cleaning).
- **Discharge temperature high (CMP-DISCH-TEMP):** nominal ~85 C; warn 100 C; alarm 108 C. Check cooler fouling (Texas summer), oil level and thermostatic valve; clean cooler fins; check ambient ventilation.
- **Oil separator dP high:** replace separator element (typically at 0.9 bar differential).
- **Dryer dew point alarm:** check condensate drains; service dryer.
- **Motor overload trip:** check bearings and supply voltage imbalance.
- Run the lead/lag schedule weekly so run hours stay balanced across the four compressors.
""")

sop("SOP-UTL-02", "Electrical Supply: Breaker Trip and Load Shedding Priority", "UTL", "Electrical Supervisor", """
- On feeder breaker trip: do not reclose until the relay event log is reviewed; megger test affected circuits; thermography afterwards.
- **Load shedding order when supply is constrained:** 1) non-critical HVAC and lighting, 2) cure oven zones in idle mode, 3) machining centers, 4) stamping, 5) body shop, 6) battery and EOL test systems, 7) paint robots (never shed during booth purge), 8) chillers/compressors (last).
- Substation transformer temperature: nominal ~62 C, warn 95 C, alarm 110 C. Check cooling fans and load; request load reduction if alarm.
""")

sop("SOP-ENV-01", "Oil and Fluid Spill Response", "ALL", "EHS Officer", """
1. Stop the leak source if safe (isolate, LOTO as needed).
2. Contain with absorbent socks/pads, protect drains.
3. Spills > 5 gallons or reaching a drain: notify EHS immediately.
4. Clean up, dispose in the labeled oily waste container, and record in the environmental log.
5. Open a work order to repair the source and review hose/fitting condition.
""")

sop("SOP-OPS-01", "Line Restart After Planned or Unplanned Shutdown", "ALL", "Operations Director", """
1. Verify the equipment is released from LOTO and all PM/CM work orders for the machines in the restart zone are closed or have supervisor-approved temporary fix.
2. Confirm utilities (air, cooling water, power) are stable.
3. Restart in flow order: casting and stamping, body-in-white, paint, battery/drive unit, general assembly, EOL.
4. First-off inspection by quality at every critical station before releasing the line; verify torque, weld, adhesive, leak test results.
5. Update the handover with restart time and any watch items.
""")

sop("SOP-OPS-02", "Run-Extension and Run-to-Failure Risk Decision (e.g. 'Keep running 2 more hours?')", "ALL", "Maintenance Manager", """
## Purpose
Provide a consistent, risk-based way to decide whether a machine showing warning signs may keep producing until a planned stop, a shift end, or a defined time extension.

## Inputs to the decision
1. Machine criticality (A/B/C) and buffer status (how many minutes of downstream stock exist).
2. Sensor channels vs thresholds: nominal / warn / alarm, trend slope (rate of change per hour), and SHAP-contributing features from the anomaly alert.
3. Fault history: same fault code in the last 14/90 days; recent PdM work orders; days since last PM.
4. Safety potential: could the failure create a hazard (HV, molten metal, Ex-zone, hydraulic burst, crane load)?
5. Consequence: estimated downtime if it fails (MTTR for the fault code from the machine manual), parts availability, lost vehicles per hour.

## Rules
- **Safety-critical channels at warn or worse:** never extend. Stop at the earliest safe point and notify L3/L4.
- **Any channel at alarm:** no extension unless the Maintenance Manager approves in writing with a mitigation (reduced speed, extra monitoring every 15 min, tech on standby).
- **Channel at warn, trend flat (< 2% change per hour):** extension up to 2 hours allowed with supervisor approval; technician inspects at the next break; re-evaluate every 30 minutes.
- **Channel at warn, trend rising (> 2% per hour or accelerating):** extension limited to the time needed to complete the current batch or reach a buffer-protected stop (max 30-60 min); schedule repair immediately.
- **Between 70% and 100% of nominal-to-warn distance:** extension allowed to the end of shift; raise PdM work order; add watch to handover.
- **Repeat failure (same fault within 14 days):** treat as warn at minimum; engineer must approve.
- **Criticality-A machine with no spare for a high-MTTR part:** do not run beyond the planned window unless production loss from stopping exceeds the expected loss from a failure (expected loss = probability of failure x MTTR x loss/hour). Document the calculation.

## Documentation
Record the decision, approver, time limit, mitigations and monitoring in the work order and shift handover. After the extension, close the loop: confirm outcome and update the PdM/anomaly model feedback.
""")

sop("SOP-EOL-01", "Roll & Brake Dynamometer and ADAS Calibration: Failure Handling", "EOL", "EOL Area Manager", """
- Dynamometer: roller surface and bearing check weekly; calibration of speed/force sensors annually. A failed dyno test never releases the vehicle: re-run once after checking tire pressure, wheel-end torque and strap tension; second failure goes to diagnostic bay.
- ADAS calibration: target alignment verified monthly; vehicle must be on level floor and tire pressures set; out-of-window results (e.g. camera aim) require recalibration and recording; repeated failures on the same bay indicate target/alignment drift (check with reference vehicle).
- Test station communication loss to MES (TST-COMM) stops release; controls technician restarts service and checks network.
""")

sop("SOP-CNC-01", "5-Axis Machining Center: Spindle Vibration, Coolant, ATC and Dimensional Drift", "CAS", "Casting Area Manager", """
- Spindle vibration trending up (nominal ~1.2 mm/s; warn 4.0; alarm 6.5): check tool balance and drawbar clamp force first, then bearings; plan spindle exchange at alarm (a 3-12 hour job).
- Coolant: concentration 7-9% by refractometer; check weekly; replace filter bags at dP alarm.
- ATC faults: check air pressure (at least 6 bar), gripper wear and positions.
- Part dimension drift: run the warm-up program, re-qualify tool offsets, check fixture clamping pads; thermal growth is common after long idle periods.
- Ballscrew and linear scale faults: check lubrication; backlash measurement.
""")
