"""Release readiness tools for watsonx Orchestrate (QA, Security and Operations specialists).

All tools are read-only and deterministic over the static mock release `rel-2025-q3`. Each
specialist agent lists only its own tools in its agent.yaml; no tool here changes state.
Every tool takes a `scope`: one component name, or the release id (all components).
"""

import json
from typing import Optional

from ibm_watsonx_orchestrate.agent_builder.tools import tool

try:
    from .data import cve_records, deployment_health, releases, runbooks_index, test_results
except ImportError:
    from data import cve_records, deployment_health, releases, runbooks_index, test_results


def _error(code: str, message: str, hint: str) -> str:
    return json.dumps(
        {"status": "error", "error_code": code, "message": message, "hint": hint}, indent=2
    )


def _components_in(scope: str) -> Optional[list]:
    """Components for a component name or a release id; None when the scope is unknown."""
    key = (scope or "").strip().lower()
    release = releases.get_release(key)
    if release:
        return list(release["components"])
    all_components = releases.RELEASES["rel-2025-q3"]["components"]
    return [key] if key in all_components else None


def _bad_scope(scope: str) -> str:
    known = ", ".join(releases.RELEASES["rel-2025-q3"]["components"])
    return _error(
        "UNKNOWN_SCOPE",
        f"Unknown component or release '{scope}'.",
        f"Use a release id (rel-2025-q3) or one component: {known}.",
    )


def _age_days(iso_date: str) -> int:
    from datetime import date

    return (date.fromisoformat(releases.AS_OF) - date.fromisoformat(iso_date)).days


# ---------------------------------------------------------------------------
# QA tools
# ---------------------------------------------------------------------------
@tool
def rr_get_test_summary(scope: str) -> str:
    """Summarizes the latest CI test results for a component, or for every component of a release.

    Use this first for any QA question. It returns the newest build per component with pass,
    fail and skip counts, plus the names of tests that failed in recent builds.

    Args:
        scope (str): A component name ('payments', 'orders_api', 'frontend') or a release id ('rel-2025-q3').

    Returns:
        str: JSON with, per component, the latest build, counts, how many of the recent builds had failures, and failing test names.
    """
    components = _components_in(scope)
    if components is None:
        return _bad_scope(scope)
    result = []
    for name in components:
        builds = test_results.BUILDS[name]
        latest = builds[0]
        failing = sorted(
            t for t, h in test_results.TEST_HISTORY.items()
            if h["component"] == name
        )
        result.append(
            {
                "component": name,
                "latest_build": latest["build"],
                "date": latest["date"],
                "total": latest["total"],
                "passed": latest["passed"],
                "failed": latest["failed"],
                "skipped": latest["skipped"],
                "builds_considered": len(builds),
                "builds_with_failures": sum(1 for b in builds if b["failed"] > 0),
                "tests_with_recent_failures": failing,
            }
        )
    return json.dumps({"status": "ok", "release": "rel-2025-q3", "components": result}, indent=2)


@tool
def rr_get_test_history(test_id: str) -> str:
    """Shows how one test did across the recent builds, to tell a consistent failure from a flaky one.

    Use this for every test name returned by rr_get_test_summary as having recent failures.

    Args:
        test_id (str): The test name, for example 'test_bulk_cancel'.

    Returns:
        str: JSON with the component, the result per build (newest first), and a failure note.
    """
    history = test_results.TEST_HISTORY.get((test_id or "").strip())
    if not history:
        known = ", ".join(sorted(test_results.TEST_HISTORY))
        return _error(
            "UNKNOWN_TEST",
            f"No history for test '{test_id}'.",
            f"Only tests with recent failures have history. Known: {known}.",
        )
    runs = history["runs"]
    failed = sum(1 for r in runs if r["result"] == "failed")
    return json.dumps(
        {
            "status": "ok",
            "test_id": test_id,
            "component": history["component"],
            "runs": runs,
            "failed_runs": failed,
            "total_runs": len(runs),
            "latest_result": runs[0]["result"],
            "failure_note": history["failure_note"],
        },
        indent=2,
    )


@tool
def rr_list_skipped_suites(scope: str) -> str:
    """Lists test suites that are skipped or disabled for a component, or for every component of a release.

    Use this when QA must confirm that a passing result is not hiding disabled coverage.

    Args:
        scope (str): A component name ('payments', 'orders_api', 'frontend') or a release id ('rel-2025-q3').

    Returns:
        str: JSON with, per component, the skipped suites, test counts, and the reason.
    """
    components = _components_in(scope)
    if components is None:
        return _bad_scope(scope)
    result = [
        {"component": c, "skipped_suites": test_results.SKIPPED_SUITES[c]} for c in components
    ]
    return json.dumps({"status": "ok", "components": result}, indent=2)


# ---------------------------------------------------------------------------
# Security tools
# ---------------------------------------------------------------------------
@tool
def rr_list_cves(scope: str) -> str:
    """Lists open CVE findings for a component, or for every component of a release.

    Use this first for any security question. It does not say whether a CVE can be exploited;
    call rr_get_cve_exposure for each CVE found.

    Args:
        scope (str): A component name ('payments', 'orders_api', 'frontend') or a release id ('rel-2025-q3').

    Returns:
        str: JSON with, per component, the open CVEs (id, severity, package, installed and fixed version).
    """
    components = _components_in(scope)
    if components is None:
        return _bad_scope(scope)
    result = [{"component": c, "open_cves": cve_records.CVES[c]} for c in components]
    return json.dumps({"status": "ok", "components": result}, indent=2)


@tool
def rr_get_cve_exposure(cve_id: str, component: str) -> str:
    """Tells whether a CVE actually affects the shipped release of a component.

    Use this for each CVE returned by rr_list_cves before calling it a blocker: a CVE in a
    dev-only dependency that is not in the production artifact is not reachable at runtime.

    Args:
        cve_id (str): The CVE identifier, for example 'CVE-2025-90011'.
        component (str): One component name ('payments', 'orders_api', 'frontend').

    Returns:
        str: JSON with dependency scope, whether it ships in the artifact, whether it is reachable at runtime, and whether a fix exists.
    """
    key = ((cve_id or "").strip().upper(), (component or "").strip().lower())
    exposure = cve_records.EXPOSURE.get(key)
    if not exposure:
        return _error(
            "NO_EXPOSURE_RECORD",
            f"No exposure record for {cve_id} in component '{component}'.",
            "Call rr_list_cves first and pass a CVE id together with the component it was listed under.",
        )
    return json.dumps(
        {"status": "ok", "cve_id": key[0], "component": key[1], **exposure}, indent=2
    )


# ---------------------------------------------------------------------------
# Operations tools
# ---------------------------------------------------------------------------
@tool
def rr_check_runbook(scope: str) -> str:
    """Checks operational readiness documents for a component, or for every component of a release.

    Use this for any question about runbooks, rollback procedures or canary deployment.

    Args:
        scope (str): A component name ('payments', 'orders_api', 'frontend') or a release id ('rel-2025-q3').

    Returns:
        str: JSON with, per component, the service tier, runbook id (null if missing), whether a rollback procedure exists, and whether a canary is configured.
    """
    components = _components_in(scope)
    if components is None:
        return _bad_scope(scope)
    result = [{"component": c, **runbooks_index.RUNBOOKS[c]} for c in components]
    return json.dumps({"status": "ok", "components": result}, indent=2)


@tool
def rr_get_last_health_check(scope: str) -> str:
    """Returns the most recent production health check for a component, or for every component of a release.

    Use this to confirm that health evidence is recent enough to rely on.

    Args:
        scope (str): A component name ('payments', 'orders_api', 'frontend') or a release id ('rel-2025-q3').

    Returns:
        str: JSON with, per component, the date, status, error rate, and the age of the check in days.
    """
    components = _components_in(scope)
    if components is None:
        return _bad_scope(scope)
    result = []
    for c in components:
        check = deployment_health.HEALTH_CHECKS[c]
        result.append({"component": c, **check, "age_days": _age_days(check["checked_on"])})
    return json.dumps({"status": "ok", "as_of": releases.AS_OF, "components": result}, indent=2)
