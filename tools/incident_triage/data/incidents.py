"""Mock incident definitions and records."""

from typing import Any, Dict, List, Optional

INCIDENTS: Dict[str, Dict[str, Any]] = {
    "INC-1001": {
        "incident_id": "INC-1001",
        "title": "Checkout API latency degradation and 504 timeouts",
        "service": "checkout",
        "severity": "critical",
        "status": "open",
        "created_at": "2025-05-12T14:15:00Z",
        "reported_by": "datadog-pagerduty-integration",
        "summary": (
            "Checkout API p99 latency spiked from baseline 180ms to 2420ms starting at 14:02 UTC. "
            "Downstream clients report slow order placement and elevated 504 Gateway Timeout errors (4.2%)."
        ),
        "impact": "Customers experiencing stalled checkout flows; conversion rate dropped 35%.",
        "related_alerts": [
            "ALERT-8810: checkout_api_p99_latency > 2000ms",
            "ALERT-8812: checkout_http_504_error_rate > 3%",
        ],
    },
    "INC-1002": {
        "incident_id": "INC-1002",
        "title": "Payments processing elevated HTTP 500 error rate",
        "service": "payments",
        "severity": "critical",
        "status": "open",
        "created_at": "2025-05-12T14:20:00Z",
        "reported_by": "payments-health-monitor",
        "summary": (
            "Payment charge transactions failing with HTTP 500 errors. Transaction success rate dropped "
            "to 81.5% (normal: 99.95%). Error rate stands at 18.5%."
        ),
        "impact": "Direct revenue impact. Credit card and digital wallet settlements failing.",
        "related_alerts": [
            "ALERT-8821: payments_http_500_rate > 10% (current: 18.5%)",
            "ALERT-8825: payments_db_pool_active_connections == 100/100",
        ],
    },
    "INC-1003": {
        "incident_id": "INC-1003",
        "title": "Authentication gateway TLS handshake failures and login errors",
        "service": "auth-gateway",
        "severity": "major",
        "status": "open",
        "created_at": "2025-05-12T14:10:00Z",
        "reported_by": "synthetic-uptime-robot",
        "summary": (
            "Users unable to authenticate via web and mobile clients. Ingress ingress-controller "
            "reporting SSLHandshakeException errors on *.auth.internal.example.com."
        ),
        "impact": "New session logins failing for 45% of traffic. Existing session tokens unaffected.",
        "related_alerts": [
            "ALERT-8799: auth_gateway_tls_handshake_errors > 25%",
            "ALERT-8801: auth_gateway_certificate_expired",
        ],
    },
    "INC-1004": {
        "incident_id": "INC-1004",
        "title": "Search service elevated latency alert (Scheduled Load Test)",
        "service": "search-service",
        "severity": "minor",
        "status": "investigating",
        "created_at": "2025-05-12T14:25:00Z",
        "reported_by": "search-slo-monitor",
        "summary": (
            "Automated alert fired because search-service p95 latency reached 820ms against a 800ms threshold. "
            "Error rate remains 0.0% and no customer impact reported."
        ),
        "impact": "Transient latency elevation during scheduled performance test window (14:00-14:30 UTC).",
        "related_alerts": [
            "ALERT-8830: search_service_p95_latency > 800ms (current: 820ms)",
        ],
    },
}


def get_incident_ids() -> List[str]:
    """Returns a list of all known incident IDs."""
    return list(INCIDENTS.keys())


def get_incident_by_id(incident_id: str) -> Optional[Dict[str, Any]]:
    """Returns incident data for the given incident ID, or None if not found."""
    return INCIDENTS.get(incident_id.upper())


def list_incidents(severity_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns list of open incidents, optionally filtered by severity."""
    results = []
    for inc in INCIDENTS.values():
        if severity_filter:
            if inc["severity"].lower() != severity_filter.lower():
                continue
        results.append(inc)
    return results
