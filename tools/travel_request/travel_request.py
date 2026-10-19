"""Travel request tools for watsonx Orchestrate.

Deterministic, read-only tools over a fictional agency (employees, budgets) and a small
hand-keyed subset of the 2026 state travel rules, plus one internal write tool that only
the travel_submit_request flow calls.

Tool outputs are language-neutral JSON (codes, numbers, section references). The agent
turns them into prose in the language of the user.
"""

import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import employees, policy, rates
except ImportError:
    from data import employees, policy, rates


def _error(code: str, message: str, hint: str) -> str:
    return json.dumps({"status": "error", "error_code": code, "message": message, "hint": hint},
                      ensure_ascii=False, indent=2)


def _resolve_country(country: Optional[str]):
    """Return ISO code for a country/city name (Finnish or English), or None."""
    key = (country or "").strip().lower()
    if not key:
        return None
    if key.upper() in rates.FOREIGN_PER_DIEM:
        return key.upper()
    if key in rates.COUNTRY_ALIASES:
        return rates.COUNTRY_ALIASES[key]
    for iso, (fi, en, _amt) in rates.FOREIGN_PER_DIEM.items():
        if key in (fi.lower(), en.lower()):
            return iso
    return None


# ---------------------------------------------------------------------------
# Tool 1: travel_get_employee_profile
# ---------------------------------------------------------------------------
@tool
def travel_get_employee_profile(employee: str) -> str:
    """Looks up an employee's grade, manager and cost center in the fictional agency directory.

    Use this tool first when a travel request names an employee, to find the cost center
    needed for the budget check and the manager who would approve.

    Args:
        employee (str): Employee id such as 'E-1001', or the full name such as 'Aino Virtanen'.

    Returns:
        str: JSON with employee_id, name, grade, manager, cost_center, home_office. If the
            employee is unknown, a structured error listing the valid employee ids.
    """
    eid, rec = employees.find_employee(employee)
    if not rec:
        return _error("EMPLOYEE_NOT_FOUND", f"Employee '{employee}' not found.",
                      f"Known employee ids: {', '.join(employees.employee_ids())}. Ask the user for their employee id.")
    out = {"status": "success", "employee_id": eid, **rec}
    return json.dumps(out, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: travel_get_budget_status
# ---------------------------------------------------------------------------
@tool
def travel_get_budget_status(cost_center: str, estimated_cost_eur: float) -> str:
    """Compares an estimated trip cost with the remaining 2026 travel budget of a cost center.

    Use this tool after estimating the trip cost. The comparison is done in code; do not
    compute it yourself.

    Args:
        cost_center (str): Cost center such as 'CC-100' (from travel_get_employee_profile).
        estimated_cost_eur (float): Estimated total cost of the trip in EUR.

    Returns:
        str: JSON with unit, remaining_eur, estimated_cost_eur, within_budget (bool) and
            director (the approver if the budget is exceeded). Structured error if unknown.
    """
    cc = (cost_center or "").strip().upper()
    rec = employees.BUDGETS.get(cc)
    if not rec:
        return _error("COST_CENTER_NOT_FOUND", f"Cost center '{cost_center}' not found.",
                      f"Known cost centers: {', '.join(sorted(employees.BUDGETS))}.")
    try:
        est = float(estimated_cost_eur)
    except (TypeError, ValueError):
        return _error("INVALID_AMOUNT", f"Cannot read '{estimated_cost_eur}' as a number.",
                      "Pass the estimated total as a number in EUR, for example 420.5.")
    out = {
        "status": "success",
        "cost_center": cc,
        "unit": rec["unit"],
        "remaining_eur": rec["remaining_eur"],
        "estimated_cost_eur": round(est, 2),
        "within_budget": est <= rec["remaining_eur"],
        "director": rec["director"],
        "policy_refs": ["TP-BUDGET-01"],
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: travel_get_per_diem_rate
# ---------------------------------------------------------------------------
@tool
def travel_get_per_diem_rate(country: str) -> str:
    """Returns the 2026 foreign per diem for a country or major city, from the state travel rules annex.

    Use this tool for any trip abroad instead of reading a rate from the knowledge base.
    Accepts Finnish or English country names, ISO codes, and a few city names (Bryssel, Brussels).

    Args:
        country (str): Country or city, for example 'Belgia', 'Belgium', 'DE', 'Tukholma'.

    Returns:
        str: JSON with iso_code, name_fi, name_en, per_diem_eur (full travel day), the
            section reference in Finnish, and the validity period. Structured error if the
            country is not in the demo subset.
    """
    iso = _resolve_country(country)
    if not iso:
        keyed = ", ".join(f"{v[0]} ({v[1]})" for v in rates.FOREIGN_PER_DIEM.values())
        return _error("COUNTRY_NOT_KEYED", f"No rate keyed for '{country}'.",
                      f"This demo includes only: {keyed}. The full annex has more countries. "
                      "Tell the user the rate is not available in this demo; do not guess a value.")
    fi, en, amount = rates.FOREIGN_PER_DIEM[iso]
    out = {
        "status": "success",
        "iso_code": iso,
        "name_fi": fi,
        "name_en": en,
        "per_diem_eur": amount,
        "unit": "per full travel day",
        "source": rates.SOURCE_TITLE,
        "section_ref": rates.SECTION_REFS["foreign_per_diem"],
        "valid_from": rates.EFFECTIVE_FROM,
        "valid_until": rates.EFFECTIVE_UNTIL,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: travel_estimate_reimbursement
# ---------------------------------------------------------------------------
def _domestic_per_diem(hours: float, meals_per_day: int):
    """Return (amount, description) for domestic per diem rules 10 § and 13 §."""
    items = []
    if hours <= 24:
        if hours > rates.FULL_PER_DIEM_MIN_HOURS:
            items.append(("full", rates.FULL_PER_DIEM_EUR))
        elif hours > rates.PARTIAL_PER_DIEM_MIN_HOURS:
            items.append(("partial", rates.PARTIAL_PER_DIEM_EUR))
    else:
        days = int(hours // 24)
        rem = hours - 24 * days
        items.extend([("full", rates.FULL_PER_DIEM_EUR)] * days)
        if rem > 6:
            items.append(("full", rates.FULL_PER_DIEM_EUR))
        elif rem > 2:
            items.append(("partial", rates.PARTIAL_PER_DIEM_EUR))
    total = 0.0
    reduced = 0
    for kind, amt in items:
        needed = rates.FREE_MEALS_NEEDED_FULL if kind == "full" else rates.FREE_MEALS_NEEDED_PARTIAL
        if meals_per_day >= needed:
            amt = amt * (1 - rates.FREE_MEAL_REDUCTION)
            reduced += 1
        total += amt
    return total, len(items), reduced


def _foreign_per_diem(hours: float, rate: float, meals_per_day: int):
    """Return (amount, number of day items, number reduced) per 12 § and 13 §."""
    if hours < 24:
        return None  # below 24 h the domestic rules apply (12 § 2 mom.)
    days = int(hours // 24)
    rem = hours - 24 * days
    total = 0.0
    reduced = 0
    n = days
    for _ in range(days):
        amt = rate
        if meals_per_day >= rates.FREE_MEALS_NEEDED_FULL:
            amt *= 1 - rates.FREE_MEAL_REDUCTION
            reduced += 1
        total += amt
    if rem > 10:
        amt, needed = rate * rates.FOREIGN_SHARE_OVER_10H, 2
        n += 1
    elif rem > 2:
        amt, needed = rate * rates.FOREIGN_SHARE_OVER_2H, 1
        n += 1
    else:
        amt, needed = 0.0, 0
    if amt and meals_per_day >= needed:
        amt *= 1 - rates.FREE_MEAL_REDUCTION
        reduced += 1
    total += amt
    return total, n, reduced


@tool
def travel_estimate_reimbursement(
    start_date: str,
    duration_hours: float,
    country: Optional[str] = None,
    free_meals_per_day: int = 0,
    max_distance_km: float = 100.0,
    own_car_km: float = 0.0,
    public_transport_cost_eur: float = 0.0,
    ticket_cost_eur: float = 0.0,
    lodging_cost_eur: float = 0.0,
) -> str:
    """Estimates the reimbursement for a trip using the 2026 state travel rules (deterministic).

    Use this tool for every amount. Never compute per diems, mileage or reductions yourself.
    Hotel breakfast included in the room price is NOT a free meal (13 §); do not count it in
    free_meals_per_day. The same number of free meals is applied to every travel day.

    Args:
        start_date (str): First day of the trip, ISO format 'YYYY-MM-DD'.
        duration_hours (float): Duration of the work trip in hours, from leaving home or office until returning.
            Exclude leave days attached to the trip; they are not reimbursed.
        country (str, optional): Destination country for trips abroad. Omit or leave empty for domestic trips (Finland also counts as domestic).
        free_meals_per_day (int): Meals per travel day provided free of charge (0, 1 or 2). Default 0.
        max_distance_km (float): Distance from home or workplace to the furthest point of the trip. Default 100.
            A value of 0 or less means unknown and is treated as the default; a per diem is dropped only for a known distance of 15 km or less.
        own_car_km (float): Kilometres driven with the employee's own car. Default 0.
        public_transport_cost_eur (float): Price of the same trip by public transport, if known. Caps the car
            reimbursement when cheaper (5 §). Default 0 meaning unknown.
        ticket_cost_eur (float): Cost of train, bus or air tickets bought for the trip (7 §). Default 0.
        lodging_cost_eur (float): Accommodation cost by receipt, room price only (15 §). Default 0.

    Returns:
        str: JSON with line items (each with amount_eur, basis and Finnish section reference), total_eur,
            assumptions and notes. Structured error for invalid input or for trips outside 2026, because
            the amounts for 2027 are agreed separately.
    """
    try:
        start = date.fromisoformat((start_date or "").strip())
        hours = float(duration_hours)
    except (TypeError, ValueError):
        return _error("INVALID_INPUT", "start_date or duration_hours could not be read.",
                      "Use start_date like '2026-04-14' and duration_hours as a number such as 8.5.")
    if hours <= 0:
        return _error("INVALID_INPUT", "duration_hours must be positive.", "Ask the user for the trip duration.")

    end = datetime.combine(start, datetime.min.time()) + timedelta(hours=hours)
    if start.year != 2026 or end.year != 2026:
        return _error("RATES_NOT_AVAILABLE",
                      "The rates in this demo are valid 2026-01-01 to 2026-12-31. Rates for 2027 are agreed separately.",
                      "Give the user the decision on the trip but say that no reimbursement estimate is available for this period.")

    domestic = (country or "").strip().lower() in ("", "suomi", "finland", "fi", "kotimaa", "domestic")
    iso = None if domestic else _resolve_country(country)
    if not domestic and not iso:
        return _error("COUNTRY_NOT_KEYED", f"No rate keyed for '{country}'.",
                      "Call travel_get_per_diem_rate to see the countries in this demo; do not guess a rate.")

    meals = max(0, min(int(free_meals_per_day or 0), 2))
    items = []
    notes = []
    assumptions = [
        "Same number of free meals applied to every travel day.",
        "Hotel breakfast in the room price is not counted as a free meal (13 §).",
        "Foreign trips shorter than 24 h use the domestic amounts (12 § 2 mom.); the 15 h / 5 h exception is not modelled.",
        f"Rates valid {rates.EFFECTIVE_FROM} to {rates.EFFECTIVE_UNTIL}.",
    ]

    # --- per diem -----------------------------------------------------------
    if not max_distance_km or max_distance_km <= 0:
        max_distance_km = 100.0
        assumptions.append("Distance not given: assumed to be over 15 km, so the per diem distance condition (9 §) is met.")
    if max_distance_km <= rates.PER_DIEM_MIN_DISTANCE_KM:
        notes.append(f"No per diem: the trip does not reach over {rates.PER_DIEM_MIN_DISTANCE_KM} km ({rates.SECTION_REFS['per_diem_distance']}).")
    else:
        result = None
        ref = rates.SECTION_REFS["full_per_diem"]
        if iso:
            result = _foreign_per_diem(hours, rates.FOREIGN_PER_DIEM[iso][2], meals)
            ref = rates.SECTION_REFS["foreign_per_diem"]
        if result is None:
            result = _domestic_per_diem(hours, meals)
            ref = rates.SECTION_REFS["full_per_diem"] + "; " + rates.SECTION_REFS["partial_per_diem"]
        amount, n_items, n_reduced = result
        if n_items == 0:
            if 4 < hours <= 6:
                notes.append(f"No per diem (6 h not exceeded). A meal allowance may apply if the employee paid for a meal themselves ({rates.SECTION_REFS['meal_allowance']}).")
            else:
                notes.append("No per diem: the trip did not last over 6 hours (10 §).")
        else:
            basis = f"{n_items} per diem day item(s)"
            if n_reduced:
                basis += f", {n_reduced} reduced by 50 % for free meals ({rates.SECTION_REFS['free_meals']})"
            items.append({"item": "per_diem", "amount_eur": round(amount, 2), "basis": basis, "section_ref": ref})

    # --- own car, with the cheapest-mode cap --------------------------------
    if own_car_km and own_car_km > 0:
        first = min(own_car_km, rates.CAR_KM_FIRST_BLOCK)
        rest = max(0.0, own_car_km - rates.CAR_KM_FIRST_BLOCK)
        car = first * rates.CAR_EUR_PER_KM_FIRST + rest * rates.CAR_EUR_PER_KM_AFTER
        basis = f"{own_car_km:g} km own car (assumes no earlier km this year)"
        ref = rates.SECTION_REFS["mileage_car"]
        if public_transport_cost_eur and public_transport_cost_eur > 0 and public_transport_cost_eur < car:
            basis += f"; capped to public transport price {public_transport_cost_eur:.2f} EUR"
            ref += "; " + rates.SECTION_REFS["travel_mode"]
            car = public_transport_cost_eur
            notes.append("Reimbursement is capped to the cheapest suitable travel mode (5 §).")
        items.append({"item": "mileage_car", "amount_eur": round(car, 2), "basis": basis, "section_ref": ref})

    if ticket_cost_eur and ticket_cost_eur > 0:
        items.append({"item": "tickets", "amount_eur": round(float(ticket_cost_eur), 2),
                      "basis": "by receipt", "section_ref": "7 §"})
    if lodging_cost_eur and lodging_cost_eur > 0:
        items.append({"item": "lodging", "amount_eur": round(float(lodging_cost_eur), 2),
                      "basis": "room price by receipt", "section_ref": "15 §"})

    total = round(sum(i["amount_eur"] for i in items), 2)
    out = {
        "status": "success",
        "source": rates.SOURCE_TITLE,
        "destination": (rates.FOREIGN_PER_DIEM[iso][1] if iso else "Finland"),
        "items": items,
        "total_eur": total,
        "assumptions": assumptions,
        "notes": notes,
    }
    return json.dumps(out, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: travel_issue_request_id (INTERNAL - called only by travel_submit_request)
# ---------------------------------------------------------------------------
@tool
def travel_issue_request_id(
    employee_id: str,
    destination: str,
    start_date: str,
    end_date: str,
    purpose: str,
    estimated_total_eur: float,
    includes_leave: bool,
    abroad: bool,
    granted_level: str,
) -> str:
    """Issues a travel request id after human approval. Restricted to the approval flow.

    NOTE: This is a restricted write tool for use only by the travel_submit_request flow.
    It must NOT be called directly by an agent. It re-checks the traveler, the budget and the
    approval level against the mock data and refuses if the granted level is too low.

    Args:
        employee_id (str): Employee id such as 'E-1001'.
        destination (str): Destination name as given by the traveler.
        start_date (str): First day of the trip, 'YYYY-MM-DD'.
        end_date (str): Last day of the trip, 'YYYY-MM-DD'.
        purpose (str): One of customer, training, internal_meeting, conference, leisure.
        estimated_total_eur (float): Estimated total cost in EUR.
        includes_leave (bool): True if leave days are attached to the trip.
        abroad (bool): True for trips outside Finland.
        granted_level (str): Approval level recorded by the human decision: none, manager or director.

    Returns:
        str: JSON with request_id, status ISSUED, the validated approval level and the policy refs;
            or a structured error if validation fails.
    """
    eid, rec = employees.find_employee(employee_id)
    if not rec:
        return _error("EMPLOYEE_NOT_FOUND", f"Employee '{employee_id}' not found.",
                      f"Known employee ids: {', '.join(employees.employee_ids())}.")
    clean_purpose = (purpose or "").strip().lower()
    if clean_purpose not in policy.ALLOWED_PURPOSES:
        return _error("INVALID_PURPOSE", f"Purpose '{purpose}' is not valid.",
                      f"Allowed purposes: {', '.join(policy.ALLOWED_PURPOSES)}.")
    if clean_purpose == "leisure":
        return _error("PURPOSE_NOT_ELIGIBLE", "A leisure trip is not an official trip (3 §).",
                      "Do not issue a request id for leisure trips.")
    try:
        s = date.fromisoformat((start_date or "").strip())
        e = date.fromisoformat((end_date or "").strip())
        est = float(estimated_total_eur)
    except (TypeError, ValueError):
        return _error("INVALID_INPUT", "start_date, end_date or estimated_total_eur could not be read.",
                      "Use 'YYYY-MM-DD' dates and a numeric estimate.")
    if e < s:
        return _error("INVALID_DATES", "end_date is before start_date.", "Check the trip dates with the user.")
    if s.year != 2026 or e.year != 2026:
        return _error("RATES_NOT_AVAILABLE", "This demo issues request ids only for trips in 2026.",
                      "Rates for 2027 are agreed separately.")
    level = (granted_level or "").strip().lower()
    if level not in policy.LEVELS:
        return _error("INVALID_LEVEL", f"Level '{granted_level}' is not valid.",
                      f"Allowed levels: {', '.join(policy.LEVELS)}.")

    budget = employees.BUDGETS[rec["cost_center"]]["remaining_eur"]
    needed = policy.required_level(est, bool(abroad), bool(includes_leave), budget)
    if policy.LEVELS.index(level) < policy.LEVELS.index(needed):
        return _error("APPROVAL_LEVEL_TOO_LOW",
                      f"Granted level '{level}' is lower than the required level '{needed}'.",
                      f"This trip needs approval at level '{needed}' (policy {', '.join(policy.policy_refs_for(est, bool(abroad), bool(includes_leave), budget))}). No request id was issued.")

    seed = f"{eid}|{destination.strip().lower()}|{s}|{e}|{clean_purpose}|{round(est, 2)}".encode("utf-8")
    num = int(hashlib.md5(seed).hexdigest()[:6], 16) % 900000 + 100000
    request_id = f"TR-2026-{num}"
    out = {
        "status": "ISSUED",
        "request_id": request_id,
        "employee_id": eid,
        "traveler": rec["name"],
        "destination": destination,
        "start_date": str(s),
        "end_date": str(e),
        "estimated_total_eur": round(est, 2),
        "approval_level_required": needed,
        "approval_level_granted": level,
        "policy_refs": policy.policy_refs_for(est, bool(abroad), bool(includes_leave), budget),
        "valid_for": "booking and expense apps (mock)",
    }
    return json.dumps(out, ensure_ascii=False, indent=2)
