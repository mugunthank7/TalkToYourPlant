# Demo questions (all verified high confidence)

Every question below was run against the live stack (real engine, local brain) and returned **high confidence**, not degraded, with the expected content. Re-check any time:

```bash
brain/scripts/start_all.sh                 # engine, brain, dashboards, 3D twin
python3 brain/eval/demo_check.py --reset   # rewinds the engine to just after the M05 alert, asks all 18 questions
```

**Setup the answers assume:** engine at t = 12,500 s (just after the M05 bearing alert), faults cleared, brain in live mode. Questions in a group share one chat session, so follow-ups like "What should I do?" work. Source of truth: `brain/eval/demo_questions.json`.

## 90-second demo path
1. Open the 3D twin (http://localhost:5180). S06 Weld cell B is red.
2. Click **S06**. The panel shows what went wrong, what to do, who to page.
3. Open **Ask your plant**: "Why is M05 red?" then "What should I do?" then "Can we keep running M05 2 more hours?"
4. "Create a work order for the M05 bearing replacement." The technician walks in the 3D view.
5. Break something else: **Simulate failure here** on S05 or ask "What happens if the conveyor stops?"
6. Open the monitor (http://localhost:8300) to show the plant and the brain reacting to the change in real time.

## A. The hero moment (M05 bearing wear)

### "Why is M05 red?"
*What it shows:* Status card: cause, evidence, impact, steps, who to page, part, SOP.  
*Confidence:* high (0.9)

```
M05 Weld robot 2 (station S06)  |  CRITICAL
Needs action now.

WHAT HAPPENED
- Joint bearing wear (bearing_wear).
- Likely cause: lubricant breakdown or missed regrease interval.
- Vibration is 1.08x the healthy level.
- Flagged because of: bearing-defect band, bearing-band trend.

IMPACT
- About 157 minutes of useful life left.
...
```

### "What should I do?"
*What it shows:* Follow-up: remembers M05, gives the action list.  
*Confidence:* high (0.9)

```
M05 Weld robot 2 (station S06)  |  CRITICAL
Needs action now.

WHAT HAPPENED
- Joint bearing wear (bearing_wear).
- Likely cause: lubricant breakdown or missed regrease interval.
- Vibration is 1.08x the healthy level.
- Flagged because of: bearing-defect band, bearing-band trend.

IMPACT
- About 157 minutes of useful life left.
...
```

### "Who do I page for M05?"
*What it shows:* Escalation chain for the current shift with timers.  
*Confidence:* high (0.9)

```
M05 Weld robot 2 (station S06)  |  INFO
On shift A, page in this order.

DO NOW
1. Press andon, tell Line Lead, note fault code/time

WHO TO PAGE
- L0 Latoya Joshi (line lead), x4199, radio BIW-FA
- L1 Yuki Alvarez (Robotics Technician (L1)), x4438, radio PLT-22: now
- L2 Nicholas Mukherjee (Robotics Technician (L2)), x4434, radio PLT-CA: after 8 min if no answer
- L3 George Sato (Maintenance Supervisor), x4265, 830-555-0126, radio PLT-4D: after 15 min if no answer
...
```

### "Which part do we need for M05 and is it in stock?"
*What it shows:* Part number and stock from the knowledge base.  
*Confidence:* high (0.9)

```
M05 Weld robot 2 (station S06)  |  INFO
bearing_wear: Joint bearing wear.

WHAT HAPPENED
- Likely causes: Lubricant breakdown or missed regrease interval; Contamination at the axis 1 joint; Collision or overload event

IMPACT
- Shows in vibration_rms (None)

PART
- bearing_6208 (Deep groove ball bearing 6208 (A1 joint)), 2 in stock
...
```

### "Can we keep running M05 2 more hours?"
*What it shows:* Live what-if from the engine plus the SOP-OPS-02 rule.  
*Confidence:* high (0.9)

```
M05 Weld robot 2 (station S06)  |  WARNING
Keep running 2 more hours? NOT RECOMMENDED. Exceeds the SOP-OPS-02 limit for a rising trend.

WHAT HAPPENED
- With the alert ignored for 2.0 h: 260 cars instead of 267 (7 fewer), downtime 69 min vs 77 min, OEE 79% vs 82%, 274,070 dollars saved in downtime cost.

IMPACT
- Downtime 69.4 min if you wait, versus 76.6 min if repaired now.
- Downtime cost $2,636,109 versus $2,910,179.
- OEE 0.793 versus 0.82.
- Predicted remaining life 157 min (safe lower bound 25 min).
...
```

### "Create a work order for the M05 bearing replacement."
*What it shows:* Opens a real work order in the engine.  
*Confidence:* high (0.9)

```
M05 Weld robot 2 (station S06)  |  INFO
Work order WO-SIM-0002 created.

WHAT HAPPENED
- Component m05_joint1_bearing; fault bearing_wear.

IMPACT
- Downtime costs about $38,000 per minute until it is fixed.

DO NOW
1. A technician is dispatched; the engine opens the work order.
...
```

## B. What if something breaks

### "What happens if the conveyor stops?"
*What it shows:* Engine fault branch: cars lost and cost.  
*Confidence:* high (0.9)

```
M06 Main conveyor (station S04)  |  WARNING
If M06 Main conveyor stops for 30 minutes: about 26 fewer cars and $1,498,796 extra downtime cost.

WHAT HAPPENED
- With a breakdown of M06: 241 cars instead of 267 (26 fewer), downtime 116 min vs 77 min, OEE 74% vs 82%, 1,498,796 dollars extra in downtime cost.

IMPACT
- Downtime 116.0 min versus 76.6 min.
- OEE 0.738 versus 0.82.

DO NOW
...
```

### "What happens if the decoiler fails?"
*What it shows:* Same, upstream machine.  
*Confidence:* high (0.9)

```
M10 Decoiler (station S01)  |  WARNING
If M10 Decoiler stops for 30 minutes: about 0 fewer cars and $0 extra downtime cost.

WHAT HAPPENED
- With a breakdown of M10: 267 cars instead of 267 (0 more), downtime 77 min vs 77 min, OEE 82% vs 82%, 0 dollars extra in downtime cost.

IMPACT
- Downtime 76.6 min versus 76.6 min.
- OEE 0.82 versus 0.82.

DO NOW
...
```

### "How many cars have we built so far?"
*What it shows:* Live KPIs: output, OEE, downtime cost.  
*Confidence:* high (0.9)

```
Plant output  |  INFO
122 cars so far this shift against a plan of 320.

IMPACT
- OEE 0.867, throughput 36.0 cars per hour.
- Downtime 24.1 min, about $915,057.
```

## C. Know the plant

### "What does the casting press do?"
*What it shows:* Station record with machines and flow.  
*Confidence:* high (0.84)

```
From the station record: Station S02 (Casting and press): Large casting press forms underbody parts; a transfer robot moves parts out. Machines: M01 Casting press, M02 Press transfer robot. [S02]
```

### "What are the safety rules in the weld cell?"
*What it shows:* Procedure lookup with source.  
*Confidence:* high (0.95)

```
From SOP-SAF-04, Robot Cell Entry, Teaching and Safeguarding: Purpose Protect personnel who enter robot cells for maintenance, teaching or troubleshooting. Applies to all FANUC, KUKA, ABB, Duerr and cobot cells. [SOP-SAF-04]
```

### "Which SOP covers lockout tagout?"
*What it shows:* Procedure finder.  
*Confidence:* high (0.9)

```
Procedures  |  INFO
1 relevant procedure(s).

PROCEDURE
- SOP-SAF-01: Lockout/Tagout (Control of Hazardous Energy)

Sources: [SOP-SAF-01]
```

### "What does fault code SRVO-062 mean on M04?"
*What it shows:* Fault-code meaning from the manual catalogue.  
*Confidence:* high (0.9)

```
M04 Weld robot 1 (station S05)  |  INFO
SRVO-062: BZAL alarm: pulsecoder backup battery voltage zero, absolute position lost.

WHAT HAPPENED
- Likely causes: Encoder backup battery fully discharged; Battery cable disconnected or broken inside base; Controller powered off for a long period with dead battery

IMPACT
- Shows in battery_voltage_v (decay)

PART
- FAN-A02B-0200-K102 (Lithium backup battery A02B-0200-K102)
...
```

### "What spare part is needed to fix KSS-GEAR-LEAK on BIW-WK-03?"
*What it shows:* Fault to part mapping.  
*Confidence:* high (0.9)

```
BIW-WK-03 Spot Weld Robot (KUKA) 3  |  INFO
KSS-GEAR-LEAK: Oil leak detected at A1-A3 gearbox seal.

WHAT HAPPENED
- Likely causes: Seal wear; Over-filled gearbox; Vent plug blocked

IMPACT
- Shows in gearbox_temp_c (drift_up)

PART
- KUKA-SEAL-A2 (Axis 2 shaft seal kit)
...
```

### "How many times has CAS-GP-01 had GP-SHOT-SLOW in the last 90 days?"
*What it shows:* Repeat-failure history from 20k work orders.  
*Confidence:* high (0.9)

```
CAS-GP-01 Giga Press 1  |  WARNING
GP-SHOT-SLOW happened 2 times in the last 90 days.

WHAT HAPPENED
- 16 times in the whole history; latest 2026-10-02.

IMPACT
- Repeat faults should be treated as at least warning level (SOP-OPS-02).

DO NOW
1. Ask the engineer for a root-cause review if it keeps coming back.
...
```

### "Who do I page for CAS-GP-01 on shift B?"
*What it shows:* Escalation for a specific machine and shift.  
*Confidence:* high (0.9)

```
CAS-GP-01 Giga Press 1  |  INFO
On shift B, page in this order.

DO NOW
1. Press andon, tell Line Lead, note fault code/time

WHO TO PAGE
- L0 Michael Taylor (line lead), x4269, radio CAS-11
- L1 Kwame Sato (Hydraulics / Pneumatics Technician (L1)), x4474, radio PLT-CB: now
- L2 Deepak Hicks (Hydraulics / Pneumatics Technician (L2)), x4475, radio PLT-BA: after 8 min if no answer
- L3 Larry Banerjee (Maintenance Supervisor), x4348, 737-555-0121, radio PLT-16: after 15 min if no answer
...
```

### "Explain OEE"
*What it shows:* Plain-language glossary.  
*Confidence:* high (1.0)

```
OEE (overall equipment effectiveness) is availability x performance x quality: how much of the planned production time the line really produces good cars.
```

### "What can you do?"
*What it shows:* Capability answer with example questions.  
*Confidence:* high (1.0)

```
I can tell you why a machine is alarming, what is likely wrong, who to page, which part and procedure apply, and what happens if you keep running. Click a station in the 3D view and I'll focus on it.
Try: "Why is M05 red?" / "Who do I page for M05?" / "Can we keep running M05 2 more hours?"
```

## Questions to avoid in a demo
These get an honest but plain "not in the plant records" answer (still no AI-style disclaimers), so they do not showcase well:
- Schedules: "When is the next maintenance for the press?"
- Appearance or trivia: "What colour is the robot?"
- Anything about days other than the current shift ("How many cars yesterday?" answers with the current shift and says so).
- Machines outside the simulated line (the knowledge base holds 119 machines but the engine simulates M01 to M10).
