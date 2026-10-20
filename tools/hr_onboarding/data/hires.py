"""Mock new-hire records for the HR Onboarding scenario.

All people are fictional. Dates are explicit ISO dates; nothing depends on today's date.
A value of None means the field is missing from the record and must be asked for.
"""

from __future__ import annotations
from typing import Optional

EQUIPMENT_CHOICES = ["standard_laptop", "developer_laptop", "no_equipment"]

HIRES: dict[str, dict] = {
    # HR-001: standard employee, one missing field (equipment choice).
    "H-1001": {
        "hire_id": "H-1001",
        "name": "Alex Kim",
        "role": "software_engineer",
        "department": "engineering",
        "employment_type": "employee",
        "location": "Helsinki",
        "start_date": "2025-06-09",
        "end_date": None,
        "manager": "Maria Lindholm",
        "equipment_choice": None,
    },
    # HR-002: contractor, restricted systems, end date present.
    "H-1002": {
        "hire_id": "H-1002",
        "name": "Jordan Lee",
        "role": "contractor",
        "department": "engineering",
        "employment_type": "contractor",
        "location": "Tampere",
        "start_date": "2025-06-09",
        "end_date": "2025-09-05",
        "manager": "Maria Lindholm",
        "equipment_choice": "standard_laptop",
    },
    # HR-003: Finance analyst, department needs a compliance sign-off.
    "H-1003": {
        "hire_id": "H-1003",
        "name": "Sarah Chen",
        "role": "finance_analyst",
        "department": "finance",
        "employment_type": "employee",
        "location": "Helsinki",
        "start_date": "2025-06-16",
        "end_date": None,
        "manager": "Tomas Berg",
        "equipment_choice": "standard_laptop",
    },
}

# Per-system provisioning status. Systems not listed are "not_requested".
PROVISIONING: dict[str, dict[str, str]] = {
    "H-1001": {},
    "H-1002": {},
    "H-1003": {"vpn": "pending"},
}

LIST_CAP = 10


def get_hire(hire_id: str) -> Optional[dict]:
    return HIRES.get((hire_id or "").strip().upper())


def hire_ids() -> list[str]:
    return list(HIRES.keys())


def find_hires(query: str) -> list[dict]:
    """Match by hire id, or by name (every word of the query must appear in the name)."""
    q = (query or "").strip()
    if not q:
        return []
    by_id = get_hire(q)
    if by_id:
        return [by_id]
    words = q.lower().split()
    return [h for h in HIRES.values() if all(w in h["name"].lower() for w in words)]


def missing_fields(hire: dict) -> list[str]:
    """Fields that must be present before a provisioning request can be filed."""
    required = ["location", "start_date", "manager", "equipment_choice"]
    if hire["employment_type"] == "contractor":
        required.append("end_date")
    return [f for f in required if not hire.get(f)]


def list_by_start_date(start_from: str, start_to: str) -> list[dict]:
    """Hires whose start date lies in [start_from, start_to] (ISO strings compare correctly)."""
    rows = [h for h in HIRES.values() if start_from <= h["start_date"] <= start_to]
    return sorted(rows, key=lambda h: (h["start_date"], h["hire_id"]))


def get_provisioning(hire_id: str) -> dict[str, str]:
    return PROVISIONING.get((hire_id or "").strip().upper(), {})
