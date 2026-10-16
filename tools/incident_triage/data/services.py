"""Mock service catalog and health status definitions."""

from typing import Any, Dict, List, Optional

SERVICES: Dict[str, Dict[str, Any]] = {
    "checkout": {
        "service_name": "checkout",
        "display_name": "Checkout API Service",
        "tier": "tier-1",
        "owner": "team-checkout",
        "status": "degraded",
        "uptime_pct": 98.2,
        "dependencies": ["payments", "inventory-db"],
        "active_alerts": [
            "Checkout API p99 latency > 2000ms (Current: 2420ms)",
            "Elevated 504 Gateway Timeout rate (4.2%)",
        ],
        "tls_certificate": {
            "domain": "*.checkout.internal.example.com",
            "status": "valid",
            "expires_at": "2026-01-15T00:00:00Z",
            "days_until_expiration": 248,
        },
    },
    "payments": {
        "service_name": "payments",
        "display_name": "Payment Processing Service",
        "tier": "tier-1",
        "owner": "team-payments",
        "status": "failing",
        "uptime_pct": 91.5,
        "dependencies": ["inventory-db"],
        "active_alerts": [
            "Payment Processing HTTP 500 error rate > 10% (Current: 18.5%)",
            "Database connection pool saturation (100/100 connections active)",
        ],
        "tls_certificate": {
            "domain": "*.payments.internal.example.com",
            "status": "valid",
            "expires_at": "2025-11-20T00:00:00Z",
            "days_until_expiration": 192,
        },
    },
    "auth-gateway": {
        "service_name": "auth-gateway",
        "display_name": "Authentication & Ingress Gateway",
        "tier": "tier-1",
        "owner": "team-security-infra",
        "status": "degraded",
        "uptime_pct": 94.1,
        "dependencies": [],
        "active_alerts": [
            "TLS handshake failures on auth endpoints (45.0% error rate)",
            "Certificate validation expired for *.auth.internal.example.com",
        ],
        "tls_certificate": {
            "domain": "*.auth.internal.example.com",
            "status": "EXPIRED",
            "expires_at": "2025-05-10T00:00:00Z",
            "days_until_expiration": -2,
        },
    },
    "search-service": {
        "service_name": "search-service",
        "display_name": "Product Search & Catalog Indexer",
        "tier": "tier-2",
        "owner": "team-search",
        "status": "healthy",
        "uptime_pct": 99.9,
        "dependencies": ["inventory-db"],
        "active_alerts": [
            "Transient latency alert: search-service p95 latency > 800ms (Current: 820ms, scheduled load test)",
        ],
        "tls_certificate": {
            "domain": "*.search.internal.example.com",
            "status": "valid",
            "expires_at": "2025-12-01T00:00:00Z",
            "days_until_expiration": 203,
        },
    },
    "notification-service": {
        "service_name": "notification-service",
        "display_name": "Customer Notification & Email Dispatcher",
        "tier": "tier-3",
        "owner": "team-growth",
        "status": "healthy",
        "uptime_pct": 99.98,
        "dependencies": [],
        "active_alerts": [],
        "tls_certificate": {
            "domain": "*.notifications.internal.example.com",
            "status": "valid",
            "expires_at": "2026-03-01T00:00:00Z",
            "days_until_expiration": 293,
        },
    },
    "inventory-db": {
        "service_name": "inventory-db",
        "display_name": "Core Inventory & Data Store",
        "tier": "tier-1",
        "owner": "team-dba",
        "status": "healthy",
        "uptime_pct": 99.95,
        "dependencies": [],
        "active_alerts": [],
        "tls_certificate": {
            "domain": "*.db.internal.example.com",
            "status": "valid",
            "expires_at": "2026-06-30T00:00:00Z",
            "days_until_expiration": 414,
        },
    },
}


def get_service_names() -> List[str]:
    """Returns a list of all known service names."""
    return list(SERVICES.keys())


def get_service(service_name: str) -> Optional[Dict[str, Any]]:
    """Returns service information for the given service name, or None if not found."""
    return SERVICES.get(service_name)
