# rr_security (Release Readiness Security specialist)

Collaborator of `release_readiness`. Reports vulnerability evidence only; never decides go or no-go.

| Tool | Purpose |
|---|---|
| `rr_list_cves` | Open CVEs per component (id, severity, package, versions) |
| `rr_get_cve_exposure` | Whether a CVE is dev-only or runtime, shipped, reachable, fixable |

Does not handle: tests, runbooks, rollback, health checks, the release decision.
Limitations: mock static data with invented CVE ids.
