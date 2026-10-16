# Customer Returns and Refunds Agent - Plan

> Phase B of [`plans/incident-triage-plan.md`](incident-triage-plan.md). Start only after Phase A is complete and accepted.
> Scenario id: `customer-returns` | Sidebar position: 2 | Status: `soon`

## Top-Level Overview

**Goal.** Show a conversational agent that handles messy, ambiguous return requests against a knowledge-base return policy and routes deterministic refund decisions through a Decisions-node flow rather than agent reasoning.

**Why it passes the agent-washing test.** The customer's input is vague and incomplete ("I want to return this"; no order id, no product, no reason). The agent must ask clarifying questions, look up the order, check warranty or policy, and decide whether to escalate. The deterministic part (refund eligibility rule) belongs in a flow Decisions node, not in the agent -- this split is the teaching point.

**Key design decisions (to be confirmed before building).**

| Decision | Rationale |
|---|---|
| Read tools on the agent: `lookup_order`, `check_warranty`, `get_return_policy` (KB lookup) | Stays under the 8-tool target; KB retrieval handles policy questions. |
| Write/quote tool `issue_refund_quote` behind a flow Decisions node | Never attached to the agent; flow checks eligibility rule before calling it. |
| Deterministic refund-eligibility rule in the Decisions node | Separates the agent's open-ended reasoning from a rule that a flowchart handles correctly. |
| Return-policy documents as `.txt` KB | Matches the supported formats; policy text has stable symptom -> procedure structure. |
| All orders, warranties, and return history are static mock data | Stateless containers; deterministic runs. |

**Mock world (to be designed before building).**

| Case | Customer complaint | Planted situation | Teaches |
|---|---|---|---|
| CR-001 | "I bought this last week and it broke" | Within warranty, eligible for replacement | Happy path, clarifying question on order id |
| CR-002 | "I just don't like it anymore" | 45 days old, outside 30-day no-reason window | Policy lookup, correct denial |
| CR-003 | "This was a gift, I don't have the order" | Eligible by product serial, policy allows gift returns | Vague input, serial-number lookup |
| CR-004 | "I was charged twice" | Billing issue, not a return; escalation path | Restraint: out of scope, hand off |

At least one case should have a red herring (for example a warranty record that looks applicable but is for a different SKU).

## Sub-Tasks

### Sub-Task 1: Mock data and tools

- **Intent:** Static Python modules for orders, warranties, and return history; read-only `@tool` functions.
- **Expected Outcomes:**
  - `tools/customer_returns/data/` with `orders.py`, `warranties.py`, `return_history.py`.
  - `tools/customer_returns/customer_returns.py` with `lookup_order`, `check_warranty`, `get_return_eligibility`, and any needed lookup helpers (target 7 attached tools + flow).
  - Direct Python tests against each tool (no WXO needed).
- **Status:** `[ ] pending`

### Sub-Task 2: Return-policy knowledge base

- **Intent:** KB documents describing return conditions, gift-return policy, and out-of-scope escalation paths.
- **Expected Outcomes:**
  - `knowledge/customer-returns/<name>.yaml` + `policies/*.txt` (3-5 documents).
  - Each document has a stable ID (e.g. `RP-WARRANTY-01`) the agent can cite.
- **Status:** `[ ] pending`

### Sub-Task 3: Approval / eligibility flow

- **Intent:** A flow that checks eligibility with a Decisions node before calling `issue_refund_quote`; human-approval step if the quote exceeds a threshold (TBD).
- **Expected Outcomes:**
  - `flows/customer_returns/process_return.py` using `flows/incident_triage/request_remediation.py` as structural reference.
  - Decisions node encodes the 30-day / warranty rule; does not rely on agent instructions.
  - Browser-verified: form renders, Approve runs the write tool, Reject does not (cannot be driven by the evaluator).
- **Status:** `[ ] pending`

### Sub-Task 4: Agent YAML and README

- **Expected Outcomes:**
  - `agents/customer-returns/agent.yaml` (`spec_version: v1`, `kind: native`, `style: react_core`). Instructions follow the Incident Triage structure: method, evidence standard, clarifying-question rule, propose-action rule, what not to do.
  - `agents/customer-returns/README.md`: tools table, KB, mock data table, limitations.
  - `scenarios/customer-returns/scenario.yaml` updated from the `soon` stub (all resource names, `evaluation.tier: core`, `status: live` once deployed).
- **Status:** `[ ] pending`

### Sub-Task 5: Evaluation

- **Expected Outcomes:**
  - `evaluation/customer-returns/ground_truth.json`: one entry per case (id, symptom, expected outcome, expected action or `no_action`, approval required, red herrings, expected key tools, `smoke_prompts`).
  - Optional full tier (baseline.py, test_cases/, eval_config.yaml) only if needed to answer "why not a script?".
- **Status:** `[ ] pending`

### Sub-Task 6: Deploy and smoke test

- **Expected Outcomes:**
  - `python scripts/deploy-all.ps1 -Scenario customer-returns` (or `.sh`) deploys without error.
  - `python scripts/smoke_test.py --scenario customer-returns` sends each `smoke_prompts` entry and reports pass/fail.
  - Each demo prompt run at least once in the browser; results recorded honestly.
- **Status:** `[ ] pending`

### Sub-Task 7: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/customer-returns-demo.md` from the `scenario-demo-docs` template: 10 sections, at minimum a vague-input scene, main-path scene, policy-denial scene, flow-gate scene, and restraint scene.
  - `docs/demo/scenarios/customer-returns.js` filled from the slide template; `status: "live"`; all six slides.
  - `python .bob/skills/scenario-demo-docs/check_demo_consistency.py customer-returns` exits 0.
  - Slide tags say "Scenario 2 • ..." (sidebar position 2).
- **Status:** `[ ] pending`

## Open Items

- Confirm the 30-day no-reason return window and the warranty-replacement rule with the user before building mock data.
- Decide whether the approval-flow human step is needed (it is the teaching point for the governed-action scene) or whether the Decisions-node-only split is enough.
- Tool name uniqueness: verify `lookup_order`, `check_warranty`, `get_return_eligibility`, `issue_refund_quote`, `process_return` do not clash with any existing `scenarios/*/scenario.yaml` names before import.
- Rule 7 from `wxo-scenario-authoring`: add a validation check inside the flow that the order id and customer id match before issuing a quote.

## Suggested Build Order

Sub-Tasks 1 and 2 are independent and can start together. Sub-Task 3 depends on 1. Sub-Task 4 depends on 1-3. Sub-Tasks 5-7 follow 4.

## Not Done by This Plan

- No change to Incident Triage resources.
- No optional evaluation tier unless explicitly requested.
- Phase C (Release Readiness) is a separate plan.
