# HR Onboarding Agent - Plan

> Scenario 4 in the presentation sidebar. Start after Release Readiness (Scenario 3) is complete, unless the user reorders.
> Scenario id: `hr-onboarding` | Sidebar position: 4 | Status: `soon`
> Linked from [`plans/incident-triage-plan.md`](incident-triage-plan.md) "Additional scenarios" section.

## Top-Level Overview

**Goal.** Show an agent that guides an HR coordinator through provisioning a new employee: gathering required information, checking role-based access policy, triggering provisioning steps through an approval-gated flow, and answering policy questions from a knowledge base.

**Why it passes the agent-washing test.** Employee onboarding is not a fixed sequence: the required provisioning steps depend on the employee's role, department, location, and start date; the HR coordinator's input is often incomplete; the agent may need to ask several clarifying questions in a non-deterministic order. The deterministic access-mapping (role -> systems) belongs in a flow or lookup tool, not in agent reasoning.

**Key design decisions (to be confirmed before building).**

| Decision | Rationale |
|---|---|
| Read tools: `lookup_role_policy`, `check_provisioning_status`, `list_required_systems`, `get_department_config` | Open-ended retrieval; agent decides which to call based on what it learns. |
| Write tool `provision_access` behind a flow with an HR-manager Approve step | Governance gate; manager confirms before any access is granted. |
| Access-policy documents as `.txt` KB | Role -> systems matrix and policy exceptions are stable structured text. |
| Mock world: 3-4 employee profiles in different roles/departments | Deterministic; one profile triggers an exception case. |

**Mock world (to be designed before building).**

| Case | Coordinator input | Planted situation | Teaches |
|---|---|---|---|
| HR-001 | "Onboard Alex Kim, Software Engineer, starts Monday" | Standard role, all required systems clear | Happy path, clarifying questions for missing fields |
| HR-002 | "Set up contractor access for Jordan Lee" | Contractor role has restricted system list; policy exception applies | Policy lookup, KB retrieval, restricted provisioning |
| HR-003 | "Add Sarah Chen to the Finance team" | Finance requires additional compliance approval | Extra approval gate, escalation path |
| HR-004 | "Can you provision admin rights for the whole team?" | Policy prohibits bulk admin grants | Restraint: agent declines, cites policy document id |

At least one case should have a red herring (for example a role that looks like it needs a system but does not under the current policy).

## Sub-Tasks

### Sub-Task 1: Mock data and tools

- **Intent:** Static employee profiles, role-to-system mappings, department configs. Read-only `@tool` functions.
- **Expected Outcomes:**
  - `tools/hr_onboarding/data/` with `employees.py`, `role_policies.py`, `department_configs.py`, `provisioning_status.py`.
  - `tools/hr_onboarding/hr_onboarding.py` with `lookup_role_policy`, `check_provisioning_status`, `list_required_systems`, `get_department_config` (target 7 attached tools + flow).
  - Direct Python tests.
- **Status:** `[ ] pending`

### Sub-Task 2: Policy knowledge base

- **Expected Outcomes:**
  - `knowledge/hr-onboarding/<name>.yaml` + `policies/*.txt` (3-5 documents): role-access matrix, contractor policy, compliance-approval requirements, off-limits bulk-provisioning rule.
  - Each document has a stable ID (e.g. `HR-POL-01`) the agent can cite.
- **Status:** `[ ] pending`

### Sub-Task 3: Approval flow

- **Expected Outcomes:**
  - `flows/hr_onboarding/provision_access_flow.py` following the Incident Triage approval-flow pattern.
  - Write tool `provision_access` is only called by the flow after HR manager approves; it is listed in the manifest under `names` but not `attached`.
  - Browser-verified: form renders, Approve triggers provisioning, Reject does not.
- **Status:** `[ ] pending`

### Sub-Task 4: Agent YAML and README

- **Expected Outcomes:**
  - `agents/hr-onboarding/agent.yaml` (`spec_version: v1`, `kind: native`, `style: react_core`). Instructions: clarifying-question rule for missing fields, propose-action rule, what to do when policy is ambiguous, what to never do (bulk grants, skip approval).
  - `agents/hr-onboarding/README.md`.
  - `scenarios/hr-onboarding/scenario.yaml` updated from the `soon` stub.
- **Status:** `[ ] pending`

### Sub-Task 5: Evaluation

- **Expected Outcomes:**
  - `evaluation/hr-onboarding/ground_truth.json`: one entry per case, `smoke_prompts` (diagnosis-only; approval form not drivable through the run API).
  - Optional full tier only if requested.
- **Status:** `[ ] pending`

### Sub-Task 6: Deploy and smoke test

- **Expected Outcomes:**
  - `scripts/deploy-all.ps1 -Scenario hr-onboarding` deploys without error.
  - `python scripts/smoke_test.py --scenario hr-onboarding` runs the `smoke_prompts`.
  - Each demo prompt run at least once in the browser.
- **Status:** `[ ] pending`

### Sub-Task 7: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/hr-onboarding-demo.md` from the template: vague-input scene, standard-path scene, policy-exception scene, governed-action scene, restraint scene.
  - `docs/demo/scenarios/hr-onboarding.js` filled; `status: "live"`; slide tags "Scenario 4 • ...".
  - Checker exits 0.
- **Status:** `[ ] pending`

## Open Items

- Confirm the role-to-system mapping scope (how many roles, how many systems) before building mock data -- keep it small enough to be readable in a demo.
- Decide whether Finance compliance approval is a second human-approval step in the same flow or a separate flow.
- Tool name uniqueness: verify `lookup_role_policy`, `check_provisioning_status`, `list_required_systems`, `get_department_config`, `provision_access` do not clash with any existing scenario names.
- Rule 7 from `wxo-scenario-authoring`: add a deterministic check inside the flow that role and department are consistent before calling `provision_access`.

## Suggested Build Order

Sub-Tasks 1 and 2 are independent. Sub-Task 3 depends on 1. Sub-Task 4 depends on 1-3. Sub-Tasks 5-7 follow 4.

## Not Done by This Plan

- No change to earlier scenario resources.
- Cloud FinOps is a separate plan.
