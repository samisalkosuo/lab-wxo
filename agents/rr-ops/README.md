# rr_ops (Release Readiness Operations specialist)

Collaborator of `release_readiness`. Reports operational evidence only; never decides go or no-go.

| Tool | Purpose |
|---|---|
| `rr_check_runbook` | Service tier, runbook id, rollback procedure, canary |
| `rr_get_last_health_check` | Latest health check with its age in days |

Does not handle: tests, CVEs, the release decision, whether a health check is "too old" (the policy decides).
Limitations: mock static data (fixed "today" 2025-09-15).
