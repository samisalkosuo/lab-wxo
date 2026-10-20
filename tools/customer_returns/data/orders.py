"""Mock order data for the Customer Returns scenario.

Every order is static. Order IDs are ORD-XXXX.
customer_id links to the customer who placed the order.
purchase_date drives the 30-day no-reason return window.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

# ---------------------------------------------------------------------------
# Static order catalogue
# ---------------------------------------------------------------------------
_ORDERS: dict[str, dict] = {
    "ORD-1001": {
        "order_id": "ORD-1001",
        "customer_id": "CUST-101",
        "customer_name": "Alice Mäkinen",
        "product_sku": "SKU-BLND-500",
        "product_name": "ProBlend 500 Blender",
        "quantity": 1,
        "unit_price_eur": 89.99,
        "purchase_date": "2025-05-20",   # within 30-day window from reference date 2025-06-03
        "purchase_channel": "online",
        "status": "delivered",
        "notes": "Customer reports product broke after 3 uses.",
    },
    "ORD-1002": {
        "order_id": "ORD-1002",
        "customer_id": "CUST-102",
        "customer_name": "Ben Virtanen",
        "product_sku": "SKU-HDPH-200",
        "product_name": "SoundWave 200 Headphones",
        "quantity": 1,
        "unit_price_eur": 129.00,
        "purchase_date": "2025-04-18",   # 46 days before 2025-06-03 — outside 30-day window
        "purchase_channel": "online",
        "status": "delivered",
        "notes": "Customer says they no longer want it.",
    },
    "ORD-1003": {
        "order_id": "ORD-1003",
        "customer_id": "CUST-103",
        "customer_name": "Carol Lehto",
        "product_sku": "SKU-KTCH-780",
        "product_name": "ChefMate 780 Kitchen Scale",
        "quantity": 1,
        "unit_price_eur": 49.50,
        "purchase_date": "2025-05-10",
        "purchase_channel": "gift",       # gift purchase — gift-return policy applies
        "status": "delivered",
        "notes": "Received as a gift. Customer does not have order confirmation.",
    },
    "ORD-1004": {
        "order_id": "ORD-1004",
        "customer_id": "CUST-104",
        "customer_name": "David Korhonen",
        "product_sku": "SKU-BLND-500",   # same SKU as ORD-1001 — red herring: different customer
        "product_name": "ProBlend 500 Blender",
        "quantity": 1,
        "unit_price_eur": 89.99,
        "purchase_date": "2025-05-28",
        "purchase_channel": "in_store",
        "status": "delivered",
        "notes": "Customer reports a double charge on their statement.",
    },
    # Red-herring warranty order: same SKU as ORD-1001, different customer
    "ORD-1005": {
        "order_id": "ORD-1005",
        "customer_id": "CUST-101",       # Alice — used to plant red-herring warranty
        "customer_name": "Alice Mäkinen",
        "product_sku": "SKU-BLND-PRO",   # different SKU — warranty not applicable to ORD-1001
        "product_name": "ProBlend PRO 1000 Blender",
        "quantity": 1,
        "unit_price_eur": 199.00,
        "purchase_date": "2024-11-01",
        "purchase_channel": "online",
        "status": "delivered",
        "notes": "Older purchase. Warranty expired.",
    },
}

# ---------------------------------------------------------------------------
# Lookup functions
# ---------------------------------------------------------------------------

def get_order(order_id: str) -> Optional[dict]:
    """Return the order dict for the given id, or None."""
    return _ORDERS.get(order_id.strip().upper())


def get_order_ids() -> list[str]:
    return list(_ORDERS.keys())


def get_orders_by_customer(customer_id: str) -> list[dict]:
    cid = customer_id.strip().upper()
    return [o for o in _ORDERS.values() if o["customer_id"] == cid]


def get_order_age_days(order_id: str, reference_date: str = "2025-06-03") -> Optional[int]:
    """Return the number of days since purchase, or None if order not found."""
    order = get_order(order_id)
    if not order:
        return None
    purchased = date.fromisoformat(order["purchase_date"])
    ref = date.fromisoformat(reference_date)
    return (ref - purchased).days


def list_all_orders() -> list[dict]:
    """Return a lightweight summary list of all orders (id, product, date, status)."""
    return [
        {
            "order_id": o["order_id"],
            "product_name": o["product_name"],
            "purchase_date": o["purchase_date"],
            "status": o["status"],
            "purchase_channel": o["purchase_channel"],
        }
        for o in _ORDERS.values()
    ]
