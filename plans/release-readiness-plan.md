# Release Readiness Supervisor - Plan

> Phase C of [`plans/incident-triage-plan.md`](incident-triage-plan.md). Start only after Phase B (Customer Returns) is complete.
> Scenario id: `release-readiness` | Sidebar position: 3 (confirmed: third `<script>` tag in `presentation.html`) | Status: `soon`
> Revised after a repo/ADK check: see "Review findings" at the end for what changed and why.

## Top-Level Overview

**Goal.** Show a supervisor agent that routes a release-readiness check to three specialist sub-agents (QA, Security, Operations) and reasons over their potentially conflicting answers to produce a go / conditional-go / no-go **recommendation** (advisory only).

**Why it passes the agent-washing test.** The supervisor cannot draw the decision tree in advance: each specialist may return a partial result, a blocker, a flag that turns out to be a red herring, or a conditional pass with caveats. The supervisor must weigh contradictions (for example, Security says "pass" but Operations flags a missing runbook for the same component) against a written release policy. A fixed flowchart gives a wrong answer when specialists disagree in an unexpected combination or when a flag needs a judgement call. Source: ADK docs, agent design, "agent-washing" decision matrix.

**ADK caution.** The ADK docs list "multi-agent chaos" (no coordination, duplication; mitigation: "tightly bounded agent per use case"). Mitigations here: each specialist has a small, non-overlapping tool set; the supervisor has explicit routing and termination rules (below); collaborator `description` fields are written as routing instructions, because the supervisor routes on them (ADK docs, `agents/descriptions`).

**Routing and termination rules (replaces the earlier contradictory wording).**

- Full readiness question ("is X ready?", "can we deploy Y?"): consult all three specialists, always in the order QA -> Security -> Operations, once each.
- Targeted question (for example "what is blocking us on security?"): consult only the relevant specialist.
- One round only: the supervisor may re-ask a specialist once, and only to resolve a flag (for example, to ask Security whether a CVE is reachable at runtime). Then it must answer. No loops.
- Request to skip checks: the supervisor still reads the specialists' findings (it cannot refuse on evidence it has not read), then declines citing the policy document.
- A specialist that returns no data is reported as "no data", never filled in by the supervisor.

**Key design decisions (proposed, confirm before building).**

| Decision | Rationale |
|---|---|
| Supervisor + three specialist agents (QA, Security, Operations) | Minimum structure that shows routing and contradiction resolution. Supervisor has 3 collaborators, no tools. Well under the ADK guidance of 10 or fewer tools/collaborators. |
| Each specialist has at most 3 tools | Avoids tool soup; non-overlapping scopes. |
| One tool package `tools/release_readiness/` with one entry file | The manifest accepts several packages, but one shared mock world (one `data/` folder) is simpler and one import. Per-agent limits are enforced in each `agent.yaml` `tools:` list. |
| All tool names prefixed `rr_` | Instance-wide uniqueness. Incident Triage tools **cannot** be reused: the validator rejects tools the scenario does not own and rejects duplicate names across manifests (`src/wxodemo/manifest.py`). Release-specific variants with unique names only. |
| Small policy knowledge base `release_readiness_policy` on the **supervisor** | Without a written rule, "go / no-go" is the model's opinion. The KB gives the supervisor a citable basis (blocker definitions, conditional-go conditions, who may waive, why skipping checks is refused). `.txt` documents with stable IDs. |
| Specialists summarize findings; supervisor receives summaries, not raw tool output | Keeps supervisor context bounded. |
| Supervision only, **no gate flow, no write tool** (recommended) | The teaching point is multi-agent supervision. The recommendation is advisory; the supervisor must say a human Release Manager decides and that only they can waive a blocker. Revisit only if you want a governance scene. |
| Static mock world, one release `rel-2025-q3`, three components | Deterministic. Cases RR-002 and RR-004 ask about a single component, so the world needs components, not just a release. |

**Mock world (proposed).** Release `rel-2025-q3` has components `payments`, `orders_api`, `frontend`.

| Component | QA | Security | Operations |
|---|---|---|---|
| `payments` | Pass. One test failed in an old run, then 3 consecutive passes (**red herring**: flaky, not a blocker) | Pass. One CVE in a **dev-only** test dependency, not shipped in the runtime artifact (**red herring**) | Last health check 19 days old; policy requires 7 days or less |
| `orders_api` | **1 failing test** (`test_bulk_cancel`, failed in all 3 recent runs) | Pass | **Runbook missing** (tier-1 service) |
| `frontend` | End-to-end suite **skipped** | **High-severity runtime CVE**, fix available | No rollback runbook, canary not configured |

| Case | Query | Expected outcome | Teaches |
|---|---|---|---|
| RR-001 | "Is rel-2025-Q3 ready to ship?" | No-go. Blockers: `orders_api` failing test + missing runbook (Security says pass for it), `frontend` runtime CVE. Cites the blocker policy doc | Full contradiction path across three specialists |
| RR-002 | "Can we deploy the payments service?" | Conditional go: QA and Security flags are resolved as non-blocking; the only open item is a stale health check that Operations must refresh | Resolving red herrings; partial pass is not a no-go |
| RR-003 | "What's blocking rel-2025-Q3 on security?" | Only the Security specialist is consulted; the frontend CVE is reported, `payments` dev-only CVE is explained as non-blocking | Routing to one specialist |
| RR-004 | "Release the frontend now, skip the checks" | Declined: all three specialists report blockers, policy says checks cannot be skipped, a human Release Manager is the only one who can waive | Restraint |

Open data question: what the user can do in RR-002 is limited, because specialists read static data. The supervisor's output is "conditional go, pending a fresh health check by Operations", not a clarifying question to the user.

## Sub-Tasks

### Sub-Task 1: Mock data and specialist tools

- **Intent:** Static data for `rel-2025-q3` and read-only `@tool` functions per specialist.
- **Expected Outcomes:**
  - `tools/release_readiness/release_readiness.py` (single entry), `requirements.txt` (pins `ibm-watsonx-orchestrate==2.18.2`), `__init__.py`, with the import fallback copied from `tools/incident_triage/incident_triage.py`.
  - `tools/release_readiness/data/`: `test_results.py`, `cve_records.py`, `runbooks_index.py`, `deployment_health.py`.
  - Tools (7, all read-only, bounded output, error objects with a `hint`):
    - QA: `rr_get_test_summary(component)`, `rr_get_test_history(test_id)`, `rr_list_skipped_suites(component)`
    - Security: `rr_list_cves(component)`, `rr_get_cve_exposure(cve_id, component)`
    - Operations: `rr_check_runbook(component)`, `rr_get_last_health_check(component)`
  - Direct Python calls against every tool and every planted fact.
- **Status:** `[x] done` (7 tools in `tools/release_readiness/`; every planted fact asserted by calling the tools directly from Python in one session; no agent involved)

### Sub-Task 2: Knowledge base

- **Expected Outcomes:**
  - `knowledge/release-readiness/release_readiness_policy.yaml` (`name: release_readiness_policy`) plus `.txt` documents with stable IDs, symptoms first then procedure: `RG-BLOCKER-01` (what blocks a release), `RG-CONDITIONAL-01` (conditions for a conditional go, health check older than 7 days), `RG-WAIVER-01` (only the Release Manager can waive), `RG-SKIP-01` (checks cannot be skipped on request).
- **Status:** `[x] done` (files written; the KB has not been imported or queried in WXO)

### Sub-Task 3: Specialist agent YAMLs

- **Expected Outcomes:**
  - `agents/rr-qa/`, `agents/rr-security/`, `agents/rr-ops/` with agent names `rr_qa`, `rr_security`, `rr_ops` (snake_case WXO names). Each has `description` written as a routing instruction (what it covers, which tools, what it does not cover) and narrow `instructions` (summarize for the supervisor, state facts and the source tool, do not decide go/no-go, do not speculate beyond tool data).
  - Each README: tools table, what it does not handle.
- **Status:** `[x] done` (YAML written; not imported into WXO)

### Sub-Task 4: Supervisor agent YAML

- **Expected Outcomes:**
  - `agents/release-readiness/agent.yaml`, name `release_readiness`, `collaborators: [rr_qa, rr_security, rr_ops]` (field confirmed in ADK docs `agents/build_agent`), `knowledge_base: [release_readiness_policy]` (same key as `agents/incident-triage/agent.yaml` and the ADK docs; `agents/customer-returns/agent.yaml` uses `knowledge_bases:`, which looks like a different key and is not touched here), no tools.
  - Instructions follow the structure of `agents/incident-triage/agent.yaml`: routing and termination rules above, how to weigh contradictions, red-herring handling, cite one policy document ID, output format (verdict, blockers per component per specialist, conditions, who decides), "what you must not do" (never decide unilaterally, never waive a blocker, never invent a specialist result).
  - `agents/release-readiness/README.md`.
- **Status:** `[x] done` (YAML and README written; not imported into WXO)

### Sub-Task 5: Manifest and ground truth

- Run `python wxodemo.py new-scenario release-readiness --name "Release Readiness Supervisor" --description "Multi-agent routing across QA, security & operations"` first. It creates the manifest stub, supervisor agent stub, `ground_truth.json`, and demo script. The slide placeholder and `<script>` tag already exist and are left unchanged.
- **Expected Outcomes:**
  - `scenarios/release-readiness/scenario.yaml` listing four agents, seven tools (all attached to specialists; none is write-capable), one KB, no flows. **Agent order matters, see finding 1 below.**
  - `evaluation/release-readiness/ground_truth.json`: one entry per case (expected verdict, expected specialists consulted, expected blockers, red herrings, policy doc), plus `smoke_prompts` for the supervisor only. Tier `core`.
  - `python wxodemo.py validate release-readiness` prints OK.
- **Status:** `[x] done` (`validate` prints OK; `smoke_agent` field added to the CLI with tests, option A). Manifest `status` stays `soon`.

### Sub-Task 6: Deploy and smoke test

- **Expected Outcomes:**
  - `python wxodemo.py login`, then `python wxodemo.py deploy release-readiness` (preview first with `--dry-run`).
  - `python wxodemo.py smoke release-readiness` after the smoke-target fix (finding 1).
  - Each demo prompt run several times in the browser chat UI, recording: were the specialists actually called, in which order, did targeted queries route to one specialist, were collaborator answers visible to the user, did the supervisor cite the right policy ID.
  - Record whether the run API thread messages show collaborator calls (the smoke helper currently reads `tool_call` steps only); if not, say so and verify routing in the UI or traces.
- **Status:** `[~] partly verified` Deployed by the user. After the instruction fixes (health-check age, both policy searches, separate answer formats) the user reported the behaviour as "okay". No post-fix transcripts or run counts were recorded. Specialist routing, collaborator visibility and `smoke` output for collaborator calls remain unverified. Pre-fix: RR-001 correct; RR-002, RR-003, RR-004 showed the defects that were then fixed.

### Sub-Task 7: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/release-readiness-demo.md` and `docs/demo/scenarios/release-readiness.js` written **after** real runs, from the `scenario-demo-docs` templates. Scenes: full-blocker path (RR-001), red-herring/conditional path (RR-002), targeted routing (RR-003), restraint (RR-004).
  - `status: "live"` only after deploy; tags "Scenario 3 • ...".
  - No time-saved or accuracy numbers unless a recorded run supports them. Benefits slide must be honest on agent vs script: latency and cost of 4 agents versus one is a trade-off, not a claim to hide.
  - `python wxodemo.py validate release-readiness` OK.
- **Status:** `[x] done` Script (`docs/demo/release-readiness-demo.md`) and 6 slides (`docs/demo/scenarios/release-readiness.js`, status `live`) written. The script separates "Intended" from "Seen (pre-fix, 1 run)". Slides not yet viewed in a browser.

## Open Items

- ~~Smoke target and deploy order conflict~~ Resolved: optional manifest field `smoke_agent` (read by `smoke.py`, checked by `validate`); specialists are listed before the supervisor in `scenario.yaml`.
- Check whether `agents/customer-returns/agent.yaml` `knowledge_bases:` (vs `knowledge_base:`) actually attaches its KB. Out of scope here; not changed.
- Capture post-fix transcripts (`python wxodemo.py export-chats`) and run each prompt several times; confirm scenes 3 and 4 routing.
- Fallback if the stale-health-check rule regresses: have `rr_get_last_health_check` return `stale` and `policy_limit_days` fields so the rule lives in code.
- Confirm whether collaborator replies reach the user verbatim in the chat UI or only to the supervisor (affects the demo "point out" lines and the "summaries not raw output" claim). Unverified.
- Confirm that a specialist imported with `agents deploy` appears as a selectable agent in the chat UI; decide whether that matters for the demo.
- Optional full-tier evaluation (routing accuracy) only if requested.

## Review findings (what was added or corrected, with evidence)

1. **Deploy order vs smoke target.** `agents import` of a supervisor resolves collaborators by name and exits if one is not found (`agents_controller.py`, `dereference_collaborators`), and `deploy_plan` imports agents in manifest order. So the three specialists must be listed **before** the supervisor in `scenario.yaml`. But `smoke.py` sends prompts to `agents[0]`, which would then be `rr_qa`. Smallest fix: let the manifest name the smoke agent (or have smoke pick the agent that has collaborators). That is a change to shared CLI code, not scenario files, so it needs your approval.
2. **Tool reuse is impossible.** The validator rejects tools a scenario does not own and the cross-scenario name-clash check rejects duplicates, so the "reuse Incident Triage ops tools" open item is resolved: build `rr_*` variants.
3. **Routing rule contradicted a case.** "Always QA -> Security -> Operations" conflicted with RR-003 (Security only). Replaced with explicit rules above.
4. **Stale commands.** The old plan referenced `scripts/scenario_manifest.py`, `scripts/deploy-all.ps1`, `scripts/smoke_test.py`. The repo uses `python wxodemo.py ...`.
5. **Mock world was under-specified.** Cases mention `payments` and `frontend` but the world was "one release". Added components and a concrete data table; red herrings are now specified, not optional.
6. **No decision basis for go/no-go.** Added a policy KB with citable IDs; the restraint case now has a document to cite.
7. **Collaborator descriptions were missing.** The ADK says supervisors route on collaborator descriptions; added as a requirement.
8. **Gate flow decided as out of scope**, with the reason, and the supervisor must state that a human decides.
9. **Verification gaps added**: smoke output may not show collaborator calls; whether collaborator output is visible to the user; recording latency honestly (no numbers without runs).

## Suggested Build Order

Sub-Tasks 1 and 2 first (data, tools, KB), then 3, then 4. Sub-Task 5 (`new-scenario` first), then 6 and 7.

## Not Done by This Plan

- No change to Incident Triage, Customer Returns or Travel Request resources.
- HR Onboarding and Cloud FinOps are separate plans.
