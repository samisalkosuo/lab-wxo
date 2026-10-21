"""Partial Early Old-Age Pension (OVE) tools for watsonx Orchestrate.

Read-only calculation and member exploration tools over the Finnish pension OVE domain.
Write actions (ove_create_application_record) are internal and only called by the approval flow.
"""

import json
from datetime import datetime
from typing import Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import members, accruals, cohort_tables
except ImportError:
    from data import members, accruals, cohort_tables


def _calculate_ove_reduction_core(
    member_id: str,
    draw_percentage: int,
    start_date: str = "2026-05-01"
) -> dict:
    """Core calculation logic for OVE reduction."""
    if draw_percentage not in (25, 50):
        return {
            "status": "error",
            "error_code": "INVALID_DRAW_PERCENTAGE",
            "message": f"Draw percentage must be exactly 25 or 50 (got {draw_percentage}%).",
            "hint": "Under Finnish TyEL legislation, only 25% or 50% partial draw is permitted.",
        }

    member = members.get_member(member_id)
    if "error" in member:
        return {"status": "error", "message": member["error"]}

    # Check for conflicting active benefits
    active_benefit = member.get("active_pension_benefit")
    if active_benefit and active_benefit.get("status") == "ACTIVE":
        return {
            "status": "ineligible_conflict",
            "member_id": member_id,
            "name": member["name"],
            "conflict_reason": f"Member is currently receiving an active benefit: {active_benefit['benefit_type']}.",
            "policy_rule": "Under Finnish pension law (OVE-POL-02), OVE cannot be granted concurrently with an active full disability pension or old-age pension.",
        }

    accrual = accruals.get_accrued_pension(member_id)
    if "error" in accrual:
        return {"status": "error", "message": accrual["error"]}

    birth_year = member["birth_year"]
    cohort = cohort_tables.get_cohort_rule(birth_year)

    # Parse dates
    try:
        target_start = datetime.strptime(start_date, "%Y-%m-%d")
        dob = datetime.strptime(member["date_of_birth"], "%Y-%m-%d")
    except ValueError:
        target_start = datetime(2026, 5, 1)
        dob = datetime.strptime(member["date_of_birth"], "%Y-%m-%d")

    # Member's age at start date (in months)
    age_months_at_start = (target_start.year - dob.year) * 12 + (target_start.month - dob.month)
    min_ove_months = cohort["min_ove_age_years"] * 12 + cohort["min_ove_age_months"]
    full_pension_months = cohort["full_pension_age_years"] * 12 + cohort["full_pension_age_months"]

    if age_months_at_start < min_ove_months:
        age_years = age_months_at_start // 12
        age_rem_months = age_months_at_start % 12
        return {
            "status": "ineligible_underage",
            "member_id": member_id,
            "name": member["name"],
            "current_age": f"{age_years} years {age_rem_months} months",
            "min_ove_age": f"{cohort['min_ove_age_years']} years {cohort['min_ove_age_months']} months",
            "shortfall_months": min_ove_months - age_months_at_start,
            "message": f"Member does not meet the minimum statutory OVE age for birth cohort {birth_year}.",
            "policy_ref": "OVE-POL-01",
        }

    # Calculate months early prior to full retirement age
    months_early = max(0, full_pension_months - age_months_at_start)
    reduction_pct = months_early * 0.4  # 0.4% per month permanent reduction
    reduction_multiplier = (100.0 - reduction_pct) / 100.0

    total_accrued_monthly = accrual["accrued_pension_monthly"]
    drawn_fraction = draw_percentage / 100.0
    drawn_base = total_accrued_monthly * drawn_fraction
    remaining_base = total_accrued_monthly * (1.0 - drawn_fraction)

    life_coeff = cohort["life_expectancy_coeff"]
    # Monthly OVE payout after actuarial reduction and life expectancy coefficient
    monthly_ove_gross = round(drawn_base * reduction_multiplier * life_coeff, 2)
    undiscounted_portion = round(drawn_base * life_coeff, 2)

    return {
        "status": "eligible",
        "member_id": member_id,
        "name": member["name"],
        "birth_year": birth_year,
        "draw_percentage": f"{draw_percentage}%",
        "target_start_date": start_date,
        "months_before_full_pension_age": months_early,
        "permanent_actuarial_reduction_pct": f"{reduction_pct:.1f}%",
        "life_expectancy_coefficient": life_coeff,
        "total_accrued_pension_baseline": f"{total_accrued_monthly:.2f} €/mo",
        "drawn_baseline_portion": f"{drawn_base:.2f} €/mo",
        "monthly_ove_gross_payout": f"{monthly_ove_gross:.2f} €/mo",
        "monthly_reduction_amount": f"{round(undiscounted_portion - monthly_ove_gross, 2):.2f} €/mo",
        "remaining_untouched_accrual": f"{remaining_base:.2f} €/mo",
        "note": "The reduction of 0.4%/month is permanent and applies for life to the drawn portion.",
    }


# ---------------------------------------------------------------------------
# Tool 1: ove_get_member_profile
# ---------------------------------------------------------------------------
@tool
def ove_get_member_profile(member_id: str) -> str:
    """Retrieves the member's personal profile, date of birth, employment, and active pension benefits.

    Use this tool first to check the member's birth year, current employment status,
    and verify if they are already receiving any conflicting statutory pension benefits
    (such as a full disability pension / kuntoutustuki).

    Args:
        member_id (str): Member identifier (e.g. 'MEM-101', 'MEM-102', 'MEM-103', 'MEM-104').

    Returns:
        str: JSON string containing member details, birth year, employer, and active benefits.
    """
    record = members.get_member(member_id)
    if "error" in record:
        return json.dumps({
            "status": "error",
            "error_code": "MEMBER_NOT_FOUND",
            "message": record["error"],
            "hint": "Valid member IDs: MEM-101, MEM-102, MEM-103, MEM-104.",
        }, indent=2)
    return json.dumps({"status": "success", "member": record}, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: ove_get_accrued_pension
# ---------------------------------------------------------------------------
@tool
def ove_get_accrued_pension(member_id: str) -> str:
    """Retrieves the member's total accrued earnings-related pension (karttunut eläke) to date.

    Use this tool to find the member's current total monthly accrued pension baseline
    before calculating OVE partial withdrawal portions.

    Args:
        member_id (str): Member identifier (e.g. 'MEM-101', 'MEM-102', 'MEM-103', 'MEM-104').

    Returns:
        str: JSON string with accrued monthly pension, total insured years, and calculation date.
    """
    record = accruals.get_accrued_pension(member_id)
    if "error" in record:
        return json.dumps({
            "status": "error",
            "error_code": "ACCRUAL_NOT_FOUND",
            "message": record["error"],
            "hint": "Valid member IDs: MEM-101, MEM-102, MEM-103, MEM-104.",
        }, indent=2)
    return json.dumps({"status": "success", "accrual": record}, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: ove_calculate_reduction
# ---------------------------------------------------------------------------
@tool
def ove_calculate_reduction(
    member_id: str,
    draw_percentage: int,
    start_date: str = "2026-05-01"
) -> str:
    """Calculates the partial early old-age pension (OVE) amount and permanent actuarial reduction.

    Evaluates statutory age eligibility for the member's birth cohort, computes
    the 0.4% per month early withdrawal penalty (varhennusvähennys) prior to full retirement age,
    and applies the statutory life expectancy coefficient (elinaikakerroin).

    Args:
        member_id (str): Member identifier (e.g. 'MEM-101').
        draw_percentage (int): Chosen OVE withdrawal percentage — must be 25 or 50.
        start_date (str, optional): Target start date in YYYY-MM-DD format (default: '2026-05-01').

    Returns:
        str: JSON string with eligibility status, monthly OVE payout, permanent reduction percentage,
             and remaining untouched accrued pension baseline.
    """
    result = _calculate_ove_reduction_core(member_id, draw_percentage, start_date)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: ove_simulate_combined_income
# ---------------------------------------------------------------------------
@tool
def ove_simulate_combined_income(
    member_id: str,
    draw_percentage: int,
    projected_monthly_salary: float,
    planned_working_months: int = 24
) -> str:
    """Simulates total monthly income (pension + salary) and new 1.5% annual pension accrual from continuing work.

    Under Finnish TyEL legislation, an employee working while receiving OVE accrues
    new pension at 1.5% per year on their gross work earnings until full retirement age.

    Args:
        member_id (str): Member identifier (e.g. 'MEM-101', 'MEM-103').
        draw_percentage (int): 25 or 50 percent OVE.
        projected_monthly_salary (float): Expected future gross monthly salary (e.g. 2800.0 or 4200.0).
        planned_working_months (int, optional): Duration of planned employment in months (default: 24).

    Returns:
        str: JSON string with combined gross monthly income and newly accrued future pension amount.
    """
    reduction_res = _calculate_ove_reduction_core(member_id, draw_percentage)
    if reduction_res.get("status") != "eligible":
        return json.dumps(reduction_res, indent=2)

    ove_gross_str = reduction_res["monthly_ove_gross_payout"].replace(" €/mo", "")
    ove_gross = float(ove_gross_str)

    combined_gross_monthly = round(ove_gross + projected_monthly_salary, 2)

    # 1.5% annual TyEL accrual on gross salary
    # Monthly pension accrued per year worked = (salary * 12 * 0.015) / 12 = salary * 0.015
    working_years = planned_working_months / 12.0
    monthly_accrual_per_year = round(projected_monthly_salary * 0.015, 2)
    total_new_accrued_monthly_pension = round(monthly_accrual_per_year * working_years, 2)

    remaining_untouched_str = reduction_res["remaining_untouched_accrual"].replace(" €/mo", "")
    remaining_untouched = float(remaining_untouched_str)
    life_coeff = float(reduction_res["life_expectancy_coefficient"])

    future_final_pension_at_target_age = round(
        ove_gross + (remaining_untouched * life_coeff) + total_new_accrued_monthly_pension,
        2
    )

    return json.dumps({
        "status": "simulation_complete",
        "member_id": member_id,
        "draw_percentage": f"{draw_percentage}%",
        "projected_monthly_salary": f"{projected_monthly_salary:.2f} €/mo",
        "monthly_ove_pension": f"{ove_gross:.2f} €/mo",
        "total_combined_monthly_gross": f"{combined_gross_monthly:.2f} €/mo",
        "continuing_work_accrual_rate": "1.5% per year (TyEL)",
        "newly_accrued_monthly_pension": f"{total_new_accrued_monthly_pension:.2f} €/mo (from {planned_working_months} months / {working_years:.1f} years of work)",
        "projected_total_pension_at_full_retirement": f"{future_final_pension_at_target_age:.2f} €/mo",
        "policy_ref": "OVE-POL-03",
    }, indent=2)


# ---------------------------------------------------------------------------
# Internal Write Tool (for Approval Flow only)
# ---------------------------------------------------------------------------
def ove_create_application_record(
    member_id: str,
    draw_percentage: int,
    start_date: str,
    approved_by: str,
    decision_notes: Optional[str] = None
) -> dict:
    """Internal write tool executed only after human-in-the-loop approval in the flow."""
    member = members.get_member(member_id)
    if "error" in member:
        return {"status": "error", "message": member["error"]}

    app_id = f"OVE-APP-{member_id[-3:]}-{datetime.now().strftime('%Y%m%d')}"
    return {
        "status": "APPLICATION_REGISTERED",
        "application_id": app_id,
        "member_id": member_id,
        "member_name": member["name"],
        "draw_percentage": f"{draw_percentage}%",
        "start_date": start_date,
        "approved_by": approved_by,
        "decision_notes": decision_notes or "Formal OVE election approved by advisor/member.",
        "confirmation_timestamp": datetime.now().isoformat(),
        "pension_system": member["pension_system"],
    }
