"""Mock Maximo ASSET records (field names follow Maximo: ASSETNUM, LOCATION, ...).

All data is fictional. `keywords` is demo-only search helper data used by mx_find_asset;
real Maximo would be searched through its own APIs.
"""

# The mock "today" so results are deterministic (ISO date).
TODAY = "2026-11-02"

LOCATIONS = {
    "LINE2": "Production Line 2",
    "PACK": "Packaging Hall",
    "UTIL": "Utilities Hall",
    "YARD": "Tank Yard",
    "BOILER": "Boiler Room",
}

ASSETS = {
    "PUMP-L2-03": {
        "assetnum": "PUMP-L2-03",
        "description": "Cooling water circulation pump P-203",
        "location": "LINE2",
        "operating_status": "OPERATING",
        "criticality": 1,
        "hazard_class": "rotating_equipment",
        "model": "Centrifugal pump, 45 kW motor",
        "keywords": ["pump", "cooling", "line2", "p203", "pump03"],
    },
    "PUMP-L2-04": {
        "assetnum": "PUMP-L2-04",
        "description": "Cooling water circulation pump P-204 (standby)",
        "location": "LINE2",
        "operating_status": "STANDBY",
        "criticality": 1,
        "hazard_class": "rotating_equipment",
        "model": "Centrifugal pump, 45 kW motor",
        "keywords": ["pump", "cooling", "line2", "p204", "pump04"],
    },
    "PNL-L2-01": {
        "assetnum": "PNL-L2-01",
        "description": "Line 2 motor control panel MCC-2",
        "location": "LINE2",
        "operating_status": "OPERATING",
        "criticality": 2,
        "hazard_class": "electrical",
        "model": "Low-voltage MCC, 400 V",
        "keywords": ["panel", "mcc", "line2", "pnl", "electrical"],
    },
    "MTR-CV-04": {
        "assetnum": "MTR-CV-04",
        "description": "Conveyor 4 drive motor",
        "location": "PACK",
        "operating_status": "OPERATING",
        "criticality": 2,
        "hazard_class": "rotating_equipment",
        "model": "Induction motor, 30 kW",
        "keywords": ["conveyor", "conveyor4", "cv04", "motor4", "drivemotor"],
    },
    "CMP-01": {
        "assetnum": "CMP-01",
        "description": "Plant air compressor C-01",
        "location": "UTIL",
        "operating_status": "OPERATING",
        "criticality": 2,
        "hazard_class": "rotating_equipment",
        "model": "Screw compressor, 75 kW",
        "keywords": ["compressor", "aircompressor", "c01", "cmp01"],
    },
    "TNK-12": {
        "assetnum": "TNK-12",
        "description": "Process water storage tank T-12 (with isolation valve V-12)",
        "location": "YARD",
        "operating_status": "OPERATING",
        "criticality": 2,
        "hazard_class": "confined_space",
        "model": "Vertical steel tank, 40 m3",
        "keywords": ["tank", "tank12", "t12", "tnk12", "v12"],
    },
    "BLR-01": {
        "assetnum": "BLR-01",
        "description": "Boiler 1 feedwater pump",
        "location": "BOILER",
        "operating_status": "OPERATING",
        "criticality": 1,
        "hazard_class": "rotating_equipment",
        "model": "Multistage pump, 22 kW",
        "keywords": ["boiler", "feedpump", "feedwater", "bfp"],
    },
    "BLR-02": {
        "assetnum": "BLR-02",
        "description": "Boiler 1 combustion air fan",
        "location": "BOILER",
        "operating_status": "OPERATING",
        "criticality": 1,
        "hazard_class": "rotating_equipment",
        "model": "Centrifugal fan, 15 kW",
        "keywords": ["boiler", "airfan", "combustionair", "burnerfan"],
    },
    "BLR-03": {
        "assetnum": "BLR-03",
        "description": "Boiler 1 burner control panel",
        "location": "BOILER",
        "operating_status": "OPERATING",
        "criticality": 1,
        "hazard_class": "electrical",
        "model": "Burner management panel",
        "keywords": ["boiler", "burnerpanel", "burnercontrol", "controlpanel"],
    },
}


def get_asset(assetnum: str):
    return ASSETS.get(assetnum)


def asset_ids():
    return sorted(ASSETS)
