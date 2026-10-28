"""Mock harvested artifacts for the HR Tacit Knowledge scenario.

All text is fictional. Dates are explicit ISO dates; nothing depends on today's date.
Artifact IDs A-101..A-106 cover cases TK-001 to TK-005.
A-107 is the sample expert-notes document used in TK-003 (pasted text, no upload route).
"""

from __future__ import annotations

ARTIFACTS: dict[str, dict] = {
    # TK-001 batch -----------------------------------------------------------
    # A-101: ticket with an undocumented workaround. No matching KB article.
    "A-101": {
        "artifact_id": "A-101",
        "source": "ticket",
        "date": "2025-05-12",
        "author_role": "HR Specialist",
        "title": "Ticket SHR-4421: retroactive role-change salary correction keeps failing",
        "text": (
            "Resolved SHR-4421. Root cause: the automatic recalculation for a retroactive "
            "role change locks the record if the salary component is already in a period-close "
            "batch. Workaround: call the payroll team to set a hold flag on the component "
            "before changing the role, then release the hold after the date change is saved. "
            "The system re-calculates on the next overnight run. Took me 2 hours to find. "
            "The intranet page on role changes says nothing about this."
        ),
        "expert_id": "X-103",
    },
    # A-102: routine chat — looks helpful but is fully covered by ART-03.
    "A-102": {
        "artifact_id": "A-102",
        "source": "chat",
        "date": "2025-05-14",
        "author_role": "HR Coordinator",
        "title": "Chat snippet: employment certificate question",
        "text": (
            "Question in the HR Coordinators channel: 'Does a new hire get an employment "
            "certificate automatically or do they have to request it?' Reply: 'They request "
            "it through the employee self-service portal under My Documents > Certificates. "
            "Select Employment Certificate, choose the language and submit. HR Operations "
            "processes it within 3 working days.'"
        ),
        "expert_id": "X-102",
    },
    # A-103: near-duplicate of ART-03 (employment certificate).
    "A-103": {
        "artifact_id": "A-103",
        "source": "repository",
        "date": "2025-04-30",
        "author_role": "HR Operations Lead",
        "title": "Internal FAQ: how to request an employment certificate",
        "text": (
            "Q: How does an employee request a proof-of-employment letter? "
            "A: Log into Employee Self-Service > My Documents > Certificates. "
            "Choose 'Employment Certificate', select the language (Finnish, English or Swedish), "
            "and submit. HR Operations issues the certificate within 3 working days. "
            "The certificate shows your job title, start date and employment type. "
            "If you need a specific reference added (for example a bank loan letter), "
            "add a note in the free-text field. HR Operations will contact you if more "
            "information is needed."
        ),
        "expert_id": "X-102",
    },
    # A-104: noise — general meeting reminder.
    "A-104": {
        "artifact_id": "A-104",
        "source": "chat",
        "date": "2025-05-15",
        "author_role": "HR Coordinator",
        "title": "Chat: monthly HR operations sync reminder",
        "text": (
            "Reminder: HR Operations monthly sync is on Friday 2025-05-16 at 10:00. "
            "Agenda: (1) open tickets, (2) upcoming policy updates, (3) AOB. "
            "Teams link in the calendar invite."
        ),
        "expert_id": None,
    },
    # TK-002 -----------------------------------------------------------------
    # A-105: contradicts ART-04 (Finland: HR-22 / 10 days is stale; real: e-form PR-1 / 5 days).
    "A-105": {
        "artifact_id": "A-105",
        "source": "ticket",
        "date": "2025-05-20",
        "author_role": "HR Specialist",
        "title": "Ticket SHR-4490: position-change request form changed",
        "text": (
            "Closed SHR-4490. The employee had been using the old paper form HR-22 for "
            "internal position changes in Finland. That form was retired in January 2025. "
            "The correct route is now the e-form PR-1 in the HR portal (HR > Requests > "
            "Position Change). Processing time is 5 working days, not 10. "
            "The process page on the intranet still says 10 days and references HR-22. "
            "Raised with the HR Content team as a page update request."
        ),
        "expert_id": "X-104",
    },
    # TK-003 -----------------------------------------------------------------
    # A-107 is the expert-notes document (pasted text). Defined here as metadata;
    # the full text lives in docs/demo/hr-tk-sample/ and is pasted by the expert.
    "A-107": {
        "artifact_id": "A-107",
        "source": "repository",
        "date": "2025-05-22",
        "author_role": "Senior HR Specialist",
        "title": "expert-notes-retroactive-leave-dates",
        "text": (
            "(Full text pasted by the expert in chat. Contains PII — see the sample document "
            "in docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt)"
        ),
        "expert_id": "X-101",
    },
}

LIST_CAP = 10


def list_new_artifacts() -> list[dict]:
    """All artifacts in arrival order, capped at LIST_CAP."""
    return list(ARTIFACTS.values())[:LIST_CAP]


def get_artifact(artifact_id: str) -> dict | None:
    return ARTIFACTS.get((artifact_id or "").strip().upper())


def artifact_ids() -> list[str]:
    return list(ARTIFACTS.keys())
