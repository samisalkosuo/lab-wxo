"""Mock learner (employee) profiles for the HR Tacit Knowledge scenario.

All names are fictional. Dates are explicit ISO dates.
L-201: new hire at the Finland desk (TK-004, TK-005).
L-202: role-changer in HR Operations.
"""

from __future__ import annotations
from typing import Optional

EMPLOYEES: dict[str, dict] = {
    "L-201": {
        "employee_id": "L-201",
        "name": "Emilia Saarinen",
        "role": "HR Coordinator",
        "desk": "Finland",
        "start_date": "2025-04-01",
        "tenure_months": 2,
        "profile": "New hire at the Finland HR desk. Familiar with basic onboarding processes; "
                   "has not dealt with corrections or certificates yet.",
    },
    "L-202": {
        "employee_id": "L-202",
        "name": "Mikael Strand",
        "role": "HR Operations Specialist",
        "desk": "Nordic",
        "start_date": "2023-09-01",
        "tenure_months": 20,
        "profile": "Role-changer from Payroll Support to HR Operations. Familiar with payroll "
                   "processes; learning HR Operations procedures.",
    },
}


def get_employee(employee_id: str) -> Optional[dict]:
    return EMPLOYEES.get((employee_id or "").strip().upper())


def employee_ids() -> list[str]:
    return list(EMPLOYEES.keys())


def find_employee_by_name(query: str) -> list[dict]:
    """Match by employee id or name words."""
    q = (query or "").strip()
    if not q:
        return []
    by_id = get_employee(q)
    if by_id:
        return [by_id]
    words = q.lower().split()
    return [e for e in EMPLOYEES.values() if all(w in e["name"].lower() for w in words)]
