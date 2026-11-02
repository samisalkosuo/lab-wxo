"""Mock Maximo INVENTORY records and asset spare-part lists (ITEMNUM, STORELOC, CURBAL)."""

ITEMS = {
    "BRG-6310": {"itemnum": "BRG-6310", "description": "Ball bearing 6310, drive end", "qty_on_hand": 4,
                 "storeroom": "MAIN", "bin": "A-12", "eta": ""},
    "CPL-INS-14": {"itemnum": "CPL-INS-14", "description": "Flexible coupling insert, size 14", "qty_on_hand": 0,
                   "storeroom": "MAIN", "bin": "A-14", "eta": "2026-11-09"},
    "SEAL-KIT-P2": {"itemnum": "SEAL-KIT-P2", "description": "Mechanical seal kit, P-200 series", "qty_on_hand": 2,
                    "storeroom": "MAIN", "bin": "B-03", "eta": ""},
    "CONTACTOR-40A": {"itemnum": "CONTACTOR-40A", "description": "Contactor 40 A, 3-pole", "qty_on_hand": 2,
                      "storeroom": "ELEC", "bin": "E-07", "eta": ""},
    "BELT-B120": {"itemnum": "BELT-B120", "description": "V-belt B120", "qty_on_hand": 6,
                  "storeroom": "MAIN", "bin": "C-02", "eta": ""},
    "GASKET-V12": {"itemnum": "GASKET-V12", "description": "Valve gasket set V-12", "qty_on_hand": 1,
                   "storeroom": "MAIN", "bin": "D-05", "eta": ""},
}

# Which items are used on which asset (Maximo ASSETSPAREPART).
ASSET_PARTS = {
    "PUMP-L2-03": ["BRG-6310", "CPL-INS-14", "SEAL-KIT-P2"],
    "PUMP-L2-04": ["BRG-6310", "CPL-INS-14", "SEAL-KIT-P2"],
    "MTR-CV-04": ["CONTACTOR-40A", "BELT-B120"],
    "TNK-12": ["GASKET-V12"],
}
