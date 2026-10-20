"""Mock operations data: most recent health check per component.

Ages are computed from releases.AS_OF so they never drift.

Planted facts
  payments   : last health check 2025-08-27, 19 days old (policy limit is 7 days).
  orders_api : checked 2025-09-14, healthy.
  frontend   : checked 2025-09-13, healthy.
"""

HEALTH_CHECKS = {
    "payments": {"checked_on": "2025-08-27", "status": "healthy", "error_rate_pct": 0.1},
    "orders_api": {"checked_on": "2025-09-14", "status": "healthy", "error_rate_pct": 0.3},
    "frontend": {"checked_on": "2025-09-13", "status": "healthy", "error_rate_pct": 0.2},
}
