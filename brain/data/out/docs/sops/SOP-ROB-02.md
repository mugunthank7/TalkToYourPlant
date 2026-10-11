# SOP-ROB-02: FANUC Backup Battery Alarms (SRVO-062 BZAL / SRVO-065 BLAL) and Re-mastering

**Area:** ALL  |  **Owner:** Robotics Supervisor  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

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

## References
- Public FANUC knowledge-base articles (alarm definitions)
