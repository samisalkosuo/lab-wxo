"""Mock role -> systems matrix for the HR Onboarding scenario.

Six fictional systems and five roles. This matrix is the single source of truth for
what a role may be granted; the policy documents in knowledge/hr-onboarding explain it
and must not contradict it. Policy references (HR-POL-xx) name those documents.
"""

from __future__ import annotations
from typing import Optional

# Stable order used in every tool output.
SYSTEM_ORDER = ["email", "chat", "source_code", "production_access", "finance_ledger", "vpn"]

SYSTEMS: dict[str, str] = {
    "email": "Corporate email mailbox",
    "chat": "Team chat",
    "source_code": "Source code repositories",
    "production_access": "Production environment access",
    "finance_ledger": "Finance ledger",
    "vpn": "VPN",
}

# Access level is always "standard" in onboarding. Admin-level access is never granted
# through onboarding (HR-POL-04).
ROLES: dict[str, dict] = {
    "software_engineer": {
        "title": "Software Engineer",
        "employment_type": "employee",
        "requires_end_date": False,
        "allowed": {
            "email": "Corporate mailbox",
            "chat": "Full account",
            "source_code": "Read and write on team repositories",
            "vpn": "Standard profile",
        },
        "policy_refs": ["HR-POL-01"],
    },
    "site_reliability_engineer": {
        "title": "Site Reliability Engineer",
        "employment_type": "employee",
        "requires_end_date": False,
        "allowed": {
            "email": "Corporate mailbox",
            "chat": "Full account",
            "source_code": "Read and write on team repositories",
            "production_access": "On-call production access",
            "vpn": "Standard profile",
        },
        "policy_refs": ["HR-POL-01"],
    },
    "finance_analyst": {
        "title": "Finance Analyst",
        "employment_type": "employee",
        "requires_end_date": False,
        "allowed": {
            "email": "Corporate mailbox",
            "chat": "Full account",
            "finance_ledger": "Read-only ledger access",
            "vpn": "Standard profile",
        },
        "policy_refs": ["HR-POL-01", "HR-POL-03"],
    },
    "hr_coordinator": {
        "title": "HR Coordinator",
        "employment_type": "employee",
        "requires_end_date": False,
        "allowed": {
            "email": "Corporate mailbox",
            "chat": "Full account",
            "vpn": "Standard profile",
        },
        "policy_refs": ["HR-POL-01"],
    },
    "contractor": {
        "title": "Contractor",
        "employment_type": "contractor",
        "requires_end_date": True,
        "allowed": {
            "chat": "Guest account only",
            "vpn": "Time-limited profile, expires on the contract end date",
        },
        "policy_refs": ["HR-POL-01", "HR-POL-02"],
    },
}


def normalize_role(role: str) -> str:
    return (role or "").strip().lower().replace("-", "_").replace(" ", "_")


def get_role(role: str) -> Optional[dict]:
    return ROLES.get(normalize_role(role))


def role_ids() -> list[str]:
    return list(ROLES.keys())


def normalize_system(system: str) -> str:
    return (system or "").strip().lower().replace("-", "_").replace(" ", "_")
