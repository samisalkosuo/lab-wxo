"""Fictional employees, cost centers and budgets for the Travel Request scenario.

Everything here is invented for the demo. The state travel rules (rates) are in rates.py;
the agency approval rules are in policy.py.
"""

MOCK_TODAY = "2026-03-02"  # fixed "current date" so runs are deterministic

EMPLOYEES = {
    "E-1001": {
        "name": "Aino Virtanen",
        "grade": "specialist",
        "manager": "Mika Laine",
        "cost_center": "CC-100",
        "home_office": "Helsinki",
    },
    "E-1002": {
        "name": "Jukka Korhonen",
        "grade": "senior specialist",
        "manager": "Mika Laine",
        "cost_center": "CC-100",
        "home_office": "Helsinki",
    },
    "E-1003": {
        "name": "Sofia Lindholm",
        "grade": "principal specialist",
        "manager": "Katri Heikkinen",
        "cost_center": "CC-300",
        "home_office": "Tampere",
    },
    "E-1004": {
        "name": "Mikko Nieminen",
        "grade": "specialist",
        "manager": "Katri Heikkinen",
        "cost_center": "CC-200",
        "home_office": "Oulu",
    },
}

# Remaining travel budget for 2026 in EUR (fictional).
BUDGETS = {
    "CC-100": {"unit": "Development Unit", "remaining_eur": 8000.0, "director": "Pekka Salonen"},
    "CC-200": {"unit": "Customer Service", "remaining_eur": 700.0, "director": "Pekka Salonen"},
    "CC-300": {"unit": "Information Management", "remaining_eur": 5000.0, "director": "Leena Rantanen"},
}


def find_employee(key: str):
    """Return (employee_id, record) by id (E-1001) or by name (case-insensitive), or (None, None)."""
    k = (key or "").strip()
    if not k:
        return None, None
    if k.upper() in EMPLOYEES:
        return k.upper(), EMPLOYEES[k.upper()]
    low = k.lower()
    for eid, rec in EMPLOYEES.items():
        if rec["name"].lower() == low:
            return eid, rec
    return None, None


def employee_ids():
    return sorted(EMPLOYEES)
