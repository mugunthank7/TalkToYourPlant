"""Machines, employees, shift rosters, assignments, escalation matrix, on-call rota, vendor contacts."""
import datetime as dt
import random
import zlib
from collections import Counter, defaultdict

from .catalog import AREAS, FAMILIES, PLANT, TRADES

AS_OF = dt.date(2026, 10, 10)
SOP_DATE = dt.date(2024, 3, 4)          # start of production

FIRST_NAMES = """James Maria Robert Priya Michael Linda David Aisha William Elena Richard Sofia Joseph Mei Thomas Carlos
Christopher Fatima Daniel Ananya Matthew Olivia Anthony Hiroshi Mark Grace Steven Jamal Paul Rosa Andrew Dmitri Joshua Leila
Kenneth Yuki Kevin Amara Brian Camila Edward Tariq George Ingrid Ronald Nia Timothy Mateo Jason Hana Jeffrey Zoe Ryan Samuel
Jacob Lucia Gary Vikram Nicholas Chloe Eric Imani Jonathan Raj Stephen Bianca Larry Omar Justin Keiko Scott Naomi Brandon
Alicia Benjamin Deepak Samantha Frank Luis Gregory Tanya Raymond Wei Patrick Marcus Jack Esperanza Dennis Kwame Jerry Sara
Tyler Latoya Aaron Jorge Henry Nadia Douglas Ravi Adam Beatriz Peter Ahmed Nathan Jin Zachary Monica Walter Abena Kyle Diego
Harold Anita Carl Terrence Arthur Lena Gerald Santiago Roger Priyanka Keith Hector Jeremy Mina Lawrence Dwayne Sean Rachel""".split()

LAST_NAMES = """Johnson Garcia Patel Nguyen Williams Martinez Smith Kim Brown Hernandez Davis Lopez Miller Gonzalez Wilson
Anderson Thomas Taylor Moore Jackson Martin Lee Perez Thompson White Harris Sanchez Clark Ramirez Lewis Robinson Walker
Young Allen King Wright Scott Torres Hill Flores Green Adams Nelson Baker Hall Rivera Campbell Mitchell Carter Roberts
Gomez Phillips Evans Turner Diaz Parker Cruz Edwards Collins Reyes Stewart Morris Morales Murphy Cook Rogers Gutierrez
Ortiz Morgan Cooper Peterson Bailey Reed Kelly Howard Ramos Cox Ward Richardson Watson Brooks Chavez Wood James Bennett
Gray Mendoza Ruiz Hughes Price Alvarez Castillo Sanders Patterson Fischer Jimenez Powell Long Foster Singh Chen Okafor
Haddad Kowalski Nakamura Ivanov Tran Banerjee Mensah Lindqvist Rossi Kaur Sato Alvarado Mukherjee Duarte Novak Holm
Schmidt Vasquez Boyd Warren Fuller Dunn Ford Hicks Barnes Silva Ibrahim Reddy Bhatt Joshi Shah Das""".split()

ROLES = {
    "PLM": "Plant Manager", "OPD": "Operations Director", "MTM": "Maintenance Manager", "ARM": "Area Manager",
    "PSV": "Production Supervisor", "MSV": "Maintenance Supervisor", "LDH": "Line Lead", "OPR": "Machine Operator",
    "TEC": "Maintenance Technician", "REL": "Reliability Engineer", "CTE": "Controls Engineer",
    "PRE": "Process Engineer", "QAI": "Quality Inspector", "QAE": "Quality Engineer", "EHS": "EHS Officer",
    "PLN": "Maintenance Planner", "STK": "Storekeeper", "HVE": "HV Safety Engineer",
}

CERTS = {
    "LOTO": "Authorized LOTO (OSHA 1910.147)",
    "HV": "NFPA 70E qualified person (HV)",
    "HVB": "EV high-voltage battery safe-work (non-electrical)",
    "FANUC": "FANUC certified robot maintenance",
    "KUKA": "KUKA robot maintenance (KRC4/KRC5)",
    "ABB": "ABB robot service",
    "HYD": "Fluid power specialist (CFPS-equivalent)",
    "LASER": "Laser safety officer (Class 4)",
    "CRANE": "Overhead crane operator/inspector",
    "FORK": "Powered industrial truck",
    "CS": "Confined space entry",
    "FIRE": "Fire watch / hot work",
    "TORQ": "Torque tool calibration",
    "ATEX": "Ex-zone (paint) competent person",
}

ZONES = {
    "Z1": ["CAS", "STP"], "Z2": ["BIW", "PNT"], "Z3": ["BAT", "DRV"], "Z4": ["GA", "EOL", "LOG", "UTL"],
}
AREA_TO_ZONE = {a: z for z, areas in ZONES.items() for a in areas}

# layout origins (metres) for the 3-D plant model
AREA_ORIGIN = {"CAS": (0, 0), "STP": (80, 0), "LOG": (150, 0), "UTL": (230, 0),
               "BIW": (0, 60), "PNT": (110, 60), "BAT": (0, 130), "DRV": (80, 130),
               "GA": (150, 130), "EOL": (240, 130)}


def _hex(rng, n):
    return "".join(rng.choice("0123456789ABCDEF") for _ in range(n))


def dominant_trade(fam):
    c = Counter()
    for f in fam["faults"]:
        c[f["trade"]] += f["w"]
    return c.most_common(1)[0][0] if c else "MECH"


def build_machines(rng):
    machines = []
    area_counter = defaultdict(int)
    for fam in FAMILIES:
        for n in range(1, fam["count"] + 1):
            area = fam["area"]
            mid = f"{area}-{fam['key']}-{n:02d}"
            idx = area_counter[area]
            area_counter[area] += 1
            ox, oy = AREA_ORIGIN[area]
            x = ox + (idx % 6) * 12.0
            y = oy + (idx // 6) * 14.0
            install = SOP_DATE - dt.timedelta(days=rng.randint(30, 300))
            if fam["key"] in ("PR", "WK", "WF", "WA") and rng.random() < 0.15:
                install = dt.date(2025, rng.randint(1, 6), rng.randint(1, 28))  # later capacity adds
            days = (AS_OF - max(install, SOP_DATE)).days
            if area == "UTL":
                weekly_hours = 150
            elif area == "LOG":
                weekly_hours = 110
            else:
                weekly_hours = rng.choice([92, 96, 100, 104])
            # slightly different utilisation per machine
            hours = int(days * weekly_hours / 7.0 * rng.uniform(0.9, 1.0))
            machines.append(dict(
                machine_id=mid, family=fam["key"], area=area, area_name=AREAS[area]["name"], bay=AREAS[area]["bay"],
                zone=AREA_TO_ZONE[area], name=f"{fam['name']} {n}", vendor=fam["vendor"], model=fam["model"],
                serial=f"{fam['vendor'][:3].upper()}-{rng.randint(2022, 2025)}-{rng.randint(10000, 99999)}",
                criticality=fam["criticality"], install_date=install.isoformat(),
                commissioned_date=max(install + dt.timedelta(days=rng.randint(20, 80)), SOP_DATE - dt.timedelta(days=20)).isoformat(),
                runtime_hours=hours, weekly_hours=weekly_hours, dominant_trade=dominant_trade(fam),
                asset_value_usd=int(fam["price"] * rng.uniform(0.95, 1.08)),
                avg_cycle_s=fam["avg_cycle_s"], description=fam["desc"],
                x_m=round(x, 1), y_m=round(y, 1), z_m=0.0, rotation_deg=rng.choice([0, 0, 0, 90, 180]),
                line=f"{area}-L{(idx // 6) + 1}",
            ))
    return machines


# --------------------------------------------------------------------------------------
# Employees
# --------------------------------------------------------------------------------------

class Namer:
    def __init__(self, rng):
        self.rng = rng
        self.used = set()

    def name(self):
        for _ in range(500):
            n = f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(LAST_NAMES)}"
            if n not in self.used:
                self.used.add(n)
                return n
        raise RuntimeError("name pool exhausted")


def build_employees(rng, machines):
    namer = Namer(rng)
    emps = []
    mobile_pool = [(ac, n) for ac in (512, 737, 830, 979) for n in range(100, 200)]  # 555-01xx = fictional range
    rng.shuffle(mobile_pool)
    ext_counter = [4100]

    def add(role, area=None, zone=None, shift="D", trade=None, level=None, certs=None, mobile=False, title=None,
            hire_min=2023, hire_max=2026):
        eid = f"BAP-E{len(emps) + 1:04d}"
        nm = namer.name()
        hire = dt.date(rng.randint(hire_min, hire_max), rng.randint(1, 12), rng.randint(1, 28))
        if hire > AS_OF:
            hire = AS_OF - dt.timedelta(days=rng.randint(30, 400))
        ext_counter[0] += 1
        first, last = nm.split()
        e = dict(employee_id=eid, name=nm, role_code=role, role=title or ROLES[role], area=area, zone=zone,
                 shift=shift, trade=trade, skill_level=level, hire_date=hire.isoformat(),
                 certifications=sorted(set(certs or [])), extension=f"x{ext_counter[0]}",
                 radio=f"{(area or 'PLT')}-{_hex(rng, 2)}",
                 email=f"{first.lower()}.{last.lower()}@voltara-motors.example",
                 mobile=((lambda t: f"{t[0]}-555-0{t[1]:03d}")(mobile_pool.pop()) if mobile and mobile_pool else None),
                 pager_id=f"PG-{_hex(rng, 5)}" if mobile else None)
        emps.append(e)
        return e

    # leadership (day shift)
    add("PLM", shift="D", certs=["FIRE"], mobile=True, hire_min=2023, hire_max=2023)
    add("OPD", shift="D", mobile=True, hire_min=2023, hire_max=2023)
    add("MTM", shift="D", certs=["LOTO", "HV"], mobile=True, hire_min=2023, hire_max=2023)
    add("PLN", shift="D", mobile=True)
    add("PLN", shift="D", mobile=False)
    for _ in range(2):
        add("STK", shift="A")
        add("STK", shift="B")
    for _ in range(3):
        add("EHS", shift="D", certs=["LOTO", "HVB", "CS", "FIRE"], mobile=True)
    add("HVE", shift="D", certs=["LOTO", "HV", "HVB"], mobile=True, title="HV Safety Engineer")

    area_machine_count = Counter(m["area"] for m in machines)

    # area managers + engineers + quality
    for area in AREAS:
        add("ARM", area=area, zone=AREA_TO_ZONE[area], shift="D", certs=["LOTO"], mobile=True)
        for kind in ("REL", "CTE", "PRE"):
            if kind == "REL" or area_machine_count[area] > 4:
                add(kind, area=area, zone=AREA_TO_ZONE[area], shift="D", certs=["LOTO"], mobile=True)
        if area in ("CAS", "BIW", "PNT", "BAT", "DRV", "GA", "EOL", "STP"):
            add("QAE", area=area, zone=AREA_TO_ZONE[area], shift="D", mobile=True)
            for sh in "ABC":
                add("QAI", area=area, zone=AREA_TO_ZONE[area], shift=sh)

    # shift-based people
    for sh in "ABC":
        for area in AREAS:
            add("PSV", area=area, zone=AREA_TO_ZONE[area], shift=sh, certs=["LOTO"], mobile=True)
            add("LDH", area=area, zone=AREA_TO_ZONE[area], shift=sh, certs=["LOTO"])
            n_ops = max(2, int(round(area_machine_count[area] * 0.55)))
            if area in ("UTL", "LOG"):
                n_ops = max(2, n_ops // 2)
            if sh == "C":
                n_ops = max(2, int(n_ops * 0.7))
            for _ in range(n_ops):
                c = ["FORK"] if area in ("STP", "LOG", "GA") and rng.random() < 0.5 else []
                add("OPR", area=area, zone=AREA_TO_ZONE[area], shift=sh, certs=c + (["LOTO"] if rng.random() < 0.4 else []))
        for z in ZONES:
            add("MSV", zone=z, shift=sh, certs=["LOTO", "HV", "FIRE"], mobile=True)

    # maintenance technicians per zone per shift by trade
    zone_trade_plan = {
        "Z1": {"MECH": 3, "ELEC": 2, "HYD": 3, "ROBO": 2, "CTRL": 1, "PROC": 1},
        "Z2": {"MECH": 2, "ELEC": 2, "HYD": 1, "ROBO": 5, "CTRL": 1, "PROC": 2},
        "Z3": {"MECH": 2, "ELEC": 3, "HYD": 1, "ROBO": 3, "CTRL": 1, "PROC": 3},
        "Z4": {"MECH": 3, "ELEC": 3, "HYD": 1, "ROBO": 2, "CTRL": 2, "PROC": 2},
    }
    robot_cert_by_zone = {"Z1": ["KUKA", "FANUC"], "Z2": ["KUKA", "FANUC", "ABB"], "Z3": ["FANUC"], "Z4": ["KUKA"]}
    for sh in "ABC":
        for z, plan in zone_trade_plan.items():
            for trade, n in plan.items():
                nn = n if sh != "C" else max(1, n - 1)
                for i in range(nn):
                    lvl = rng.choices(["L1", "L2", "L3"], weights=[3, 4, 2])[0]
                    certs = ["LOTO"]
                    if trade in ("ELEC", "CTRL") or lvl != "L1":
                        certs.append("HV") if rng.random() < 0.6 else None
                    if trade == "ROBO":
                        certs.append(rng.choice(robot_cert_by_zone[z]))
                        if lvl == "L3":
                            certs.extend(robot_cert_by_zone[z])
                    if trade == "HYD":
                        certs.append("HYD")
                    if trade == "PROC":
                        certs.append("TORQ")
                        if z == "Z2" and rng.random() < 0.3:
                            certs.append("LASER")
                    if z == "Z3":
                        certs.append("HVB")
                    if z == "Z2" and rng.random() < 0.4:
                        certs.append("ATEX")
                    if z == "Z1" and rng.random() < 0.5:
                        certs.append("CRANE")
                    if rng.random() < 0.2:
                        certs.append("FIRE")
                    add("TEC", zone=z, shift=sh, trade=trade, level=lvl, certs=certs,
                        mobile=(lvl == "L3"), title=f"{TRADES[trade]} Technician ({lvl})")
    return emps


# --------------------------------------------------------------------------------------
# Roster
# --------------------------------------------------------------------------------------

def build_roster(rng, emps, start=dt.date(2026, 7, 13), end=dt.date(2026, 10, 24)):
    rows = []
    shift_alias = {"D": "A"}  # day-shift staff are present during crew A hours
    for e in emps:
        sh = e["shift"]
        crew = shift_alias.get(sh, sh)
        d = start
        sat_ot_prob = 0.2
        while d <= end:
            wd = d.weekday()
            status = "off"
            if wd < 5:
                status = "working"
            elif wd == 5 and rng.random() < sat_ot_prob and e["role_code"] in ("OPR", "TEC", "LDH"):
                status = "overtime"
            if status != "off" and d <= AS_OF:
                r = rng.random()
                if r < 0.035:
                    status = "pto"
                elif r < 0.05:
                    status = "sick"
            if d == dt.date(2026, 9, 7):
                status = "holiday" if status == "working" else status
            rows.append(dict(date=d.isoformat(), employee_id=e["employee_id"], shift=crew if sh != "D" else "D",
                             status=status))
            d += dt.timedelta(days=1)
    return rows


# --------------------------------------------------------------------------------------
# Assignments
# --------------------------------------------------------------------------------------

def build_assignments(rng, machines, emps):
    by_key = defaultdict(list)
    for e in emps:
        by_key[(e["role_code"], e.get("zone"), e["shift"], e.get("trade"))].append(e)
        by_key[(e["role_code"], e.get("area"), e["shift"], None)].append(e)
    ops = defaultdict(list)
    for e in emps:
        if e["role_code"] == "OPR":
            ops[(e["area"], e["shift"])].append(e)
    area_machines = defaultdict(list)
    for m in machines:
        area_machines[m["area"]].append(m)

    rows = []
    # operators round-robin over machines of the area, 1-2 operators/machine
    op_assign = defaultdict(list)
    for (area, sh), lst in ops.items():
        ms = area_machines[area]
        for i, m in enumerate(ms):
            op_assign[(m["machine_id"], sh)].append(lst[i % len(lst)])
            if len(lst) > len(ms) and i < len(lst) - len(ms):
                op_assign[(m["machine_id"], sh)].append(lst[(i + len(ms)) % len(lst)])

    def pick(role, zone_or_area, sh, trade=None, idx=0):
        lst = by_key.get((role, zone_or_area, sh, trade), [])
        return lst[idx % len(lst)] if lst else None

    for m in machines:
        mid = m["machine_id"]
        tr = m["dominant_trade"]
        for sh in "ABC":
            for e in op_assign.get((mid, sh), []):
                rows.append(dict(machine_id=mid, shift=sh, role="operator", employee_id=e["employee_id"], trade=None))
            lead = pick("LDH", m["area"], sh)
            if lead:
                rows.append(dict(machine_id=mid, shift=sh, role="line_lead", employee_id=lead["employee_id"], trade=None))
            psv = pick("PSV", m["area"], sh)
            if psv:
                rows.append(dict(machine_id=mid, shift=sh, role="production_supervisor", employee_id=psv["employee_id"], trade=None))
            # primary & backup tech: same trade within zone
            lst = by_key.get(("TEC", m["zone"], sh, tr), [])
            if lst:
                h = zlib.crc32(mid.encode()) % len(lst)
                prim = lst[h]
                back = lst[(h + 1) % len(lst)] if len(lst) > 1 else None
                rows.append(dict(machine_id=mid, shift=sh, role="primary_tech", employee_id=prim["employee_id"], trade=tr))
                if back:
                    rows.append(dict(machine_id=mid, shift=sh, role="backup_tech", employee_id=back["employee_id"], trade=tr))
            # secondary trade coverage (electrical backstop)
            if tr != "ELEC":
                lst2 = by_key.get(("TEC", m["zone"], sh, "ELEC"), [])
                if lst2:
                    rows.append(dict(machine_id=mid, shift=sh, role="electrical_support", employee_id=lst2[zlib.crc32(mid.encode()) % len(lst2)]["employee_id"], trade="ELEC"))
            msv = pick("MSV", m["zone"], sh)
            if msv:
                rows.append(dict(machine_id=mid, shift=sh, role="maintenance_supervisor", employee_id=msv["employee_id"], trade=None))
        # day-shift engineers & managers (all shifts via on-call)
        for role, key in (("area_manager", "ARM"), ("reliability_engineer", "REL"), ("controls_engineer", "CTE"),
                          ("process_engineer", "PRE"), ("quality_engineer", "QAE")):
            e = by_key.get((key, m["area"], "D", None), [])
            if e:
                rows.append(dict(machine_id=mid, shift="ALL", role=role, employee_id=e[0]["employee_id"], trade=None))
    return rows


# --------------------------------------------------------------------------------------
# Vendors, escalation, on-call
# --------------------------------------------------------------------------------------

VENDOR_SLA = {
    "IDRA": dict(hotline="+1-800-555-0111", response_h=2, onsite_h=24, contract="Premium 24/7"),
    "KUKA": dict(hotline="+1-800-555-0112", response_h=2, onsite_h=24, contract="Gold 24/7"),
    "FANUC": dict(hotline="+1-800-555-0113", response_h=1, onsite_h=12, contract="Premier 24/7"),
    "ABB": dict(hotline="+1-800-555-0114", response_h=2, onsite_h=24, contract="Standard 8x5 + emergency"),
    "Schuler": dict(hotline="+1-800-555-0115", response_h=4, onsite_h=36, contract="Standard"),
    "Striko Westofen": dict(hotline="+1-800-555-0116", response_h=4, onsite_h=48, contract="Standard"),
    "Yxlon": dict(hotline="+1-800-555-0117", response_h=8, onsite_h=48, contract="Standard"),
    "DMG MORI": dict(hotline="+1-800-555-0118", response_h=4, onsite_h=24, contract="Gold"),
    "TRUMPF": dict(hotline="+1-800-555-0119", response_h=2, onsite_h=24, contract="Gold 24/7"),
    "Duerr": dict(hotline="+1-800-555-0120", response_h=2, onsite_h=24, contract="Premium 24/7"),
    "ZEISS": dict(hotline="+1-800-555-0121", response_h=8, onsite_h=48, contract="Standard"),
    "Desoutter": dict(hotline="+1-800-555-0122", response_h=8, onsite_h=48, contract="Standard"),
    "Atlas Copco": dict(hotline="+1-800-555-0123", response_h=4, onsite_h=24, contract="Gold"),
    "Nordson": dict(hotline="+1-800-555-0124", response_h=8, onsite_h=48, contract="Standard"),
    "INFICON": dict(hotline="+1-800-555-0125", response_h=8, onsite_h=48, contract="Standard"),
    "Chroma": dict(hotline="+1-800-555-0126", response_h=8, onsite_h=72, contract="Standard"),
    "Aumann": dict(hotline="+1-800-555-0127", response_h=4, onsite_h=48, contract="Gold"),
    "AVL": dict(hotline="+1-800-555-0128", response_h=4, onsite_h=48, contract="Gold"),
    "MAHA": dict(hotline="+1-800-555-0129", response_h=8, onsite_h=48, contract="Standard"),
    "Hunter": dict(hotline="+1-800-555-0130", response_h=8, onsite_h=72, contract="Standard"),
    "Carrier": dict(hotline="+1-800-555-0131", response_h=4, onsite_h=24, contract="Gold"),
    "Siemens": dict(hotline="+1-800-555-0132", response_h=2, onsite_h=12, contract="Premium 24/7"),
    "MiR": dict(hotline="+1-800-555-0133", response_h=8, onsite_h=48, contract="Standard"),
    "Konecranes": dict(hotline="+1-800-555-0134", response_h=4, onsite_h=24, contract="Gold"),
}


def build_vendors(rng):
    out = []
    for v, d in VENDOR_SLA.items():
        nm = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        out.append(dict(vendor=v, field_service_contact=nm, email=f"service.us@{v.lower().replace(' ', '')}.example",
                        **d))
    return out


ESCALATION_TEMPLATE = {
    # criticality -> minutes of line-impacting downtime before each escalation level triggers
    "A": dict(L1_tech=2, L2_backup=8, L3_supervisor=15, L4_engineer=30, L5_vendor=90, L6_plant_mgmt=180),
    "B": dict(L1_tech=5, L2_backup=15, L3_supervisor=30, L4_engineer=60, L5_vendor=180, L6_plant_mgmt=360),
    "C": dict(L1_tech=10, L2_backup=30, L3_supervisor=60, L4_engineer=120, L5_vendor=360, L6_plant_mgmt=720),
}

SAFETY_TRIGGERS = [
    "Any injury or first-aid case: page EHS + production supervisor immediately; call 911 if life-threatening",
    "Any high-voltage (battery/HV bus) fault, arc flash, swelling, smoke or thermal event: evacuate area, page HV Safety Engineer and EHS (Level 6 immediately)",
    "Paint shop explosion-protection (Ex) purge fault: shut down booth, do not restart; page paint area engineer and EHS",
    "Hydraulic oil spill > 5 gallons or any fire: page EHS and emergency response team",
    "Molten metal breakout or die water leak at Giga Press: clear area, page casting area manager and EHS",
]


def build_escalation(machines, emps, assignments):
    by_machine_shift = defaultdict(dict)
    for a in assignments:
        by_machine_shift[(a["machine_id"], a["shift"])].setdefault(a["role"], []).append(a["employee_id"])
    emp_by_id = {e["employee_id"]: e for e in emps}
    out = []
    for m in machines:
        fam = next(f for f in FAMILIES if f["key"] == m["family"])
        sla = VENDOR_SLA[m["vendor"]]
        thr = ESCALATION_TEMPLATE[m["criticality"]]
        chain = {}
        for sh in "ABC":
            d = by_machine_shift.get((m["machine_id"], sh), {})
            chain[sh] = dict(
                L0_operator_action="Press andon, tell Line Lead, note fault code/time",
                L0_line_lead=(d.get("line_lead") or [None])[0],
                L1_primary_tech=(d.get("primary_tech") or [None])[0],
                L2_backup_tech=(d.get("backup_tech") or [None])[0],
                L3_maintenance_supervisor=(d.get("maintenance_supervisor") or [None])[0],
            )
        allr = by_machine_shift.get((m["machine_id"], "ALL"), {})
        out.append(dict(
            machine_id=m["machine_id"], criticality=m["criticality"],
            escalation_minutes=thr,
            on_shift_chain=chain,
            L4_engineers=dict(reliability=(allr.get("reliability_engineer") or [None])[0],
                              controls=(allr.get("controls_engineer") or [None])[0],
                              process=(allr.get("process_engineer") or [None])[0],
                              area_manager=(allr.get("area_manager") or [None])[0]),
            L5_vendor=dict(vendor=m["vendor"], hotline=sla["hotline"], contract=sla["contract"],
                           phone_response_h=sla["response_h"], onsite_h=sla["onsite_h"]),
            L6_plant_mgmt="Maintenance Manager -> Operations Director -> Plant Manager",
            safety_triggers=SAFETY_TRIGGERS,
        ))
    return out


def build_oncall(rng, emps, start=dt.date(2026, 1, 5), weeks=52):
    pools = defaultdict(list)
    for e in emps:
        if e["role_code"] in ("REL", "CTE", "PRE", "HVE", "MTM", "PLM", "OPD", "MSV"):
            pools[e["role_code"]].append(e)
        if e["role_code"] == "TEC" and e["skill_level"] == "L3":
            pools[f"TEC-{e['trade']}"].append(e)
    rows = []
    for w in range(weeks):
        ws = start + dt.timedelta(weeks=w)
        for pool, lst in pools.items():
            if pool in ("PLM", "OPD") and len(lst) == 1:
                continue
            if not lst:
                continue
            prim = lst[w % len(lst)]
            sec = lst[(w + 1) % len(lst)] if len(lst) > 1 else None
            rows.append(dict(week_start=ws.isoformat(), week_end=(ws + dt.timedelta(days=6)).isoformat(),
                             pool=pool, primary=prim["employee_id"], secondary=(sec or {}).get("employee_id")))
    return rows
