"""Mock social benefit estimation formulas for the YEL income assessment demo.

These formulas compute illustrative daily allowance and annual benefit amounts
based on the entrepreneur's YEL confirmed work income. All figures are
approximations for demo purposes only; real Kela calculations differ.

References:
  - Sickness allowance (sairauspäiväraha): Kela formula, YEL income base
  - Parental allowance (vanhempainpäiväraha): same YEL income base
  - Unemployment security (työttömyysturva): YTK / unemployment fund daily rate
  - Pension accrual (eläkekertymä): 1.5 % of YEL income per year (< 53 yrs)
"""

from typing import Any, Dict


# ---------------------------------------------------------------------------
# Benefit formula constants (illustrative 2024/2025 approximations)
# ---------------------------------------------------------------------------

# Kela sickness/parental allowance: ~70 % of YEL income / 300 working days
SICKNESS_ALLOWANCE_RATE = 0.70
WORKING_DAYS_PER_YEAR = 300

# Unemployment daily allowance: basic amount + earnings-related increment
# Approximation: YTK-style formula — 45 % of (daily YEL wage above a threshold)
UNEMPLOYMENT_BASE_DAILY = 37.21           # Kela basic daily amount 2024 (EUR)
UNEMPLOYMENT_EARNINGS_RATE = 0.45         # % of daily YEL income above threshold
UNEMPLOYMENT_THRESHOLD_DAILY = 119.0      # daily YEL floor for earnings component

# Pension accrual rate (Earnings-Related Pension Act, TyEL/YEL, age < 53)
PENSION_ACCRUAL_RATE = 0.015              # 1.5 % per year

# Maximum number of sick days per calendar year (Kela rule: 300 days)
MAX_SICK_DAYS = 300


def estimate_sickness_allowance(yel_income: float) -> Dict[str, Any]:
    """Compute illustrative daily sickness allowance from YEL income.

    Args:
        yel_income: Annual YEL confirmed work income (EUR/yr).

    Returns:
        dict with daily_allowance, annual_max, and a note.
    """
    daily = round((yel_income * SICKNESS_ALLOWANCE_RATE) / WORKING_DAYS_PER_YEAR, 2)
    annual_max = round(daily * MAX_SICK_DAYS, 2)
    return {
        "daily_sickness_allowance_eur": daily,
        "annual_maximum_eur": annual_max,
        "basis": f"70 % of YEL income / {WORKING_DAYS_PER_YEAR} working days (Kela approximation 2024)",
    }


def estimate_parental_allowance(yel_income: float) -> Dict[str, Any]:
    """Compute illustrative daily parental allowance from YEL income.

    Args:
        yel_income: Annual YEL confirmed work income (EUR/yr).

    Returns:
        dict with daily_allowance and note.
    """
    daily = round((yel_income * SICKNESS_ALLOWANCE_RATE) / WORKING_DAYS_PER_YEAR, 2)
    return {
        "daily_parental_allowance_eur": daily,
        "basis": "Same base as sickness allowance; Kela formula, YEL income base (illustrative)",
    }


def estimate_unemployment_allowance(yel_income: float) -> Dict[str, Any]:
    """Compute illustrative earnings-related unemployment daily allowance.

    Args:
        yel_income: Annual YEL confirmed work income (EUR/yr).

    Returns:
        dict with daily_allowance and note.
    """
    daily_yel = yel_income / WORKING_DAYS_PER_YEAR
    if daily_yel <= UNEMPLOYMENT_THRESHOLD_DAILY:
        daily = round(UNEMPLOYMENT_BASE_DAILY, 2)
        component = "basic amount only (YEL income below earnings threshold)"
    else:
        earnings_component = (daily_yel - UNEMPLOYMENT_THRESHOLD_DAILY) * UNEMPLOYMENT_EARNINGS_RATE
        daily = round(UNEMPLOYMENT_BASE_DAILY + earnings_component, 2)
        component = "basic amount + earnings-related component (YTK approximation 2024)"
    return {
        "daily_unemployment_allowance_eur": daily,
        "basis": component,
    }


def estimate_pension_accrual(yel_income: float) -> Dict[str, Any]:
    """Compute annual pension accrual from YEL income.

    Args:
        yel_income: Annual YEL confirmed work income (EUR/yr).

    Returns:
        dict with annual_accrual_eur and note.
    """
    annual = round(yel_income * PENSION_ACCRUAL_RATE, 2)
    return {
        "annual_pension_accrual_eur": annual,
        "basis": "1.5 % of YEL income per year (TyEL/YEL pension accrual, age < 53)",
    }


def estimate_all_benefits(yel_income: float) -> Dict[str, Any]:
    """Compute all four illustrative social benefits for a given YEL income level.

    Args:
        yel_income: Annual YEL confirmed work income (EUR/yr).

    Returns:
        dict containing all four benefit estimates.
    """
    return {
        "yel_income_eur": yel_income,
        "sickness_allowance": estimate_sickness_allowance(yel_income),
        "parental_allowance": estimate_parental_allowance(yel_income),
        "unemployment_allowance": estimate_unemployment_allowance(yel_income),
        "pension_accrual": estimate_pension_accrual(yel_income),
        "disclaimer": (
            "All figures are illustrative approximations for demo purposes only. "
            "Actual amounts are calculated by Kela, the unemployment fund (YTK), "
            "and the Finnish Centre for Pensions (ETK) based on official rules."
        ),
    }
