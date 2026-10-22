"""Static mock claimant registry for the Disability Pension & Rehab Triage demo.

Each entry represents a claimant whose case is deliberately planted to teach a
specific evaluation path (see plans/pension-disability-triage-plan.md).

  CLM-701  Full permanent disability  — straightforward full pension evaluation
  CLM-702  Back surgery recovery      — "Rehabilitation before Pension" rule
  CLM-703  Young factory accident     — occupational accident exception waiver
  CLM-704  Long uninsured residency   — red herring / clear refusal case
"""

from typing import Optional

CLAIMANTS = {
    "CLM-701": {
        "claimant_id": "CLM-701",
        "name": "Matti Virtanen",
        "date_of_birth": "1968-03-14",
        "nationality": "Finnish",
        "residence_country": "Finland",
        "claim_type": "Työkyvyttömyyseläke",            # Full disability pension
        "claim_subtype": "permanent",
        "submission_date": "2025-01-08",
        "claim_status": "under_review",
        "occupational_history_summary": (
            "Insured continuously in Finland for 12 years. "
            "Most recent employment: senior logistics coordinator, 2013–2025."
        ),
        "employer": "Virtanen Logistics Oy",
        "last_working_day": "2024-11-30",
    },
    "CLM-702": {
        "claimant_id": "CLM-702",
        "name": "Sanna Mäkinen",
        "date_of_birth": "1979-07-22",
        "nationality": "Finnish",
        "residence_country": "Finland",
        "claim_type": "Työkyvyttömyyseläke",
        "claim_subtype": "permanent",
        "submission_date": "2025-02-14",
        "claim_status": "under_review",
        "occupational_history_summary": (
            "Insured for 7 years in Finland. "
            "Most recent employment: warehouse operative, 2018–2025."
        ),
        "employer": "NordStorage Oy",
        "last_working_day": "2024-12-15",
    },
    "CLM-703": {
        "claimant_id": "CLM-703",
        "name": "Aleksi Heikkinen",
        "date_of_birth": "2000-11-05",
        "nationality": "Finnish",
        "residence_country": "Finland",
        "claim_type": "Työkyvyttömyyseläke",
        "claim_subtype": "permanent",
        "submission_date": "2025-03-03",
        "claim_status": "under_review",
        "occupational_history_summary": (
            "Insured for 14 months only. "
            "Employment: factory machine operator at Teräs Metalli Oy, 2024–2025. "
            "Injury sustained on 2025-02-14 during normal work shift."
        ),
        "employer": "Teräs Metalli Oy",
        "last_working_day": "2025-02-14",
        "accident_date": "2025-02-14",
        "accident_type": "työtapaturma",  # occupational accident
        "accident_verified": True,
    },
    "CLM-704": {
        "claimant_id": "CLM-704",
        "name": "Pirjo Leinonen",
        "date_of_birth": "1966-04-30",
        "nationality": "Finnish",
        "residence_country": "Finland",
        "claim_type": "Työkyvyttömyyseläke",
        "claim_subtype": "permanent",
        "submission_date": "2025-01-20",
        "claim_status": "under_review",
        "occupational_history_summary": (
            "Worked in Finland 1995–2016, then lived abroad 2016–2024 "
            "with no Finnish insurance coverage and no bilateral treaty coverage. "
            "Returned to Finland mid-2024; only 8 months of insured Finnish work "
            "in the last 60-month window."
        ),
        "employer": "Leinonen Consulting Oy",
        "last_working_day": "2025-01-10",
        "abroad_period": {"start": "2016-01-01", "end": "2024-06-30", "treaty_applies": False},
    },
}


def get_claimant(claimant_id: str) -> Optional[dict]:
    """Return claimant record by ID (case-insensitive) or None."""
    return CLAIMANTS.get(claimant_id.strip().upper())


def get_claimant_ids() -> list:
    return list(CLAIMANTS.keys())
