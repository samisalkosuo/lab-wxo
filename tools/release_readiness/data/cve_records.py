"""Mock security data. CVE ids are invented (the 9xxxx range) and do not refer to real issues.

Planted facts
  payments   : CVE-2025-90011 is HIGH severity but sits in a dev-only test dependency that is
               NOT in the shipped artifact (RED HERRING, not a blocker).
  orders_api : no open CVEs.
  frontend   : CVE-2025-90022 is HIGH, in a runtime dependency, reachable, fix available (BLOCKER).
"""

CVES = {
    "payments": [
        {
            "cve_id": "CVE-2025-90011",
            "severity": "high",
            "package": "mock-test-utils",
            "installed_version": "3.2.0",
            "fixed_version": "3.2.4",
        }
    ],
    "orders_api": [],
    "frontend": [
        {
            "cve_id": "CVE-2025-90022",
            "severity": "high",
            "package": "ui-markdown-render",
            "installed_version": "4.1.0",
            "fixed_version": "4.1.3",
        }
    ],
}

# Exposure facts per (cve_id, component).
EXPOSURE = {
    ("CVE-2025-90011", "payments"): {
        "dependency_scope": "dev_only",
        "shipped_in_artifact": False,
        "reachable_at_runtime": False,
        "fix_available": True,
        "note": "Used only by the test harness; excluded from the production build.",
    },
    ("CVE-2025-90022", "frontend"): {
        "dependency_scope": "runtime",
        "shipped_in_artifact": True,
        "reachable_at_runtime": True,
        "fix_available": True,
        "note": "Renders user-supplied markdown in the order notes page.",
    },
}
