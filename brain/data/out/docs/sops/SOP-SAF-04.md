# SOP-SAF-04: Robot Cell Entry, Teaching and Safeguarding

**Area:** ALL  |  **Owner:** Robotics Supervisor  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

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

## References
- ISO 10218-1/-2
- ANSI/RIA R15.06
