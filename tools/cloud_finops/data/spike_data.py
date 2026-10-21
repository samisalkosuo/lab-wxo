"""Mock cost-spike investigation records for the Cloud FinOps demo."""

from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Cost spike explanations keyed by service name
# ---------------------------------------------------------------------------
SPIKE_EXPLANATIONS: Dict[str, Dict[str, Any]] = {
    "Compute (VMs)": {
        "service": "Compute (VMs)",
        "prior_cost_usd": 44_200.00,
        "current_cost_usd": 72_400.00,
        "change_usd": 28_200.00,
        "change_pct": 63.8,
        "root_cause_summary": (
            "The Compute spend increase is driven primarily by vm-zombie-01, "
            "a VM running continuously since 2024-11-15 with no workload activity since 2025-04-10. "
            "Owner tag is missing. The VM is contributing USD 640/month to cost "
            "with zero business value."
        ),
        "contributing_resources": [
            {
                "resource_id": "vm-zombie-01",
                "contribution_usd": 640.00,
                "note": "Zombie VM — no owner, no workload for 35+ days.",
            },
            {
                "resource_id": "vm-idle-finance-01",
                "contribution_usd": 320.00,
                "note": "Idle VM — CPU < 2% for 14 days.",
            },
            {
                "resource_id": "vm-idle-dev-03",
                "contribution_usd": 320.00,
                "note": "Idle VM — CPU < 3% for 10 days.",
            },
            {
                "resource_id": "vm-batch-weekend-01",
                "contribution_usd": 640.00,
                "note": "Looks idle on weekdays; active Saturday batch job (do not reclaim).",
            },
        ],
        "recommended_action": (
            "Reclaim vm-zombie-01 (no owner, no workload). "
            "Investigate vm-idle-finance-01 and vm-idle-dev-03 per CF-POL-01 idle threshold. "
            "Do not act on vm-batch-weekend-01 without verifying scheduled-job calendar."
        ),
    },
    "GPU Compute": {
        "service": "GPU Compute",
        "prior_cost_usd": 23_000.00,
        "current_cost_usd": 28_000.00,
        "change_usd": 5_000.00,
        "change_pct": 21.7,
        "root_cause_summary": (
            "The GPU Compute increase contains a billing data error. "
            "Line item BL-5001 (GPU-BATCH-MAY) reports 1 000 GPU hours (USD 5 000) "
            "but usage telemetry shows 0 GPU hours consumed. "
            "This is a suspected billing feed error; it should not be acted on. "
            "Escalate to finance for correction per CF-POL-04."
        ),
        "contributing_resources": [],
        "recommended_action": (
            "Do not reclaim any GPU resources. "
            "Escalate billing discrepancy BL-5001 to finance (CF-POL-04). "
            "Actual GPU inference spend (BL-5002) is correct."
        ),
    },
    "Database (Managed)": {
        "service": "Database (Managed)",
        "prior_cost_usd": 33_800.00,
        "current_cost_usd": 34_100.00,
        "change_usd": 300.00,
        "change_pct": 0.9,
        "root_cause_summary": "Stable spend. No anomaly.",
        "contributing_resources": [],
        "recommended_action": (
            "No immediate action needed on spend. "
            "Note: db-cluster-prod-01 is over-provisioned (22% CPU, 28% memory) — "
            "a rightsizing opportunity of ~40% saving (illustrative) exists but is a "
            "separate change-control action, not a billing anomaly."
        ),
    },
}


def explain_spike(service: str) -> Optional[Dict[str, Any]]:
    """Return a root-cause explanation for a cost spike in the named service."""
    # case-insensitive match
    for key, record in SPIKE_EXPLANATIONS.items():
        if key.lower() == service.lower():
            return record
    return None


def list_explainable_services() -> List[str]:
    """Return the service names for which spike explanations are available."""
    return list(SPIKE_EXPLANATIONS.keys())
