"""Mock condition-monitoring readings (static snapshot plus last-24h trend, 4 h steps).

Maximo stores meter readings (ASSETMETER / MEASUREMENT); this is a deterministic stand-in.
"""

METERS = {
    "PUMP-L2-03": {
        "vibration_mm_s": {"unit": "mm/s", "warn": 4.5, "alarm": 7.1, "latest": 8.2,
                           "trend_24h": [3.1, 3.4, 4.9, 6.2, 7.5, 8.2]},
        "bearing_temp_c": {"unit": "C", "warn": 75, "alarm": 90, "latest": 94,
                           "trend_24h": [68, 71, 79, 85, 91, 94]},
        "motor_current_a": {"unit": "A", "warn": 46, "alarm": 52, "latest": 41,
                            "trend_24h": [40, 41, 41, 41, 41, 41]},
    },
    "PUMP-L2-04": {
        "vibration_mm_s": {"unit": "mm/s", "warn": 4.5, "alarm": 7.1, "latest": 1.2,
                           "trend_24h": [1.2, 1.2, 1.1, 1.2, 1.2, 1.2]},
        "bearing_temp_c": {"unit": "C", "warn": 75, "alarm": 90, "latest": 38,
                           "trend_24h": [38, 38, 38, 38, 38, 38]},
    },
    "MTR-CV-04": {
        "motor_current_a": {"unit": "A", "warn": 33, "alarm": 36, "latest": 37,
                            "trend_24h": [29, 30, 34, 36, 37, 37]},
        "winding_temp_c": {"unit": "C", "warn": 110, "alarm": 130, "latest": 82,
                           "trend_24h": [78, 79, 81, 82, 82, 82]},
        "vibration_mm_s": {"unit": "mm/s", "warn": 4.5, "alarm": 7.1, "latest": 2.0,
                           "trend_24h": [2.0, 2.0, 2.1, 2.0, 2.0, 2.0]},
    },
    "CMP-01": {
        "discharge_temp_c": {"unit": "C", "warn": 105, "alarm": 115, "latest": 88,
                             "trend_24h": [87, 88, 88, 89, 88, 88]},
    },
    "TNK-12": {
        "level_pct": {"unit": "%", "warn": 95, "alarm": 98, "latest": 64,
                      "trend_24h": [66, 66, 65, 65, 64, 64]},
    },
    "PNL-L2-01": {
        "cabinet_temp_c": {"unit": "C", "warn": 55, "alarm": 70, "latest": 41,
                           "trend_24h": [40, 41, 41, 42, 41, 41]},
    },
    "BLR-01": {
        "vibration_mm_s": {"unit": "mm/s", "warn": 4.5, "alarm": 7.1, "latest": 2.4,
                           "trend_24h": [2.3, 2.4, 2.4, 2.4, 2.4, 2.4]},
        "bearing_temp_c": {"unit": "C", "warn": 75, "alarm": 90, "latest": 61,
                           "trend_24h": [60, 61, 61, 61, 61, 61]},
    },
    "BLR-02": {
        "vibration_mm_s": {"unit": "mm/s", "warn": 4.5, "alarm": 7.1, "latest": 3.0,
                           "trend_24h": [3.0, 3.0, 2.9, 3.0, 3.0, 3.0]},
    },
    "BLR-03": {
        "cabinet_temp_c": {"unit": "C", "warn": 55, "alarm": 70, "latest": 43,
                           "trend_24h": [42, 43, 43, 43, 43, 43]},
    },
}
