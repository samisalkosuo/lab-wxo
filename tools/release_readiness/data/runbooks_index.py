"""Mock operations data: runbook index per component.

Planted facts
  payments   : runbook, rollback and canary all present.
  orders_api : tier-1 service with NO runbook (BLOCKER).
  frontend   : runbook exists but has no rollback procedure and no canary (BLOCKER).
"""

RUNBOOKS = {
    "payments": {
        "service_tier": 1,
        "runbook_id": "OPS-RB-PAY-01",
        "has_rollback_procedure": True,
        "canary_configured": True,
    },
    "orders_api": {
        "service_tier": 1,
        "runbook_id": None,
        "has_rollback_procedure": False,
        "canary_configured": True,
    },
    "frontend": {
        "service_tier": 2,
        "runbook_id": "OPS-RB-FE-01",
        "has_rollback_procedure": False,
        "canary_configured": False,
    },
}
