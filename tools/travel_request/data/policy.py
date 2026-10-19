"""Fictional agency approval rules for the Travel Request scenario.

These rules mirror the mock agency policy documents in knowledge/travel-request/policy/.
They live in code so the numbers are deterministic and the write tool can re-check them.
The state rules themselves (rates, thresholds of the collective agreement) are in rates.py.
"""

ALLOWED_PURPOSES = ("customer", "training", "internal_meeting", "conference", "leisure")

# Trip total (per diem + transport + lodging) in EUR.
SELF_APPROVAL_LIMIT_EUR = 600.0      # TP-APPR-01: domestic, no leave, within budget
MANAGER_LIMIT_EUR = 2500.0           # TP-APPR-01: above this the director decides

LEVELS = ("none", "manager", "director")


def required_level(total_eur: float, abroad: bool, includes_leave: bool, budget_remaining_eur: float) -> str:
    """Return the approval level needed for a trip: 'none', 'manager' or 'director'."""
    if total_eur > budget_remaining_eur or total_eur > MANAGER_LIMIT_EUR:
        return "director"
    if abroad or includes_leave or total_eur > SELF_APPROVAL_LIMIT_EUR:
        return "manager"
    return "none"


def policy_refs_for(total_eur: float, abroad: bool, includes_leave: bool, budget_remaining_eur: float) -> list:
    """Stable ids of the mock agency policy documents that explain the level."""
    refs = ["TP-APPR-01"]
    if total_eur > budget_remaining_eur:
        refs.append("TP-BUDGET-01")
    if includes_leave:
        refs.append("TP-PURPOSE-01")
    if abroad:
        refs.append("TP-ABROAD-01")
    return refs
