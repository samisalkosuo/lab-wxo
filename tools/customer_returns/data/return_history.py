"""Mock return history for the Customer Returns scenario.

Records past return requests (submitted, approved, denied).
Useful for the agent to check whether a return has already been filed.
"""

from __future__ import annotations
from typing import Optional

_RETURN_HISTORY: dict[str, dict] = {
    # No prior returns for the four demo cases — clean slate so the agent
    # does not find stale decisions that would confuse the demo.
}


def get_return_by_order(order_id: str) -> Optional[dict]:
    """Return the most recent return record for an order, or None."""
    oid = order_id.strip().upper()
    matches = [r for r in _RETURN_HISTORY.values() if r["order_id"] == oid]
    if not matches:
        return None
    return sorted(matches, key=lambda r: r["submitted_at"], reverse=True)[0]


def list_returns_by_customer(customer_id: str) -> list[dict]:
    cid = customer_id.strip().upper()
    return [r for r in _RETURN_HISTORY.values() if r["customer_id"] == cid]


def get_return_ids() -> list[str]:
    return list(_RETURN_HISTORY.keys())
