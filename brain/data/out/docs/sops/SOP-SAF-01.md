# SOP-SAF-01: Lockout/Tagout (Control of Hazardous Energy)

**Area:** ALL  |  **Owner:** EHS Officer  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

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

## References
- OSHA 29 CFR 1910.147
