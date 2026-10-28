"""Mock KB article metadata for the HR Tacit Knowledge scenario.

IDs HR-TK-ART-01 to HR-TK-ART-06. The actual article text lives in
knowledge/hr-tacit-knowledge/articles/. This module exposes the structured
metadata that Python tools use (status, topics, owner, etc.).

Planted conflicts (documented in ground_truth.json):
  ART-01: leave-correction payroll cutoff states 18th  (real: 22nd — matches A-107)
  ART-04: Finland position-change form HR-22 / 10 days (real: e-form PR-1 / 5 days — matches A-105)
  ART-02: superseded by ART-03 (employment certificates)
  ART-05: Sweden position-change look-alike (different country — red herring for TK-002)
"""

from __future__ import annotations

ARTICLES: dict[str, dict] = {
    # ART-01: leave-correction hold procedure (stale cutoff: 18th; real: 22nd)
    "HR-TK-ART-01": {
        "article_id": "HR-TK-ART-01",
        "title": "Correcting a Retroactive Leave Start Date Without Triggering Overpayment Recovery",
        "status": "current",
        "owner_role": "Senior HR Specialist",
        "last_verified": "2024-11-15",
        "applies_to": "All Finland HR Specialists",
        # topics used by find_related_articles — no generic terms.
        # "payroll hold" excluded: it also appears in ART-06 (role-change salary) which would
        # cause a false match when searching A-101 (role-change artifact).
        # ART-01 is specifically about *leave-date* corrections.
        "topics": ["retroactive leave", "leave start date", "overpayment recovery",
                   "leave correction", "payroll cutoff"],
        "stale_fact": "payroll cutoff stated as 18th; real cutoff is 22nd",
    },
    # ART-02: superseded employment certificate process (red herring for TK-004)
    "HR-TK-ART-02": {
        "article_id": "HR-TK-ART-02",
        "title": "Requesting an Employment Certificate (Legacy Process — Superseded)",
        "status": "superseded",
        "owner_role": "HR Operations",
        "last_verified": "2023-06-01",
        "applies_to": "Historical reference only — superseded by HR-TK-ART-03",
        "topics": ["employment certificate", "proof of employment", "HR Operations",
                   "self-service portal"],
        "successor_id": "HR-TK-ART-03",
    },
    # ART-03: current employment certificate process (TK-001 A-102/A-103 near-dup, TK-004 answer)
    "HR-TK-ART-03": {
        "article_id": "HR-TK-ART-03",
        "title": "Requesting an Employment Certificate via Employee Self-Service",
        "status": "current",
        "owner_role": "HR Operations Lead",
        "last_verified": "2025-03-10",
        "applies_to": "All employees in Finland",
        "topics": ["employment certificate", "proof of employment", "employee self-service",
                   "HR Operations", "certificate request"],
    },
    # ART-04: Finland position-change process (stale: HR-22 / 10 days; real: PR-1 / 5 days)
    "HR-TK-ART-04": {
        "article_id": "HR-TK-ART-04",
        "title": "Internal Position Change Request Process — Finland",
        "status": "current",
        "owner_role": "HR Specialist",
        "last_verified": "2024-08-20",
        "applies_to": "Finland HR Coordinators and managers",
        "topics": ["position change", "internal transfer", "HR portal", "Finland",
                   "position-change form"],
        "stale_fact": "references form HR-22 and 10 working days; real: e-form PR-1 and 5 working days",
    },
    # ART-05: Sweden position-change process (different-country look-alike — red herring TK-002)
    "HR-TK-ART-05": {
        "article_id": "HR-TK-ART-05",
        "title": "Internal Position Change Request Process — Sweden",
        "status": "current",
        "owner_role": "HR Specialist",
        "last_verified": "2025-01-08",
        "applies_to": "Sweden HR Coordinators and managers",
        "topics": ["position change", "internal transfer", "HR portal", "Sweden",
                   "position-change form"],
    },
    # NOTE: ART-06 does NOT exist yet — it is the article created BY TK-001 after the curator runs.
    # Seeding it would make A-101 appear as a DUPLICATE instead of NEW.
    # After TK-001 is published the article lives at knowledge/hr-tacit-knowledge/articles/HR-TK-ART-06.txt.
}

LIST_CAP = 10


def get_article(article_id: str) -> dict | None:
    return ARTICLES.get((article_id or "").strip().upper())


def article_ids() -> list[str]:
    return list(ARTICLES.keys())


def list_articles() -> list[dict]:
    return list(ARTICLES.values())[:LIST_CAP]


def next_article_id() -> str:
    """Return the next free HR-TK-ART-nn id (one beyond the seeded set)."""
    nums = [int(k.split("-")[-1]) for k in ARTICLES]
    return f"HR-TK-ART-{max(nums) + 1:02d}"
