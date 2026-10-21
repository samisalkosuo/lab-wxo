"""Mock resource inventory for the Cloud FinOps demo.

Planted resources:
  vm-zombie-01         — running, no active workload since 2025-04-10, full cost.
  vm-idle-finance-01   — CPU < 2% for 14 days; genuinely idle.
  vm-idle-dev-03       — CPU < 3% for 10 days; genuinely idle.
  vm-batch-weekend-01  — CPU < 2% weekdays; scheduled weekend batch jobs (red herring).
  db-cluster-prod-01   — over-provisioned; utilisation ~22%, optimal size saves ~40% (illustrative).
  vm-app-server-01     — healthy, fully utilised.
  vm-app-server-02     — healthy, fully utilised.
"""

from typing import Any, Dict, List, Optional

RESOURCES: Dict[str, Dict[str, Any]] = {
    "vm-zombie-01": {
        "resource_id": "vm-zombie-01",
        "account_id": "acct-001",
        "type": "VM",
        "region": "eu-de",
        "size": "standard-8cpu-32gb",
        "status": "running",
        "owner_tag": "",
        "cost_centre": "unknown",
        "monthly_cost_usd": 640.00,
        "running_since": "2024-11-15",
        "last_workload_activity": "2025-04-10",
        "note": (
            "VM has been running continuously since 2024-11-15 with no workload activity "
            "since 2025-04-10 (over 30 days). Owner tag is missing. Full cost is accruing."
        ),
    },
    "vm-idle-finance-01": {
        "resource_id": "vm-idle-finance-01",
        "account_id": "acct-001",
        "type": "VM",
        "region": "eu-de",
        "size": "standard-4cpu-16gb",
        "status": "running",
        "owner_tag": "finance-team",
        "cost_centre": "finance",
        "monthly_cost_usd": 320.00,
        "running_since": "2025-01-10",
        "last_workload_activity": "2025-04-28",
        "note": "CPU < 2% for the last 14 days. No scheduled jobs recorded.",
    },
    "vm-idle-dev-03": {
        "resource_id": "vm-idle-dev-03",
        "account_id": "acct-001",
        "type": "VM",
        "region": "eu-de",
        "size": "standard-4cpu-16gb",
        "status": "running",
        "owner_tag": "dev-team",
        "cost_centre": "engineering",
        "monthly_cost_usd": 320.00,
        "running_since": "2025-02-01",
        "last_workload_activity": "2025-05-02",
        "note": "CPU < 3% for the last 10 days. No scheduled jobs recorded.",
    },
    "vm-batch-weekend-01": {
        "resource_id": "vm-batch-weekend-01",
        "account_id": "acct-001",
        "type": "VM",
        "region": "eu-de",
        "size": "standard-8cpu-32gb",
        "status": "running",
        "owner_tag": "data-engineering",
        "cost_centre": "analytics",
        "monthly_cost_usd": 640.00,
        "running_since": "2025-01-20",
        "last_workload_activity": "2025-05-11",   # last Sunday
        "note": (
            "CPU < 2% on weekdays (looks idle). "
            "Scheduled batch job 'weekly-etl-pipeline' runs every Saturday 02:00–06:00 UTC. "
            "Reclaiming this VM would break the batch pipeline."
        ),
    },
    "db-cluster-prod-01": {
        "resource_id": "db-cluster-prod-01",
        "account_id": "acct-001",
        "type": "DatabaseCluster",
        "region": "eu-de",
        "size": "xlarge-16cpu-128gb-3nodes",
        "status": "running",
        "owner_tag": "platform-team",
        "cost_centre": "platform",
        "monthly_cost_usd": 8_400.00,
        "running_since": "2024-06-01",
        "last_workload_activity": "2025-05-14",
        "note": (
            "Active database cluster. Average CPU utilisation 22%, memory 28%. "
            "Recommended size: large-8cpu-64gb-2nodes. "
            "Illustrative saving: ~40% monthly cost reduction (USD 3 360/month). "
            "Rightsizing requires change-control approval."
        ),
    },
    "vm-app-server-01": {
        "resource_id": "vm-app-server-01",
        "account_id": "acct-001",
        "type": "VM",
        "region": "eu-de",
        "size": "standard-8cpu-32gb",
        "status": "running",
        "owner_tag": "platform-team",
        "cost_centre": "platform",
        "monthly_cost_usd": 640.00,
        "running_since": "2024-03-01",
        "last_workload_activity": "2025-05-14",
        "note": "Healthy. CPU 68% average. Fully utilised.",
    },
    "vm-app-server-02": {
        "resource_id": "vm-app-server-02",
        "account_id": "acct-001",
        "type": "VM",
        "region": "eu-de",
        "size": "standard-8cpu-32gb",
        "status": "running",
        "owner_tag": "platform-team",
        "cost_centre": "platform",
        "monthly_cost_usd": 640.00,
        "running_since": "2024-03-01",
        "last_workload_activity": "2025-05-14",
        "note": "Healthy. CPU 72% average. Fully utilised.",
    },
}


def list_resources(account_id: str, resource_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all resources for the account, optionally filtered by type."""
    if account_id != "acct-001":
        return [{"error": f"Unknown account_id '{account_id}'."}]
    results = list(RESOURCES.values())
    if resource_type:
        results = [r for r in results if r["type"].lower() == resource_type.lower()]
    return results


def get_resource(resource_id: str) -> Optional[Dict[str, Any]]:
    """Return a single resource by id, or None if not found."""
    return RESOURCES.get(resource_id)


def list_resource_ids() -> List[str]:
    """Return all known resource ids."""
    return list(RESOURCES.keys())
