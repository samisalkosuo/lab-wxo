"""Static mock insurance period records for the Disability Pension & Rehab Triage demo.

Provides insured-month counts over 36-month and 60-month windows, plus
the tuleva aika (future period) eligibility flag for each claimant.

  CLM-701  58 / 60 months insured  — passes 36/60 rule, tuleva aika eligible
  CLM-702  36 / 60 months insured  — exactly on the minimum threshold
  CLM-703  14 months only          — fails 36/60 rule; occupational accident waiver applies
  CLM-704   8 / 60 months insured  — fails 36/60 rule; no waiver; refer to Kela
"""

from typing import Optional

INSURANCE_PERIODS = {
    "CLM-701": {
        "claimant_id": "CLM-701",
        # 36/60-month qualifying condition
        "insured_months_last_36": 36,
        "insured_months_last_60": 58,
        "required_threshold_months": 36,
        "qualifying_condition_met": True,
        # Tuleva aika: future-period accrual (tulevan ajan ansioedellytys)
        # Requires at least 36/60 months; annual earnings ≥ threshold
        "tuleva_aika_eligible": True,
        "annual_earnings_eur": 38400,
        "tuleva_aika_earnings_threshold_eur": 8755,    # 2025 statutory floor
        # Summary of full insured career
        "total_insured_years": 12,
        "coverage_gaps": [],
        "bilateral_treaty": None,
        "notes": "Continuous Finnish TyEL coverage, no gaps.",
    },
    "CLM-702": {
        "claimant_id": "CLM-702",
        "insured_months_last_36": 36,
        "insured_months_last_60": 36,
        "required_threshold_months": 36,
        "qualifying_condition_met": True,
        "tuleva_aika_eligible": True,
        "annual_earnings_eur": 28200,
        "tuleva_aika_earnings_threshold_eur": 8755,
        "total_insured_years": 7,
        "coverage_gaps": [],
        "bilateral_treaty": None,
        "notes": (
            "Meets the minimum 36-month qualifying condition exactly. "
            "Medical prognosis shows recovery potential — rehab assessment required."
        ),
    },
    "CLM-703": {
        "claimant_id": "CLM-703",
        "insured_months_last_36": 14,
        "insured_months_last_60": 14,
        "required_threshold_months": 36,
        "qualifying_condition_met": False,
        "qualifying_condition_waived": True,
        "waiver_reason": "työtapaturma",   # occupational accident
        "waiver_statute": "TyEL § 12 momentti 3 — waiting period waived for work-related accidents",
        "tuleva_aika_eligible": True,      # waiver extends to tuleva aika
        "annual_earnings_eur": 22800,
        "tuleva_aika_earnings_threshold_eur": 8755,
        "total_insured_years": 1,
        "coverage_gaps": [],
        "bilateral_treaty": None,
        "notes": (
            "Standard 36-month condition NOT met (only 14 months). "
            "However, the incapacity arose directly from a verified occupational "
            "accident (työtapaturma), which waives the waiting period per TyEL § 12. "
            "Tuleva aika eligibility is also preserved under the waiver."
        ),
    },
    "CLM-704": {
        "claimant_id": "CLM-704",
        "insured_months_last_36": 8,
        "insured_months_last_60": 8,
        "required_threshold_months": 36,
        "qualifying_condition_met": False,
        "qualifying_condition_waived": False,
        "waiver_reason": None,
        "tuleva_aika_eligible": False,
        "annual_earnings_eur": 14400,
        "tuleva_aika_earnings_threshold_eur": 8755,
        "total_insured_years": 21,        # total career, but large gap
        "coverage_gaps": [
            {
                "start": "2016-01-01",
                "end": "2024-06-30",
                "reason": "Uninsured residency abroad",
                "bilateral_treaty": False,
            }
        ],
        "bilateral_treaty": None,
        "notes": (
            "Only 8 insured months in the last 60-month window due to 8.5-year "
            "uninsured residency abroad. No bilateral social-security treaty applies. "
            "Does not meet the 36/60 qualifying condition. No waiver applies. "
            "Claimant should be directed to Kela for the national disability pension (SOLITA)."
        ),
    },
}


def get_insurance_period(claimant_id: str) -> Optional[dict]:
    """Return insurance period record by claimant ID or None."""
    return INSURANCE_PERIODS.get(claimant_id.strip().upper())


def get_claimant_ids() -> list:
    return list(INSURANCE_PERIODS.keys())
