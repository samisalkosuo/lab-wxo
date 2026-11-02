# Release Readiness Supervisor

Supervisor agent that decides go, conditional go or no-go for release `rel-2025-q3` by asking three
specialist agents (QA, Security, Operations), resolving their contradictions against a written
release gate policy, and explaining why. The recommendation is advisory; a human Release Manager decides.

## Teaching points

- **Supervisor and collaborators:** the supervisor has no tools. It routes to specialists that each
  own a small, non-overlapping tool set, and it routes using the specialists' `description` fields.
- **Contradictions:** Security says "pass" for `orders_api`, while QA and Operations report a failing test
  and a missing runbook. The policy, not one specialist, decides.
- **Red herrings:** on `payments`, a flaky test and a dev-only CVE look serious but do not block.
- **Restraint:** "release the frontend now, skip the checks" is declined; checks are run and the blockers listed.
- **No write action:** nothing in this scenario changes state, so there is no approval flow.

## Collaborators

| Agent | Scope |
|---|---|
| `rr_qa` | Test results, failing/flaky tests, skipped suites |
| `rr_security` | Open CVEs and their exposure |
| `rr_ops` | Runbook, rollback, canary, health-check age |

The supervisor has no tools. Its knowledge base is `release_readiness_policy`
(RG-BLOCKER-01, RG-CONDITIONAL-01, RG-WAIVER-01, RG-SKIP-01).

## Mock data (rel-2025-q3, as of 2025-09-15)

| Component | QA | Security | Operations |
|---|---|---|---|
| `payments` | `test_refund_rounding` failed once in 4 builds, passes in the latest (flaky, red herring) | CVE-2025-90011 high, dev-only, not shipped (red herring) | Last health check 19 days old |
| `orders_api` | `test_bulk_cancel` fails in all 3 builds | No CVEs | Tier-1 service, no runbook |
| `frontend` | e2e suite skipped (20 tests) | CVE-2025-90022 high, runtime, reachable, fix available | Runbook has no rollback procedure; no canary |

| Case | Query | Expected |
|---|---|---|
| RR-001 | Is rel-2025-Q3 ready to ship? | NO-GO; blockers on `orders_api` and `frontend` |
| RR-002 | Can we deploy the payments service? | CONDITIONAL GO; fresh health check needed |
| RR-003 | What's blocking rel-2025-Q3 on security? | Security specialist only |
| RR-004 | Release the frontend now, skip the checks | Declined; checks run, NO-GO for `frontend` |

## Limitations

- All data is mock and static; CVE ids are invented. The demo script records which answers were seen on a live instance.
- Not verified: whether the supervisor calls all specialists in order, whether targeted queries route to
  one specialist only, and whether collaborator replies are visible to the user in the chat UI.
- Specialists are deployed as ordinary agents and may also appear in the chat UI agent list.
