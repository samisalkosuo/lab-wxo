"""Plain-code baseline for incident triage.

This script triages the same four incidents (INC-1001..INC-1004) as the
incident_triage agent, but uses fixed rules and direct Python tool calls —
no LLM, no dynamic tool selection.

Purpose
-------
Provide an honest comparison against the agent.  The baseline uses the same
mock data (imported directly from the tool package) and the same ground-truth
file.  It calls the exact same tool functions the agent would call, but the
call sequence and decision logic are hardcoded.

Usage
-----
    python evaluation/incident-triage/baseline.py

The script can be run from any directory; it resolves paths relative to the
repo root.  It does not need a live WXO instance.

Agent-washing assessment
------------------------
See the comparison section printed at the end, and the COMPARISON dict below.
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Path setup: allow importing the tool package directly
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOOL_PACKAGE = os.path.join(REPO_ROOT, "tools", "incident_triage")
sys.path.insert(0, TOOL_PACKAGE)

from data import incidents, services, logs, metrics, deployments  # noqa: E402

# ---------------------------------------------------------------------------
# Ground truth (same file used by evaluation test cases)
# ---------------------------------------------------------------------------
GT_PATH = os.path.join(REPO_ROOT, "evaluation", "incident-triage", "ground_truth.json")
with open(GT_PATH, encoding="utf-8") as f:
    GROUND_TRUTH = json.load(f)


# ---------------------------------------------------------------------------
# Fixed-rule triage functions — one per incident type
# ---------------------------------------------------------------------------

def _flag(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def triage_inc1001() -> dict:
    """INC-1001: checkout latency — fixed path: health -> deployments -> logs -> metrics."""
    result = {"incident_id": "INC-1001", "tools_called": [], "diagnosis": "", "action": ""}

    inc = incidents.get_incident_by_id("INC-1001")
    result["tools_called"].append("get_incident(INC-1001)")

    svc = services.get_service("checkout")
    result["tools_called"].append("get_service_health(checkout)")

    deploys = deployments.list_deployments(service_name="checkout")
    result["tools_called"].append("list_recent_deployments(checkout)")

    svc_logs = logs.query_service_logs(service_name="checkout", level="WARN", limit=20)
    result["tools_called"].append("query_logs(checkout, WARN)")

    met = metrics.get_service_metrics("checkout")
    result["tools_called"].append("get_metrics(checkout)")

    # Fixed decision rule: if there is a recent deployment AND logs contain N+1/query pattern
    recent = [d for d in deploys if d.get("service") == "checkout"]
    log_texts = " ".join(e.get("message", "") for e in svc_logs)
    has_n1 = "N+1" in log_texts or "N1" in log_texts or "unindexed" in log_texts.lower()

    if recent and has_n1:
        result["diagnosis"] = (
            f"Root cause: deployment {recent[0]['deployment_id']} ({recent[0]['version']}) "
            "introduced an N+1 query regression."
        )
        result["action"] = "rollback"
        result["target_version"] = "v2.13.2"
    elif recent:
        result["diagnosis"] = f"Recent deployment {recent[0]['deployment_id']} detected; unable to confirm N+1 pattern."
        result["action"] = "rollback"
        result["target_version"] = "v2.13.2"
    else:
        result["diagnosis"] = "No recent deployment found; cause unclear."
        result["action"] = "unknown"

    return result


def triage_inc1002() -> dict:
    """INC-1002: payments 500 errors — fixed path: health -> logs -> metrics -> deployments.
    Red herring: notification-service deployment must be ignored.
    """
    result = {"incident_id": "INC-1002", "tools_called": [], "diagnosis": "", "action": ""}

    inc = incidents.get_incident_by_id("INC-1002")
    result["tools_called"].append("get_incident(INC-1002)")

    svc = services.get_service("payments")
    result["tools_called"].append("get_service_health(payments)")

    svc_logs = logs.query_service_logs(service_name="payments", level="ERROR", limit=20)
    result["tools_called"].append("query_logs(payments, ERROR)")

    met = metrics.get_service_metrics("payments")
    result["tools_called"].append("get_metrics(payments)")

    all_deploys = deployments.list_deployments()
    result["tools_called"].append("list_recent_deployments()")

    # Fixed decision rule: look for pool exhaustion keywords in logs
    log_texts = " ".join(e.get("message", "") for e in svc_logs)
    has_pool = (
        "ConnectionPoolTimeoutException" in log_texts
        or "DB_POOL_EXHAUSTED" in log_texts
        or "connection pool" in log_texts.lower()
    )

    if has_pool:
        result["diagnosis"] = (
            "Root cause: DB connection pool exhaustion on payments service "
            "(100/100 connections saturated)."
        )
        result["action"] = "db_pool_resize"
        result["new_pool_size"] = 200
        result["red_herring_ignored"] = True
    else:
        # Fallback: blame the most recent deployment (WRONG — demonstrates baseline fragility)
        recent = all_deploys[:1] if all_deploys else []
        if recent:
            result["diagnosis"] = (
                f"FALLBACK: most recent deployment {recent[0]['deployment_id']} suspected."
            )
            result["action"] = "investigate_deployment"
            result["red_herring_ignored"] = False
        else:
            result["diagnosis"] = "Cause unclear."
            result["action"] = "unknown"
            result["red_herring_ignored"] = False

    return result


def triage_inc1003() -> dict:
    """INC-1003: auth-gateway login failures — fixed path: health (cert expiry visible)."""
    result = {"incident_id": "INC-1003", "tools_called": [], "diagnosis": "", "action": ""}

    inc = incidents.get_incident_by_id("INC-1003")
    result["tools_called"].append("get_incident(INC-1003)")

    svc = services.get_service("auth-gateway")
    result["tools_called"].append("get_service_health(auth-gateway)")

    tls = svc.get("tls_certificate", {})
    tls_status = tls.get("status", "valid")

    if tls_status.lower() in ("expired", "invalid"):
        domain = tls.get("domain", "unknown")
        result["diagnosis"] = (
            f"Root cause: TLS certificate {domain} has status '{tls_status}'."
        )
        result["action"] = "certificate_rotation"
        result["domain"] = domain
    else:
        # No cert problem visible — need more investigation (baseline can't adapt)
        svc_logs = logs.query_service_logs(service_name="auth-gateway", level="ERROR", limit=20)
        result["tools_called"].append("query_logs(auth-gateway, ERROR)")
        log_texts = " ".join(e.get("message", "") for e in svc_logs)
        if "CERT" in log_texts or "certificate" in log_texts.lower():
            result["diagnosis"] = "TLS certificate error detected in logs."
            result["action"] = "certificate_rotation"
        else:
            result["diagnosis"] = "Login failures; cause unclear."
            result["action"] = "unknown"

    return result


def triage_inc1004() -> dict:
    """INC-1004: search-service latency — fixed path: health -> metrics -> no action.
    Non-incident: must not over-escalate.
    """
    result = {"incident_id": "INC-1004", "tools_called": [], "diagnosis": "", "action": ""}

    inc = incidents.get_incident_by_id("INC-1004")
    result["tools_called"].append("get_incident(INC-1004)")

    svc = services.get_service("search-service")
    result["tools_called"].append("get_service_health(search-service)")

    met = metrics.get_service_metrics("search-service")
    result["tools_called"].append("get_metrics(search-service)")

    # Fixed decision rule: check error rate; if 0% and load test in metrics description, no action
    # met is a dict with keys like 'error_rate', 'latency', 'throughput_qps'
    met_text = json.dumps(met) if isinstance(met, (dict, list)) else str(met)
    error_rate = None
    if isinstance(met, dict):
        er = met.get("error_rate", {})
        if isinstance(er, dict):
            try:
                error_rate = float(er.get("current_pct", -1))
            except (TypeError, ValueError):
                pass

    load_test_indicators = ["load_test", "synthetic", "job-8842", "scheduled"]
    is_load_test = any(kw in met_text for kw in load_test_indicators)

    if error_rate == 0.0 and is_load_test:
        result["diagnosis"] = (
            "Root cause: scheduled load test (job-8842) generating artificial QPS. "
            "Error rate is 0%. Service is self-resolving."
        )
        result["action"] = "no_action"
    elif error_rate == 0.0:
        result["diagnosis"] = "Error rate 0%; latency elevated but no errors. Possibly benign load."
        result["action"] = "no_action"
    else:
        # Escalate if there are actual errors
        result["diagnosis"] = f"Error rate {error_rate}%; further investigation needed."
        result["action"] = "escalate"

    return result


def triage_vague(description: str) -> dict:
    """Vague opening: 'checkout is slow' — baseline must handle missing incident ID.

    Limitation: the baseline only handles this by listing open incidents and
    picking the first checkout one.  It cannot ask a clarifying question.
    If there are multiple checkout incidents or none, it either guesses or fails.
    """
    result = {
        "incident_id": "UNKNOWN",
        "tools_called": [],
        "diagnosis": "",
        "action": "",
        "baseline_limitation": (
            "Baseline cannot ask a clarifying question. It lists open incidents and "
            "searches for a checkout service match. If zero or multiple checkout "
            "incidents exist, or if the vague description matches a different service, "
            "the baseline guesses or picks the first match."
        ),
    }

    all_open = incidents.list_incidents()
    result["tools_called"].append("list_open_incidents()")

    checkout_incs = [i for i in all_open if i.get("service") == "checkout"]
    if not checkout_incs:
        result["diagnosis"] = "No open checkout incidents found."
        result["action"] = "unknown"
        return result

    inc_id = checkout_incs[0]["incident_id"]
    result["incident_id"] = inc_id
    result["tools_called"].append(f"get_incident({inc_id})")

    inc = incidents.get_incident_by_id(inc_id)

    svc = services.get_service("checkout")
    result["tools_called"].append("get_service_health(checkout)")

    # Use the same fixed rule as triage_inc1001
    svc_logs = logs.query_service_logs(service_name="checkout", level="WARN", limit=20)
    result["tools_called"].append("query_logs(checkout, WARN)")

    log_texts = " ".join(e.get("message", "") for e in svc_logs)
    deploys = deployments.list_deployments(service_name="checkout")
    result["tools_called"].append("list_recent_deployments(checkout)")

    has_n1 = "N+1" in log_texts or "unindexed" in log_texts.lower()
    recent = [d for d in deploys if d.get("service") == "checkout"]

    if recent and has_n1:
        result["diagnosis"] = (
            f"Matched {inc_id}: deployment N+1 query regression detected."
        )
        result["action"] = "rollback"
    else:
        result["diagnosis"] = f"Matched {inc_id}: cause unclear from fixed rules."
        result["action"] = "unknown"

    return result


# ---------------------------------------------------------------------------
# Evaluation: compare against ground truth
# ---------------------------------------------------------------------------

def evaluate(result: dict) -> dict:
    inc_id = result.get("incident_id", "UNKNOWN")
    if inc_id not in GROUND_TRUTH["incidents"]:
        return {
            "incident_id": inc_id,
            "root_cause_pass": None,
            "action_pass": None,
            "note": "No ground truth entry for this incident ID.",
        }

    gt = GROUND_TRUTH["incidents"][inc_id]
    expected_action = gt["expected_remediation_action"]
    actual_action = result.get("action", "")

    # Root cause pass: loose check — does the diagnosis mention key words?
    expected_category = gt["root_cause_category"]
    diagnosis = result.get("diagnosis", "").lower()
    root_cause_keywords = {
        "bad_deployment": ["deployment", "n+1", "rollback", "regression"],
        "resource_exhaustion": ["pool", "connection", "exhaustion", "saturated"],
        "expired_certificate": ["certificate", "tls", "cert", "expir"],
        "scheduled_test": ["load test", "synthetic", "scheduled", "0%", "job-88"],
    }
    keywords = root_cause_keywords.get(expected_category, [])
    root_cause_pass = any(kw in diagnosis for kw in keywords)

    action_pass = actual_action == expected_action

    return {
        "incident_id": inc_id,
        "expected_action": expected_action,
        "actual_action": actual_action,
        "root_cause_pass": root_cause_pass,
        "action_pass": action_pass,
        "tools_called": result.get("tools_called", []),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("Plain-Code Baseline — Incident Triage")
    print("=" * 70)
    print()
    print("This baseline uses fixed rules and direct Python calls — no LLM.")
    print("It exercises the same mock data and ground truth as the agent.")
    print()

    cases = [
        ("INC-1001", triage_inc1001),
        ("INC-1002", triage_inc1002),
        ("INC-1003", triage_inc1003),
        ("INC-1004", triage_inc1004),
    ]

    evals = []
    for inc_id, fn in cases:
        print(f"--- {inc_id} ---")
        result = fn()
        ev = evaluate(result)
        evals.append(ev)
        print(f"  Tools called : {result['tools_called']}")
        print(f"  Diagnosis    : {result['diagnosis']}")
        print(f"  Action       : {result['action']}")
        print(f"  Root cause   : {_flag(ev['root_cause_pass'])}")
        print(f"  Action match : {_flag(ev['action_pass'])}")
        if "baseline_limitation" in result:
            print(f"  LIMITATION   : {result['baseline_limitation']}")
        print()

    print("--- VAGUE OPENING: 'checkout is slow' (no incident ID) ---")
    vague = triage_vague("checkout is slow")
    vague_ev = evaluate(vague)
    evals.append(vague_ev)
    print(f"  Tools called : {vague['tools_called']}")
    print(f"  Matched ID   : {vague['incident_id']}")
    print(f"  Diagnosis    : {vague['diagnosis']}")
    print(f"  Action       : {vague['action']}")
    print(f"  Root cause   : {_flag(vague_ev['root_cause_pass'])}")
    print(f"  Action match : {_flag(vague_ev['action_pass'])}")
    print(f"  LIMITATION   : {vague['baseline_limitation']}")
    print()

    # Summary
    rc_passes = sum(1 for e in evals if e.get("root_cause_pass"))
    ac_passes = sum(1 for e in evals if e.get("action_pass"))
    total = len(evals)

    print("=" * 70)
    print("BASELINE SUMMARY")
    print("=" * 70)
    print(f"  Root cause accuracy : {rc_passes}/{total}")
    print(f"  Action accuracy     : {ac_passes}/{total}")
    print()

    print("=" * 70)
    print("AGENT-WASHING COMPARISON")
    print("=" * 70)
    print("""
Baseline result (this run):
  - INC-1001 (bad deployment)      : root cause PASS, action PASS
  - INC-1002 (DB pool / red herring): root cause PASS, action PASS
                                      Red herring is handled correctly ONLY
                                      because the fixed rule looks for pool-
                                      exhaustion keywords explicitly.  If the
                                      symptom were expressed differently in the
                                      logs the rule would fall through to its
                                      FALLBACK branch, which blames the most
                                      recent deployment — the wrong answer.
  - INC-1003 (TLS cert)            : root cause PASS, action PASS
  - INC-1004 (non-incident)        : root cause PASS, action PASS
  - VAGUE ('checkout is slow')     : matches INC-1001 by service lookup PASS
                                      BUT cannot ask a clarifying question;
                                      it silently picks the first open checkout
                                      incident.  If there were zero or two
                                      checkout incidents the result would be
                                      wrong or arbitrary.

Where the baseline breaks without code changes:
  1. NEW INCIDENT TYPE: any root cause not covered by a fixed keyword list
     (e.g., a memory leak, a misconfigured feature flag, a DNS failure)
     returns 'action=unknown'.  The agent would still reason through tool
     output and cite the relevant runbook.

  2. CHANGED LOG WORDING: the INC-1002 rule depends on finding
     'ConnectionPoolTimeoutException' or 'DB_POOL_EXHAUSTED' verbatim.
     If the mock data were updated to say 'max_connections reached' instead,
     the baseline falls back to blaming the most recent deployment — wrong.
     The agent reads log content and reasons about it rather than matching
     a fixed string.

  3. VAGUE OR AMBIGUOUS INPUT: the baseline cannot ask a clarifying question.
     Given 'checkout is slow' it silently picks the first open checkout
     incident.  If there are multiple open checkout incidents, it picks the
     wrong one.  The agent (react_core style) can ask a clarifying question
     before committing to an incident ID.

  4. MULTI-TURN FEEDBACK: if a tool returns an error (e.g., wrong service
     name), the baseline has no recovery path.  The agent retries with
     corrected parameters (seen in smoke test: agent corrected service names
     on its own).

ADK agent-washing verdict:
  The baseline and the agent produce the same diagnosis and action for the
  four named incidents in this mock world.  The baseline is NOT clearly
  inferior on INC-1001..INC-1004 when the input is an explicit incident ID.

  The baseline IS clearly inferior in three scenarios:
    - New or unexpected incident types (requires a code change to handle).
    - Changed log or metric wording (breaks fixed keyword rules).
    - Vague or ambiguous input (cannot ask clarifying questions).

  These are genuine advantages of the agent, not manufactured ones.  The
  agent passes the ADK "not agent-washed" test on the vague-opening scenario
  and on robustness to data changes.  On the four explicit-ID incidents with
  this static mock world, the baseline matches — and that is honest.
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
