# SOP-MNT-M05-01: Weld robot axis 1 joint bearing wear: diagnosis and replacement

**Area:** BIW (twin station S06)  |  **Machine:** M05 Weld robot 2  |  **Owner:** Maintenance Supervisor  |  **Revision:** A  |  **Effective:** 2026-10-01

> **Synthetic training document** for the Voltara/Voltline digital-twin demo. Values tagged `synthetic` are invented. Not an OEM document.

## Symptom pattern
- `vibration_rms` rises steadily over hours, with energy in the bearing defect band growing faster than overall RMS.
- `temperature_c` (axis 1 housing) climbs 10 to 15 C above baseline; `motor_current_a` rises about 10 to 15 percent under the same weld cycle.
- Cycle time slips and weld position quality can degrade as play grows.

## Likely cause (failure mode: bearing_wear)
Lubricant breakdown or contamination at the axis 1 joint bearing (`m05_joint1_bearing`), often after a collision event or a missed regrease interval. Left running, wear accelerates and can seize the joint (long unplanned stop).

## Decision: keep running?
Apply SOP-OPS-02. For M05 (criticality A) with vibration above 2x baseline and a rising trend, do not extend beyond the current batch. Plan the bearing change at the next buffer-protected stop.

## Replacement procedure (synthetic)
1. Notify line lead and maintenance bay (S10). Raise a corrective work order for `m05_joint1_bearing`.
2. Pick spare part `bearing_6208` (Deep groove ball bearing 6208, A1 joint) from the spare parts cage (S12). Confirm stock and bin.
3. Lockout/tagout per SOP-SAF-01. Move robot to the service pose and support the arm.
4. Remove axis 1 cover, inspect for metal particles and contamination, take a photo for the work order.
5. Press out the worn bearing, clean the seat, fit the new bearing, regrease with the specified grease.
6. Reassemble, remove LOTO, run a dry cycle, then weld cycles at reduced speed for 10 cycles.
7. Confirm vibration and current back within 10 percent of baseline; close the work order and note the bearing hours.

## Time and parts (synthetic)
- Typical repair time: 90 to 150 minutes (planned) once the part is at the machine.
- Crew: 1 technician plus 1 assistant. Spare stock: 2 on hand, lead time 9 days.

## Escalation
Follow the M05 on-shift chain in the escalation matrix (L1 primary tech, L2 backup, L3 maintenance supervisor).
