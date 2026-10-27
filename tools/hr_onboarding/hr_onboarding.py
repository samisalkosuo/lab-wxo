"""HR Onboarding tools for watsonx Orchestrate.

Read-only tools the agent uses to look up new hires, role access and department rules.
The write tool (hr_provision_access) is in this file but is NOT attached to the agent --
only the hr_request_provisioning and hr_request_compliance_provisioning flows call it,
after human approval.

Tool names are prefixed hr_ to keep them unique across the WXO instance.
All data is fictional and static; nothing depends on today's date.
"""

import hashlib
import json
from typing import List, Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import departments, hires, role_access
except ImportError:
    from data import departments, hires, role_access

_ISO_LEN = 10


def _error(code: str, message: str, hint: str) -> str:
    return json.dumps({"status": "error", "error_code": code, "message": message, "hint": hint},
                      indent=2)


def _valid_iso(value: str) -> bool:
    from datetime import date
    try:
        date.fromisoformat((value or "").strip())
        return len((value or "").strip()) == _ISO_LEN
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Tool 1: hr_list_pending_hires
# ---------------------------------------------------------------------------
@tool
def hr_list_pending_hires(start_from: str, start_to: str) -> str:
    """List new hires whose start date falls in an explicit date range.

    Use this when the coordinator asks who starts in a period, for example
    'who starts between 2025-06-09 and 2025-06-13?'. Always pass explicit ISO dates;
    ask the coordinator for the dates if they gave a relative expression such as 'Monday'.

    Args:
        start_from (str): First start date to include, 'YYYY-MM-DD'.
        start_to (str): Last start date to include, 'YYYY-MM-DD'.

    Returns:
        str: JSON with up to 10 hires (id, name, role, department, start date) in the range,
             or a structured error if a date cannot be read.
    """
    if not _valid_iso(start_from) or not _valid_iso(start_to):
        return _error("INVALID_DATE", "start_from and start_to must be ISO dates.",
                      "Use 'YYYY-MM-DD', for example 2025-06-09. Ask the coordinator for explicit dates.")
    s, e = start_from.strip(), start_to.strip()
    if e < s:
        return _error("INVALID_RANGE", "start_to is before start_from.", "Swap the dates or ask again.")
    rows = hires.list_by_start_date(s, e)
    shown = rows[:hires.LIST_CAP]
    return json.dumps({
        "status": "found" if rows else "none",
        "start_from": s,
        "start_to": e,
        "total": len(rows),
        "shown": len(shown),
        "hires": [
            {"hire_id": h["hire_id"], "name": h["name"], "role": h["role"],
             "department": h["department"], "start_date": h["start_date"]}
            for h in shown
        ],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: hr_get_new_hire
# ---------------------------------------------------------------------------
@tool
def hr_get_new_hire(name_or_id: str) -> str:
    """Retrieve one new-hire record by name or hire ID, with a list of missing fields.

    Use this first for any onboarding request. The result includes 'missing_fields':
    fields that must be asked from the coordinator before a provisioning request can be
    filed. If the name matches more than one person, candidates are returned instead of
    a single record: ask the coordinator which one is meant, never guess.

    Args:
        name_or_id (str): Hire ID such as 'H-1001', or the person's name (full or partial).

    Returns:
        str: JSON with the hire record and missing_fields, or candidates, or a structured error.
    """
    matches = hires.find_hires(name_or_id)
    if not matches:
        return _error("HIRE_NOT_FOUND", f"No new hire matches '{name_or_id}'.",
                      f"Known hire IDs: {', '.join(hires.hire_ids())}. "
                      "Ask the coordinator for the full name or the hire ID.")
    if len(matches) > 1:
        return json.dumps({
            "status": "ambiguous",
            "message": f"{len(matches)} hires match '{name_or_id}'. Ask which one is meant.",
            "candidates": [{"hire_id": h["hire_id"], "name": h["name"], "role": h["role"],
                            "start_date": h["start_date"]} for h in matches],
        }, indent=2)
    h = matches[0]
    return json.dumps({
        "status": "found",
        "hire": h,
        "missing_fields": hires.missing_fields(h),
        "allowed_equipment_choices": hires.EQUIPMENT_CHOICES,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: hr_get_role_access
# ---------------------------------------------------------------------------
@tool
def hr_get_role_access(role: str) -> str:
    """Return which systems a role may be granted, and which it may not.

    Use this to decide what to propose for a hire. The result is the authoritative
    role-to-systems matrix. Do not propose a system that is listed under 'not_allowed'.
    The policy documents in the knowledge base explain the reasons; cite them.

    Args:
        role (str): Role id or title, for example 'software_engineer', 'Site Reliability Engineer',
            'finance_analyst', 'hr_coordinator' or 'contractor'.

    Returns:
        str: JSON with allowed systems (and access detail), not_allowed systems, whether an
             end date is required, and the policy document IDs. Or a structured error.
    """
    r = role_access.get_role(role)
    if not r:
        return _error("ROLE_NOT_FOUND", f"Role '{role}' is not defined.",
                      f"Known roles: {', '.join(role_access.role_ids())}.")
    allowed = [{"system": s, "name": role_access.SYSTEMS[s], "access": r["allowed"][s]}
               for s in role_access.SYSTEM_ORDER if s in r["allowed"]]
    not_allowed = [{"system": s, "name": role_access.SYSTEMS[s]}
                   for s in role_access.SYSTEM_ORDER if s not in r["allowed"]]
    return json.dumps({
        "status": "found",
        "role": role_access.normalize_role(role),
        "title": r["title"],
        "employment_type": r["employment_type"],
        "requires_end_date": r["requires_end_date"],
        "allowed": allowed,
        "not_allowed": not_allowed,
        "admin_access": "never granted through onboarding (HR-POL-04)",
        "policy_refs": r["policy_refs"],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: hr_get_department_config
# ---------------------------------------------------------------------------
@tool
def hr_get_department_config(department: str) -> str:
    """Return the onboarding rules of a department, including which approval flow to use.

    Use this after finding the hire's department. If 'compliance_signoff_required' is true
    the compliance-gated flow (hr_request_compliance_provisioning) must be used; otherwise
    use the standard flow (hr_request_provisioning).

    Args:
        department (str): Department id or name, for example 'engineering', 'finance' or 'people'.

    Returns:
        str: JSON with compliance_signoff_required, approval_flow, approvers and policy IDs,
             or a structured error.
    """
    d = departments.get_department(department)
    if not d:
        return _error("DEPARTMENT_NOT_FOUND", f"Department '{department}' is not defined.",
                      f"Known departments: {', '.join(departments.department_ids())}.")
    return json.dumps({
        "status": "found",
        "department": departments.normalize_department(department),
        "name": d["name"],
        "compliance_signoff_required": d["compliance_signoff_required"],
        "approval_flow": d["approval_flow"],
        "approvers": d["approvers"],
        "policy_refs": d["policy_refs"],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: hr_check_provisioning_status
# ---------------------------------------------------------------------------
@tool
def hr_check_provisioning_status(hire_id: str) -> str:
    """Check the provisioning status of every system for one hire.

    Use this before proposing a request, to avoid asking for access that is already
    requested or granted.

    Args:
        hire_id (str): Hire ID such as 'H-1003'.

    Returns:
        str: JSON with per-system status (not_requested, pending or granted), or a structured error.
    """
    h = hires.get_hire(hire_id)
    if not h:
        return _error("HIRE_NOT_FOUND", f"Hire '{hire_id}' not found.",
                      f"Known hire IDs: {', '.join(hires.hire_ids())}.")
    state = hires.get_provisioning(h["hire_id"])
    return json.dumps({
        "status": "found",
        "hire_id": h["hire_id"],
        "name": h["name"],
        "systems": [{"system": s, "status": state.get(s, "not_requested")}
                    for s in role_access.SYSTEM_ORDER],
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 6 (write - flow only): hr_provision_access
# ---------------------------------------------------------------------------
@tool
def hr_provision_access(
    hire_id: str,
    role: str,
    department: str,
    systems: List[str],
    approval_path: str,
    hr_manager_approver: str,
    compliance_approver: Optional[str] = "",
    equipment_choice: Optional[str] = "",
) -> str:
    """Grant system access to one new hire after human approval. Restricted to the approval flows.

    RESTRICTED: this tool must only be called by hr_request_provisioning or
    hr_request_compliance_provisioning after human approval. It must never be attached to
    an agent. It re-checks everything in code (skill rule 7): one named hire, role and
    department match the record, systems are within the role's allowed list, no admin
    access, required fields present, and compliance sign-off when the department needs it.

    Args:
        hire_id (str): Exactly one hire ID such as 'H-1001'. Lists, teams and wildcards are refused.
        role (str): The role the request is for; must match the hire's record.
        department (str): The department the request is for; must match the hire's record.
        systems (List[str]): System ids to grant, for example ['email', 'chat'].
        approval_path (str): 'standard' or 'compliance', the flow that collected the approval.
        hr_manager_approver (str): Name or role of the HR Manager who approved.
        compliance_approver (str): Name or role of the Compliance Reviewer; required for compliance-gated departments.
        equipment_choice (str): Equipment choice supplied by the coordinator when the record had none.

    Returns:
        str: JSON with a provisioning reference and message, or a structured error.
    """
    raw_id = (hire_id or "").strip()
    if (not raw_id or any(c in raw_id for c in ",;*") or " " in raw_id
            or raw_id.lower() in ("all", "team", "everyone")):
        return _error("BULK_NOT_PERMITTED", "Provisioning must name exactly one hire.",
                      "Bulk and team-wide grants are prohibited (HR-POL-04). File one request per hire.")
    h = hires.get_hire(raw_id)
    if not h:
        return _error("HIRE_NOT_FOUND", f"Hire '{hire_id}' not found.",
                      f"Known hire IDs: {', '.join(hires.hire_ids())}.")

    if role_access.normalize_role(role) != h["role"]:
        return _error("ROLE_MISMATCH",
                      f"Request role '{role}' does not match the record for {h['hire_id']} ({h['role']}).",
                      "Access not granted. Re-read the hire record and resubmit.")
    if departments.normalize_department(department) != h["department"]:
        return _error("DEPARTMENT_MISMATCH",
                      f"Request department '{department}' does not match the record for "
                      f"{h['hire_id']} ({h['department']}).",
                      "Access not granted. Re-read the hire record and resubmit.")

    requested = [role_access.normalize_system(s) for s in (systems or [])]
    if not requested:
        return _error("NO_SYSTEMS", "No systems were requested.", "List at least one system id.")
    role_def = role_access.get_role(h["role"])
    for s in requested:
        if "admin" in s:
            return _error("ADMIN_NOT_PERMITTED", f"Admin access ('{s}') cannot be granted through onboarding.",
                          "Admin and bulk grants are prohibited (HR-POL-04).")
        if s not in role_access.SYSTEMS:
            return _error("UNKNOWN_SYSTEM", f"System '{s}' is not defined.",
                          f"Known systems: {', '.join(role_access.SYSTEM_ORDER)}.")
        if s not in role_def["allowed"]:
            return _error("SYSTEM_NOT_ALLOWED_FOR_ROLE",
                          f"System '{s}' is not allowed for role {role_def['title']}.",
                          "Allowed: " + ", ".join(s2 for s2 in role_access.SYSTEM_ORDER if s2 in role_def["allowed"])
                          + ". See " + ", ".join(role_def["policy_refs"]) + ".")

    path = (approval_path or "").strip().lower()
    if path not in ("standard", "compliance"):
        return _error("INVALID_APPROVAL_PATH", f"approval_path '{approval_path}' is not valid.",
                      "Use 'standard' or 'compliance'.")
    if not (hr_manager_approver or "").strip():
        return _error("APPROVER_MISSING", "No HR Manager approval is recorded.",
                      "Access not granted without HR Manager approval.")
    dept = departments.get_department(h["department"])
    flagged = ""
    if dept["compliance_signoff_required"]:
        if path != "compliance" or not (compliance_approver or "").strip():
            return _error("COMPLIANCE_REQUIRED",
                          f"Department {dept['name']} requires compliance sign-off.",
                          "Access not granted. Use hr_request_compliance_provisioning so a "
                          "Compliance Reviewer approves (HR-POL-03).")
    elif path == "compliance":
        flagged = (f" Note: the compliance flow was used, but {dept['name']} does not require "
                   "compliance sign-off.")

    record = dict(h)
    if (equipment_choice or "").strip():
        choice = equipment_choice.strip().lower().replace("-", "_").replace(" ", "_")
        if choice not in hires.EQUIPMENT_CHOICES:
            return _error("INVALID_EQUIPMENT", f"Equipment choice '{equipment_choice}' is not valid.",
                          f"Allowed: {', '.join(hires.EQUIPMENT_CHOICES)}.")
        record["equipment_choice"] = choice
    still_missing = hires.missing_fields(record)
    if still_missing:
        return _error("MISSING_FIELDS", f"Record is incomplete: {', '.join(still_missing)}.",
                      "Ask the coordinator for the missing fields before filing the request.")

    ordered = [s for s in role_access.SYSTEM_ORDER if s in requested]
    seed = f"{h['hire_id']}_{'-'.join(ordered)}_{path}".encode()
    ref = f"PRV-{int(hashlib.md5(seed).hexdigest()[:5], 16) % 90000 + 10000}"
    approvers = [hr_manager_approver.strip()]
    if (compliance_approver or "").strip():
        approvers.append(compliance_approver.strip())
    return json.dumps({
        "status": "success",
        "provisioning_reference": ref,
        "hire_id": h["hire_id"],
        "name": h["name"],
        "systems_granted": ordered,
        "approval_path": path,
        "approved_by": approvers,
        "message": (f"APPROVED AND PROVISIONED. Reference: {ref}. {h['name']} ({h['hire_id']}): "
                    f"{', '.join(ordered)}. Approved by {', '.join(approvers)}.{flagged}"),
    }, indent=2)
