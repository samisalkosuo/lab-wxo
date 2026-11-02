"""Mock Maximo PM (preventive maintenance) schedules."""

PM_SCHEDULES = [
    {"pmnum": "PM-P203-Q", "assetnum": "PUMP-L2-03", "description": "Quarterly lubrication and inspection",
     "frequency_days": 90, "last_done": "2026-10-05", "next_due": "2027-01-03"},
    {"pmnum": "PM-P204-Q", "assetnum": "PUMP-L2-04", "description": "Quarterly lubrication and inspection",
     "frequency_days": 90, "last_done": "2026-09-20", "next_due": "2026-12-19"},
    {"pmnum": "PM-CV04-M", "assetnum": "MTR-CV-04", "description": "Monthly motor and contactor inspection",
     "frequency_days": 30, "last_done": "2026-08-26", "next_due": "2026-09-25"},
    {"pmnum": "PM-CMP01-S", "assetnum": "CMP-01", "description": "Six-monthly service",
     "frequency_days": 180, "last_done": "2026-07-15", "next_due": "2027-01-11"},
    {"pmnum": "PM-TNK12-A", "assetnum": "TNK-12", "description": "Annual external inspection",
     "frequency_days": 365, "last_done": "2025-11-20", "next_due": "2026-11-20"},
    {"pmnum": "PM-PNL201-Y", "assetnum": "PNL-L2-01", "description": "Annual thermographic inspection",
     "frequency_days": 365, "last_done": "2026-03-12", "next_due": "2027-03-12"},
    {"pmnum": "PM-BLR01-Q", "assetnum": "BLR-01", "description": "Quarterly seal check",
     "frequency_days": 90, "last_done": "2026-08-05", "next_due": "2026-11-03"},
]


def by_asset(assetnum: str):
    return [p for p in PM_SCHEDULES if p["assetnum"] == assetnum]
