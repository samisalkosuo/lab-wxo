"""Mock sector wage benchmarks for the YEL income assessment demo.

Data represents Statistics Finland / ETK (Finnish Centre for Pensions) sector
median wage statistics used as the reference point for YEL income assessments.

All figures are annual gross wages in EUR, based on illustrative 2024/2025 data.
"""

from typing import Any, Dict

# Keyed by NACE sector code (short form used in businesses.py).
# Fields:
#   sector_code   : short identifier matching businesses.py sector values
#   sector_name   : human-readable sector label
#   median_wage   : sector median annual wage (EUR/yr), the statutory benchmark
#   p25_wage      : 25th percentile (lower bound for plausible part-time/entry)
#   p75_wage      : 75th percentile (upper bound for senior / intensive work)
#   source_note   : data source reference for citation in assessments
SECTOR_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "NACE J.62": {
        "sector_code": "NACE J.62",
        "sector_name": "Computer programming, consultancy and related activities",
        "median_wage": 46000,
        "p25_wage": 34000,
        "p75_wage": 60000,
        "source_note": "ETK / Statistics Finland sector wage index 2024, J.62 ICT services.",
    },
    "NACE C.10": {
        "sector_code": "NACE C.10",
        "sector_name": "Manufacture of food products (artisan / small-scale)",
        "median_wage": 32000,
        "p25_wage": 24000,
        "p75_wage": 42000,
        "source_note": "ETK / Statistics Finland sector wage index 2024, C.10 food manufacturing.",
    },
    "NACE M.74": {
        "sector_code": "NACE M.74",
        "sector_name": "Other professional, scientific and technical activities (creative/photography)",
        "median_wage": 26000,
        "p25_wage": 18000,
        "p75_wage": 36000,
        "source_note": "ETK / Statistics Finland sector wage index 2024, M.74 creative services.",
    },
}

# Statutory YEL thresholds and limits (2024/2025 values)
YEL_STATUTORY = {
    "minimum_income": 9010,           # EUR/yr — below this YEL is NOT mandatory
    "maximum_income": 204625,         # EUR/yr — statutory ceiling
    "transition_cap": 4000,           # EUR/yr — maximum mandatory increase per triennial review
    "beginner_discount_pct": 22,      # % discount for first 48 months (aloittavan yrittäjän alennus)
    "beginner_discount_months": 48,   # months of entitlement
    "review_cycle_years": 3,          # statutory triennial review interval
    "yel_contribution_rate_pct": 24.1,  # approximate 2024 YEL contribution rate (age 18-52)
    "threshold_year": "2024/2025",
}


def get_benchmark(sector_code: str) -> Dict[str, Any] | None:
    """Return the benchmark dict for a sector code, or None if not found."""
    return SECTOR_BENCHMARKS.get(sector_code)


def get_statutory_limits() -> Dict[str, Any]:
    """Return the statutory YEL thresholds for 2024/2025."""
    return YEL_STATUTORY
