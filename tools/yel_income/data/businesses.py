"""Mock entrepreneur business profiles for the YEL income assessment demo."""

from typing import Any, Dict

# Static lookup keyed by entrepreneur ID (ENT-xxx).
# Fields:
#   entrepreneur_id     : stable identifier
#   name                : display name
#   sector              : Statistics Finland industry classification
#   yel_start_date      : date YEL insurance started (ISO 8601)
#   months_insured      : total months under YEL at review date
#   current_yel_income  : current confirmed YEL work income (EUR/yr)
#   annual_revenue      : most recent full-year turnover (EUR/yr)
#   weekly_hours        : self-reported average weekly working hours
#   employees           : number of hired employees
#   subcontracting_cost : annual subcontracting / sub-purchasing costs (EUR/yr)
#   notes               : free text from the case file
BUSINESSES: Dict[str, Dict[str, Any]] = {
    "ENT-801": {
        "entrepreneur_id": "ENT-801",
        "name": "Aleksi Mäkinen",
        "sector": "Software consulting (NACE J.62)",
        "yel_start_date": "2018-03-01",
        "months_insured": 86,
        "current_yel_income": 18000,
        "annual_revenue": 95000,
        "weekly_hours": 45,
        "employees": 0,
        "subcontracting_cost": 0,
        "notes": (
            "Full-time sole proprietor, no employees. "
            "Current YEL income has not been reviewed since inception. "
            "Triennial review triggered automatically."
        ),
    },
    "ENT-802": {
        "entrepreneur_id": "ENT-802",
        "name": "Kaisa Virtanen",
        "sector": "Artisan food production / bakery (NACE C.10)",
        "yel_start_date": "2016-06-01",
        "months_insured": 105,
        "current_yel_income": 32000,
        "annual_revenue": 140000,
        "weekly_hours": 20,
        "employees": 3,
        "subcontracting_cost": 48000,
        "notes": (
            "Owner manages logistics and finances approximately 20 h/wk; "
            "hands-on baking is performed by hired staff. "
            "Proposed income of €38,000 contested by entrepreneur. "
            "High raw-material and subcontracting costs reduce net business income."
        ),
    },
    "ENT-803": {
        "entrepreneur_id": "ENT-803",
        "name": "Juhani Korhonen",
        "sector": "Software development / startup (NACE J.62)",
        "yel_start_date": "2023-09-01",
        "months_insured": 19,
        "current_yel_income": 14000,
        "annual_revenue": 28000,
        "weekly_hours": 40,
        "employees": 0,
        "subcontracting_cost": 0,
        "notes": (
            "First-time entrepreneur within the statutory 48-month beginner period. "
            "Qualifies for the 22 % YEL beginner discount (aloittavan yrittäjän alennus). "
            "Asking about mandatory income level and discount entitlement."
        ),
    },
    "ENT-804": {
        "entrepreneur_id": "ENT-804",
        "name": "Meri Leinonen",
        "sector": "Freelance content creation / photography (NACE M.74)",
        "yel_start_date": None,
        "months_insured": 0,
        "current_yel_income": 0,
        "annual_revenue": 5200,
        "weekly_hours": 8,
        "employees": 0,
        "subcontracting_cost": 0,
        "notes": (
            "Side-hustle freelancer; primary income from a TyEL-covered employment. "
            "Annual self-employment revenue €5,200 is below the statutory YEL minimum "
            "threshold (€9,010/yr in 2024/2025). YEL insurance is NOT mandatory."
        ),
    },
}


def get_business(entrepreneur_id: str) -> Dict[str, Any] | None:
    """Return the business profile dict, or None if not found."""
    return BUSINESSES.get(entrepreneur_id)


def list_businesses() -> list[Dict[str, Any]]:
    """Return all profiles as a list."""
    return list(BUSINESSES.values())
