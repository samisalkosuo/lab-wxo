"""Mock product catalogue — lookup by serial number for gift-return path (CR-003)."""

from __future__ import annotations
from typing import Optional

_PRODUCTS_BY_SERIAL: dict[str, dict] = {
    "SN-KTCH-780-C103": {
        "serial_number": "SN-KTCH-780-C103",
        "product_sku": "SKU-KTCH-780",
        "product_name": "ChefMate 780 Kitchen Scale",
        "order_id": "ORD-1003",
        "purchase_date": "2025-05-10",
        "purchase_channel": "gift",
    },
    "SN-BLND-500-A101": {
        "serial_number": "SN-BLND-500-A101",
        "product_sku": "SKU-BLND-500",
        "product_name": "ProBlend 500 Blender",
        "order_id": "ORD-1001",
        "purchase_date": "2025-05-20",
        "purchase_channel": "online",
    },
    "SN-HDPH-200-B102": {
        "serial_number": "SN-HDPH-200-B102",
        "product_sku": "SKU-HDPH-200",
        "product_name": "SoundWave 200 Headphones",
        "order_id": "ORD-1002",
        "purchase_date": "2025-04-18",
        "purchase_channel": "online",
    },
    "SN-BLND-PRO-A101": {
        "serial_number": "SN-BLND-PRO-A101",
        "product_sku": "SKU-BLND-PRO",
        "product_name": "ProBlend PRO 1000 Blender",
        "order_id": "ORD-1005",
        "purchase_date": "2024-11-01",
        "purchase_channel": "online",
    },
}


def get_product_by_serial(serial_number: str) -> Optional[dict]:
    return _PRODUCTS_BY_SERIAL.get(serial_number.strip().upper())


def get_serial_numbers() -> list[str]:
    return list(_PRODUCTS_BY_SERIAL.keys())
