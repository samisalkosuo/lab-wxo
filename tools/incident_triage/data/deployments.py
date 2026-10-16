"""Mock deployment records and history."""

from typing import Any, Dict, List, Optional

DEPLOYMENTS: List[Dict[str, Any]] = [
    {
        "deployment_id": "DEP-4109",
        "service": "notification-service",
        "version": "v1.8.0",
        "commit": "e4c8d91",
        "deployed_at": "2025-05-12T14:05:00Z",
        "deployed_by": "m.taylor@example.com",
        "status": "success",
        "change_summary": "Add email notification batching and worker queue processing.",
        "previous_version": "v1.7.4",
    },
    {
        "deployment_id": "DEP-4108",
        "service": "checkout",
        "version": "v2.14.0",
        "commit": "a9f3b12",
        "deployed_at": "2025-05-12T13:55:00Z",
        "deployed_by": "d.chen@example.com",
        "status": "success",
        "change_summary": "Optimize cart item pricing calculations and bundle rules.",
        "previous_version": "v2.13.2",
    },
    {
        "deployment_id": "DEP-4100",
        "service": "search-service",
        "version": "v2.4.1",
        "commit": "7d22b04",
        "deployed_at": "2025-05-05T11:15:00Z",
        "deployed_by": "a.kumar@example.com",
        "status": "success",
        "change_summary": "Index tokenizer update and fuzzy search threshold tuning.",
        "previous_version": "v2.4.0",
    },
    {
        "deployment_id": "DEP-4085",
        "service": "checkout",
        "version": "v2.13.2",
        "commit": "8c12e45",
        "deployed_at": "2025-05-01T10:00:00Z",
        "deployed_by": "s.patel@example.com",
        "status": "success",
        "change_summary": "Stable release with Redis cart cache enhancements.",
        "previous_version": "v2.13.1",
    },
    {
        "deployment_id": "DEP-4072",
        "service": "payments",
        "version": "v3.1.0",
        "commit": "3b77a10",
        "deployed_at": "2025-04-28T16:00:00Z",
        "deployed_by": "k.novak@example.com",
        "status": "success",
        "change_summary": "Update payment provider webhook signature verification.",
        "previous_version": "v3.0.8",
    },
    {
        "deployment_id": "DEP-4020",
        "service": "auth-gateway",
        "version": "v1.12.4",
        "commit": "1f99c82",
        "deployed_at": "2025-03-28T09:30:00Z",
        "deployed_by": "j.wilson@example.com",
        "status": "success",
        "change_summary": "Rate limiting header fix and session token refresh tuning.",
        "previous_version": "v1.12.3",
    },
]


def list_deployments(service_name: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Returns deployment records, optionally filtered by service name, capped at limit."""
    results = []
    for dep in DEPLOYMENTS:
        if service_name and dep["service"].lower() != service_name.lower():
            continue
        results.append(dep)
        if len(results) >= limit:
            break
    return results
