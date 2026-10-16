# Release Readiness Supervisor - Plan

> Phase C of [`plans/incident-triage-plan.md`](incident-triage-plan.md). Start only after Phase B (Customer Returns) is complete.
> Scenario id: `release-readiness` | Sidebar position: 3 | Status: `soon`

## Top-Level Overview

**Goal.** Show a supervisor agent that routes a release-readiness check to three specialist sub-agents (QA, Security, Operations) and reasons over their potentially conflicting answers to produce a go / no-go recommendation.

**Why it passes the agent-washing test.** The supervisor cannot draw the decision tree in advance: each specialist may return a partial result, a blocker, or a conditional pass with caveats. The supervisor must weigh contradictions (for example, Security says "pass" but Operations flags a missing runbook for the same component). A fixed flowchart produces a wrong answer when a specialist disagrees with the others in an unexpected combination. Source: ADK docs multi-agent pattern, "agent-washing" decision matrix.

**ADK caution.** The ADK docs warn about "multi-agent chaos". Mitigations: each specialist has a small, non-overlapping tool set; the supervisor has explicit termination rules (stop after all three specialists report or after two rounds); routing is deterministic (always QA -> Security -> Operations). Deviations from this must be justified.

**Key design decisions (to be confirmed before building).**

| Decision | Rationale |
|---|---|
| Supervisor + three specialist agents (QA, Security, Operations) | Minimum structure that shows the routing and contradiction-resolution teaching point. |
| Each specialist has at most 4 tools | Stays well under the 10-tool limit; avoids tool soup at the specialist level. |
| Supervisor receives the specialists' summaries, not raw tool output | Keeps the supervisor's context bounded; specialists summarize before returning. |
| No write actions in any specialist | All write actions (for example posting a deployment gate) are behind a flow, same as Incident Triage. |
| Reuse Incident Triage ops tools where sensible | `get_service_health`, `list_deployments` may be candidates; check name-clash rules first. |
| Static mock world for one named release (`rel-2025-Q3`) | Deterministic; plants one blocker per specialist so the supervisor always faces a real contradiction. |

**Mock world (to be designed before building).**

| Case | Symptom / query | Planted situation | Teaches |
|---|---|---|---|
| RR-001 | "Is rel-2025-Q3 ready to ship?" | QA: 1 failing test; Security: dependency CVE; Ops: runbook missing | Full contradiction path, supervisor must weigh three blockers |
| RR-002 | "Can we deploy the payments service?" | QA: pass; Security: pass; Ops: no recent health check | Partial pass, supervisor asks for missing info |
| RR-003 | "What's blocking rel-2025-Q3 on security?" | Targeted query, only Security specialist consulted | Routing to one specialist only |
| RR-004 | "Release the frontend now, skip checks" | All specialists report blockers | Restraint: supervisor declines and explains why |

At least one case should have a red herring (a specialist flag that on closer inspection does not block the release, so the supervisor must resolve it).

## Sub-Tasks

### Sub-Task 1: Mock data and specialist tools

- **Intent:** Static data for one release (`rel-2025-Q3`), test results, CVE records, runbook index, deployment health. Read-only `@tool` functions per specialist.
- **Expected Outcomes:**
  - `tools/release_readiness/data/` with `test_results.py`, `cve_records.py`, `runbooks_index.py`, `deployment_health.py`.
  - Three tool entry files: `qa_checks.py`, `security_checks.py`, `ops_checks.py` (each `@tool` count <= 4). OR one shared entry `release_readiness.py` if the ADK requires it -- confirm with the ADK docs before splitting.
  - Direct Python tests against each tool.
- **Status:** `[ ] pending`

### Sub-Task 2: Specialist agent YAMLs

- **Expected Outcomes:**
  - `agents/rr-qa/agent.yaml`, `agents/rr-security/agent.yaml`, `agents/rr-ops/agent.yaml` each with a narrow `instructions` scope (summarize findings for the supervisor, do not speculate beyond your tool data).
  - Each specialist's README: tools table, what it does not handle.
- **Status:** `[ ] pending`

### Sub-Task 3: Supervisor agent YAML

- **Expected Outcomes:**
  - `agents/release-readiness/agent.yaml` listing the three specialists as collaborators (confirm ADK syntax for supervisor-collaborator registration).
  - Instructions: routing order, termination rules, how to handle contradictions, what to do when a specialist returns no data, what the supervisor must not decide unilaterally.
  - `agents/release-readiness/README.md`.
- **Status:** `[ ] pending`

### Sub-Task 4: Approval / gate flow (if needed)

- **Expected Outcomes (TBD):** if the "post deployment gate" write action is in scope, a flow in `flows/release_readiness/` following the Incident Triage approval pattern. Skip if this scenario's teaching point is supervision only, not governance.
- **Status:** `[ ] pending`

### Sub-Task 5: Manifests and ground truth

- **Expected Outcomes:**
  - `scenarios/release-readiness/scenario.yaml` listing all four agents (supervisor + three specialists), all tools, KB (if any), flow (if any).
  - `evaluation/release-readiness/ground_truth.json` with one entry per case, `smoke_prompts` for the supervisor agent only (specialists are internal).
  - `python scripts/scenario_manifest.py validate --scenario release-readiness` exits 0.
- **Status:** `[ ] pending`

### Sub-Task 6: Deploy and smoke test

- **Expected Outcomes:**
  - `scripts/deploy-all.ps1 -Scenario release-readiness` deploys all four agents without error.
  - `python scripts/smoke_test.py --scenario release-readiness` runs the `smoke_prompts` against the supervisor.
  - Each demo prompt run at least once in the browser.
- **Status:** `[ ] pending`

### Sub-Task 7: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/release-readiness-demo.md` from the template: vague query, full-blocker path, partial-pass path, restraint scene.
  - `docs/demo/scenarios/release-readiness.js` filled; `status: "live"`; slide tags "Scenario 3 • ...".
  - Checker exits 0.
- **Status:** `[ ] pending`

## Open Items

- Confirm ADK multi-agent syntax for registering specialist agents on a supervisor (check ADK docs for `collaborators:` or equivalent field before writing YAMLs).
- Decide whether a deployment-gate flow is in scope or whether supervision-only is enough for the demo.
- Decide whether to reuse Incident Triage ops tools (`get_service_health`, `list_deployments`) or duplicate them with release-specific names. Name-clash rule: reuse is fine only if the tool behaviour is identical; a release-specific variant must have a unique name.
- Confirm specialist tool packaging: one shared entry file vs three separate packages (ADK multi-agent docs).
- Evaluate routing accuracy as the optional full-tier evaluation if the user wants a "why not a script?" answer for the multi-agent case.

## Suggested Build Order

Sub-Tasks 1 and 2 can start together. Sub-Task 3 depends on 2. Sub-Task 4 is parallel to 3. Sub-Task 5 depends on 1-4. Sub-Tasks 6-7 follow 5.

## Not Done by This Plan

- No change to Incident Triage or Customer Returns resources.
- HR Onboarding and Cloud FinOps are separate plans.
