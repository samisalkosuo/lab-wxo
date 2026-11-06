# Pipeline Docs and Test Gap Agent - Plan

## Top-Level Overview

**Goal.** Add a demo scenario (`pipeline-doc-gap`) for a multi-country data platform team. Per the source slide, the scaling challenge is that the amount of work grows faster than capacity: number of repos and pipelines, dependency updates, testing and documentation, key-person dependency. The agent finds pipelines whose documentation or tests are missing or ineffective, ranks them, drafts the missing artefacts, and opens a **draft pull request** in the owner's existing review process.

**Scope decisions (confirmed by the user).**

1. **Phase A only.** Mock data, runs entirely inside WXO, no external services. Same conventions as Incident Triage.
2. **Draft PR behind an approval flow (revised at build time).** The first version of this plan attached the write tool directly to the agent. That breaks the repo rule that write tools sit behind a flow gate, and tool-side checks cannot stop an unprompted PR. The user decided to follow the rule: `flows/pipeline_doc_gap/pdg_request_draft_pr.py` is a copy of the `request_remediation` pattern (Approve / Reject form), and `pdg_create_draft_pr` is in `names` but not `attached`. The organisation's PR review stays the second gate.
3. **Agents in WXO are the primary purpose.** Everything lives in this repo's WXO resources.
4. **Bob integration is out of scope for the repo.** It is mentioned only on the presentation slides (Sub-Task 7), not in the README, plan sub-tasks for code, agent files or manifest.

**Agent-washing check (required by the scenario skill).**

- The next step depends on what the previous step found: gap in docs vs gap in tests vs tests that exist but never run in CI.
- User input is vague ("the Finnish ones", "the risky ones") and may need a clarifying question.
- Country requirements change what counts as a gap, so the decision tree cannot be drawn in advance.

**Write-tool safeguards.** In addition to the flow gate, the write tool enforces deterministic checks (not prompt text):

| Safeguard | Where enforced |
|---|---|
| The PR is always a draft; the tool has no parameter to make it ready | Tool code |
| `repo`, `pipeline_id` and `owner` must match the mock catalog, otherwise structured error with a hint | Tool code (addresses the Incident Triage Open Item 7 pattern) |
| Only paths under `docs/` and `tests/` may be written; any other path is rejected | Tool code |
| Review and merge stay with the existing PR process | Organisation process (mock: stated in tool output) |

The manifest lists `pdg_create_draft_pr` under `names` only, like Incident Triage's `execute_remediation`. The agent gets the flow `pdg_request_draft_pr`.

**Key design decisions.**

| Decision | Rationale |
|---|---|
| Static, read-only mock world; the PR tool returns a deterministic record (ID from `hashlib.md5` of inputs) and stores nothing | Python tools run in isolated containers; state cannot persist between calls |
| 5 tools on the agent (target at most 8) | Avoids "tool soup" |
| Business-capability tools with bounded output | Avoids "glorified API wrapper" and "data firehose" |
| Knowledge base as `.txt` documents with stable IDs | Built-in KB does not support markdown |
| Tool, KB and agent names use prefix `pdg_` / `pipeline_doc_gap` | Names are instance-wide resources; a grep found no existing `pdg_` or `pipeline-doc-gap` names |

**Mock world (specification level).** Three countries, each with a few repos and pipelines. Case F (`de-sales-rollup`, a second healthy pipeline) was added at build time so that not every country has a gap.

| Case | Situation | Planted cause | Teaches |
|---|---|---|---|
| A | Pipeline with no README and no tests | Clear gap, high risk | Main path: rank and draft both artefacts |
| B | Pipeline with a tests folder, but CI never runs it (red herring) | Tests exist but are not executed in CI history | Do not trust "tests present"; check CI history |
| C | Pipeline with README but missing a country-specific requirement (local integration or data-residency note) | Requirement in the country KB document | Grounded, cited gap; standards differ per country |
| D | Pipeline whose only committer has left (key-person risk) | Ownership tool shows no active owner | Gap is riskier; PR needs a reviewer fallback |
| E | Healthy pipeline with docs, running tests and an active owner | No action needed | Restraint: do not flag everything |

**Planned tools on the agent.**

- Read-only Python: `pdg_list_pipelines`, `pdg_get_pipeline`, `pdg_get_ci_history`, `pdg_get_ownership` (attached)
- Write (mock, deterministic, draft-only): `pdg_create_draft_pr` (called only by the flow)
- Flow: `pdg_request_draft_pr` (attached; Approve / Reject)
- Knowledge base: `pdg_standards` (documentation standard, test standard, country requirements, PR policy; IDs `STD-DOC-01`, `STD-TEST-01`, `REQ-FI-01`, `REQ-SE-01`, `REQ-DE-01`, `POL-PR-01`)
- Drafting of README and test skeleton is done by the agent from tool output and KB templates, then passed as file content to `pdg_create_draft_pr`.

**Target repository layout (additions).**

```
scenarios/pipeline-doc-gap/        scenario.yaml (created by new-scenario)
agents/pipeline-doc-gap/           agent.yaml, README.md
tools/pdg/                         pdg.py + data/ + requirements.txt + __init__.py
flows/pipeline_doc_gap/            pdg_request_draft_pr.py
knowledge/pipeline-doc-gap/        pdg_standards.yaml + standards/*.txt
evaluation/pipeline-doc-gap/       ground_truth.json, eval_config.yaml, test_cases/tc_*.json
docs/demo/pipeline-doc-gap-demo.md
docs/demo/scenarios/pipeline-doc-gap.js
tests/test_pdg_tools.py            direct tool tests (pattern of existing tool tests)
```

## Items To Verify During Implementation (not assumed)

- Tool package naming: the manifest `names` must equal the `@tool` function names; `tools/pdg/` folder name satisfies the snake_case rule.
- The agent LLM `groq/openai/gpt-oss-120b` and the KB embedding model exist in the target instance.
- KB indexing delay after import before the first query.
- Whether the agent reliably passes matching `repo`, `pipeline_id` and `owner` to `pdg_request_draft_pr` (the tool rejects mismatches, but the rate is unmeasured). Note: the flow input form shows the values but the mismatch error appears only after Approve.
- Whether the agent calls the flow only when asked, and not unprompted after finding a gap (instruction wording plus live test; the flow adds a human click either way).
- The flow, in a browser: form renders (long README/test content in read-only fields), Approve returns the PR record, Reject creates nothing, agent reports `message` verbatim. The flow module has only been syntax-checked (`py_compile`); importing it needs a valid ADK token and was not run.
- The flow passes empty strings for omitted README/test fields; the tool treats `""` as "not provided" (covered by `test_empty_strings_mean_not_provided`).
- Existing scenario layout details (`ground_truth.json` keys, `eval_config.yaml` fields) are generated by `python wxodemo.py new-scenario`; fill the generated stubs, do not hand-roll them.

## Open Items (to remain visible in demo talking points)

1. Agent-washing is argued, not measured. No baseline script comparison exists for this scenario.
2. The mock catalog is easy: the planted cases were written before the prompts.
3. No real GitHub or CI integration; PR creation is a mock record. A real integration would be a separate effort and is not planned here.
4. Draft artefact quality depends on metadata only; the agent never sees the pipeline source code in this scenario.

---

## Phase A - Pipeline Docs and Test Gap Agent

### Sub-Task 1: Scaffold and mock world

- **Intent:** Create the scenario skeleton and the static mock catalog so every later step has deterministic data.
- **Expected Outcomes:**
  - `python wxodemo.py new-scenario pipeline-doc-gap --name "Pipeline Docs and Test Gap" --description "Platform-wide docs and test gap detection with draft PRs into existing review"` has run; manifest, evaluation stubs, demo-script copy and slide placeholder exist; status stays `soon`.
  - `tools/pdg/data/` holds the catalog for the 5 cases above across three countries.
- **Todo List:**
  - [ ] Run the scaffold command and review the generated files.
  - [ ] Define catalog fields: country, repo, pipeline id, description, inputs/outputs, schedule, doc status, tests folder presence, CI run history, committers, CODEOWNERS.
  - [ ] Encode cases A-E with a short comment per case saying what it teaches.
  - [ ] Confirm no tool/KB/agent name collides with other manifests.
- **Relevant Context:** `.bob/skills/wxo-scenario-authoring/SKILL.md`, `scenarios/incident-triage/scenario.yaml` (schema reference), `tools/incident_triage/data/`.
- **Status:** `[x] done` (scaffolded; mock data in `tools/pdg/data/catalog.py`, `ci_runs.py`, `ownership.py`; no name clash found by grep for `pdg` / `pipeline-doc-gap` before building)

### Sub-Task 2: Read-only tools

- **Intent:** Provide business-capability tools that let the agent decide its own next step.
- **Expected Outcomes:** Four read-only tools that take keys (country, repo, pipeline id) and return bounded, deterministic output or a structured error with a hint.
- **Todo List:**
  - [ ] `pdg_list_pipelines` (filter by country and optional gap type; capped list with summary counts).
  - [ ] `pdg_get_pipeline` (metadata plus doc and test status).
  - [ ] `pdg_get_ci_history` (recent runs; shows whether tests are executed).
  - [ ] `pdg_get_ownership` (CODEOWNERS and active committers; flags key-person risk).
  - [ ] Copy the import fallback pattern from `tools/incident_triage/incident_triage.py`.
  - [ ] Add `requirements.txt` pinning `ibm-watsonx-orchestrate==2.18.2`.
  - [ ] Write `tests/test_pdg_tools.py` covering each case, bad inputs and output caps; run pytest.
- **Relevant Context:** `tools/incident_triage/incident_triage.py` (docstring and error style), `tests/` (existing tool tests, for example `test_hr_tk_tools.py`).
- **Status:** `[x] done` (`tests/test_pdg_tools.py`, 37 tests pass)

### Sub-Task 3: Draft-PR tool with deterministic safeguards

- **Intent:** The one write action, constrained so that it is safe without an approval flow.
- **Expected Outcomes:** `pdg_create_draft_pr` returns a deterministic draft-PR record; rejects mismatched repo/pipeline/owner, paths outside `docs/` and `tests/`, and any attempt at a non-draft PR.
- **Todo List:**
  - [ ] Implement the tool with explicit validation and structured errors.
  - [ ] ID from `hashlib.md5` of inputs; no persistence.
  - [ ] Tests for every rejection path and for the success path.
- **Relevant Context:** `open_ticket` and `execute_remediation` in `tools/incident_triage/incident_triage.py`.
- **Status:** `[x] done` for the tool; the approval flow `flows/pipeline_doc_gap/pdg_request_draft_pr.py` was added (decision above) and is only syntax-checked.

### Sub-Task 4: Knowledge base

- **Intent:** Give the agent citable standards and per-country requirements.
- **Expected Outcomes:** KB `pdg_standards` with `.txt` documents, each carrying a stable ID, written as symptom first, then procedure.
- **Todo List:**
  - [ ] Documentation standard (`STD-DOC-01`) and test standard (`STD-TEST-01`), including README and test-skeleton templates.
  - [ ] One country requirements document per country (for example `REQ-FI-01`), including the requirement planted in case C.
  - [ ] KB yaml with `spec_version: v1`, `kind: knowledge_base`, name `pdg_standards`.
- **Relevant Context:** `knowledge/incident-triage/incident_triage_runbooks.yaml` and its `runbooks/` folder.
- **Status:** `[x] done` (six `.txt` documents; indexing in WXO not verified)

### Sub-Task 5: Agent definition and README

- **Intent:** Define the agent with instructions following the Incident Triage structure.
- **Expected Outcomes:** `agents/pipeline-doc-gap/agent.yaml` with the 5 tools and the KB; README with tools table, KB, mock data table, limitations and the draft-PR design note.
- **Todo List:**
  - [ ] Instructions sections: method, evidence standard (cite a standard ID; do not call a pipeline a gap on one signal), one pipeline at a time, clarifying-question rule, when to open a draft PR (only after the user asks for it), restraint (healthy pipelines get no action), "what you must not do".
  - [ ] Require the agent to report `pdg_create_draft_pr` output verbatim.
  - [ ] README limitations: mock only, metadata-only drafts, no real repo access.
- **Relevant Context:** `agents/incident-triage/agent.yaml`, `agents/incident-triage/README.md`.
- **Status:** `[x] done` (agent attaches the flow, not the write tool; README limitations written)

### Sub-Task 6: Manifest, ground truth, evaluation

- **Intent:** Make the scenario deployable and checkable.
- **Expected Outcomes:** `python wxodemo.py validate pipeline-doc-gap` prints OK; evaluation files cover cases A-E.
- **Todo List:**
  - [ ] Complete `scenario.yaml`: agent, tool package (`names` and `attached` both include `pdg_create_draft_pr`), KB, evaluation `tier: full`, demo script path.
  - [ ] `ground_truth.json`: `smoke_prompts` plus a case entry per A-E with expected gaps, expected tools and the red herring.
  - [ ] `eval_config.yaml` and `tc_*.json` test cases (at least cases A, B, E, plus one vague-input case).
  - [ ] Run `python wxodemo.py validate pipeline-doc-gap` and `python wxodemo.py eval pipeline-doc-gap --dry-run`.
- **Relevant Context:** `evaluation/incident-triage/`, `src/wxodemo/` (validation rules).
- **Status:** `[x] done` (`validate` prints OK; `smoke --dry-run` lists 5 prompts; `eval --dry-run` and `deploy --dry-run` print their commands; 6 test cases: A, B, C, D, E, vague). No eval run exists.

### Sub-Task 7: Deploy, live verification, demo script and slides

- **Intent:** Verify in a real WXO instance, then write the demo documents from observed behaviour only.
- **Expected Outcomes:**
  - Scenario deployed and smoke-tested; the user confirms each scene in the WXO chat; results recorded in a Live Verification Log in this plan.
  - `docs/demo/pipeline-doc-gap-demo.md` and `docs/demo/scenarios/pipeline-doc-gap.js` follow the `scenario-demo-docs` skill (six slides in fixed order, Target Fit card with Industry, Function, Target Roles).
  - **Slides only:** one card (on the benefits slide, or a short extra card on the mapping slide) describes the optional Bob integration: an agent-assisted developer in the repo takes the WXO agent's ranked target and writes real documentation and tests against the actual code, closing the "metadata-only drafts" limitation. The card says clearly that this is not implemented in this repo. It contains no invented numbers. No other file mentions Bob.
- **Todo List:**
  - [ ] `python wxodemo.py deploy pipeline-doc-gap`, then `python wxodemo.py smoke pipeline-doc-gap`.
  - [ ] User runs scenes in the chat: vague opening, main path (case A), trap (case B), country requirement (case C), key-person (case D), restraint (case E), draft PR request.
  - [ ] Record results in a Live Verification Log table below.
  - [ ] Fill the demo script (honest "not verified" rows until the user confirms; no invented figures).
  - [ ] Fill the slides; set `status: live` in slides and manifest only after the user confirms every scene.
  - [ ] `python docs/demo/build-demo-scripts-bundle.py`, `python wxodemo.py validate pipeline-doc-gap`, open `presentation.html`.
  - [ ] Add the root README row only after user confirmation.
- **Relevant Context:** `.bob/skills/scenario-demo-docs/SKILL.md`, `docs/demo/incident-triage-demo.md`, `docs/demo/scenarios/incident-triage.js`, `docs/demo/presentation.html`.
- **Status:** `[x] done`. Done: deploy and user browser runs (see the Live Verification Log), demo script and six slides written from those results, bundle rebuilt, manifest and slides set to `live`, root README row added on the user's instruction. Not done: the `REQ-DE-01` smoke anomaly on `de-payroll-feed` is open and, by the user's decision, left unfixed; no `eval` run exists.

## Live Verification Log

Source: `evaluation/pipeline-doc-gap/live-test-sheet.md`, filled in by the user in the WXO browser chat (agent `pipeline_doc_gap`). Bob did not drive these runs. Tester name, date, instance and LLM shown in the UI were not recorded. KB indexing delay (P6) was not recorded. Run counts are as reported by the user; no transcripts were saved in the repo.

| Scene | Prompt | Result reported by user | Changes made |
|---|---|---|---|
| P1-P5 | `login`, `deploy`, `status`, `agents list`, agent picker | All fine. `status`: `agents 1/1, tools 6/6, kbs 1/1` | None |
| P7 smoke (CLI) | 5 `smoke_prompts` A-E | All 5 completed. Agent claims on D (below) and E need review; see notes | None |
| 1 Vague opening | Which of the Finnish ones have documentation or test problems? | Pass, 3 runs | None |
| 2 Case A | Check pipeline fi-customer-ingest ... (with "Do NOT call pdg_request_draft_pr") | Pass/partial, 4 runs. `pdg_get_ci_history` not called (expected: optional). `pdg_standards` called in 3 of 4. Owner mentioned in 1 of 4 | None |
| 2b No unprompted PR | Check pipeline fi-customer-ingest for documentation and test gaps. | Pass, 4 runs. Lists gaps, offers a draft. After "yes" it showed the form, sometimes directly and sometimes after showing the README first. No form appeared unprompted | None |
| 3 Case B | Check pipeline se-invoice-batch ... | Pass, as expected (run count not stated) | None |
| 4 Case C | Check pipeline fi-claims-export ... including country requirements ... | Pass, 4 runs. When asked to continue, proposes a draft PR for the README data-residency section | None |
| 5 Case D | Check pipeline de-payroll-feed ... | Pass, 4 runs | None |
| 6 Case E | Check pipeline se-tax-report ... | Pass, 4 runs | None |
| 7a Approve | Create a draft PR with a README and a test skeleton for fi-customer-ingest. | Pass, 3 runs | None |
| 7b Reject | same prompt, click Reject | Pass, 3 runs | None |
| 7c Fallback reviewer | Create a draft PR with a test skeleton for de-payroll-feed. | Pass, 3 runs | None |
| 8 Ranking | Rank all pipelines by documentation and test risk and tell me which to fix first. | Pass, 4 runs | None |
| 9 Unknown pipeline | Check pipeline fi-orders-export for documentation and test gaps. | Pass, 3 runs | None |

**Observed in the user's pasted smoke output (CLI, 1 run per prompt), not reproduced in the browser runs:**

- Smoke D (`de-payroll-feed`): the agent reported a missing "Data residency" section under `REQ-DE-01`. That is wrong: `REQ-DE-01` requires "Employee data handling", which the README has. The agent did not call the knowledge base in that run. Scene 5 passed in 4 browser runs, so this may be a one-off. Not fixed; kept as an open item.
- Smoke E: the pasted text attributes the README sections to `pdg_get_ci_history`, not `pdg_get_pipeline`. Conclusion (no gap) was right.
- Smoke A cited `REQ-FI-01` "Data residency" for `fi-customer-ingest`; this is correct for a Finnish personal-data pipeline.
- Only the first characters of each smoke answer were pasted, so nothing beyond them is known.
