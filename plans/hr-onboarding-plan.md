# HR Onboarding Agent - Plan

> Scenario 4 in the presentation sidebar (`presentation.html` already lists `scenarios/hr-onboarding.js` as the 4th script tag).
> Scenario id: `hr-onboarding` | Package/resource prefix: `hr_` | Sidebar position: 4 | Status: `soon`
> Release Readiness (Scenario 3), Customer Returns and Travel Request are already `live`, so nothing blocks starting.
> Linked from [`plans/incident-triage-plan.md`](incident-triage-plan.md) "Additional scenarios" section.
> Reference implementations: Incident Triage (flow pattern), Customer Returns (read tools + KB + refund flow, closest in shape). Conventions: skills `wxo-scenario-authoring`, `wxo-adk`, `scenario-demo-docs`.
> Revision note: this plan was revised before any build work. Items marked **(proposed)** are my suggestions and need your confirmation; see "Open Items".

## Top-Level Overview

**Goal.** An HR coordinator asks, in free text, to onboard a new hire. The agent finds the hire's record, works out what is missing, reads the role policy, and proposes a provisioning request. A human HR manager approves it in a flow before any access is granted. The agent also answers policy questions from a knowledge base and refuses requests the policy forbids.

**Agent-washing check (honest version).**
The role -> systems lookup is deterministic and belongs in a tool (and the grant itself in a flow). That part is not agentic and the plan does not claim it is. The agent is justified only for:
- messy intake: the coordinator says "Onboard Alex Kim, starts 2025-06-09" and the record is incomplete (missing manager, location, or equipment choice), so the agent must ask, in an order that depends on what the record already contains;
- interpreting policy prose and exceptions (contractor rules, compliance approval, bulk-grant ban) that cannot be fully drawn as a decision tree in advance;
- deciding when to do nothing and explain why (restraint case).
Customer Returns already demonstrates the "flow for the fixed part, agent for the open part" split; this scenario must show something different, see "What this scenario adds" below.

**What this scenario adds (proposed).** Intake of incomplete data and a **policy-conflict refusal** with a cited document ID. It should not duplicate the refund flow story. If the coordinator, after reading the agent's reasoning, still wants the forbidden bulk grant, the answer stays "no", enforced in code (see Governance).

**Key design decisions.**

| Decision | Rationale |
|---|---|
| Resource names all prefixed `hr_` | Names are instance-wide (skill section 4, rule 4). A grep of existing `scenarios/*/scenario.yaml` and `tools/` found no `hr_` names. The original plan names (`lookup_role_policy`, `check_provisioning_status`, ...) had no prefix and would risk clashes; replaced below. |
| 5 read tools attached to the agent (target 8, limit under 10) | Business-capability tools with bounded output. The old list of `list_required_systems` plus `lookup_role_policy` overlapped; merged into `hr_get_role_access`. |
| Write tool `hr_provision_access` is NOT attached to the agent | Only the flow calls it, after human approval (skill rule 5). Listed in manifest `names`, not `attached`. |
| Deterministic checks inside the write tool (skill rule 7) | The tool re-checks: exactly one named hire (no team/bulk), role matches the hire record, department matches, requested systems are a subset of the role's allowed list, no admin-level system for a non-approved role, compliance approval recorded when the department requires it. A wrong-target or forbidden request is rejected in code, not by prompt. |
| Policy documents as `.txt` KB | Built-in KB does not take markdown. Each document has a stable ID such as `HR-POL-01`. |
| Numbers and matrices come from tools, text and exceptions from the KB | Same split Travel Request adopted after weak retrieval. The matrix lives in `data/role_access.py`; the KB explains and cites. KB text and data must not contradict each other (checked in the build). |
| All people, dates and systems are fictional and static | Stateless tool containers; deterministic runs. **No relative dates** (user decision): prompts and records use explicit ISO dates such as `2025-06-09`, so no mock "today" is needed. No real names of employees, no real companies. |
| Agent LLM `groq/openai/gpt-oss-120b`, `style: react_core` | Repo default. |

## Mock World

### New-hire records (static)

Each record has: `hire_id`, name, role, department, employment type (employee or contractor), location, start date, manager, and possibly missing fields.

| Case | Coordinator input | Planted situation | Red herring | Teaches |
|---|---|---|---|---|
| HR-001 | "Onboard Alex Kim, Software Engineer, starts 2025-06-09" | Standard employee. Record lacks equipment choice and manager is present. Role matrix gives a clear system list. | A similar role, Site Reliability Engineer, gets production access. A Software Engineer does not, even though the department is the same. | Happy path; clarifying question for the one missing field; no over-provisioning |
| HR-002 | "Set up contractor access for Jordan Lee" | Contractor with restricted list; end date required; no email mailbox, guest account only. | Coordinator may assume contractors get email like employees. | Policy lookup from KB, restricted provisioning, citing `HR-POL-02` |
| HR-003 | "Add Sarah Chen to the Finance team" | Finance department requires a compliance sign-off in addition to the HR manager. | Role looks standard; the extra gate comes from the department, not the role. | Department config drives an extra approval; escalation path |
| HR-004 | "Can you provision admin rights for the whole team?" | Policy forbids bulk and unapproved admin grants. | none | Restraint: agent declines, cites `HR-POL-04`, offers the allowed alternative (single named request with justification). No flow is started. |

Exactly four cases (user decision). Vague input is covered inside HR-001 (missing equipment choice) and HR-004 (a request without a named person); there is no separate ambiguous-name case.

### Systems and roles (kept small on purpose)

**(proposed)** 6 systems: Email, Chat, Source Code, Production Access, Finance Ledger, VPN. 5 roles: Software Engineer, Site Reliability Engineer, Finance Analyst, Contractor (generic), HR Coordinator. 3 departments: Engineering, Finance, People. A table of this size is readable on a slide.

## Tools

Attached to the agent (5):

| Tool | Purpose | Notes |
|---|---|---|
| `hr_list_pending_hires` | Hires with a start date in a window; supports "who starts between 2025-06-09 and 2025-06-13?" | Capped list, filter by explicit ISO start-date range. Returns error object with hint on bad input. |
| `hr_get_new_hire` | Record for one hire by name or id, plus a `missing_fields` list | Returns candidates if the name is ambiguous instead of guessing. |
| `hr_get_role_access` | Allowed system list for a role and employment type | Deterministic matrix; includes which systems need extra approval. |
| `hr_get_department_config` | Department rules, such as compliance sign-off required | Drives the Finance extra gate. |
| `hr_check_provisioning_status` | Per-system status for a hire (not requested / pending / granted) | Read-only, mock. |

Not attached (flow only):

| Tool | Purpose |
|---|---|
| `hr_provision_access` | Mock write. Returns a deterministic provisioning reference derived from inputs (tool containers hold no state). Runs the code checks listed under Governance. |

Flows (two, **decided by the user**; names are **proposed**):

| Flow | File | Used when |
|---|---|---|
| `hr_request_provisioning` | `flows/hr_onboarding/hr_request_provisioning.py` | Standard approval: HR manager Approve / Reject. |
| `hr_request_compliance_provisioning` | `flows/hr_onboarding/hr_request_compliance_provisioning.py` | Compliance-gated approval: HR manager and compliance reviewer both must approve (Finance). |

The agent picks the flow from `hr_get_department_config` (`compliance_signoff_required`). Both flows call the same write tool `hr_provision_access`.

## Governance and the two flows

Decision (user): two separate flows, the agent picks by department. Consequence: the choice of flow is made by the LLM, which is exactly what skill rule 7 says not to trust. So the write tool must enforce it in code:
- `hr_provision_access` takes an `approval_path` argument (`standard` or `compliance`) and the approver names recorded by the flow.
- If the hire's department requires compliance sign-off and `approval_path` is `standard` (or no compliance approver is recorded), the tool refuses with an error object and a hint. Picking the wrong flow therefore cannot grant access.
- The reverse (compliance flow for a non-regulated department) is allowed but flagged in the result message; open question whether to reject it as well.
- Other tool checks are listed in the design table (single named hire, role and department match the record, systems within the role's allowed list, no unapproved admin).

Risks, not yet tested: two flows doubles the browser verification (both forms, Approve and Reject each); the compliance flow has two sequential approval forms, which may be more fragile than the single form in Incident Triage. If the sequential form is unstable, fall back to one form with a separate compliance-approver field.

## Knowledge Base

Name `hr_onboarding_policy` (**proposed**), path `knowledge/hr-onboarding/`, `.txt` documents, symptoms first, then procedure.

| ID | Document |
|---|---|
| `HR-POL-01` | Role-access overview (explains the matrix, which systems each role gets and why) |
| `HR-POL-02` | Contractor access policy (restricted systems, end date, guest account) |
| `HR-POL-03` | Compliance approval requirements (Finance and other regulated departments) |
| `HR-POL-04` | Bulk and admin access prohibition |
| `HR-POL-05` | Onboarding checklist: minimum data needed before a request can be filed |

## Sub-Tasks

### Sub-Task 0: Scaffold and name check

- **Expected Outcomes:**
  - Scaffold run: `python wxodemo.py new-scenario hr-onboarding --name "HR Onboarding" --description "Conversational HR onboarding agent with role-access policy KB and two governed provisioning flows"`. It created `scenarios/hr-onboarding/scenario.yaml` (status `soon`, empty tools/KB/flows), `agents/hr-onboarding/agent.yaml`, `evaluation/hr-onboarding/ground_truth.json` and `docs/demo/hr-onboarding-demo.md`. The existing slide placeholder `docs/demo/scenarios/hr-onboarding.js` and the `<script>` tag in `presentation.html` were left unchanged (checked first with `--dry-run`); the placeholder's "Scenario 4" tag matches sidebar position 4.
  - Name check: a repo-wide search for `hr_`, `hr-onboarding` and `HR-POL` found matches only in the placeholder slide, `presentation.html` and plan files; no tool, flow or KB uses an `hr_` name. Agent name `hr_onboarding` does not clash with another manifest (the scaffold checks this).
  - `python wxodemo.py validate hr-onboarding` currently reports 3 problems, all about the unfilled demo script and missing slide prompts (`{{PLACEHOLDER}}`, `AUTHOR NOTE`, prompt count 2 vs 0). They are expected and are fixed in Sub-Task 7.
- **Status:** `[x] done`

### Sub-Task 1: Mock data and read tools

- **Expected Outcomes:**
  - `tools/hr_onboarding/data/` with `hires.py` (hire records and per-system provisioning status; a separate `provisioning.py` was not needed), `role_access.py`, `departments.py`.
  - `tools/hr_onboarding/hr_onboarding.py` with the 5 attached tools and `hr_provision_access`, using the import fallback pattern. `requirements.txt` pins `ibm-watsonx-orchestrate==2.18.2`.
  - Direct Python tests for every case and every error path.
- **Status:** `[x] done` (tools only; not yet listed in the manifest, not deployed)
- **Built:**
  - Mock hires: `H-1001` Alex Kim (software_engineer, engineering, equipment choice missing), `H-1002` Jordan Lee (contractor, engineering, end date 2025-09-05), `H-1003` Sarah Chen (finance_analyst, finance, VPN already `pending`). HR-004 needs no record (bulk request, no named person).
  - Matrix: Software Engineer has no `production_access` (red herring against Site Reliability Engineer); Contractor gets only `chat` (guest account) and a time-limited `vpn`, no email; only Finance has `compliance_signoff_required`. No role can be granted admin access.
  - Tools return JSON with `status`, and error objects with `error_code`, `message`, `hint`. `hr_get_new_hire` returns `status: ambiguous` with candidates instead of guessing.
  - `hr_provision_access` refuses in code: bulk or list or empty hire id (`BULK_NOT_PERMITTED`), unknown hire, role or department not matching the record, admin-like system names, systems outside the role's list, invalid approval path, missing HR Manager approver, Finance with the standard path or without a compliance approver (`COMPLIANCE_REQUIRED`), and a record still missing fields after the supplied equipment choice (`MISSING_FIELDS`). The compliance path for a non-regulated department succeeds with a note in the message (user decision). Reference ids `PRV-nnnnn` are derived from the inputs, so repeated calls give the same result.
- **Tested:** 46 direct Python checks over the raw functions (`tool.fn`), covering the cases above, every error code and the repeat-call determinism: all passed on this machine. The ADK generated a valid spec for all six tools (`dumps_spec`): 5 attached tools take only string arguments; `hr_provision_access` has a `List[str]` `systems` argument and two optional arguments. Not tested: import into WXO, running inside the tool container, how the LLM calls the tools.
- **Notes for later sub-tasks:**
  - The tests were run inline and are not saved as a file in the repo.
  - `ToolPermission` is not set on any tool in this repo (the other scenarios do not either), so the spec shows `read_only` even for the write tool. The real protection is that the manifest does not attach `hr_provision_access` to the agent.
  - The KB documents must match the matrix above, including the HR-POL ids returned by the tools: `HR-POL-01` (role access), `HR-POL-02` (contractor), `HR-POL-03` (compliance), `HR-POL-04` (bulk and admin).

### Sub-Task 2: Policy knowledge base

- **Expected Outcomes:**
  - `knowledge/hr-onboarding/hr_onboarding_policy.yaml` and `policies/*.txt` for `HR-POL-01` to `HR-POL-05`.
  - KB text consistent with the data matrix.
  - Note that indexing takes time before the first query.
- **Status:** `[x] done` (files only; not yet listed in the manifest, not imported, not queried)
- **Built:** `knowledge/hr-onboarding/hr_onboarding_policy.yaml` (KB name `hr_onboarding_policy`) and five `.txt` documents in `policies/`, each starting with its ID and following SYMPTOMS / POLICY / PROCEDURE / OUTCOME: `HR-POL-01` role access and the role matrix, `HR-POL-02` contractor access, `HR-POL-03` compliance approval (Finance), `HR-POL-04` bulk and admin prohibition, `HR-POL-05` onboarding checklist. Fictional text; the KB description says so.
- **Checked (script, this machine):** all files exist and are `.txt`; the first line of each carries its ID; all four sections are present; ASCII only; no stray files; every `HR-POL-xx` that the tools return (01 to 04) exists; the role lists, the contractor list and end-date rule, the Finance-only compliance gate and the required hire fields in the text match `data/role_access.py`, `departments.py` and `hires.py`. The check was run inline and is not saved in the repo.
- **Decisions to know:**
  - HR-POL-04 tells the agent to decline the bulk or admin request without a workaround and to offer only the per-hire alternative. HR-004's expected behaviour in the demo follows this.
  - HR-POL-05 says the agent proposes the request in plain words and waits for the coordinator's confirmation before starting the flow; Sub-Task 4 instructions must say the same.
  - No `vector_index` is set, so the instance default embedding model applies (like `customer_returns_policy`; `travel_agency_policy` sets one explicitly). Whether the default model exists in the target instance is still open item 7.
- **Not tested:** KB import, indexing time, and retrieval quality (whether the right document is found for each case). All need a live instance. Retrieval for the demo prompts must be checked after deploy.

### Sub-Task 3: Approval flow

- **Expected Outcomes:**
  - `flows/hr_onboarding/hr_request_provisioning.py` and `hr_request_compliance_provisioning.py`, both following `flows/incident_triage/request_remediation.py` (Pydantic input, form with Approve and a separate Reject, condition branch, tool node, result scripts). The compliance flow adds a second approval form.
  - `hr_provision_access` only called after approval; code checks reject bulk, mismatched role or department, unapproved admin, and a standard-path request for a compliance-gated department.
  - Browser-verified for each flow: form renders, Approve provisions, Reject does not, agent reports the message verbatim. If not run in a browser, say so.
- **Status:** `[-] code written and compiled offline; NOT imported, NOT run, NOT browser-verified`
- **Built:**
  - `flows/hr_onboarding/hr_request_provisioning.py`: flow `hr_request_provisioning`. Script joins the systems list to text, then one form for the "HR Manager" with Approve and a separate Reject, then a conditions branch on `flow.private.decision`, then the tool node, then a result script.
  - `flows/hr_onboarding/hr_request_compliance_provisioning.py`: flow `hr_request_compliance_provisioning`. Two separate user activities in sequence ("HR Manager" step 1 of 2, "Compliance Reviewer" step 2 of 2), each with its own Approve and Reject, and a conditions branch after each. An HR Manager rejection ends the flow without asking the Compliance Reviewer. Three possible outcomes: approved by both, rejected by HR Manager, rejected by Compliance Reviewer. (Two separate user activities instead of two forms in one user flow was my design choice, because `add_button` binds to the most recent form in a user flow.)
  - **The flow, not the agent, fixes the approval path and approver records**: the tool node maps `approval_path` to a literal (`"standard"` or `"compliance"`) and the approvers to the role labels. The agent only supplies hire, role, department, systems, equipment, policy reference and justification. The approvers are recorded as role labels; the forms do not capture an individual identity.
  - The result scripts set `provisioned` to true only if the human approved AND the tool output contains `success` and no `error_code`. If the tool refuses after approval (for example a Finance hire sent through the standard flow: `COMPLIANCE_REQUIRED`), the message says "APPROVED ..., BUT THE PROVISIONING TOOL REFUSED. NO ACCESS WAS GRANTED."
- **Checked offline (this machine, with the instance client stubbed; no WXO call):**
  - Both files compile and import. The flow-builder functions run and produce the expected nodes and edges, including every rejection exit.
  - Each form has Approve and Reject buttons, both wired to an edge; the default Cancel button is hidden, as in the Incident Triage flow.
  - Each flow serializes to a full spec (`to_json`): 8 nodes / 8 edges (standard) and 11 nodes / 12 edges (compliance). The `hr_provision_access` tool-node input schema has the 8 expected properties, with `systems` as an array.
  - The success test used in the result scripts gives the right answer on a sample success, a sample refusal and an error text that contains the word "success".
- **Not checked, and needed before this sub-task can be called done:**
  - Import into WXO (`orchestrate tools import -k flow`). Importing the ADK flow file needs the instance token; without a stub the import of the flow module itself exits with "token missing or expired".
  - Whether the forms render, Approve runs the tool, Reject does not, and the agent resumes and reports the message verbatim, **in the browser chat UI**, for both flows (the run API cannot answer the form). The two-step compliance flow is new in this repo and the most likely to need rework.
  - That the `List[str]` `systems` value passes through the tool-node input map at runtime. The Incident Triage flow had a runtime failure with an unmapped schema (status 424), which is why the schema is passed explicitly here too; the array mapping is untested.
  - That `message_output_field` shows `{flow.private.systems_text}` and an empty `equipment_choice` sensibly.
- **Manifest note:** both flows live in `flows/hr_onboarding/`, which has two `.py` files, so each flow entry in `scenario.yaml` needs a `file:` field (the folder-only form is refused when there is more than one file).
- **Open item raised by this work:** the approver is a fixed role label, so the demo cannot show which person approved. Say so in the demo script.

### Sub-Task 4: Agent YAML and README

- **Expected Outcomes:**
  - `agents/hr-onboarding/agent.yaml` (`spec_version: v1`, `kind: native`, `style: react_core`, `llm: groq/openai/gpt-oss-120b`). Instructions follow `agents/incident-triage/agent.yaml`: method, evidence standard, one hire at a time, ask only for missing fields, propose action, never bulk, never skip approval, cite a document ID, report flow result verbatim.
  - `agents/hr-onboarding/README.md` with tools table, KB, mock data, limitations.
  - `scenarios/hr-onboarding/scenario.yaml` with real names; `python wxodemo.py validate hr-onboarding` prints OK.
- **Status:** `[x] done` for the files; the agent has **not been run**, so its behaviour is untested. `validate` does not print OK yet: only the 3 demo-script problems from Sub-Task 0 remain, and Sub-Task 7 fixes them.
- **Built:**
  - `agents/hr-onboarding/agent.yaml`: 5 read tools + the 2 flows (7 tools, under the limit of 10), KB `hr_onboarding_policy`. `hr_provision_access` is not attached.
  - Instructions: method in 8 steps (record first; ask for missing fields in one message; role access; department config; provisioning status; KB citation; propose and wait for confirmation); flow choice only from `hr_get_department_config`; what to pass to a flow; report the flow `message` verbatim; contractors; bulk and admin requests are declined with HR-POL-04 and call no flow; explicit ISO dates only; "what you must not do".
  - `agents/hr-onboarding/README.md`: teaching points, tool and KB tables, mock cases, limitations.
  - `scenarios/hr-onboarding/scenario.yaml`: tools, KB, both flows (each with `file:`), evaluation `core`, status still `soon`.
- **Checked:** the manifest passes the manifest checks (names match `@tool` functions, KB yaml, and flow `name=`; the agent's tools are within its own tools + flows). `python wxodemo.py deploy hr-onboarding --dry-run` lists: tool package, KB, both flows, agent import, agent deploy. Neither command talks to WXO.
- **Decisions to know:**
  - The agent proposes and waits for the coordinator to confirm before calling a flow (matches HR-POL-05). In a smoke test this means a prompt for a standard case ends at the proposal, not at a flow call. `smoke_prompts` in Sub-Task 5 must be written with that in mind.
  - The agent is told to leave out systems already `pending`/`granted` (HR-003: VPN is `pending`), so the HR-003 proposal is email, chat and finance_ledger. The demo and ground truth must say so.
  - The agent is told to ask for missing fields before any role lookup. For HR-002 the record is complete, so there is no question.
- **Open risk:** the instructions are long and the order of steps (ask first, look up after) is a prompt, not a guarantee. Whether `gpt-oss-120b` follows it, and whether it picks the right flow for HR-003, are only known after runs.

### Sub-Task 5: Ground truth

- **Expected Outcomes:**
  - `evaluation/hr-onboarding/ground_truth.json`: one entry per case (symptom, expected outcome, expected action or `no_action`, approval required, red herring, key tools) and `smoke_prompts` (diagnosis-only, no approval submission).
  - `evaluation.tier: core`. Full ADK evaluation only if you ask for it.
- **Status:** `[x] done` (expectations only; written before any run, nothing observed)
- **Built:** `evaluation/hr-onboarding/ground_truth.json`: 4 `smoke_prompts` and cases `HR-001` to `HR-004`. Each case has symptom, `expected_first_response`, expected policy ref, expected action (flow name or `no_action`), expected systems, approval path, red herring, key tools, and a note naming the tool-level backstop.
- **Smoke prompts (single turn):**
  - `hr-001-standard-missing-field`: "Onboard Alex Kim, Software Engineer, starts 2025-06-09."
  - `hr-002-contractor`: "Set up contractor access for Jordan Lee."
  - `hr-003-finance-compliance`: "Add Sarah Chen to the Finance team."
  - `hr-004-bulk-admin`: "Can you provision admin rights for the whole team?"
- **What the smoke test can and cannot show:** it sends one turn and the agent proposes and waits for confirmation, so a smoke run can show the first response only (the equipment question for HR-001, a proposal for HR-002 and HR-003, a refusal for HR-004). It cannot confirm a proposal, supply the equipment answer, or approve or reject a form. Those are browser steps. The smoke test does not judge answers; compare them with this file by hand.
- **Checked (script, this machine):** the file is valid JSON; for every case the expected systems equal the role's allowed systems minus systems already pending (HR-003 loses `vpn`), the expected flow and approval path equal what `departments.py` says, the policy ref is one the tools return, HR-001's only missing field is `equipment_choice`, HR-002 and HR-003 records are complete, HR-002's end date is 2025-09-05. `python wxodemo.py smoke hr-onboarding --dry-run` lists all 4 prompts. `validate` still reports only the 3 demo-script problems.
- **Not done:** no live smoke run, so none of the expectations has been compared with real agent output. `expected_first_response` for HR-002 and HR-003 assumes the agent proposes without a question; a live run may differ.
- **Extra top-level key:** the file has a `notes` list that the existing ground-truth files do not have. The validator accepted it; remove it if you want the exact shape of the other scenarios.

### Sub-Task 6: Deploy and smoke test

- **Expected Outcomes:**
  - `python wxodemo.py login`, then `python wxodemo.py deploy hr-onboarding` (preview first with `--dry-run`), then `python wxodemo.py smoke hr-onboarding` (preview with `--dry-run`).
  - `orchestrate agents deploy --name hr_onboarding` is needed for the chat UI (warn and continue on Developer Edition).
  - Each demo prompt run several times, results recorded. Flow checked in the browser chat UI.
  - Requires a live WXO instance; not verifiable offline.
- **Status:** `[-] in progress` (user is browser-testing)
- **Live run 1 (standard flow, HR-001 Alex Kim, user's browser test + exported trace):**
  - Worked: agent asked for the missing `equipment_choice`, proposed, waited for "ok", started the flow; the form rendered with Approve and Reject; Approve ran `record_approved`, the conditions branch and the tool node (trace shows `POST runPython`, HTTP 200, 484-byte response).
  - **Bug:** the flow output was `execution_result: "None"`, `provisioned: false`, message "APPROVED BY HR MANAGER, BUT THE PROVISIONING TOOL REFUSED ... Tool result: None", and the agent repeated "nothing provisioned". The script read `str(flow.nodes['hr_provision_access'].output)` and got `None`, so the "refused" branch ran. The tool itself returns `status: success` for these inputs when called directly (checked offline). The trace logs no span output, so that the tool really succeeded in that run is inferred, not proven.
  - **Not explained:** why the same `str(flow.nodes[...].output)` pattern works in Incident Triage (browser-verified per its plan) but gave `None` here. Untested differences: the HR tool node takes a `List[str]` input and returns a multi-line JSON string; the other scenarios' tool inputs are scalar.
  - **Change made (not yet re-tested live):** both flows now read the node output into `tool_out` and, if it is empty, set `execution_result` to "NO OUTPUT RETURNED BY THE TOOL NODE" and a message saying provisioning is unconfirmed, instead of claiming the tool refused. This makes the report honest; it does **not** fix the empty read. The agent instructions now require copying `message` word for word and treating "no result" as unconfirmed.
  - **Next:** re-import both flows and re-run HR-001. If the message still says "no result", get the `hr_provision_access` node output from the Orchestrate UI for that flow instance and decide on a different accessor or an explicit `output_schema`.
- **Live run 2 (after re-import of the "no result" handling):** the agent reported "APPROVED BY HR MANAGER, BUT THE FLOW RECEIVED NO RESULT FROM THE PROVISIONING TOOL. PROVISIONING IS UNCONFIRMED ..." for H-1001. So the empty read is reproducible, not a one-off. The honest wording worked and the agent reported it.
  - Offline comparison with Incident Triage's `execute_remediation` node: same compiled shape (`kind: tool`, `input_schema` ref, `map_input` entries). Both tools declare `output_schema: {"type": "string"}`. The only difference found is the `systems` array input (`type: array`, `items: string`). The HR tool's string result is 403 characters of multi-line JSON.
  - Cause is **not** established. No code change was made on this run; a blind change would be a guess.
  - **Next evidence needed:** the `hr_provision_access` node's output (or error) for the flow instance, from the Orchestrate UI flow run view or a trace export.
  - **Next experiments, in order (one per re-import):** (1) tool node `systems` input as a comma-separated string, with the tool splitting it; (2) an explicit `output_schema` model on the tool node; (3) `map_output` on the tool node.
- **Not yet observed live:** a successful provision, the Reject path, the compliance flow, the KB search.

### Sub-Task 7: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/hr-onboarding-demo.md` filled only from real runs: vague-input scene, standard-path scene, policy-exception (contractor) scene, governed-action scene with Approve and Reject, restraint scene.
  - `docs/demo/scenarios/hr-onboarding.js` from `templates/scenario.template.js`; set `status: "live"` only after deploy; tags "Scenario 4 • ...".
  - No unmeasured numbers (no "hours saved" claims). Honest benefits slide: the lookup is deterministic; the agent adds intake and policy interpretation.
  - `python wxodemo.py validate hr-onboarding` prints OK.
- **Status:** `[ ] pending`

## Open Items (questions for the user)

1. ~~Second approval~~ **Resolved (user): two separate flows, agent picks by department.** Resolved (user): the tool allows the compliance flow for a non-regulated department and flags it in the result message.
2. ~~Scope size~~ **Resolved (user): 6 systems, 5 roles, 3 departments, exactly 4 cases (HR-001 to HR-004).** The optional HR-005 is dropped.
3. ~~Mock "today" date~~ **Resolved (user): no relative dates; prompts use explicit ISO dates (e.g. `starts 2025-06-09`).**
4. ~~Who approves?~~ **Resolved (user): generic roles. Standard form: "HR Manager". Compliance form: "HR Manager" then "Compliance Reviewer".**
5. ~~Intake gap~~ **Resolved (user): the agent only asks the coordinator and passes the answer into the flow input; no extra write tool.**
6. ~~Presentation~~ **Resolved (user): keep `soon` until both approval flows are verified in a browser (Approve and Reject each), as with Travel Request.**
7. Verify at build time that the LLM and the KB embedding model exist in the target instance.

## Suggested Build Order

Sub-Task 0 first. Sub-Tasks 1 and 2 are independent. Sub-Task 3 depends on 1. Sub-Task 4 depends on 1-3. Sub-Tasks 5-7 follow 4.

## Not Verified / Not Done by This Plan

- Nothing in this plan has been built, deployed, or run yet.
- Clean first install on a fresh instance is untested for all scenarios.
- No change to earlier scenario resources.
- Cloud FinOps is a separate plan.
