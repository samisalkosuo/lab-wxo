"""Mock cloud spend data for the Cloud FinOps demo.

Billing period: 2025-05 (current month).
Baseline period: 2025-04 (prior month).

Planted anomalies (for cases CF-001 through CF-004):
  - CF-001: vm-zombie-01 running at full cost since 2025-04-10 (zombie, no owner alert).
  - CF-002: vm-idle-finance-01 and vm-idle-dev-03 look idle; vm-batch-weekend-01 has
            scheduled weekend batch jobs (red herring — looks idle on weekday utilisation).
  - CF-003: db-cluster-prod-01 is over-provisioned; rightsizing saves ~40% (illustrative).
  - CF-004: Billing line GPU-BATCH-MAY shows 1 000 GPU hours; actual recorded usage is 0.
"""

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Per-service spend summary (current vs prior period)
# ---------------------------------------------------------------------------
SPEND_SUMMARY: Dict[str, Any] = {
    "account_id": "acct-001",
    "billing_period": "2025-05",
    "prior_period": "2025-04",
    "currency": "USD",
    "total_current": 148_320.00,
    "total_prior": 114_080.00,
    "change_pct": 30.0,
    "services": [
        {
            "service": "Compute (VMs)",
            "current": 72_400.00,
            "prior":   44_200.00,
            "change_pct": 63.8,
            "note": "Largest mover — review VM inventory.",
        },
        {
            "service": "Database (Managed)",
            "current": 34_100.00,
            "prior":   33_800.00,
            "change_pct": 0.9,
            "note": "Stable.",
        },
        {
            "service": "Object Storage",
            "current": 8_320.00,
            "prior":   7_900.00,
            "change_pct": 5.3,
            "note": "Within normal variance.",
        },
        {
            "service": "GPU Compute",
            "current": 28_000.00,
            "prior":   23_000.00,
            "change_pct": 21.7,
            "note": "Review GPU billing lines — a discrepancy has been flagged.",
        },
        {
            "service": "Network Egress",
            "current": 5_500.00,
            "prior":   5_180.00,
            "change_pct": 6.2,
            "note": "Stable.",
        },
    ],
}

# ---------------------------------------------------------------------------
# Detailed billing line items (for CF-004: GPU discrepancy)
# ---------------------------------------------------------------------------
BILLING_LINE_ITEMS: List[Dict[str, Any]] = [
    {
        "line_id": "BL-5001",
        "service": "GPU Compute",
        "description": "GPU-BATCH-MAY: GPU cluster batch job hours",
        "reported_units": 1000,
        "unit": "GPU-hours",
        "unit_rate_usd": 5.00,
        "reported_cost_usd": 5_000.00,
        "recorded_usage_units": 0,
        "discrepancy": True,
        "discrepancy_note": (
            "Billing feed reports 1 000 GPU hours (USD 5 000) for GPU-BATCH-MAY. "
            "Usage telemetry shows 0 GPU hours consumed in this period. "
            "This is a data error in the billing feed; escalate to finance (CF-POL-04)."
        ),
    },
    {
        "line_id": "BL-5002",
        "service": "GPU Compute",
        "description": "GPU-INFERENCE: real-time inference cluster",
        "reported_units": 4_600,
        "unit": "GPU-hours",
        "unit_rate_usd": 5.00,
        "reported_cost_usd": 23_000.00,
        "recorded_usage_units": 4_600,
        "discrepancy": False,
        "discrepancy_note": "",
    },
]


def get_spend_summary(account_id: str, billing_period: str) -> Dict[str, Any]:
    """Return the spend summary for the given account and billing period."""
    if account_id != SPEND_SUMMARY["account_id"]:
        return {"error": f"Unknown account_id '{account_id}'. Valid: acct-001."}
    if billing_period not in (SPEND_SUMMARY["billing_period"], SPEND_SUMMARY["prior_period"]):
        return {
            "error": (
                f"No data for billing_period '{billing_period}'. "
                "Valid values: 2025-05 (current), 2025-04 (prior)."
            )
        }
    if billing_period == SPEND_SUMMARY["prior_period"]:
        # Summarise the prior period
        return {
            "account_id": account_id,
            "billing_period": billing_period,
            "currency": "USD",
            "total": SPEND_SUMMARY["total_prior"],
            "note": "Prior period — no anomaly breakdown available.",
        }
    return SPEND_SUMMARY


def get_billing_lines(account_id: str, service: str = "") -> List[Dict[str, Any]]:
    """Return billing line items, optionally filtered by service."""
    if account_id != "acct-001":
        return [{"error": f"Unknown account_id '{account_id}'."}]
    if service:
        return [b for b in BILLING_LINE_ITEMS if b["service"].lower() == service.lower()]
    return BILLING_LINE_ITEMS
