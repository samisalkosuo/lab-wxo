"""Mock service metrics and summarized metrics query functions."""

from typing import Any, Dict, List, Optional

METRICS: Dict[str, Dict[str, Any]] = {
    "checkout": {
        "latency": {
            "p50_ms": 320,
            "p95_ms": 1850,
            "p99_ms": 2420,
            "baseline_p99_ms": 180,
            "unit": "milliseconds",
            "status": "critical",
            "summary": "p99 latency 2420ms is 13.4x higher than normal baseline (180ms)",
        },
        "error_rate": {
            "current_pct": 4.2,
            "baseline_pct": 0.08,
            "error_type": "HTTP 504 Gateway Timeout",
            "status": "critical",
            "summary": "504 Gateway Timeout rate elevated to 4.2% due to downstream query latency",
        },
        "cpu_usage": {
            "current_pct": 68.4,
            "baseline_pct": 28.0,
            "status": "warning",
            "summary": "CPU utilization elevated due to thread blocking in calculation engine",
        },
        "throughput_qps": {
            "current_qps": 850,
            "baseline_qps": 900,
            "status": "normal",
            "summary": "Incoming request volume is within normal range",
        },
    },
    "payments": {
        "latency": {
            "p50_ms": 480,
            "p95_ms": 2200,
            "p99_ms": 3100,
            "baseline_p99_ms": 220,
            "unit": "milliseconds",
            "status": "critical",
            "summary": "p99 latency 3100ms is 14.1x higher than baseline (220ms) due to pool queue timeouts",
        },
        "error_rate": {
            "current_pct": 18.5,
            "baseline_pct": 0.05,
            "error_type": "HTTP 500 Internal Server Error (DB_POOL_EXHAUSTED)",
            "status": "critical",
            "summary": "Error rate is 18.5% with transaction failures caused by connection exhaustion",
        },
        "db_connections": {
            "active_connections": 100,
            "max_pool_size": 100,
            "pool_saturation_pct": 100.0,
            "queued_requests": 45,
            "status": "critical",
            "summary": "Database connection pool is 100% saturated (100/100 active connections, 45 queued)",
        },
        "cpu_usage": {
            "current_pct": 42.0,
            "baseline_pct": 35.0,
            "status": "normal",
            "summary": "CPU utilization is normal",
        },
    },
    "auth-gateway": {
        "error_rate": {
            "current_pct": 45.0,
            "baseline_pct": 0.10,
            "error_type": "TLS Handshake Rejection / SSLHandshakeException",
            "status": "critical",
            "summary": "45.0% of client TLS handshakes are failing due to expired certificate",
        },
        "tls_certificate": {
            "domain": "*.auth.internal.example.com",
            "days_remaining": -2,
            "status": "EXPIRED",
            "summary": "Certificate expired 2 days ago (2025-05-10T00:00:00Z)",
        },
        "throughput_qps": {
            "current_qps": 320,
            "baseline_qps": 580,
            "status": "degraded",
            "summary": "Throughput depressed due to connection rejections at ingress",
        },
    },
    "search-service": {
        "latency": {
            "p50_ms": 120,
            "p95_ms": 820,
            "p99_ms": 940,
            "baseline_p95_ms": 250,
            "unit": "milliseconds",
            "status": "elevated_transient",
            "summary": "p95 latency is 820ms (baseline 250ms) during active 5000 QPS load test",
        },
        "error_rate": {
            "current_pct": 0.0,
            "baseline_pct": 0.0,
            "status": "normal",
            "summary": "Error rate is 0.0% (all queries succeeding despite load)",
        },
        "throughput_qps": {
            "current_qps": 5120,
            "baseline_qps": 400,
            "status": "high_load",
            "summary": "Traffic elevated by scheduled synthetic load test job-8842 (14:00-14:30 UTC)",
        },
        "cpu_usage": {
            "current_pct": 72.0,
            "baseline_pct": 22.0,
            "status": "elevated_transient",
            "summary": "CPU utilization elevated as expected during load test run",
        },
    },
    "notification-service": {
        "latency": {
            "p50_ms": 15,
            "p95_ms": 42,
            "p99_ms": 68,
            "baseline_p95_ms": 40,
            "unit": "milliseconds",
            "status": "normal",
            "summary": "Latency is normal across all percentiles",
        },
        "error_rate": {
            "current_pct": 0.0,
            "baseline_pct": 0.0,
            "status": "normal",
            "summary": "Error rate is 0.0%",
        },
        "cpu_usage": {
            "current_pct": 12.0,
            "baseline_pct": 10.0,
            "status": "normal",
            "summary": "CPU utilization is normal",
        },
    },
    "inventory-db": {
        "cpu_usage": {
            "current_pct": 34.0,
            "baseline_pct": 30.0,
            "status": "normal",
            "summary": "Database CPU is healthy",
        },
        "db_connections": {
            "active_connections": 215,
            "max_connections": 500,
            "saturation_pct": 43.0,
            "status": "normal",
            "summary": "Database server connections healthy (215/500 active)",
        },
    },
}


def get_service_metrics(service_name: str, metric_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Returns metrics for a service, optionally filtered by metric_name."""
    svc_metrics = METRICS.get(service_name.lower())
    if not svc_metrics:
        return None
    if metric_name:
        if metric_name.lower() in svc_metrics:
            return {metric_name.lower(): svc_metrics[metric_name.lower()]}
        return None
    return svc_metrics
