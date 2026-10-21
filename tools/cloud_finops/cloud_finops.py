"""Cloud FinOps tools for watsonx Orchestrate.

Read-only diagnostic and investigation tools over the mock Cloud FinOps environment.
Write tools (cf_reclaim_resource, cf_resize_resource) are NOT exported here;
they live in this package but are only callable by the approval flows.
"""

import json
from typing import Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import spend_data, resource_inventory, utilisation_records, spike_data
except ImportError:
    from data import spend_data, resource_inventory, utilisation_records, spike_data


# ---------------------------------------------------------------------------
# Tool 1: cf_get_spend_summary
# ---------------------------------------------------------------------------
@tool
def cf_get_spend_summary(account_id: str, billing_period: str) -> str:
    """Returns a cloud spend summary for the specified account and billing period.

    Use this tool first when investigating a bill increase or cost anomaly to get
    a service-level breakdown and the overall change versus the prior period.

    Args:
        account_id (str): Cloud account identifier (e.g. 'acct-001').
        billing_period (str): The billing month in YYYY-MM format (e.g. '2025-05').

    Returns:
        str: JSON summary showing total spend, prior-period comparison, percentage change,
             and a per-service breakdown with change highlights.
    """
    result = spend_data.get_spend_summary(account_id, billing_period)
    if "error" in result:
        return json.dumps({
            "status": "error",
            "error_code": "SPEND_NOT_FOUND",
            "message": result["error"],
            "hint": "Valid account_id: acct-001. Valid billing_period: 2025-05 (current), 2025-04 (prior).",
        }, indent=2)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: cf_list_idle_resources
# ---------------------------------------------------------------------------
@tool
def cf_list_idle_resources(account_id: str, resource_type: Optional[str] = None) -> str:
    """Lists cloud resources that appear idle based on utilisation data.

    Use this tool to identify candidates for reclamation or rightsizing.
    Always call cf_get_resource_utilization on candidates before recommending action:
    some resources appear idle on short windows but have scheduled batch jobs.

    Args:
        account_id (str): Cloud account identifier (e.g. 'acct-001').
        resource_type (str, optional): Filter by type — 'VM', 'DatabaseCluster'.
            If omitted, all resource types are returned.

    Returns:
        str: JSON list of resources with their status, cost, owner tag, and a
             note describing why each was flagged (or confirmed healthy).
    """
    resources = resource_inventory.list_resources(account_id, resource_type)
    if resources and "error" in resources[0]:
        return json.dumps({
            "status": "error",
            "error_code": "ACCOUNT_NOT_FOUND",
            "message": resources[0]["error"],
            "hint": "Valid account_id: acct-001.",
        }, indent=2)

    # Flag resources whose 7-day CPU is below a nominal idle threshold for display.
    # Thresholds are defined in CF-POL-01; this tool surfaces all resources so the
    # agent can apply policy. The batch-weekend VM is included with its full note.
    flagged = []
    for r in resources:
        util = utilisation_records.get_utilisation(r["resource_id"])
        cpu_7d = util["cpu_avg_7d_pct"] if util else None
        flagged.append({
            "resource_id": r["resource_id"],
            "type": r["type"],
            "size": r["size"],
            "status": r["status"],
            "owner_tag": r["owner_tag"],
            "cost_centre": r["cost_centre"],
            "monthly_cost_usd": r["monthly_cost_usd"],
            "cpu_avg_7d_pct": cpu_7d,
            "last_workload_activity": r.get("last_workload_activity"),
            "note": r["note"],
        })

    # Sort: zero-activity / zombie first, then by CPU asc
    flagged.sort(key=lambda x: (x["cpu_avg_7d_pct"] is None, x["cpu_avg_7d_pct"] or 0))
    return json.dumps({"account_id": account_id, "resources": flagged}, indent=2)


# ---------------------------------------------------------------------------
# Tool 3: cf_get_resource_utilization
# ---------------------------------------------------------------------------
@tool
def cf_get_resource_utilization(resource_id: str) -> str:
    """Returns detailed CPU, memory, and network utilisation for a specific resource.

    Use this tool to verify whether a resource flagged as idle truly has no workload,
    or to check utilisation before proposing a resize. Always call this before
    recommending reclamation (CF-POL-01 requires a 30-day window check).

    Args:
        resource_id (str): The cloud resource identifier (e.g. 'vm-zombie-01',
            'db-cluster-prod-01'). Valid IDs: vm-zombie-01, vm-idle-finance-01,
            vm-idle-dev-03, vm-batch-weekend-01, db-cluster-prod-01,
            vm-app-server-01, vm-app-server-02.

    Returns:
        str: JSON record with 30-day and 7-day CPU/memory/network averages,
             any scheduled jobs, and a plain-text note summarising the finding.
    """
    # Validate resource exists
    resource = resource_inventory.get_resource(resource_id)
    if resource is None:
        valid_ids = resource_inventory.list_resource_ids()
        return json.dumps({
            "status": "error",
            "error_code": "RESOURCE_NOT_FOUND",
            "message": f"Resource '{resource_id}' not found.",
            "hint": f"Valid resource IDs: {', '.join(valid_ids)}.",
        }, indent=2)

    util = utilisation_records.get_utilisation(resource_id)
    if util is None:
        return json.dumps({
            "status": "error",
            "error_code": "UTILISATION_NOT_FOUND",
            "message": f"No utilisation data for '{resource_id}'.",
        }, indent=2)

    # Merge resource metadata with utilisation
    result = {
        "resource_id": resource_id,
        "account_id": resource["account_id"],
        "type": resource["type"],
        "size": resource["size"],
        "owner_tag": resource["owner_tag"],
        "cost_centre": resource["cost_centre"],
        "monthly_cost_usd": resource["monthly_cost_usd"],
        "cpu_avg_30d_pct": util["cpu_avg_30d_pct"],
        "cpu_avg_7d_pct": util["cpu_avg_7d_pct"],
        "mem_avg_30d_pct": util["mem_avg_30d_pct"],
        "mem_avg_7d_pct": util["mem_avg_7d_pct"],
        "network_avg_30d_mbps": util["network_avg_30d_mbps"],
        "scheduled_jobs": util["scheduled_jobs"],
        "observation_window_days": util["observation_window_days"],
        "note": util["note"],
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 4: cf_explain_cost_spike
# ---------------------------------------------------------------------------
@tool
def cf_explain_cost_spike(account_id: str, service: str) -> str:
    """Returns a root-cause explanation for a cost spike in a named cloud service.

    Use this tool after cf_get_spend_summary identifies a service with an
    unexpected change. It returns contributing resources, the root cause, and a
    recommended action (which may be 'escalate' rather than 'reclaim').

    Args:
        account_id (str): Cloud account identifier (e.g. 'acct-001').
        service (str): The cloud service name as returned by cf_get_spend_summary,
            e.g. 'Compute (VMs)', 'GPU Compute', 'Database (Managed)'.

    Returns:
        str: JSON record with root cause summary, contributing resources,
             and a recommended action string. For billing errors, the action
             will be 'escalate to finance', not 'reclaim'.
    """
    if account_id != "acct-001":
        return json.dumps({
            "status": "error",
            "error_code": "ACCOUNT_NOT_FOUND",
            "message": f"Unknown account_id '{account_id}'.",
            "hint": "Valid account_id: acct-001.",
        }, indent=2)

    explanation = spike_data.explain_spike(service)
    if explanation is None:
        valid = spike_data.list_explainable_services()
        return json.dumps({
            "status": "error",
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"No spike explanation available for service '{service}'.",
            "hint": f"Services with explanations: {', '.join(valid)}.",
        }, indent=2)

    return json.dumps(explanation, indent=2)


# ---------------------------------------------------------------------------
# Tool 5: cf_get_billing_lines
# ---------------------------------------------------------------------------
@tool
def cf_get_billing_lines(account_id: str, service: Optional[str] = None) -> str:
    """Returns detailed billing line items for the current period, optionally filtered by service.

    Use this tool when investigating a specific billing entry, verifying reported usage
    against actual telemetry, or following up on a discrepancy flagged in the spend summary.
    For GPU Compute discrepancy case CF-004, this tool shows the erroneous line item BL-5001.

    Args:
        account_id (str): Cloud account identifier (e.g. 'acct-001').
        service (str, optional): Filter by service name (e.g. 'GPU Compute').
            If omitted, all billing lines are returned.

    Returns:
        str: JSON list of billing line items. Items with discrepancy=true include
             a discrepancy_note explaining the difference and the recommended action.
    """
    lines = spend_data.get_billing_lines(account_id, service or "")
    if lines and "error" in lines[0]:
        return json.dumps({
            "status": "error",
            "error_code": "ACCOUNT_NOT_FOUND",
            "message": lines[0]["error"],
            "hint": "Valid account_id: acct-001.",
        }, indent=2)
    return json.dumps({"account_id": account_id, "billing_lines": lines}, indent=2)


# ---------------------------------------------------------------------------
# Write tools — NOT attached to the agent; only flows may call them.
# ---------------------------------------------------------------------------

@tool
def cf_reclaim_resource(resource_id: str, account_id: str, approved_by: str) -> str:
    """(Internal write tool — called only by cf_approve_reclaim flow after cost-owner approval.)

    Records the reclamation of an idle or zombie cloud resource.
    Always validate that resource_id belongs to account_id before executing.

    Args:
        resource_id (str): The cloud resource to reclaim.
        account_id (str): The account the resource belongs to. Must match the resource record.
        approved_by (str): The approver label recorded by the flow.

    Returns:
        str: JSON result with status, resource_id, account_id, and a confirmation message.
    """
    # Guard: resource must belong to this account
    resource = resource_inventory.get_resource(resource_id)
    if resource is None:
        return json.dumps({
            "status": "error",
            "error_code": "RESOURCE_NOT_FOUND",
            "message": f"Resource '{resource_id}' does not exist.",
        }, indent=2)
    if resource["account_id"] != account_id:
        return json.dumps({
            "status": "error",
            "error_code": "ACCOUNT_MISMATCH",
            "message": (
                f"Resource '{resource_id}' belongs to account '{resource['account_id']}', "
                f"not '{account_id}'. Reclamation refused."
            ),
        }, indent=2)
    # Guard: do not reclaim the batch VM (safety check in code, not just in prompt)
    if resource_id == "vm-batch-weekend-01":
        return json.dumps({
            "status": "error",
            "error_code": "RECLAIM_BLOCKED",
            "message": (
                "Reclamation of 'vm-batch-weekend-01' is blocked. "
                "This VM has a scheduled batch job (weekly-etl-pipeline, every Saturday). "
                "Reclaiming it would break the pipeline. Review and reschedule the job first."
            ),
        }, indent=2)

    return json.dumps({
        "status": "success",
        "action": "reclaim",
        "resource_id": resource_id,
        "account_id": account_id,
        "approved_by": approved_by,
        "message": (
            f"MOCK RECLAIM EXECUTED (demo only — no real resource was deleted). "
            f"Resource '{resource_id}' in account '{account_id}' reclaimed. "
            f"Approved by: {approved_by}. "
            f"Estimated saving: USD {resource['monthly_cost_usd']:.2f}/month."
        ),
    }, indent=2)


@tool
def cf_resize_resource(
    resource_id: str,
    account_id: str,
    target_size: str,
    approved_by: str,
) -> str:
    """(Internal write tool — called only by cf_approve_resize flow after cost-owner approval.)

    Records the rightsizing of a cloud resource to a smaller tier.
    Always validate that resource_id belongs to account_id before executing.

    Args:
        resource_id (str): The cloud resource to resize.
        account_id (str): The account the resource belongs to. Must match the resource record.
        target_size (str): The target size tier (e.g. 'large-8cpu-64gb-2nodes').
        approved_by (str): The approver label recorded by the flow.

    Returns:
        str: JSON result with status, resource_id, current size, target size, and a
             confirmation message including the illustrative saving estimate.
    """
    resource = resource_inventory.get_resource(resource_id)
    if resource is None:
        return json.dumps({
            "status": "error",
            "error_code": "RESOURCE_NOT_FOUND",
            "message": f"Resource '{resource_id}' does not exist.",
        }, indent=2)
    if resource["account_id"] != account_id:
        return json.dumps({
            "status": "error",
            "error_code": "ACCOUNT_MISMATCH",
            "message": (
                f"Resource '{resource_id}' belongs to account '{resource['account_id']}', "
                f"not '{account_id}'. Resize refused."
            ),
        }, indent=2)
    if resource["type"] not in ("DatabaseCluster",):
        # Only database clusters support resize in this mock
        return json.dumps({
            "status": "error",
            "error_code": "RESIZE_NOT_SUPPORTED",
            "message": (
                f"Resize is only supported for DatabaseCluster resources in this demo. "
                f"'{resource_id}' is a {resource['type']}."
            ),
        }, indent=2)

    current_size = resource["size"]
    return json.dumps({
        "status": "success",
        "action": "resize",
        "resource_id": resource_id,
        "account_id": account_id,
        "current_size": current_size,
        "target_size": target_size,
        "approved_by": approved_by,
        "message": (
            f"MOCK RESIZE EXECUTED (demo only — no real resource was changed). "
            f"Resource '{resource_id}' in account '{account_id}' "
            f"resized from '{current_size}' to '{target_size}'. "
            f"Approved by: {approved_by}. "
            "Illustrative saving: ~40% monthly cost reduction (USD ~3 360/month). "
            "This figure is illustrative; actual saving depends on production workload."
        ),
    }, indent=2)
