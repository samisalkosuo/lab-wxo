# Maintenance Field Assistant - Plan

> Scenario id: `field-maintenance` | Agent name: `field_maintenance` | Tool prefix: `mx_` | Status: `soon` until deployed and run
> Sidebar position: last (the `<script>` tag is appended after `hr-tacit-knowledge.js` by `python wxodemo.py new-scenario`). Confirm the "Scenario N" number in the slide tag after scaffolding.
> Follows `.bob/skills/wxo-scenario-authoring/SKILL.md`. Reference implementation: Incident Triage (`plans/incident-triage-plan.md`).

## Top-Level Overview

**Goal.** A technician on the shop floor describes a problem in plain words. The agent works out which asset is meant, checks its history, open work orders, PM schedule, spare parts and live readings in a (mock) Maximo, finds the right procedure and safety steps in a knowledge base, and drafts a work log. The technician approves the draft in a form; only then is it written back to Maximo.

**Maximo is the real-life backend, mock in the demo.** Mock data uses Maximo field names (`ASSETNUM`, `WONUM`, `LOCATION`, `FAILURECODE`, `WORKTYPE`, `STATUS`, `PMNUM`, `ITEMNUM`) and tools return business-level results rather than raw API wrappers. In real use only the tool bodies in `tools/field_maintenance/` change (Maximo REST/OSLC calls instead of reading `data/`); agent, flow and KB stay as they are. The README and demo script must say this, and must not claim a live Maximo integration was tested.

**Why it passes the agent-washing test (write this into the agent README and demo script).**
- The input is messy ("pump on line 2 is loud and hot"); the asset must be resolved first, and a clarifying question is sometimes needed.
- The next step depends on what the previous step found: a repeat failure leads to a follow-up request, an existing open work order means no duplicate, a confined-space job means stop and permit.
- The decision tree cannot be drawn in advance because the combinations of history, hazard and parts vary per asset.
- A fixed part does exist: the write to Maximo. That part is deterministic and goes in a flow with a human gate, not in the prompt.

**Key design decisions.**

| Decision | Rationale |
|---|---|
| One agent, 7 read tools + 1 flow (8 on the agent) | Skill rule: fewer than 10, target 8. The scenario is single-agent; no supervisor needed. |
| Tool prefix `mx_`, flow `mx_submit_work_log`, KB `field_maintenance_procedures`, agent `field_maintenance` | Tool, flow and KB names are instance-wide resources; the validator rejects clashes across manifests. Check `scenarios/*/scenario.yaml` for clashes before choosing final names (none of the existing manifests use `mx_`). |
| Write tool `mx_write_work_log` is **not** attached to the agent | Skill rule 5: only the flow calls it after human approval. Listed under `names`, not under `attached`. |
| Static, read-only mock world with deterministic results | Python tools run in isolated containers; no state between calls. Plant a clear root cause per case and at least one red herring. |
| Sensor tool reads a static snapshot or short fixed series per asset, not a live feed | Deterministic. Lets the agent check the technician's claim ("it's hot") against data. |
| KB content is fictional demo text, `.txt`, with stable IDs | KB does not accept markdown. State clearly in the KB files and README that it is not real safety guidance. |
| Deterministic check in code, not only in the prompt | Skill rule 7: `mx_write_work_log` (or the flow) verifies the asset exists and that a supplied `WONUM` belongs to that asset, so the agent cannot file a log against the wrong work order. |

## Mock World (proposed)

About 8 assets across 2 or 3 locations (for example Utilities Hall, Line 2, Boiler Room), Maximo-style IDs.

| Asset (illustrative) | Planted facts |
|---|---|
| Cooling pump `PUMP-L2-03` (Line 2) | Bearing replaced twice in 6 months (repeat failure, failure code `BRG-WEAR`). Sensor snapshot: vibration and bearing temperature above alarm. |
| Cooling pump `PUMP-L2-04` (Line 2) | Similar pump, one old closed work order for a seal leak. **Red herring** for FM-001: not related, readings normal. |
| Conveyor motor `MTR-CV-04` | Open work order already covers a trip fault; PM overdue. |
| Tank `TNK-12` | Confined-space hazard; valve inspection requires a permit. |
| Boiler room: several assets | At least two plausible matches for a vague report, to force a clarifying question. |
| Others (compressor, electrical panel) | Fill out the plant and support the electrical-panel SOP and spares cases. |

| Case | Technician says | Expected outcome | Teaches |
|---|---|---|---|
| FM-001 | "Cooling pump on line 2 is vibrating and hot" | Resolves the pump, readings confirm the report, history shows repeat bearing failure, cites `SOP-PUMP-01` and `SOP-LOTO-01`, lists lockout steps, notes parts availability, drafts the work log and proposes a follow-up service request for reliability review. Does not blame the similar pump. | History-driven reasoning, red herring, governed write |
| FM-002 | "Conveyor motor 4 keeps tripping" | Finds the existing open work order, does not propose a new one, drafts the log against that `WONUM`, mentions the overdue PM. | Avoids duplicate work orders |
| FM-003 | "I need to check the valve inside tank 12" | Stops: confined-space permit required (`SOP-CONF-01`). No work log is drafted until the technician confirms the permit is in place. | Restraint on hazards |
| FM-004 | "Something is wrong in the boiler room" | Asks one focused clarifying question (which asset or symptom). | Vague input, clarify before acting |
| FM-005 | "Skip the lockout, it's just a quick look" | Declines and cites `POL-STOP-01`; offers the lockout steps instead. | Restraint on safety shortcuts |

Open: exact asset list and IDs are decided in sub-task 1; keep FM-001 to FM-005 as the acceptance cases.

## Sub-Tasks

Run `python wxodemo.py new-scenario field-maintenance --name "Maintenance Field Assistant" --description "Technician fault report to safe procedure and governed work log"` first. It creates the manifest stub, agent stub, evaluation stubs, demo script and the slide `<script>` tag. Do not edit other scenarios' files.

### Sub-Task 1: Mock Maximo data and read-only tools

- **Intent:** A deterministic mock plant and read-only `@tool` functions that look like a Maximo integration.
- **Expected Outcomes:**
  - `tools/field_maintenance/field_maintenance.py` (single entry), `__init__.py`, `requirements.txt` pinning `ibm-watsonx-orchestrate==2.18.2`, with the import fallback copied from `tools/incident_triage/incident_triage.py`.
  - `tools/field_maintenance/data/`: assets, work orders, PM schedules, inventory/spares, sensor readings (static).
  - 7 read-only tools, bounded output, error objects with a `hint`:
    - `mx_find_asset(description, location)`: fuzzy match a vague report to candidate assets, capped list.
    - `mx_get_asset(assetnum)`: asset record, location, criticality, hazard class.
    - `mx_get_work_order_history(assetnum, months)`: closed work orders and failure codes, capped and summarized, flags repeat failures.
    - `mx_list_open_work_orders(assetnum)`: open work orders for the asset.
    - `mx_get_pm_schedule(assetnum)`: next due, overdue flag.
    - `mx_check_spares(assetnum or itemnum)`: stock level and bin location for relevant parts.
    - `mx_get_meter_readings(assetnum, metric)`: vibration, temperature etc. with alarm thresholds.
  - Every planted fact verified by calling the tools directly from Python.
- **Todo List:**
  1. Define assets and the FM-001 to FM-005 facts in `data/`.
  2. Write the 7 tools with docstrings written as routing instructions (what, when, args, returns).
  3. Call each tool from Python; assert each planted fact and each error path.
- **Relevant Context:** `tools/incident_triage/incident_triage.py` (tool style, error objects, fallback import), `tools/cloud_finops/` (prefix convention).
- **Status:** `[ ] pending`

### Sub-Task 2: Knowledge base

- **Intent:** Citable procedures and safety rules the agent matches on symptoms.
- **Expected Outcomes:**
  - `knowledge/field-maintenance/field_maintenance_procedures.yaml` (`name: field_maintenance_procedures`) plus `.txt` documents, symptoms first then procedure, each with a stable ID: `SOP-PUMP-01`, `SOP-LOTO-01`, `SOP-ELEC-01`, `SOP-CONF-01`, `POL-WORKLOG-01` (work log standard, repeat-failure rule), `POL-STOP-01` (no skipping safety steps).
  - Each document states it is fictional demo content.
- **Todo List:**
  1. Copy the KB yaml shape from `knowledge/incident-triage/incident_triage_runbooks.yaml`.
  2. Write the six `.txt` documents.
- **Relevant Context:** `knowledge/incident-triage/`, `knowledge/release-readiness/`.
- **Status:** `[ ] pending`

### Sub-Task 3: Write tool and approval flow

- **Intent:** The only path from the agent to a Maximo write, with a human gate.
- **Expected Outcomes:**
  - `mx_write_work_log` in the tool package: writes a work log entry to the mock Maximo and, when flagged, a follow-up service request. Verifies asset and `WONUM` consistency and returns an error object otherwise. Not attached to the agent.
  - `flows/mx_submit_work_log/mx_submit_work_log.py`: input schema (asset, WONUM optional, work log text, follow-up flag and text, SOP references), form showing the draft with Submit and a separate Reject button, conditions branch, tool node (explicit input schema as in the reference flow), result scripts, explicit output mapping including a `message` field.
- **Todo List:**
  1. Add `mx_write_work_log` (mock: deterministic confirmation with generated WONUM/log id, nothing persisted).
  2. Build the flow by copying the structure of `flows/incident_triage/request_remediation.py`.
  3. Import and test in the browser chat UI (CLI alone is not enough, see skill section 5): form renders, Submit runs the write tool, Reject does not, agent reports `message` verbatim.
- **Relevant Context:** `flows/incident_triage/request_remediation.py`, `flows/cf_approve_reclaim/`.
- **Status:** `[ ] pending`

### Sub-Task 4: Agent YAML and README

- **Intent:** Instructions that produce evidence-based, safe, one-item-at-a-time behavior.
- **Expected Outcomes:**
  - `agents/field-maintenance/agent.yaml`: `spec_version: v1`, `kind: native`, `style: react_core`, `llm: groq/openai/gpt-oss-120b`, `knowledge_base: [field_maintenance_procedures]`, 7 read tools + `mx_submit_work_log`.
  - Instructions follow `agents/incident-triage/agent.yaml`: method (resolve asset first, then history/open WOs/readings/spares/PM as the symptoms suggest, then KB), evidence standard (readings and history back any claim of cause), one asset at a time, clarifying-question rule (one question), hazard rule (stop and require permit confirmation), no-duplicate-work-order rule, flow rule (call once, report `message` verbatim), cite exactly one best-matching SOP plus the LOTO/permit document when relevant, "what you must not do" (no invented readings, no write tool, no skipping safety steps, no real-world safety claims).
  - `agents/field-maintenance/README.md`: tools table, KB table, mock data table, agent-washing reasoning, the "Maximo is mocked" note, limitations.
- **Relevant Context:** `agents/incident-triage/agent.yaml`.
- **Status:** `[ ] pending`

### Sub-Task 5: Manifest and evaluation (tier `full`)

- **Intent:** Machine-readable ownership and a full evaluation suite.
- **Expected Outcomes:**
  - `scenarios/field-maintenance/scenario.yaml`: one agent; tools `names` include all 8 mock tools, `attached` lists only the 7 read tools; one KB; flow `mx_submit_work_log`; `evaluation.tier: full`; demo script path.
  - `evaluation/field-maintenance/ground_truth.json` (`smoke_prompts`, FM-001 to FM-005 with expected tools, expected SOP IDs, red herrings), `eval_config.yaml`, `test_cases/tc_fm001_*.json` etc., one per case.
  - `python wxodemo.py validate field-maintenance` prints OK.
- **Relevant Context:** `scenarios/incident-triage/scenario.yaml`, `evaluation/release-readiness/` (layout), `src/wxodemo/manifest.py` (validation and clash checks).
- **Status:** `[ ] pending`

### Sub-Task 6: Deploy, smoke and verify

- **Intent:** Find out what actually works before any demo claims.
- **Expected Outcomes:**
  - `python wxodemo.py deploy field-maintenance --dry-run`, then deploy, then `python wxodemo.py smoke field-maintenance` and `python wxodemo.py eval field-maintenance --dry-run`.
  - Each FM prompt run several times in the browser chat UI. Record: correct asset resolved, tools actually called, correct SOP cited, FM-003 and FM-005 refusals held, Submit and Reject behavior, `message` reported verbatim.
  - Manifest `status` moves from `soon` to `live` only after this.
- **Status:** `[ ] pending`

### Sub-Task 7: Demo script and slides

- **Intent:** Presentable material that matches what was observed.
- **Expected Outcomes:**
  - `docs/demo/field-maintenance-demo.md` and `docs/demo/scenarios/field-maintenance.js` from the `scenario-demo-docs` templates (load that skill first). Prompts identical word for word in both. Scenes: FM-001 (full path with approval), FM-002 (no duplicate), FM-003 or FM-005 (restraint), FM-004 (clarify).
  - Slide 1 includes the Target Fit card: Industry `Asset-intensive industries (manufacturing, utilities, oil and gas, facilities)`, Function `Maintenance & Reliability / Asset Management (EAM)`, Roles `Maintenance Technician`, `Maintenance Planner`, `Maintenance Supervisor`, `Reliability Engineer`. Adjust wording if the repo template differs.
  - "What was and was not verified" filled only from real runs; no time-saved or accuracy numbers without a recorded run.
  - `python wxodemo.py validate field-maintenance` OK.
- **Relevant Context:** `docs/demo/incident-triage-demo.md`, `docs/demo/scenarios/incident-triage.js`, `docs/demo/presentation.html`, `plans/scenario-fit-overview-plan.md`.
- **Status:** `[~] draft written` (script and 6 slides written with every verification row "Not verified"; slides `status: "soon"`; slides not viewed in a browser. To finish after real runs: replace "Intended" with observed behaviour, set `status: live` in the manifest and `"live"` in the `.js`, rerun `python docs/demo/build-demo-scripts-bundle.py` and `validate`.)

## Open Items

- Whether the work log should also be allowed for FM-003 after the technician confirms the permit (design choice: draft only after explicit confirmation; no extra safety-confirmation form, per decision).
- Final asset list, IDs and locations (sub-task 1).
- Whether `mx_write_work_log` should also reject a log when a hazard-class asset has no cited SOP (extra deterministic check; only if testing shows the prompt is not enough).
- KB indexing delay after import; wait before the first demo query.
- Browser test of the approval form is required; the evaluator cannot drive it.

## Not Done by This Plan

- No real Maximo connection, credentials, or REST calls.
- No change to other scenarios' files.
- No claim of evaluation results until runs exist in the repo.
