"""Mock QA data: the last three CI builds per component, and per-test history.

Planted facts
  payments   : test_refund_rounding failed once in build 411, then passed in 412-414
               (flaky; RED HERRING, not a blocker).
  orders_api : test_bulk_cancel failed in all three builds 220-222 (consistent failure; BLOCKER).
  frontend   : the end-to-end suite is skipped (BLOCKER under the policy).
"""

BUILDS = {
    "payments": [
        {"build": 414, "date": "2025-09-14", "total": 312, "passed": 312, "failed": 0, "skipped": 0},
        {"build": 413, "date": "2025-09-13", "total": 312, "passed": 312, "failed": 0, "skipped": 0},
        {"build": 412, "date": "2025-09-12", "total": 312, "passed": 312, "failed": 0, "skipped": 0},
        {"build": 411, "date": "2025-09-11", "total": 312, "passed": 311, "failed": 1, "skipped": 0},
    ],
    "orders_api": [
        {"build": 222, "date": "2025-09-14", "total": 188, "passed": 187, "failed": 1, "skipped": 0},
        {"build": 221, "date": "2025-09-13", "total": 188, "passed": 187, "failed": 1, "skipped": 0},
        {"build": 220, "date": "2025-09-12", "total": 188, "passed": 187, "failed": 1, "skipped": 0},
    ],
    "frontend": [
        {"build": 96, "date": "2025-09-14", "total": 140, "passed": 120, "failed": 0, "skipped": 20},
        {"build": 95, "date": "2025-09-13", "total": 140, "passed": 120, "failed": 0, "skipped": 20},
        {"build": 94, "date": "2025-09-12", "total": 140, "passed": 120, "failed": 0, "skipped": 20},
    ],
}

# Failing tests, newest build first. Only tests that failed in at least one of the builds above.
TEST_HISTORY = {
    "test_refund_rounding": {
        "component": "payments",
        "runs": [
            {"build": 414, "result": "passed"},
            {"build": 413, "result": "passed"},
            {"build": 412, "result": "passed"},
            {"build": 411, "result": "failed"},
        ],
        "failure_note": "Intermittent: rounding mismatch under a parallel test run.",
    },
    "test_bulk_cancel": {
        "component": "orders_api",
        "runs": [
            {"build": 222, "result": "failed"},
            {"build": 221, "result": "failed"},
            {"build": 220, "result": "failed"},
        ],
        "failure_note": "Cancelling more than 50 orders in one call returns HTTP 500.",
    },
}

SKIPPED_SUITES = {
    "payments": [],
    "orders_api": [],
    "frontend": [
        {
            "suite": "e2e",
            "skipped_tests": 20,
            "reason": "Disabled in CI since build 94: the staging environment is unstable.",
        }
    ],
}
