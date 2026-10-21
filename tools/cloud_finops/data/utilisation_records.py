"""Mock CPU/memory utilisation records for the Cloud FinOps demo.

Each resource has a 30-day rolling average and a 7-day rolling average.
These are the values the agent uses to apply idle-resource thresholds
defined in the policy documents.
"""

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Utilisation records keyed by resource_id
# ---------------------------------------------------------------------------
UTILISATION: Dict[str, Dict[str, Any]] = {
    "vm-zombie-01": {
        "resource_id": "vm-zombie-01",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 0.0,
        "cpu_avg_7d_pct": 0.0,
        "mem_avg_30d_pct": 1.2,
        "mem_avg_7d_pct": 1.1,
        "network_avg_30d_mbps": 0.0,
        "scheduled_jobs": [],
        "observation_window_days": 30,
        "note": "Zero CPU and network activity for 30 days. No scheduled jobs.",
    },
    "vm-idle-finance-01": {
        "resource_id": "vm-idle-finance-01",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 1.8,
        "cpu_avg_7d_pct": 1.4,
        "mem_avg_30d_pct": 8.5,
        "mem_avg_7d_pct": 7.9,
        "network_avg_30d_mbps": 0.02,
        "scheduled_jobs": [],
        "observation_window_days": 30,
        "note": "CPU below 2% for 14 consecutive days. No scheduled jobs.",
    },
    "vm-idle-dev-03": {
        "resource_id": "vm-idle-dev-03",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 2.9,
        "cpu_avg_7d_pct": 2.1,
        "mem_avg_30d_pct": 11.0,
        "mem_avg_7d_pct": 10.5,
        "network_avg_30d_mbps": 0.05,
        "scheduled_jobs": [],
        "observation_window_days": 30,
        "note": "CPU below 3% for 10 consecutive days. No scheduled jobs.",
    },
    "vm-batch-weekend-01": {
        "resource_id": "vm-batch-weekend-01",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 14.3,   # elevated by weekend spikes
        "cpu_avg_7d_pct": 1.8,     # low on a typical weekday window
        "mem_avg_30d_pct": 22.0,
        "mem_avg_7d_pct": 9.5,
        "network_avg_30d_mbps": 8.4,
        "scheduled_jobs": [
            {
                "job_id": "weekly-etl-pipeline",
                "schedule": "every Saturday 02:00-06:00 UTC",
                "cpu_peak_pct": 88,
                "last_run": "2025-05-11T02:00:00Z",
                "next_run": "2025-05-18T02:00:00Z",
            }
        ],
        "observation_window_days": 30,
        "note": (
            "30-day CPU average is 14.3% (driven by Saturday batch spikes). "
            "7-day average is low because the sample window falls on weekdays. "
            "A 7-day window alone would incorrectly classify this as idle."
        ),
    },
    "db-cluster-prod-01": {
        "resource_id": "db-cluster-prod-01",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 22.1,
        "cpu_avg_7d_pct": 21.8,
        "mem_avg_30d_pct": 28.3,
        "mem_avg_7d_pct": 27.9,
        "network_avg_30d_mbps": 45.0,
        "scheduled_jobs": [],
        "observation_window_days": 30,
        "note": (
            "CPU 22%, memory 28%. Active workload but significantly under-utilised "
            "for its provisioned size (xlarge-16cpu-128gb-3nodes). "
            "Recommended resize: large-8cpu-64gb-2nodes."
        ),
    },
    "vm-app-server-01": {
        "resource_id": "vm-app-server-01",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 68.2,
        "cpu_avg_7d_pct": 66.9,
        "mem_avg_30d_pct": 74.1,
        "mem_avg_7d_pct": 73.5,
        "network_avg_30d_mbps": 220.0,
        "scheduled_jobs": [],
        "observation_window_days": 30,
        "note": "Fully utilised. No action needed.",
    },
    "vm-app-server-02": {
        "resource_id": "vm-app-server-02",
        "account_id": "acct-001",
        "cpu_avg_30d_pct": 72.0,
        "cpu_avg_7d_pct": 70.4,
        "mem_avg_30d_pct": 78.8,
        "mem_avg_7d_pct": 77.2,
        "network_avg_30d_mbps": 235.0,
        "scheduled_jobs": [],
        "observation_window_days": 30,
        "note": "Fully utilised. No action needed.",
    },
}


def get_utilisation(resource_id: str) -> Optional[Dict[str, Any]]:
    """Return utilisation record for one resource, or None if not found."""
    return UTILISATION.get(resource_id)


def list_utilisation(account_id: str) -> List[Dict[str, Any]]:
    """Return all utilisation records for the account."""
    if account_id != "acct-001":
        return [{"error": f"Unknown account_id '{account_id}'."}]
    return [u for u in UTILISATION.values() if u.get("account_id") == account_id]
