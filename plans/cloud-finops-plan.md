# Cloud FinOps Agent - Plan

> Scenario 5 in the presentation sidebar. Start after HR Onboarding (Scenario 4) is complete, unless the user reorders.
> Scenario id: `cloud-finops` | Sidebar position: 5 | Status: `soon`
> Linked from [`plans/incident-triage-plan.md`](incident-triage-plan.md) "Additional scenarios" section.

## Top-Level Overview

**Goal.** Show an agent that investigates cloud spend anomalies, identifies idle or over-provisioned resources, produces a rightsizing recommendation, and routes the actual reclamation or resize action through a cost-owner approval flow.

**Why it passes the agent-washing test.** Spend anomalies have multiple possible root causes (traffic spike, misconfiguration, zombie resource, billing error); the agent must investigate before recommending an action. The user's input is vague ("our cloud bill jumped 30% this month"). The full decision tree cannot be drawn in advance because the investigation path depends on what the anomaly analysis finds. The deterministic part (threshold-based reclamation rule) belongs in a flow, not in agent reasoning.

**Key design decisions (to be confirmed before building).**

| Decision | Rationale |
|---|---|
| Read tools: `get_spend_summary`, `list_idle_resources`, `get_resource_utilization`, `explain_cost_spike` | Progressive investigation; agent decides which to call next based on findings. |
| Write tool `reclaim_resource` or `resize_resource` behind an approval flow | Cost-owner must approve before any resource change; same governance pattern as Incident Triage. |
| Cost-anomaly and rightsizing policy as `.txt` KB | Stable thresholds and policy text; agent cites document IDs. |
| Mock world: one account, one billing period, 3-4 planted anomalies | Deterministic; one is a billing error (no action needed), one is a true idle resource. |

**Mock world (to be designed before building).**

| Case | User query | Planted situation | Teaches |
|---|---|---|---|
| CF-001 | "Why did our bill spike this month?" | Zombie VM running at full cost since last month | Root-cause investigation, multi-step tool use |
| CF-002 | "Any idle resources we can reclaim?" | Two idle VMs + one that looks idle but has weekend batch jobs | Red herring, clarifying question, governed reclamation |
| CF-003 | "Rightsize the database cluster" | Cluster is over-provisioned; resize saves 40% (illustrative, must say so) | Governed resize action, approval flow |
| CF-004 | "The billing report says we used 1 000 GPU hours" | Data error in the mock billing feed; actual usage is 0 | Restraint: agent flags the discrepancy, does not act |

At least one case should have a red herring (a resource that looks expensive but is actually justified by a scheduled job).

## Sub-Tasks

### Sub-Task 1: Mock data and tools

- **Intent:** Static spend summaries, resource inventory, utilization records, billing entries. Read-only `@tool` functions.
- **Expected Outcomes:**
  - `tools/cloud_finops/data/` with `spend_data.py`, `resource_inventory.py`, `utilization_records.py`, `billing_entries.py`.
  - `tools/cloud_finops/cloud_finops.py` with `get_spend_summary`, `list_idle_resources`, `get_resource_utilization`, `explain_cost_spike` (target 7 attached tools + flow).
  - Direct Python tests.
- **Status:** `[ ] pending`

### Sub-Task 2: Policy knowledge base

- **Expected Outcomes:**
  - `knowledge/cloud-finops/<name>.yaml` + `policies/*.txt` (3-5 documents): idle-resource threshold policy, rightsizing guidelines, billing-error escalation procedure, reclamation approval requirements.
  - Each document has a stable ID (e.g. `CF-POL-01`) the agent can cite.
- **Status:** `[ ] pending`

### Sub-Task 3: Approval flow

- **Expected Outcomes:**
  - `flows/cloud_finops/approve_resource_change.py` following the Incident Triage approval-flow pattern.
  - Write tools (`reclaim_resource`, `resize_resource`) called only by the flow after cost-owner approves; listed in the manifest under `names` but not `attached`.
  - Browser-verified: form renders, Approve triggers the write tool, Reject does not.
- **Status:** `[ ] pending`

### Sub-Task 4: Agent YAML and README

- **Expected Outcomes:**
  - `agents/cloud-finops/agent.yaml` (`spec_version: v1`, `kind: native`, `style: react_core`). Instructions: progressive-investigation method, evidence standard (cite utilization data and document id), propose-action rule, what to never do (act without approval, invent spend figures).
  - `agents/cloud-finops/README.md`.
  - `scenarios/cloud-finops/scenario.yaml` updated from the `soon` stub.
- **Status:** `[ ] pending`

### Sub-Task 5: Evaluation

- **Expected Outcomes:**
  - `evaluation/cloud-finops/ground_truth.json`: one entry per case, `smoke_prompts` (investigation queries only; approval form not drivable through the run API).
  - Optional full tier only if requested.
- **Status:** `[ ] pending`

### Sub-Task 6: Deploy and smoke test

- **Expected Outcomes:**
  - `scripts/deploy-all.ps1 -Scenario cloud-finops` deploys without error.
  - `python scripts/smoke_test.py --scenario cloud-finops` runs the `smoke_prompts`.
  - Each demo prompt run at least once in the browser.
- **Status:** `[ ] pending`

### Sub-Task 7: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/cloud-finops-demo.md` from the template: vague-input scene, root-cause-investigation scene, red-herring / idle-resource scene, governed-reclamation scene, restraint scene.
  - `docs/demo/scenarios/cloud-finops.js` filled; `status: "live"`; slide tags "Scenario 5 • ...".
  - No unmeasured percentage or time figures on any slide; any illustrative figure is labelled as such.
  - Checker exits 0.
- **Status:** `[ ] pending`

## Open Items

- Confirm the idle-resource threshold (e.g. < 5% CPU for 7 days) and rightsizing criteria before building mock data.
- Decide whether `reclaim_resource` and `resize_resource` are separate tools (each behind its own flow step) or one tool with a mode parameter.
- Tool name uniqueness: verify `get_spend_summary`, `list_idle_resources`, `get_resource_utilization`, `explain_cost_spike`, `reclaim_resource`, `resize_resource`, `approve_resource_change` do not clash with any existing scenario names.
- Rule 7 from `wxo-scenario-authoring`: add a deterministic check inside the flow that the resource id and account id are consistent before calling the write tool.
- The benefits slide must not claim a specific % cost reduction unless a recorded run supports it; use "illustrative example" if a figure is needed.

## Suggested Build Order

Sub-Tasks 1 and 2 are independent. Sub-Task 3 depends on 1. Sub-Task 4 depends on 1-3. Sub-Tasks 5-7 follow 4.

## Not Done by This Plan

- No change to earlier scenario resources.
- No real cloud account, billing API, or external service integration.
