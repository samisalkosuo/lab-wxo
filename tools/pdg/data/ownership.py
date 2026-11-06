"""Mock CODEOWNERS and committer data per pipeline.

Case D (de-payroll-feed): the only committer and CODEOWNERS entry has left the
company, so there is no active owner and the PR needs the fallback reviewer.
"""

from typing import Any, Dict, Optional

FALLBACK_REVIEWERS: Dict[str, str] = {
    "FI": "@fi-platform-lead",
    "SE": "@se-platform-lead",
    "DE": "@de-platform-lead",
}

OWNERSHIP: Dict[str, Dict[str, Any]] = {
    "fi-customer-ingest": {
        "codeowners": ["@aino-virtanen"],
        "committers": [
            {"handle": "@aino-virtanen", "last_commit": "2025-04-28", "active": True},
            {"handle": "@mikko-laine", "last_commit": "2025-03-02", "active": True},
        ],
    },
    "fi-claims-export": {
        "codeowners": ["@mikko-laine"],
        "committers": [
            {"handle": "@mikko-laine", "last_commit": "2025-05-05", "active": True},
            {"handle": "@aino-virtanen", "last_commit": "2025-02-17", "active": True},
        ],
    },
    "se-invoice-batch": {
        "codeowners": ["@elin-berg"],
        "committers": [
            {"handle": "@elin-berg", "last_commit": "2025-05-02", "active": True},
            {"handle": "@oskar-lund", "last_commit": "2025-04-11", "active": True},
        ],
    },
    "se-tax-report": {
        "codeowners": ["@oskar-lund"],
        "committers": [
            {"handle": "@oskar-lund", "last_commit": "2025-05-08", "active": True},
            {"handle": "@elin-berg", "last_commit": "2025-04-22", "active": True},
        ],
    },
    "de-payroll-feed": {
        "codeowners": ["@jonas-keller"],
        "committers": [
            {"handle": "@jonas-keller", "last_commit": "2024-12-03", "active": False},
        ],
    },
    "de-sales-rollup": {
        "codeowners": ["@lena-hoffmann"],
        "committers": [
            {"handle": "@lena-hoffmann", "last_commit": "2025-05-09", "active": True},
            {"handle": "@felix-braun", "last_commit": "2025-04-30", "active": True},
        ],
    },
}


def get_ownership(pipeline_id: str) -> Optional[Dict[str, Any]]:
    return OWNERSHIP.get(pipeline_id)


def active_codeowners(pipeline_id: str) -> list:
    """CODEOWNERS entries whose committer record is marked active."""
    data = OWNERSHIP.get(pipeline_id)
    if not data:
        return []
    active = {c["handle"] for c in data["committers"] if c["active"]}
    return [o for o in data["codeowners"] if o in active]
