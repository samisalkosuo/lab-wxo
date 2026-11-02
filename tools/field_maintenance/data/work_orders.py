"""Mock Maximo WORKORDER records (WONUM, WORKTYPE, STATUS, FAILURECODE, ...)."""

OPEN_STATUSES = ("WAPPR", "APPR", "WMATL", "INPRG")

WORK_ORDERS = [
    # --- PUMP-L2-03: repeat bearing failure (planted root-cause pattern) ---
    {
        "wonum": "WO-10234", "assetnum": "PUMP-L2-03", "worktype": "CM", "status": "CLOSE",
        "description": "High vibration, replace drive-end bearing",
        "failurecode": "BRG-WEAR", "reportdate": "2026-05-10", "actfinish": "2026-05-14",
        "notes": "Drive-end bearing replaced. Alignment not recorded.",
    },
    {
        "wonum": "WO-10871", "assetnum": "PUMP-L2-03", "worktype": "CM", "status": "CLOSE",
        "description": "Bearing noise and heat, replace drive-end bearing again",
        "failurecode": "BRG-WEAR", "reportdate": "2026-08-18", "actfinish": "2026-08-21",
        "notes": "Drive-end bearing replaced a second time. Coupling alignment not checked.",
    },
    {
        "wonum": "WO-9411", "assetnum": "PUMP-L2-03", "worktype": "PM", "status": "CLOSE",
        "description": "Quarterly lubrication and inspection",
        "failurecode": "", "reportdate": "2025-09-02", "actfinish": "2025-09-02",
        "notes": "Routine PM, no findings.",
    },
    # --- PUMP-L2-04 (standby): old unrelated seal leak (red herring) ---
    {
        "wonum": "WO-9980", "assetnum": "PUMP-L2-04", "worktype": "CM", "status": "CLOSE",
        "description": "Mechanical seal leak, replace seal",
        "failurecode": "SEAL-LEAK", "reportdate": "2026-01-08", "actfinish": "2026-01-10",
        "notes": "Seal replaced. Pump returned to standby duty.",
    },
    # --- MTR-CV-04: open work order already exists (no duplicate) ---
    {
        "wonum": "WO-11002", "assetnum": "MTR-CV-04", "worktype": "CM", "status": "INPRG",
        "description": "Conveyor 4 motor trips on overload",
        "failurecode": "OVERLOAD", "reportdate": "2026-10-28", "actfinish": "",
        "notes": "Planner assigned. Contactor suspected. Waiting for follow-up findings.",
    },
    {
        "wonum": "WO-10120", "assetnum": "MTR-CV-04", "worktype": "CM", "status": "CLOSE",
        "description": "Replace worn drive belt",
        "failurecode": "BELT-WEAR", "reportdate": "2026-06-02", "actfinish": "2026-06-03",
        "notes": "Belt replaced.",
    },
    # --- Other assets ---
    {
        "wonum": "WO-10555", "assetnum": "CMP-01", "worktype": "PM", "status": "CLOSE",
        "description": "Oil and filter change",
        "failurecode": "", "reportdate": "2026-07-15", "actfinish": "2026-07-15",
        "notes": "Routine PM.",
    },
    {
        "wonum": "WO-9755", "assetnum": "TNK-12", "worktype": "PM", "status": "CLOSE",
        "description": "Annual external inspection",
        "failurecode": "", "reportdate": "2025-11-20", "actfinish": "2025-11-20",
        "notes": "External inspection only. Internal inspection not due.",
    },
    {
        "wonum": "WO-10790", "assetnum": "BLR-01", "worktype": "PM", "status": "CLOSE",
        "description": "Feedwater pump seal check",
        "failurecode": "", "reportdate": "2026-08-05", "actfinish": "2026-08-05",
        "notes": "No findings.",
    },
]


def by_asset(assetnum: str):
    return [w for w in WORK_ORDERS if w["assetnum"] == assetnum]


def get_work_order(wonum: str):
    for w in WORK_ORDERS:
        if w["wonum"] == wonum:
            return w
    return None
