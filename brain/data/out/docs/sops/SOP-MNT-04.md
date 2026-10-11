# SOP-MNT-04: Spare Parts, Critical Spares and Emergency Purchasing

**Area:** ALL  |  **Owner:** Storekeeper  |  **Revision:** C  |  **Effective:** 2025-03-01

> **Synthetic training document.** Written for the Voltara Motors digital-twin demo. It is modeled on public OEM and industry information but it is NOT an OEM document. Items tagged `oem_public` were checked against public sources; items tagged `synthetic` are invented for realism. Do not use for real equipment.

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

## References
- Internal
