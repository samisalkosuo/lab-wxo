# rr_qa (Release Readiness QA specialist)

Collaborator of `release_readiness`. Reports test evidence only; never decides go or no-go.

| Tool | Purpose |
|---|---|
| `rr_get_test_summary` | Latest build counts and tests with recent failures |
| `rr_get_test_history` | Result of one test across recent builds (consistent vs flaky) |
| `rr_list_skipped_suites` | Skipped or disabled suites and the reason |

Does not handle: CVEs, runbooks, rollback, health checks, the release decision.
Limitations: mock static data.
