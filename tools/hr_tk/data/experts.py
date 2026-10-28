"""Mock expert directory for the HR Tacit Knowledge scenario.

All names and contacts are fictional (example.com addresses).
X-101..X-104 cover the cases defined in the plan.
"""

from __future__ import annotations
from typing import Optional

EXPERTS: dict[str, dict] = {
    "X-101": {
        "expert_id": "X-101",
        "name": "Maarit Virtanen",
        "role": "Senior HR Specialist",
        "email": "m.virtanen@example.com",
        "topics": ["retroactive leave correction", "payroll holds", "overpayment recovery",
                   "leave start date changes"],
    },
    "X-102": {
        "expert_id": "X-102",
        "name": "Janne Korhonen",
        "role": "HR Operations Lead",
        "email": "j.korhonen@example.com",
        "topics": ["employment certificates", "proof of employment", "employee self-service",
                   "work permit letters", "visa documentation", "international mobility"],
    },
    "X-103": {
        "expert_id": "X-103",
        "name": "Aino Mäkinen",
        "role": "HR Specialist",
        "email": "a.makinen@example.com",
        "topics": ["retroactive role changes", "salary corrections", "payroll",
                   "period-close batch", "recalculation holds"],
    },
    "X-104": {
        "expert_id": "X-104",
        "name": "Petri Leinonen",
        "role": "HR Specialist",
        "email": "p.leinonen@example.com",
        "topics": ["internal position changes", "Finland HR portal", "e-form PR-1",
                   "internal transfers", "role change requests"],
    },
}

EXPERT_CAP = 3


def get_expert(expert_id: str) -> Optional[dict]:
    return EXPERTS.get((expert_id or "").strip().upper())


def expert_ids() -> list[str]:
    return list(EXPERTS.keys())


def find_experts(topic: str) -> list[dict]:
    """Return up to EXPERT_CAP experts whose topics contain a keyword from topic."""
    q = (topic or "").strip().lower()
    if not q:
        return []
    words = [w for w in q.split() if len(w) > 2]
    scored: list[tuple[int, dict]] = []
    for expert in EXPERTS.values():
        score = sum(
            1 for t in expert["topics"] if any(w in t.lower() for w in words)
        )
        if score > 0:
            scored.append((score, expert))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:EXPERT_CAP]]
