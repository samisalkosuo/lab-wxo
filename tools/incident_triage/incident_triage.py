"""Incident triage and operations tools for watsonx Orchestrate.

This package provides deterministic, read-only diagnostic tools over the mock
incident triage environment, along with ticketing and mock remediation tools.
"""

import hashlib
import json
from typing import Optional
from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import deployments, incidents, logs, metrics, services
except ImportError:
    from data import deployments, incidents, logs, metrics, services


# ---------------------------------------------------------------------------
# Tool 1: list_open_incidents
# ---------------------------------------------------------------------------
@tool
def list_open_incidents(severity: Optional[str] = None) -> str:
    """Lists currently open or investigating incidents across all monitored services.

    Use this tool when you need an overview of active incidents, their identifiers,
    affected services, and severity levels.

    Args:
        severity (str, optional): Filter by severity level ('critical', 'major', 'minor', 'low'). If omitted, all open incidents are returned.

    Returns:
        str: A Markdown-formatted table of active incidents with ID, Title, Service, Severity, Status, and Created timestamp.
    """
    valid_severities = ["critical", "major", "minor", "low"]
    if severity and severity.lower() not in valid_severities:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_SEVERITY_FILTER",
            "message": f"Unknown severity '{severity}'.",
            "hint": f"Valid severity levels are: {', '.join(valid_severities)}. Or omit severity to see all.",
        }, indent=2)

    active_incidents = incidents.list_incidents(severity_filter=severity)
    if not active_incidents:
        filter_msg = f" with severity '{severity}'" if severity else ""
        return f"No open incidents found{filter_msg}."

    lines = [
        "| Incident ID | Severity | Status | Affected Service | Title | Created At (UTC) |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for inc in active_incidents:
        lines.append(
            f"| `{inc['incident_id']}` | **{inc['severity'].upper()}** | {inc['status']} | "
            f"`{inc['service']}` | {inc['title']} | {inc['created_at']} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 2: get_incident
# ---------------------------------------------------------------------------
@tool
def get_incident(incident_id: str) -> str:
    """Retrieves detailed information and active alerts for a specific incident by ID.

    Use this tool to inspect the full description, impact, reported symptoms,
    and associated alerts for an incident (e.g. 'INC-1001', 'INC-1002').

    Args:
        incident_id (str): The unique incident identifier, e.g. 'INC-1001'. Case-insensitive.

    Returns:
        str: A structured summary containing title, service, severity, status,
            summary, impact, and related alert identifiers. If not found, returns a
            structured error listing valid incident IDs.
    """
    clean_id = incident_id.strip().upper() if incident_id else ""
    inc = incidents.get_incident_by_id(clean_id)
    if not inc:
        valid_ids = incidents.get_incident_ids()
        return json.dumps({
            "status": "error",
            "error_code": "INCIDENT_NOT_FOUND",
            "message": f"Incident '{incident_id}' not found.",
            "hint": f"Known active incident IDs are: {', '.join(valid_ids)}.",
        }, indent=2)

    alerts_str = "\n".join(f"- {a}" for a in inc.get("related_alerts", []))
    output = (
        f"### Incident {inc['incident_id']}: {inc['title']}\n\n"
        f"- **Service:** `{inc['service']}`\n"
        f"- **Severity:** `{inc['severity'].upper()}`\n"
        f"- **Status:** `{inc['status']}`\n"
        f"- **Created:** `{inc['created_at']}`\n"
        f"- **Reported By:** `{inc['reported_by']}`\n\n"
        f"**Summary:**\n{inc['summary']}\n\n"
        f"**Business Impact:**\n{inc['impact']}\n\n"
        f"**Related Alerts:**\n{alerts_str}"
    )
    return output


# ---------------------------------------------------------------------------
# Tool 3: get_service_health
# ---------------------------------------------------------------------------
@tool
def get_service_health(service_name: str) -> str:
    """Checks current health status, active alerts, dependencies, and certificate info for a service.

    Use this tool to see if a service is healthy, degraded, or failing, and to identify
    its dependencies or infrastructure issues (such as TLS certificate expiration).

    Args:
        service_name (str): Name of the service to inspect ('checkout', 'payments', 'auth-gateway', 'search-service', 'notification-service', 'inventory-db').

    Returns:
        str: A structured health report including status, uptime, dependencies, active alerts, and TLS certificate details.
    """
    clean_svc = service_name.strip().lower() if service_name else ""
    svc = services.get_service(clean_svc)
    if not svc:
        valid_services = services.get_service_names()
        return json.dumps({
            "status": "error",
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"Service '{service_name}' is not recognized.",
            "hint": f"Known services in the catalog are: {', '.join(valid_services)}.",
        }, indent=2)

    status_badge = svc["status"].upper()
    deps_str = ", ".join(f"`{d}`" for d in svc["dependencies"]) if svc["dependencies"] else "None (Ingress / Root)"
    alerts = svc.get("active_alerts", [])
    alerts_str = "\n".join(f"- {a}" for a in alerts) if alerts else "None (all checks passing)"

    tls = svc.get("tls_certificate", {})
    tls_info = (
        f"- Domain: `{tls.get('domain', 'N/A')}`\n"
        f"- Status: **{tls.get('status', 'unknown').upper()}**\n"
        f"- Expiration: `{tls.get('expires_at', 'N/A')}` ({tls.get('days_until_expiration', 'N/A')} days remaining)"
    )

    output = (
        f"### Service Health: {svc['display_name']} (`{svc['service_name']}`)\n\n"
        f"- **Status:** **{status_badge}**\n"
        f"- **Tier:** `{svc['tier']}` | **Owner:** `{svc['owner']}`\n"
        f"- **30-Day Uptime:** {svc['uptime_pct']}%\n"
        f"- **Dependencies:** {deps_str}\n\n"
        f"**Active Health Alerts:**\n{alerts_str}\n\n"
        f"**TLS Certificate Status:**\n{tls_info}"
    )
    return output


# ---------------------------------------------------------------------------
# Tool 4: query_logs
# ---------------------------------------------------------------------------
@tool
def query_logs(
    service_name: str,
    level: Optional[str] = None,
    search_term: Optional[str] = None,
    limit: int = 20,
) -> str:
    """Queries and filters structured application log entries for a specified service.

    Use this tool to find error traces, exception messages, slow query warnings, or
    specific keywords in application logs during triage.

    Args:
        service_name (str): Service name to query logs for ('checkout', 'payments', 'auth-gateway', 'search-service', 'notification-service', 'inventory-db').
        level (str, optional): Log level filter ('INFO', 'WARN', 'ERROR'). If omitted, all levels are included.
        search_term (str, optional): Keyword to filter log messages (case-insensitive).
        limit (int): Maximum log lines to return (default 20, max 50).

    Returns:
        str: Timestamped log lines matching criteria, capped to bounded limit.
    """
    clean_svc = service_name.strip().lower() if service_name else ""
    if clean_svc not in services.get_service_names():
        valid_services = services.get_service_names()
        return json.dumps({
            "status": "error",
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"Service '{service_name}' not found.",
            "hint": f"Known services to query logs for: {', '.join(valid_services)}.",
        }, indent=2)

    valid_levels = ["INFO", "WARN", "ERROR"]
    if level and level.upper() not in valid_levels:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_LOG_LEVEL",
            "message": f"Invalid log level '{level}'.",
            "hint": f"Allowed log levels are: {', '.join(valid_levels)}.",
        }, indent=2)

    matching_logs = logs.query_service_logs(
        service_name=clean_svc,
        level=level,
        search_term=search_term,
        limit=limit,
    )

    if not matching_logs:
        return (
            f"No log entries found for service `{clean_svc}` matching filters "
            f"(level={level or 'ANY'}, search_term={search_term or 'NONE'}). "
            f"Try broadening your search criteria or querying another service."
        )

    lines = [f"**Recent Log Entries for `{clean_svc}` (showing {len(matching_logs)} lines):**\n```text"]
    for entry in matching_logs:
        lines.append(f"[{entry['timestamp']}] {entry['level']:5s} [{entry['service']}] {entry['message']}")
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 5: get_metrics
# ---------------------------------------------------------------------------
@tool
def get_metrics(
    service_name: str,
    metric_name: Optional[str] = None,
    time_window: str = "last_1h",
) -> str:
    """Retrieves summarized telemetry metrics (latency, error rate, CPU, DB pools) for a service.

    Use this tool to compare current performance percentiles against normal baselines
    without receiving raw data firehoses.

    Args:
        service_name (str): Service name to retrieve metrics for ('checkout', 'payments', 'auth-gateway', 'search-service', 'notification-service', 'inventory-db').
        metric_name (str, optional): Specific metric category ('latency', 'error_rate', 'cpu_usage', 'db_connections', 'throughput_qps', 'tls_certificate'). If omitted, all metrics are returned.
        time_window (str): Query time window (default 'last_1h').

    Returns:
        str: Summarized metrics comparison showing current values, normal baselines, and status badges.
    """
    clean_svc = service_name.strip().lower() if service_name else ""
    if clean_svc not in services.get_service_names():
        valid_services = services.get_service_names()
        return json.dumps({
            "status": "error",
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"Service '{service_name}' not found.",
            "hint": f"Known services: {', '.join(valid_services)}.",
        }, indent=2)

    svc_metrics = metrics.get_service_metrics(clean_svc, metric_name=metric_name)
    if not svc_metrics:
        all_metrics = metrics.get_service_metrics(clean_svc) or {}
        available_keys = list(all_metrics.keys())
        return json.dumps({
            "status": "error",
            "error_code": "METRIC_NOT_FOUND",
            "message": f"Metric '{metric_name}' is not available for service '{clean_svc}'.",
            "hint": f"Available metrics for '{clean_svc}': {', '.join(available_keys)}.",
        }, indent=2)

    lines = [f"### Metrics Summary for `{clean_svc}` (Window: {time_window})\n"]
    for m_key, m_val in svc_metrics.items():
        title = m_key.replace("_", " ").title()
        status_tag = m_val.get("status", "info").upper()
        summary = m_val.get("summary", "")
        lines.append(f"#### {title} [{status_tag}]")
        if summary:
            lines.append(f"*{summary}*")
        
        detail_items = []
        for k, v in m_val.items():
            if k not in ("status", "summary"):
                detail_items.append(f"- **{k.replace('_', ' ').capitalize()}:** {v}")
        if detail_items:
            lines.extend(detail_items)
        lines.append("")

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Tool 6: list_recent_deployments
# ---------------------------------------------------------------------------
@tool
def list_recent_deployments(service_name: Optional[str] = None, limit: int = 5) -> str:
    """Lists recent software releases, commit hashes, authors, and change summaries.

    Use this tool when investigating latency spikes or errors to correlate incident
    onset times with recent deployments or code changes.

    Args:
        service_name (str, optional): Filter by service name ('checkout', 'payments', 'notification-service', 'auth-gateway', 'search-service'). If omitted, recent deployments across all services are returned.
        limit (int): Maximum number of deployments to return (default 5, max 10).

    Returns:
        str: A Markdown table of deployment events with deployment ID, service, version, commit hash, deployment timestamp, author, status, and summary of changes.
    """
    clean_svc = service_name.strip().lower() if service_name else None
    if clean_svc and clean_svc not in services.get_service_names():
        valid_services = services.get_service_names()
        return json.dumps({
            "status": "error",
            "error_code": "SERVICE_NOT_FOUND",
            "message": f"Service '{service_name}' not found in catalog.",
            "hint": f"Valid services are: {', '.join(valid_services)}.",
        }, indent=2)

    bounded_limit = min(max(limit, 1), 10)
    deps = deployments.list_deployments(service_name=clean_svc, limit=bounded_limit)
    if not deps:
        return f"No recent deployments found for service `{service_name}`."

    lines = [
        "| Deploy ID | Service | Version | Commit | Deployed At (UTC) | Author | Status | Change Summary |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for d in deps:
        lines.append(
            f"| `{d['deployment_id']}` | `{d['service']}` | `{d['version']}` | `{d['commit']}` | "
            f"{d['deployed_at']} | {d['deployed_by']} | {d['status']} | {d['change_summary']} |"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool 7: open_ticket
# ---------------------------------------------------------------------------
@tool
def open_ticket(
    title: str,
    service: str,
    severity: str,
    description: str,
    incident_id: Optional[str] = None,
) -> str:
    """Creates a tracking ticket for an incident investigation or follow-up action.

    Use this tool when formal escalation, team notification, or record keeping is needed.
    This is a deterministic mock write tool that returns a generated ticket record.

    Args:
        title (str): Brief summary title of the ticket.
        service (str): Affected service name (e.g. 'checkout', 'payments', 'auth-gateway').
        severity (str): Ticket priority level ('critical', 'major', 'minor', 'low').
        description (str): Detailed findings, evidence, root cause hypothesis, or action items.
        incident_id (Optional[str]): Associated incident ID if applicable (e.g. 'INC-1001').

    Returns:
        str: A structured confirmation with generated ticket ID, creation timestamp,
            status, and assigned team. Returns structured error if invalid service or severity.
    """
    clean_svc = service.strip().lower() if service else ""
    if clean_svc not in services.get_service_names():
        valid_services = services.get_service_names()
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_SERVICE",
            "message": f"Service '{service}' is not in the service catalog.",
            "hint": f"Known services: {', '.join(valid_services)}.",
        }, indent=2)

    valid_severities = ["critical", "major", "minor", "low"]
    if severity.lower() not in valid_severities:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_SEVERITY",
            "message": f"Invalid severity '{severity}'.",
            "hint": f"Valid severities: {', '.join(valid_severities)}.",
        }, indent=2)

    svc_data = services.get_service(clean_svc) or {}
    assigned_team = svc_data.get("owner", "oncall-sre")

    # Generate deterministic ticket ID from inputs
    hash_seed = f"{title}_{clean_svc}_{severity}_{incident_id or ''}".encode("utf-8")
    hash_int = int(hashlib.md5(hash_seed).hexdigest()[:4], 16) % 9000 + 1000
    ticket_id = f"TICK-{hash_int}"

    result = {
        "status": "success",
        "ticket_id": ticket_id,
        "title": title,
        "service": clean_svc,
        "severity": severity.lower(),
        "assigned_team": assigned_team,
        "incident_id": incident_id.upper() if incident_id else None,
        "state": "OPEN",
        "created_at": "2025-05-12T14:30:00Z",
        "message": f"Ticket {ticket_id} successfully created and assigned to {assigned_team}.",
        "description_preview": description[:120] + ("..." if len(description) > 120 else ""),
    }
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# Tool 8: execute_remediation (Mock execution tool for approval flow ONLY)
# ---------------------------------------------------------------------------
@tool
def execute_remediation(
    service: str,
    action: str,
    parameters: Optional[str] = None,
) -> str:
    """Executes an authorized remediation operation against a target service.

    NOTE: This is a restricted operational tool designed for use exclusively
    by automated approval workflows. It must NOT be called directly by agents
    without prior human governance approval.

    Args:
        service (str): Target service name ('checkout', 'payments', 'auth-gateway', 'search-service', 'notification-service', 'inventory-db').
        action (str): Remediation action name ('rollback', 'db_pool_resize', 'certificate_rotation', 'restart', 'no_action').
        parameters (str, optional): Optional JSON string of action parameters.

    Returns:
        str: Structured execution result including action status, target service, execution timestamp, and post-remediation verification status.
    """
    clean_svc = service.strip().lower() if service else ""
    if clean_svc not in services.get_service_names():
        valid_services = services.get_service_names()
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_SERVICE",
            "message": f"Target service '{service}' not found.",
            "hint": f"Known services: {', '.join(valid_services)}.",
        }, indent=2)

    valid_actions = ["rollback", "db_pool_resize", "certificate_rotation", "restart", "no_action"]
    clean_action = action.strip().lower() if action else ""
    if clean_action not in valid_actions:
        return json.dumps({
            "status": "error",
            "error_code": "INVALID_ACTION",
            "message": f"Action '{action}' is not supported.",
            "hint": f"Allowed remediation actions are: {', '.join(valid_actions)}.",
        }, indent=2)

    # Validate action appropriateness per service
    service_allowed_actions = {
        "checkout": ["rollback", "restart"],
        "payments": ["db_pool_resize", "restart"],
        "auth-gateway": ["certificate_rotation", "restart"],
        "search-service": ["no_action", "restart"],
        "notification-service": ["restart"],
        "inventory-db": ["restart"],
    }

    allowed_for_svc = service_allowed_actions.get(clean_svc, [])
    if clean_action not in allowed_for_svc:
        return json.dumps({
            "status": "error",
            "error_code": "ACTION_NOT_APPLICABLE",
            "message": f"Action '{clean_action}' is not applicable to service '{clean_svc}'.",
            "hint": f"Allowed actions for '{clean_svc}': {', '.join(allowed_for_svc)}.",
        }, indent=2)

    action_outcomes = {
        "rollback": {
            "summary": f"Rolled back {clean_svc} to previous stable version (v2.13.2). N+1 query regression removed.",
            "resulting_health": "healthy",
            "verification": "p99 latency normalized to 182ms; error rate dropped to 0.05%.",
        },
        "db_pool_resize": {
            "summary": f"Resized database connection pool for {clean_svc} from max 100 to max 200 connections.",
            "resulting_health": "healthy",
            "verification": "Active connections: 112/200; connection timeout exceptions resolved; HTTP 500 rate 0.0%.",
        },
        "certificate_rotation": {
            "summary": f"Rotated TLS certificate for {clean_svc} (*.auth.internal.example.com). New validity: 365 days.",
            "resulting_health": "healthy",
            "verification": "TLS handshakes succeeding; error rate 0.0%; certificate status VALID.",
        },
        "restart": {
            "summary": f"Graceful rolling restart of all replicas for {clean_svc} completed.",
            "resulting_health": "healthy",
            "verification": "Replicas passed healthcheck in 18s.",
        },
        "no_action": {
            "summary": f"Alert acknowledged for {clean_svc}. No infrastructure changes executed.",
            "resulting_health": "healthy",
            "verification": "Synthetic load test completed; latency returned to baseline 250ms.",
        },
    }

    outcome = action_outcomes[clean_action]
    result = {
        "status": "success",
        "service": clean_svc,
        "action": clean_action,
        "parameters": parameters,
        "executed_at": "2025-05-12T14:32:00Z",
        "summary": outcome["summary"],
        "resulting_service_health": outcome["resulting_health"],
        "post_remediation_verification": outcome["verification"],
    }
    return json.dumps(result, indent=2)
