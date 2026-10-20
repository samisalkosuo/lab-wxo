"""Mock department configuration for the HR Onboarding scenario.

Departments, not roles, decide whether a compliance sign-off is needed (HR-POL-03).
"""

from __future__ import annotations
from typing import Optional

DEPARTMENTS: dict[str, dict] = {
    "engineering": {
        "name": "Engineering",
        "compliance_signoff_required": False,
        "approval_flow": "hr_request_provisioning",
        "approvers": ["HR Manager"],
        "policy_refs": ["HR-POL-01"],
    },
    "finance": {
        "name": "Finance",
        "compliance_signoff_required": True,
        "approval_flow": "hr_request_compliance_provisioning",
        "approvers": ["HR Manager", "Compliance Reviewer"],
        "policy_refs": ["HR-POL-03"],
    },
    "people": {
        "name": "People",
        "compliance_signoff_required": False,
        "approval_flow": "hr_request_provisioning",
        "approvers": ["HR Manager"],
        "policy_refs": ["HR-POL-01"],
    },
}


def normalize_department(department: str) -> str:
    return (department or "").strip().lower().replace("-", "_").replace(" ", "_")


def get_department(department: str) -> Optional[dict]:
    return DEPARTMENTS.get(normalize_department(department))


def department_ids() -> list[str]:
    return list(DEPARTMENTS.keys())
