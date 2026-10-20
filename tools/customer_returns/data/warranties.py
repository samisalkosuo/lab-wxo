"""Mock warranty data for the Customer Returns scenario.

Warranties are keyed by serial_number and linked to product_sku.
The red herring: Alice has a warranty for SKU-BLND-PRO (ORD-1005),
NOT for SKU-BLND-500 (ORD-1001). The agent must not confuse them.
"""

from __future__ import annotations
from typing import Optional

# Reference date for warranty expiry checks
REFERENCE_DATE = "2025-06-03"

_WARRANTIES: dict[str, dict] = {
    "SN-BLND-500-A101": {
        "serial_number": "SN-BLND-500-A101",
        "product_sku": "SKU-BLND-500",
        "product_name": "ProBlend 500 Blender",
        "order_id": "ORD-1001",
        "customer_id": "CUST-101",
        "warranty_type": "standard",
        "warranty_start": "2025-05-20",
        "warranty_end": "2026-05-20",    # 1-year manufacturer warranty, still valid
        "status": "active",
        "coverage": "Manufacturing defects and mechanical failure. Excludes accidental damage.",
    },
    # Red herring: Alice's older blender (PRO model) — warranty expired
    "SN-BLND-PRO-A101": {
        "serial_number": "SN-BLND-PRO-A101",
        "product_sku": "SKU-BLND-PRO",
        "product_name": "ProBlend PRO 1000 Blender",
        "order_id": "ORD-1005",
        "customer_id": "CUST-101",
        "warranty_type": "standard",
        "warranty_start": "2024-11-01",
        "warranty_end": "2025-11-01",    # still technically valid, but wrong SKU
        "status": "active",
        "coverage": "Manufacturing defects and mechanical failure. Excludes accidental damage.",
    },
    "SN-KTCH-780-C103": {
        "serial_number": "SN-KTCH-780-C103",
        "product_sku": "SKU-KTCH-780",
        "product_name": "ChefMate 780 Kitchen Scale",
        "order_id": "ORD-1003",
        "customer_id": "CUST-103",
        "warranty_type": "standard",
        "warranty_start": "2025-05-10",
        "warranty_end": "2026-05-10",
        "status": "active",
        "coverage": "Manufacturing defects. Excludes wear and tear.",
    },
    "SN-HDPH-200-B102": {
        "serial_number": "SN-HDPH-200-B102",
        "product_sku": "SKU-HDPH-200",
        "product_name": "SoundWave 200 Headphones",
        "order_id": "ORD-1002",
        "customer_id": "CUST-102",
        "warranty_type": "standard",
        "warranty_start": "2025-04-18",
        "warranty_end": "2026-04-18",
        "status": "active",
        "coverage": "Manufacturing defects. Excludes cosmetic damage and user wear.",
    },
}

# ---------------------------------------------------------------------------
# Lookup functions
# ---------------------------------------------------------------------------

def get_warranty_by_serial(serial_number: str) -> Optional[dict]:
    return _WARRANTIES.get(serial_number.strip().upper())


def get_warranties_by_order(order_id: str) -> list[dict]:
    oid = order_id.strip().upper()
    return [w for w in _WARRANTIES.values() if w["order_id"] == oid]


def get_warranties_by_sku(product_sku: str) -> list[dict]:
    sku = product_sku.strip().upper()
    return [w for w in _WARRANTIES.values() if w["product_sku"] == sku]


def get_serial_numbers() -> list[str]:
    return list(_WARRANTIES.keys())


def is_warranty_active(serial_number: str, reference_date: str = REFERENCE_DATE) -> bool:
    """Return True if the warranty exists and has not expired."""
    from datetime import date
    w = get_warranty_by_serial(serial_number)
    if not w or w["status"] != "active":
        return False
    return date.fromisoformat(reference_date) <= date.fromisoformat(w["warranty_end"])
