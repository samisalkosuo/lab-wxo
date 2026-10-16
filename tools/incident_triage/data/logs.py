"""Mock log streams and log query filter functions."""

from typing import Any, Dict, List, Optional

LOGS: List[Dict[str, Any]] = [
    # --- checkout logs ---
    {
        "timestamp": "2025-05-12T14:02:10Z",
        "service": "checkout",
        "level": "INFO",
        "message": "Checkout deployment v2.14.0 rollout completed across all 6 replicas.",
    },
    {
        "timestamp": "2025-05-12T14:04:22Z",
        "service": "checkout",
        "level": "WARN",
        "message": "Slow query detected in PricingEngine.apply_bundle_discount: query execution time 2150ms (threshold: 200ms).",
    },
    {
        "timestamp": "2025-05-12T14:06:45Z",
        "service": "checkout",
        "level": "WARN",
        "message": "N+1 query pattern detected: executed 18 sequential SELECT queries on cart_items for cart_id=c-98214 in calculate_cart_totals.",
    },
    {
        "timestamp": "2025-05-12T14:08:15Z",
        "service": "checkout",
        "level": "ERROR",
        "message": "Gateway timeout (504): order submission timed out after 2500ms for user=u-44012 on POST /api/v2/checkout/submit.",
    },
    {
        "timestamp": "2025-05-12T14:11:30Z",
        "service": "checkout",
        "level": "ERROR",
        "message": "Downstream client abort: 14 checkout requests aborted by client timeout in the last 60 seconds.",
    },
    {
        "timestamp": "2025-05-12T14:14:05Z",
        "service": "checkout",
        "level": "WARN",
        "message": "Worker thread pool exhaustion warning: 92% of worker threads blocked waiting on cart item price calculations.",
    },

    # --- payments logs ---
    {
        "timestamp": "2025-05-12T14:12:00Z",
        "service": "payments",
        "level": "WARN",
        "message": "Database connection pool utilization reached 90% (90/100 connections active).",
    },
    {
        "timestamp": "2025-05-12T14:15:30Z",
        "service": "payments",
        "level": "ERROR",
        "message": "ConnectionPoolTimeoutException: Timeout waiting for free connection from pool 'payments-db-pool' (active=100/100, max=100, queued=38).",
    },
    {
        "timestamp": "2025-05-12T14:17:10Z",
        "service": "payments",
        "level": "ERROR",
        "message": "Failed to process charge for order_id=ord-88319: Database connection acquisition timed out after 3000ms. Returning HTTP 500.",
    },
    {
        "timestamp": "2025-05-12T14:18:45Z",
        "service": "payments",
        "level": "ERROR",
        "message": "HTTP 500 Internal Server Error returned on endpoint POST /v1/charges (error_code: DB_POOL_EXHAUSTED, queued_threads=45).",
    },
    {
        "timestamp": "2025-05-12T14:21:00Z",
        "service": "payments",
        "level": "ERROR",
        "message": "Transaction settlement failure rate spiked to 18.5%. Connection pool continues to reject new query requests.",
    },

    # --- notification-service logs (red herring for INC-1002) ---
    {
        "timestamp": "2025-05-12T14:05:00Z",
        "service": "notification-service",
        "level": "INFO",
        "message": "Deployment v1.8.0 completed successfully. Batch email workers initialized.",
    },
    {
        "timestamp": "2025-05-12T14:08:00Z",
        "service": "notification-service",
        "level": "INFO",
        "message": "Successfully dispatched 450 email notifications in batch-0921; avg processing latency: 38ms.",
    },
    {
        "timestamp": "2025-05-12T14:15:00Z",
        "service": "notification-service",
        "level": "INFO",
        "message": "Healthcheck OK: memory 180MB/512MB, CPU 12%, error rate 0.0%. No queue backlog.",
    },

    # --- auth-gateway logs ---
    {
        "timestamp": "2025-05-12T14:00:15Z",
        "service": "auth-gateway",
        "level": "WARN",
        "message": "Certificate validation warning: TLS certificate for *.auth.internal.example.com expired at 2025-05-10T00:00:00Z.",
    },
    {
        "timestamp": "2025-05-12T14:05:22Z",
        "service": "auth-gateway",
        "level": "ERROR",
        "message": "SSLHandshakeException: TLS handshake rejected by client 198.51.100.24 (reason: Certificate Expired, serial=4A:91:FF:02).",
    },
    {
        "timestamp": "2025-05-12T14:08:40Z",
        "service": "auth-gateway",
        "level": "ERROR",
        "message": "Ingress router rejecting HTTPS connections on endpoint POST /oauth/token due to invalid/expired TLS certificate.",
    },
    {
        "timestamp": "2025-05-12T14:12:10Z",
        "service": "auth-gateway",
        "level": "ERROR",
        "message": "Authentication failure spike: 45.0% of incoming token negotiation handshakes failed with CERT_DATE_INVALID.",
    },

    # --- search-service logs ---
    {
        "timestamp": "2025-05-12T14:00:00Z",
        "service": "search-service",
        "level": "INFO",
        "message": "Scheduled synthetic load test 'load-test-runner-job-8842' started (target: 5000 QPS, window: 14:00-14:30 UTC).",
    },
    {
        "timestamp": "2025-05-12T14:10:00Z",
        "service": "search-service",
        "level": "INFO",
        "message": "Search throughput: 5120 QPS; search index cache hit ratio: 91.2%; latency p95: 820ms; error count: 0 (0.0%).",
    },
    {
        "timestamp": "2025-05-12T14:22:00Z",
        "service": "search-service",
        "level": "INFO",
        "message": "Synthetic load test job-8842 completing phase 3. Throughput ramping down, latency returning toward baseline 250ms.",
    },

    # --- inventory-db logs ---
    {
        "timestamp": "2025-05-12T14:10:00Z",
        "service": "inventory-db",
        "level": "INFO",
        "message": "PostgreSQL database engine operational. Active server connections: 215 / 500. Replication lag: 12ms.",
    },
]


def query_service_logs(
    service_name: str,
    level: Optional[str] = None,
    search_term: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Filters and returns logs for a service, capped at limit (max 50)."""
    bounded_limit = min(max(limit, 1), 50)
    results = []
    for log in LOGS:
        if log["service"].lower() != service_name.lower():
            continue
        if level and log["level"].upper() != level.upper():
            continue
        if search_term and search_term.lower() not in log["message"].lower():
            continue
        results.append(log)
        if len(results) >= bounded_limit:
            break
    return results
