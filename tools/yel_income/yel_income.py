"""YEL income assessment tools for watsonx Orchestrate.

Read-only diagnostic tools for the Finnish statutory self-employed pension
insurance (YEL — Yrittäjien eläkelaki) triennial work income review process.

Tools available to the agent:
  yel_get_business_profile          – fetch entrepreneur / policy record
  yel_get_sector_benchmark          – fetch ETK/Statistics Finland median wage data
  yel_calculate_income_recommendation – apply statutory rules and derive proposed income
  yel_estimate_social_benefits      – estimate Kela / pension benefit impact

Internal tool (called only by the yel_issue_decision approval flow):
  yel_issue_decision_record         – write the final administrative determination record
"""

import json
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import businesses, sector_benchmarks, benefit_formulas
except ImportError:
    from data import businesses, sector_benchmarks, benefit_formulas


# ---------------------------------------------------------------------------
# Tool 1: yel_get_business_profile
# ---------------------------------------------------------------------------
@tool
def yel_get_business_profile(entrepreneur_id: str) -> str:
    """Retrieve the YEL insurance profile and business details for an entrepreneur.

    Use this as the first step in any YEL income review. Returns the entrepreneur's
    current confirmed YEL income, annual turnover, sector, weekly hours, number of
    employees, subcontracting costs, months insured, and case notes.

    Args:
        entrepreneur_id (str): Entrepreneur identifier (e.g. 'ENT-801').

    Returns:
        str: JSON-formatted business profile, or an error object if not found.
    """
    profile = businesses.get_business(entrepreneur_id)
    if profile is None:
        return json.dumps({
            "status": "error",
            "error_code": "ENTREPRENEUR_NOT_FOUND",
            "message": f"No YEL record found for entrepreneur '{entrepreneur_id}'.",
            "hint": "Valid IDs are: ENT-801, ENT-802, ENT-803, ENT-804. Check the ID and retry.",
        }, indent=2)
    return json.dumps({"status": "ok", "profile": profile}, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: yel_get_sector_benchmark
# ---------------------------------------------------------------------------
@tool
def yel_get_sector_benchmark(sector_code: str) -> str:
    """Retrieve the Statistics Finland / ETK sector median wage benchmark for a given sector.

    Use this after retrieving the business profile to obtain the statutory reference
    wage for the entrepreneur's industry. Returns the median wage, 25th and 75th
    percentile wages, and the statutory YEL threshold limits.

    Args:
        sector_code (str): NACE sector code from the business profile (e.g. 'NACE J.62').

    Returns:
        str: JSON-formatted benchmark data including median, percentile wages,
             statutory minimum/maximum income, and the transition cap.
    """
    benchmark = sector_benchmarks.get_benchmark(sector_code)
    if benchmark is None:
        valid = list(sector_benchmarks.SECTOR_BENCHMARKS.keys())
        return json.dumps({
            "status": "error",
            "error_code": "SECTOR_NOT_FOUND",
            "message": f"No benchmark data found for sector '{sector_code}'.",
            "hint": f"Valid sector codes in this dataset: {valid}. Use the sector_code from yel_get_business_profile.",
        }, indent=2)
    statutory = sector_benchmarks.get_statutory_limits()
    return json.dumps({
        "status": "ok",
        "benchmark": benchmark,
        "statutory_limits": statutory,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: yel_calculate_income_recommendation
# ---------------------------------------------------------------------------
@tool
def yel_calculate_income_recommendation(entrepreneur_id: str) -> str:
    """Calculate the recommended YEL confirmed work income for an entrepreneur.

    Applies the full statutory decision logic:
      1. Determines whether YEL is mandatory (revenue >= minimum threshold).
      2. For established entrepreneurs: compares current YEL income to sector median.
      3. Applies the statutory €4,000 transition cap (korotuskatto) on mandatory increases.
      4. For beginners (< 48 months): notes the 22 % discount entitlement.
      5. Returns recommended income, monthly premium, and reasoning steps.

    Always call yel_get_business_profile and yel_get_sector_benchmark first so you
    can explain each step before presenting the result to the user.

    Args:
        entrepreneur_id (str): Entrepreneur identifier (e.g. 'ENT-801').

    Returns:
        str: JSON object with recommended_income, monthly_premium,
             transition_cap_applied, beginner_discount_applicable,
             and a step_by_step reasoning list.
    """
    profile = businesses.get_business(entrepreneur_id)
    if profile is None:
        return json.dumps({
            "status": "error",
            "error_code": "ENTREPRENEUR_NOT_FOUND",
            "message": f"No YEL record found for entrepreneur '{entrepreneur_id}'.",
        }, indent=2)

    statutory = sector_benchmarks.get_statutory_limits()
    min_income = statutory["minimum_income"]
    transition_cap = statutory["transition_cap"]
    beginner_months = statutory["beginner_discount_months"]
    discount_pct = statutory["beginner_discount_pct"]
    contribution_rate = statutory["yel_contribution_rate_pct"] / 100
    revenue = profile["annual_revenue"]
    current_income = profile["current_yel_income"]
    months_insured = profile["months_insured"]
    weekly_hours = profile["weekly_hours"]
    sector_code = profile["sector"].split(" (")[1].rstrip(")")  # extract NACE code
    benchmark = sector_benchmarks.get_benchmark(sector_code)

    reasoning: list[str] = []

    # --- Step 1: Mandatory threshold check ---
    if revenue < min_income:
        reasoning.append(
            f"Annual revenue ({revenue:,.0f} EUR) is below the statutory YEL minimum threshold "
            f"({min_income:,.0f} EUR/yr, threshold_year {statutory['threshold_year']}). "
            "YEL insurance is NOT mandatory. Voluntary insurance is possible."
        )
        return json.dumps({
            "status": "ok",
            "entrepreneur_id": entrepreneur_id,
            "yel_mandatory": False,
            "recommended_income": None,
            "monthly_premium_eur": None,
            "transition_cap_applied": False,
            "beginner_discount_applicable": False,
            "reasoning": reasoning,
            "policy_refs": ["YEL-POL-01"],
        }, indent=2)

    reasoning.append(
        f"Annual revenue ({revenue:,.0f} EUR) meets the statutory YEL threshold "
        f"({min_income:,.0f} EUR/yr). YEL is MANDATORY. (YEL-POL-01)"
    )

    # --- Step 2: Sector benchmark and target income ---
    if benchmark is None:
        target_income = current_income
        reasoning.append(
            f"No sector benchmark found for '{sector_code}'. Using current YEL income "
            f"({current_income:,.0f} EUR) as provisional target."
        )
    else:
        median = benchmark["median_wage"]
        # Adjust for part-time: scale median by ratio of actual hours to full-time (40 h/wk)
        full_time_hours = 40
        if weekly_hours < full_time_hours:
            hour_ratio = weekly_hours / full_time_hours
            target_income = round(median * hour_ratio)
            reasoning.append(
                f"Sector median wage ({median:,.0f} EUR/yr for {sector_code}). "
                f"Entrepreneur works {weekly_hours} h/wk vs full-time {full_time_hours} h/wk "
                f"(ratio {hour_ratio:.2f}). Part-time adjusted target: {target_income:,.0f} EUR/yr."
            )
        else:
            target_income = median
            reasoning.append(
                f"Sector median wage ({median:,.0f} EUR/yr for {sector_code}). "
                f"Entrepreneur works {weekly_hours} h/wk (full-time). Target income: {target_income:,.0f} EUR/yr."
            )

    # --- Step 3: Transition cap ---
    transition_cap_applied = False
    if target_income > current_income:
        uncapped_increase = target_income - current_income
        if uncapped_increase > transition_cap:
            capped_income = current_income + transition_cap
            reasoning.append(
                f"Proposed increase ({uncapped_increase:,.0f} EUR) exceeds the statutory "
                f"€{transition_cap:,.0f} transition cap (korotuskatto, YEL-POL-02). "
                f"Recommended income capped at {capped_income:,.0f} EUR/yr."
            )
            recommended_income = capped_income
            transition_cap_applied = True
        else:
            reasoning.append(
                f"Proposed increase ({uncapped_increase:,.0f} EUR) is within the "
                f"€{transition_cap:,.0f} transition cap. Full adjustment applies."
            )
            recommended_income = target_income
    else:
        reasoning.append(
            f"Current YEL income ({current_income:,.0f} EUR) is at or above the sector-based target "
            f"({target_income:,.0f} EUR). No mandatory increase. No mandatory reduction either "
            "(reductions are voluntary). (YEL-POL-02)"
        )
        recommended_income = current_income

    # --- Step 4: Beginner discount ---
    beginner_applicable = months_insured < beginner_months
    if beginner_applicable:
        reasoning.append(
            f"Entrepreneur has been insured for {months_insured} months (< {beginner_months} months). "
            f"Statutory 22 % beginner discount (aloittavan yrittäjän alennus) applies. (YEL-POL-03)"
        )
    else:
        reasoning.append(
            f"Entrepreneur has been insured for {months_insured} months. "
            "Beginner discount period has ended."
        )

    # --- Step 5: Monthly premium ---
    effective_rate = contribution_rate * (1 - discount_pct / 100) if beginner_applicable else contribution_rate
    monthly_premium = round(recommended_income * effective_rate / 12, 2)
    reasoning.append(
        f"Monthly YEL premium at {effective_rate * 100:.2f} % rate: {monthly_premium:.2f} EUR/month "
        f"(based on recommended income {recommended_income:,.0f} EUR/yr)."
    )

    return json.dumps({
        "status": "ok",
        "entrepreneur_id": entrepreneur_id,
        "yel_mandatory": True,
        "current_yel_income_eur": current_income,
        "recommended_income_eur": recommended_income,
        "sector_median_eur": benchmark["median_wage"] if benchmark else None,
        "monthly_premium_eur": monthly_premium,
        "beginner_discount_applicable": beginner_applicable,
        "transition_cap_applied": transition_cap_applied,
        "reasoning": reasoning,
        "policy_refs": ["YEL-POL-01", "YEL-POL-02", "YEL-POL-03"],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: yel_estimate_social_benefits
# ---------------------------------------------------------------------------
@tool
def yel_estimate_social_benefits(
    entrepreneur_id: str,
    compare_income: Optional[float] = None,
) -> str:
    """Estimate the impact of YEL income on social security benefits.

    Computes illustrative daily sickness allowance, parental allowance, unemployment
    daily allowance, and annual pension accrual for the entrepreneur's current YEL
    income. If compare_income is provided, also shows figures for the proposed new
    income so the entrepreneur can see the difference.

    Use this after yel_calculate_income_recommendation to show the entrepreneur
    how a higher YEL income improves their social security safety net.

    Args:
        entrepreneur_id (str): Entrepreneur identifier (e.g. 'ENT-801').
        compare_income (float, optional): Proposed new YEL income in EUR/yr to compare
            against the current income. Omit if you only want current-income figures.

    Returns:
        str: JSON object with current benefits and, if compare_income is given,
             proposed benefits and the delta for each benefit type.
    """
    profile = businesses.get_business(entrepreneur_id)
    if profile is None:
        return json.dumps({
            "status": "error",
            "error_code": "ENTREPRENEUR_NOT_FOUND",
            "message": f"No YEL record found for entrepreneur '{entrepreneur_id}'.",
        }, indent=2)

    current_income = profile["current_yel_income"]
    current_benefits = benefit_formulas.estimate_all_benefits(current_income)

    result: dict = {
        "status": "ok",
        "entrepreneur_id": entrepreneur_id,
        "current_income_eur": current_income,
        "current_benefits": current_benefits,
        "policy_refs": ["YEL-POL-03"],
    }

    if compare_income is not None:
        proposed_benefits = benefit_formulas.estimate_all_benefits(compare_income)
        delta = {
            "daily_sickness_allowance_eur": round(
                proposed_benefits["sickness_allowance"]["daily_sickness_allowance_eur"]
                - current_benefits["sickness_allowance"]["daily_sickness_allowance_eur"],
                2,
            ),
            "daily_parental_allowance_eur": round(
                proposed_benefits["parental_allowance"]["daily_parental_allowance_eur"]
                - current_benefits["parental_allowance"]["daily_parental_allowance_eur"],
                2,
            ),
            "daily_unemployment_allowance_eur": round(
                proposed_benefits["unemployment_allowance"]["daily_unemployment_allowance_eur"]
                - current_benefits["unemployment_allowance"]["daily_unemployment_allowance_eur"],
                2,
            ),
            "annual_pension_accrual_eur": round(
                proposed_benefits["pension_accrual"]["annual_pension_accrual_eur"]
                - current_benefits["pension_accrual"]["annual_pension_accrual_eur"],
                2,
            ),
        }
        result["compare_income_eur"] = compare_income
        result["proposed_benefits"] = proposed_benefits
        result["benefit_delta"] = delta

    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Internal tool: yel_issue_decision_record
# (NOT attached to the agent; only called by the yel_issue_decision flow)
# ---------------------------------------------------------------------------
@tool
def yel_issue_decision_record(
    entrepreneur_id: str,
    confirmed_income_eur: float,
    underwriter_id: str,
    decision_type: str,
    justification: str,
    policy_ref: Optional[str] = None,
) -> str:
    """Record an official YEL income determination after underwriter approval.

    This tool is called exclusively by the yel_issue_decision flow after the
    underwriter has confirmed or adjusted the proposed work income. It simulates
    issuing the legally binding administrative decision (valituskelpoinen päätös).

    Args:
        entrepreneur_id (str): Entrepreneur identifier (e.g. 'ENT-801').
        confirmed_income_eur (float): Final confirmed YEL work income in EUR/yr.
        underwriter_id (str): Identifier of the authorising underwriter (e.g. 'UW-42').
        decision_type (str): 'CONFIRM', 'ADJUST', or 'ESCALATE'.
        justification (str): Underwriter's written justification for the decision.
        policy_ref (str, optional): Primary policy document cited (e.g. 'YEL-POL-02').

    Returns:
        str: JSON confirmation with decision_id, effective_date, and next steps.
    """
    import hashlib
    import datetime

    # Generate a deterministic decision ID from the inputs
    raw = f"{entrepreneur_id}:{confirmed_income_eur}:{underwriter_id}:{decision_type}"
    decision_id = "YEL-DEC-" + hashlib.md5(raw.encode()).hexdigest()[:8].upper()
    effective_date = (datetime.date.today().replace(day=1)).isoformat()

    if decision_type == "ESCALATE":
        message = (
            f"Decision escalated to appeals review (TELK). "
            f"Case ID {decision_id} logged. Entrepreneur {entrepreneur_id} will be notified "
            "by post within 5 business days. No income change takes effect during review."
        )
    else:
        message = (
            f"YEL income determination {decision_id} issued. "
            f"Confirmed work income: {confirmed_income_eur:,.0f} EUR/yr, effective {effective_date}. "
            f"Entrepreneur {entrepreneur_id} will receive the decision letter within 5 business days. "
            "The decision is subject to appeal to TELK within 30 days of receipt. (YEL-POL-04)"
        )

    return json.dumps({
        "status": "ok",
        "decision_id": decision_id,
        "entrepreneur_id": entrepreneur_id,
        "decision_type": decision_type,
        "confirmed_income_eur": confirmed_income_eur,
        "effective_date": effective_date,
        "underwriter_id": underwriter_id,
        "policy_ref": policy_ref,
        "message": message,
    }, indent=2)
