# SOP-MNT-06: Management of Change and Robot Program Backup

**Area:** ALL  |  **Owner:** Controls Engineer  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

## Purpose
Prevent unplanned behavior after software, parameter or hardware changes.

## Rules
1. All robot, PLC, CNC and test-system programs are backed up to the plant version control server **before and after** any change. Robots: full controller backup (all programs, system variables, DCS/safety parameters, mastering data).
2. Changes to safety parameters (FANUC DCS, KUKA SafeOperation, ABB SafeMove) require controls engineer approval and a documented safety verification report.
3. After any mastering/calibration event: validate TCP, run the accuracy check and record results.
4. Firmware updates only during planned downtime with vendor support and rollback plan.
5. A DCS checksum mismatch alarm (e.g. SRVO-402) after a program change must be resolved by re-applying approved parameters, not by editing the checksum.

## References
- Internal
