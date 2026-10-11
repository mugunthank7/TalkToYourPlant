# SOP-ROB-01: General Robot Alarm Recovery

**Area:** ALL  |  **Owner:** Robotics Supervisor  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

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

## References
- Internal
