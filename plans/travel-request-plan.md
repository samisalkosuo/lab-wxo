# Travel Request and Approval Agent - Plan

> New scenario, added after the four planned Phase B/C scenarios.
> Scenario id: `travel-request` | Sidebar position: 6 | Status: `soon` (deployed on `techzone1`; stays `soon` until the approval flow has been seen working in a browser)
>
> **State at the last update:** Sub-Tasks 1 to 8 are built and deployed. The design changed twice during the build (see "Design changes"). Evidence is limited to the runs listed under Findings. The approval form (Approve, Reject, request id) has **not** been verified in a browser.
> Reference implementation: [`plans/incident-triage-plan.md`](incident-triage-plan.md). Conventions: skills `wxo-scenario-authoring`, `wxo-adk`, `scenario-demo-docs`.

## Top-Level Overview

**Goal.** An employee asks, in free text, whether a business trip may go ahead. The agent reads the rules, checks employee and budget facts, and answers **Approved**, **Needs approval** or **Denied**, with reasons, Finnish source references, an estimated reimbursement, and a **request ID**. The request ID is the handoff key for other apps or agents (booking, expense claims). The agent does not book, pay or process claims.

**Source document.** `knowledge/travel-request/VM_2025_63.pdf` (moved there from `pdf/`), *Valtion matkustussääntö 2026* (Valtiovarainministeriön julkaisuja 2025:63, 40 pages as counted by pypdf, Finnish). It is the collective agreement on compensation of travel costs. Read in full while planning. It defines when a trip counts as an official trip (3 §), the travel mode principle (5 §), mileage (6 §), per diem thresholds and amounts (9-12 §), free-meal reductions (13 §), meal allowance (14 §), accommodation (15 §), night travel allowance (16 §), travel day compensation (19 §), claim deadline (21 §) and a per-country per diem annex for 2026. It does **not** contain agency budgets, grade limits or approver levels. Those come from a small **mock agency policy** that this scenario writes (fictional, labelled as such).

**Why it passes the agent-washing test.**
- Input is messy and incomplete ("I need to go to Brussels next month"); the agent must ask what is missing (dates, purpose, mode, free meals).
- The next step depends on what was found: purpose may exclude the trip (3 §), a cheaper mode may cap reimbursement (5 §), free meals change the amount (13 §), budget may force an approval level.
- The policy is prose with exceptions, so the full decision tree cannot be drawn in advance.
- What a flowchart handles correctly stays in code: amounts, thresholds, budget comparison, request ID creation, approval gate. The agent's job is intake, interpretation, exceptions and explanation.

**Language requirements (current; the user changed them during the build, see "Design changes").**
- The user writes **English only**. The agent answers in English, including the outcome words APPROVED, NEEDS APPROVAL and DENIED.
- The source document stays Finnish. The agent searches `travel_state_rules` with **Finnish queries** and cites the document in Finnish (for example `Valtion matkustussääntö 2026, 13 §`). It never presents a translation of the document as a quotation; it explains the rule in its own English words next to the Finnish reference.
- The mock agency policy is our own text and is written in **English**.
- Language switching, Finnish prompts and Finnish answer quality are **no longer requirements**.

## Design changes during the build

1. **Bilingual to English-only (user instruction: "Only English used by user. But still uses Finnish PDF.").** The first design had Finnish and English users, language switching in one chat and a Finnish mock policy. After the change the six policy files were translated to English (`tp_*` files), the ground truth was rewritten as version 1.1 with English prompts, and the agent instructions were rewritten. The old Finnish-prompt rounds are history only.
2. **Spike round 2 skipped on the user's instruction** ("Proceed as planned... assume that everything works. It will be the task of the user to see errors."). The embedding model was therefore locked on round 1 evidence: `ibm/granite-embedding-278m-multilingual` for both knowledge bases. This was a judgement, not a measured improvement.
3. **Numbers moved out of retrieval into tools** because round 1 retrieval was unreliable (best result 11 of 20 correct).

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Two knowledge bases: `travel_state_rules` (the unmodified PDF) and `travel_agency_policy` (mock `.txt`) | Keeps the real source and the fictional policy separate and citable; the agent can say which one a rule comes from. |
| The PDF is shipped **unmodified** with attribution (user decision, option A) | The PDF is CC BY-NC-ND 4.0. Not splitting or rewriting it limits the derivative-work risk. Licensing stays an open item to confirm. |
| Numbers come from tools, not from retrieval | ADK agent-design docs list RAG as poor for factual truth and policy enforcement. Rates and thresholds are hand-keyed from the PDF into a small data module; the PDF supplies explanation and citation. |
| Hand-keyed subset only: 2026 domestic per diems, mileage, night allowance, travel day compensation, a few countries | Keeps the transcription small. Every value carries its section and an effective-until date (31.12.2026). |
| Mock agency policy is written in English (changed from Finnish) | It is our own text; the user writes English only. The Finnish source is the only Finnish text. |
| Three outcomes (Approved / Needs approval / Denied), not yes/no | Most policies have a conditional case; forcing two outcomes makes the agent invent certainty. |
| Request ID issued by an internal write tool called only by a flow after the decision | Write actions never go on the agent (skill rule 5). The ID is derived deterministically from the inputs, because tool containers hold no state between calls. |
| The issuing tool re-checks traveler, decision, estimated cost and approver level against mock data | Skill rule 7: validate in code what a prompt cannot guarantee (Incident Triage still has an open wrong-target case). |
| All employees, budgets and the "current date" are static mock data | Stateless containers; deterministic runs. |
| Agent LLM `groq/openai/gpt-oss-120b`, `style: react_core` | Repo default; instructions follow the ADK GPT-OSS guidance (knowledge base first, minimal clarifying questions, cite sources). |
| Names prefixed `travel_` for every tool, flow and KB | Names are instance-wide resources; a repo search found no existing `travel` names. |

## Mock World

Hand-keyed 2026 values, all taken from `knowledge/travel-request/VM_2025_63.pdf` (the keyed values and section references should still be re-verified against the PDF; only 3 § and 13 § were re-checked, in the demo script work):

| Item | Value | PDF section |
|---|---|---|
| Domestic partial per diem | 25 EUR, trip over 6 h | 10 §, 11 § |
| Domestic full per diem | 54 EUR, trip over 10 h | 10 §, 11 § |
| Per diem condition | trip reaches over 15 km from home or workplace, both ways | 9 § |
| Free meals | per diem reduced by 50 percent; full domestic and foreign per diem need two meals, partial needs one; hotel breakfast does not count | 13 § and its application guidance |
| Meal allowance | one quarter of the full per diem, trip over 4 h, over 10 km, no per diem due | 14 § |
| Night travel allowance | 16 EUR per day | 16 § |
| Travel day compensation | 55 EUR domestic, 150 EUR abroad, with conditions | 19 § |
| Mileage, car | 55 c/km for the first 5000 km of the year, 49 c/km after | 6 § |
| Foreign per diem, sample | Belgia (BE) 81, Saksa (DE) 78, Ruotsi (SE) 70, Viro (EE) 82, Yhdysvallat (US) 86 | Annex |
| Foreign partial-day rule | over 2 h beyond last full travel day: 35 percent; over 10 h: 65 percent | 12 § |
| Validity | agreed to 31.12.2026; 2027 amounts are agreed separately | footnote to the title page, abstract |

Mock employees (fictional names, grade, manager, cost center, remaining budget) and a short mock agency policy (six English `.txt` files, ids `TP-AUTH-01`, `TP-APPR-01`, `TP-BUDGET-01`, `TP-PURPOSE-01`, `TP-ABROAD-01`, `TP-HANDOFF-01`).

Cases as built (all prompts English; the full prompts and expected values are in `evaluation/travel-request/ground_truth.json`, version 1.1). The expected amounts are the output of `travel_estimate_reimbursement` for the stated inputs, not an independent calculation from the PDF.

| Case | Planted situation | Expected outcome | Teaches |
|---|---|---|---|
| TR-001 | Domestic day trip, 8 h, E-1001 | APPROVED, 25 EUR | Happy path |
| TR-002 | Brussels, 50 h, lunch and dinner provided, hotel breakfast, E-1002 | NEEDS APPROVAL (manager Mika Laine), 361 EUR; abroad means manager although under 600 EUR; breakfast is not a free meal (13 §) | Reading the rule exactly |
| TR-003 | "I need a trip to Brussels next month." (single turn; the demo adds a second message with the facts) | Ask the missing facts, no decision | Vague input |
| TR-004 | Berlin conference plus a holiday week, E-1003 | NEEDS APPROVAL (manager Katri Heikkinen), 763.3 EUR, holiday excluded | Exception handling |
| TR-005 | Own car 400 km, train costs 60 EUR, E-1001 | APPROVED, 85 EUR (mileage capped to 60) | Policy beats the request |
| TR-006 | Refund status question | Out of scope, no tool, no id | Restraint |
| TR-007 | Trip in 2027, E-1003 | APPROVED, no estimate (`RATES_NOT_AVAILABLE`). The expected outcome was refined after earlier runs: a missing estimate must not become DENIED | Honest limits |
| TR-008 | Rovaniemi, estimate 709 EUR, CC-200 has 700 EUR left, E-1004 | NEEDS APPROVAL (director Pekka Salonen) | Deterministic budget check |

## Tools, Knowledge, Flow

Attached to the agent (4 tools, 1 flow and 2 knowledge bases; limit is under 10):

| Name | Kind | Purpose |
|---|---|---|
| `travel_get_employee_profile` | read tool | Grade, manager, cost center for an employee id |
| `travel_get_budget_status` | read tool | Remaining travel budget for a cost center, compared with an estimated cost |
| `travel_get_per_diem_rate` | read tool | Foreign per diem by country name (Finnish or English) or ISO code; returns amount, annex reference, effective-until date, error object with hint for unknown countries (8 countries keyed) |
| `travel_estimate_reimbursement` | read tool | Deterministic estimate from hours, nights, country, free meals, mode and kilometres; returns line items with section references |
| `travel_submit_request` | flow | Approval form, then issues the request ID |
| `travel_state_rules` | knowledge base | The PDF |
| `travel_agency_policy` | knowledge base | Mock agency policy |

Internal, not attached: `travel_issue_request_id` (write tool, called only by the flow; listed under `names` and not under `attached` in the manifest).

Tool inputs and outputs are language-neutral (codes, numbers, section references). Country lookup accepts Finnish and English names because the annex uses Finnish names. `Finland`, `Suomi` and `FI` count as domestic. `max_distance_km <= 0` means unknown and defaults to 100 with an assumption note. The agent calls the flow under the name `submit_travel_request_for_approval` (its display name), not `travel_submit_request`.

## Sub-Tasks

### Sub-Task 0: Retrieval spike (gate for everything else)

- **Intent:** The default embedding model is `ibm/slate-125m-english-rtrvr-v2`, and the source is Finnish while users may ask in English. Find out whether retrieval works before building on it.
- **Expected Outcomes:**
  - A throwaway KB with the unmodified PDF imported and indexed.
  - 10 Finnish and 10 English questions run against it; for each, which section was returned and whether it was right.
  - Written result in this plan's Findings section. If retrieval is poor, the decision is recorded: set another `embeddings_model_name` (only if available in the instance, to be checked), or let the agent query in Finnish, or add Finnish synonyms to the mock policy.
  - Whether the annex table and the 13 § application guidance survive indexing.
- **Todo List:**
  0. [x] Move `pdf/VM_2025_63.pdf` to `knowledge/travel-request/VM_2025_63.pdf` (shell move; check size and hash; remove the empty root `pdf/` folder). Done: SHA256 `4578981E81975AF58622EB08AF3C3CBABD60ADEC389467C8ECB496D6DD561C40` identical before and after, 310803 bytes, root `pdf/` folder removed.

  1. [x] Check which embedding models the instance accepts (`orchestrate models list` shows only LLMs; models were probed by importing a KB). See Findings.
  2. [x] Import a temporary KB YAML with the PDF; wait for indexing, check status.
  3. [x] Run the question set through a throwaway agent (the direct retrieve route returned 404), record results. Round 1 done, one run per question, two embedding models.
  4. [x] Delete the temporary KBs and agents (verified by listing).
  5. [ ] Round 2: same 20 questions, an instruction that forces Finnish search queries, 3 runs per question, both embedding models. Also check whether `chunk_size` can be set in the KB YAML. **Skipped on the user's instruction; not done.**
- **Relevant Context:** `knowledge/incident-triage/incident_triage_runbooks.yaml` (YAML shape); ADK docs "Creating built-in Milvus knowledge bases" (`vector_index.embeddings_model_name`, PDF up to 25 MB); `wxo-adk` skill. Throwaway spike files (gitignored): `.bob/tmp/travel_spike/` (`ask.py`, `questions.json`, spike agent and KB YAMLs).
- **Status:** `[x] round 1 done, inconclusive; round 2 skipped on the user's instruction. The embedding model was locked on round 1 evidence (Granite multilingual).`

### Sub-Task 1: Scaffold and manifest

- **Intent:** Create the scenario skeleton with the repo's tool so every consistency check works from day one.
- **Expected Outcomes:**
  - `python scripts/new-scenario.py travel-request --name "Travel Request" --description "Policy-aware travel authorisation (fi/en)"` has run; stubs exist for manifest, agent, ground truth, demo script, slide file and the `<script>` tag. (The manifest description still reads "(fi/en)"; the slide file description was changed to English wording. Align the manifest description if wanted.)
  - Manifest lists real resource names, `status: soon`, `evaluation.tier: core`.
  - `python scripts/scenario_manifest.py validate --scenario travel-request` prints OK.
- **Todo List:** dry run, run, fill manifest names after Sub-Tasks 2-4, validate.
- **Relevant Context:** `scripts/new-scenario.py`, `scripts/scenario_manifest.py`, `scenarios/incident-triage/scenario.yaml`.
- **Status:** `[x] done; manifest validates (OK).`

### Sub-Task 2: Mock data and tools

- **Intent:** Static data and read-only tools, plus the internal write tool.
- **Expected Outcomes:**
  - `tools/travel_request/data/` with employees, budgets, rates (hand-keyed, each value with section and effective-until date), and the mock current date.
  - `tools/travel_request/travel_request.py` with the four read tools and `travel_issue_request_id`; import fallback copied from `tools/incident_triage/incident_triage.py`; `requirements.txt` pins `ibm-watsonx-orchestrate==2.18.2`.
  - Bounded outputs and error objects with hints. Dates after 31.12.2026 return "rates not agreed" instead of a number.
  - `travel_issue_request_id` refuses when traveler, decision, estimated cost or approver level do not match mock data.
  - Direct Python tests for every case in the mock world table (no WXO needed).
- **Todo List:** data modules, tool functions, direct tests, check name uniqueness against other manifests.
- **Relevant Context:** `tools/incident_triage/` (pattern), skill rules 1-4 and 7.
- **Status:** `[x] done. 38 direct checks in the throwaway script .bob/tmp/travel_spike/test_tools.py pass (the script is gitignored and not part of the repo). Keyed values were not independently re-verified against the PDF except 3 § and 13 §.`

### Sub-Task 3: Knowledge bases

- **Intent:** Index the real source and the mock policy so the agent can cite both.
- **Expected Outcomes:**
  - `knowledge/travel-request/travel_state_rules.yaml` listing the unmodified PDF; the file is copied byte for byte (from `pdf/VM_2025_63.pdf`), plus an attribution note (title, publisher, CC BY-NC-ND 4.0, URN `https://urn.fi/URN:ISBN:978-952-367-397-7`) in the scenario README.
  - `knowledge/travel-request/travel_agency_policy.yaml` with `.txt` documents, each with a stable ID, a banner saying the content is fictional. Built as six English files (originally planned in Finnish).
  - Embedding model decision from Sub-Task 0 applied if needed.
  - KB status `ready` with all documents.
- **Todo List:** decide where the PDF lives in the repo (and what happens to the root `pdf/` folder), write policy texts, write YAMLs, import, check status.
- **Relevant Context:** `knowledge/incident-triage/`, skill rule 8 (symptoms then procedure; markdown is not supported, use `.txt`).
- **Status:** `[x] done and imported. Updating the PDF KB in place failed ingestion twice ("1 document(s) failed in ingestion"); remove then import fresh worked each time. The policy KB also needed remove then import after its files changed, so the deploy-all script alone does not refresh KB documents reliably.`

### Sub-Task 4: Approval flow

- **Intent:** Governed issue of the request ID after the decision, with a human gate where policy requires one.
- **Expected Outcomes:**
  - `flows/travel_request/travel_submit_request.py` modelled on `flows/incident_triage/request_remediation.py`: input schema, user form with separate Approve and Reject, condition branch, tool node calling `travel_issue_request_id`, result scripts.
  - Rejected or denied requests never call the write tool.
  - Browser-verified in the chat UI: form renders, Approve issues an ID, Reject does not, agent reports the `message` verbatim. The evaluator cannot drive this.
- **Todo List:** build, import, test in browser both branches, record what happened.
- **Relevant Context:** `flows/incident_triage/request_remediation.py`; skill section 5.
- **Status:** `[-] built and imported. One run-API call reached the flow with the right inputs. NOT done: the browser test (form render, Approve issues an id, Reject issues none, agent reports the message). Open item 1.`

### Sub-Task 5: Agent and README

- **Intent:** The agent with explicit language and citation rules.
- **Expected Outcomes:**
  - `agents/travel-request/agent.yaml` (`spec_version: v1`, `kind: native`, `style: react_core`, `llm: groq/openai/gpt-oss-120b`, both KBs, four tools and the flow). Instructions in English, structured like `agents/incident-triage/agent.yaml`: method, evidence standard, clarifying-question rule (minimum missing fields in one question), outcome definitions, propose-action rule, what not to do.
  - Language rules written explicitly: reply in the language of the latest user message; search the knowledge bases with Finnish terms because both documents are Finnish; cite document references in Finnish only; quote only verbatim Finnish text from retrieved passages; never translate document text; keep section numbers and document IDs unchanged.
  - Rules to report estimates only from the estimate tool, never compute amounts or invent rates, and to say when a trip falls outside 2026.
  - `agents/travel-request/README.md`: tools table, KBs, mock data table, attribution, limitations.
  - As built the language rule is English-only (see "Design changes").
- **Relevant Context:** `agents/incident-triage/agent.yaml`, ADK GPT-OSS migration guidance (KB-first and tool-usage instruction blocks).
- **Status:** `[x] done and deployed. Lessons from tuning the instructions: (1) an added "ignore earlier turns, decide the language from the latest message" rule made Finnish answers worse (7 failures) and was reverted, so every instruction change must be followed by repeated runs; (2) what fixed outcomes was an ordered approval-level rule list (abroad, leave, over 600 EUR, over 2500 EUR or over budget, else none), "always call the budget tool after the estimate", "a missing 2027 estimate never causes DENIED", "name the outcome explicitly" and "never answer from the question text alone"; (3) an unknown or zero max_distance_km is treated as the default (a tool fix).`

### Sub-Task 6: Evaluation (core tier)

- **Expected Outcomes:**
  - `evaluation/travel-request/ground_truth.json`: one entry per case (id, user request, language, expected outcome, expected tools, red herring, approval required, expected Finnish references), plus `smoke_prompts` (diagnosis-only: at least one Finnish and one English prompt; no prompt that needs the approval form).
  - A language field per case so the demo and smoke checks can verify the reply language.
  - Manifest `evaluation.tier: core`. No optional full tier unless asked.
  - As built: version 1.1, English-only prompts, all `language: en`.
- **Relevant Context:** `evaluation/incident-triage/ground_truth.json`, skill section 6.
- **Status:** `[x] done. No evaluation run and no baseline exist; the answers were read by hand.`

### Sub-Task 7: Deploy and smoke test

- **Expected Outcomes:**
  - `scripts/deploy-all.ps1 -Scenario travel-request` deploys; KB indexing waited out before first query.
  - `python scripts/smoke_test.py --scenario travel-request` run; every demo prompt then run several times in the browser, including a mid-chat language switch; results recorded without embellishment (for example Finnish answer quality of the LLM, wrong language replies, translated quotes).
  - Manifest status set to `live` only after this.
- **Status:** `[-] deployed on techzone1. Runs went through the run API, not the browser. Eight prompts x 3 runs (24 answers) with the current English configuration: 0 failed the crude automatic checks (outcome word, expected amount, tools called, English, no flow call), and all 24 outcomes were correct when read by hand against ground_truth.json. Additional runs this session: TR-003 two-turn (4 first-turn runs and 1 second turn, matches TR-002), a PDF question run 3 times (travel_state_rules called every time), one flow-trigger run. Earlier Finnish-prompt rounds had failures that the instruction changes fixed; they no longer apply. The knowledge base travel_state_rules was called in only 1 of the 24 answers and travel_agency_policy in 8, so the PDF is barely exercised outside the dedicated PDF question. scripts/smoke_test.py (shared) got a small additive fix: it now reads tool calls from step_history, because it previously reported none. NOT done: the browser test, a fresh-instance install, Developer Edition deploy. Manifest status stays soon.`

### Sub-Task 8: Demo script and slides

- **Expected Outcomes:**
  - `docs/demo/travel-request-demo.md` and `docs/demo/scenarios/travel-request.js` from the `scenario-demo-docs` templates; same prompts word for word in both; as built: a vague-input scene with follow-up, four trap or exception scenes, a Finnish-source scene, a flow-gate scene and a restraint scene (9 scenes, 10 prompts). The Finnish-language and language-switch scenes in the original plan were dropped with the English-only decision.
  - Slide tags read "Scenario N" with N equal to the sidebar position.
  - "What was and was not verified" filled only from real runs.
  - `python .bob/skills/scenario-demo-docs/check_demo_consistency.py travel-request` exits 0.
- **Status:** `[x] written. The consistency check passes (10 prompts compared, 8 tool chips checked against the manifest). The slides were not opened in a browser and Copy Prompt was not clicked. The checker does not verify facts. In scene 7 the quoted Finnish sentence was checked against the PDF text (page 20); it differs in wording from the agent's quotes.`

## Open Items

1. **Licensing.** The PDF is CC BY-NC-ND 4.0. Confirm with the repo owner or legal contact that shipping the unmodified PDF in this repo and in the scenario zip is acceptable. Until confirmed, fallback is to leave the PDF out of the package and make the user download it from the official URN.
2. **Cross-language retrieval.** Round 1 shows retrieval is not reliable with either tested embedding model (see Findings). Round 2 was skipped. With Finnish queries the dedicated PDF question (13 § hotel breakfast) found the right passage in 3 of 3 runs, but that is one question.
3. **Finnish answer quality** is no longer a requirement (English-only users).
4. **PDF indexing quality.** The 13 § application guidance was retrieved in round 1 and again in the 3 runs of the PDF question. The annex table is indexed (some country values came back) but is not reliably retrieved. Other countries untested.
5. **Mock agency policy language**: English (changed from Finnish after the user's language change).
6. **Reading of "never translations"**: no translated passages of the document; the agent's own explanation in English is allowed next to the Finnish reference. Confirmed by the user.
7. **2027 rates**: not agreed yet per the document; mock data carries the effective-until date and the tool refuses to estimate outside it.
8. **Where the PDF lives**: `knowledge/travel-request/VM_2025_63.pdf`, moved byte for byte (hash recorded in Sub-Task 0), root `pdf/` folder removed.
9. **Approval thresholds and approver levels** in the mock policy are invented; keep them obviously fictional.
10. Items from skill section 8 that are still open for any new scenario: clean first install on a fresh instance, embedding and LLM availability, agent deploy on the Developer Edition, auth expiry.
11. **Approval flow not tested in a browser.** Form render, Approve (request id), Reject (no id), the agent reporting the flow message, and whether the flow call that shows twice in the thread data started two flow instances. Do this before setting `status: live` in the manifest and in `docs/demo/scenarios/travel-request.js`.
12. **The PDF is barely exercised.** The knowledge base `travel_state_rules` was called in 1 of 24 final answers. No test exists that shows when the agent does and does not consult it, and the agent's Finnish quotes were not exact in the 3 runs checked.
13. **No baseline and no evaluation run** for this scenario; the agent-versus-script question is argued, not measured. The demo script says so.
14. **Free-meal percentage not reconciled.** The PDF guidance (page 20) speaks of halving the foreign per diem within a 35 %/65 % scheme; the estimate tool applies 50 % per day for two free meals. The hand-keyed rule should be re-read against 12 § and 13 § before the scenario goes live.
15. **Manifest description** in `scenarios/travel-request/scenario.yaml` still reads "Policy-aware travel authorisation (fi/en)".

## Suggested Build Order

Sub-Task 0 first (gate). Then 1. Sub-Tasks 2 and 3 are independent and can run together. Sub-Task 4 depends on 2. Sub-Task 5 depends on 2-4. Sub-Tasks 6-8 follow 5.

## Not Done by This Plan

- No booking, payment or expense-claim handling; the request ID is the only handoff.
- No change to Incident Triage or any other scenario's files.
- No translation or rewriting of the source document.
- No optional evaluation tier unless requested.
- No claim that the approval flow works until a browser test has produced evidence.

## Findings

### Sub-Task 0, round 1 (instance `techzone1`, one run per question, graded by hand against the PDF text)

**Embedding models on the instance.**

| Model | Result |
|---|---|
| `ibm/slate-125m-english-rtrvr-v2` (default) | Indexed, status ready |
| `ibm/granite-embedding-278m-multilingual` | Indexed, status ready |
| `ibm/multilingual-e5-large` | Import reported "model not found" |
| `virtual-model/openai/text-embedding-3-small` | Import reported "model not found" |

Gotcha: each failed import still left a KB record listed as `ready`. They had to be deleted by hand. Deploy logic must not assume a failed import leaves nothing behind. KB settings seen on the record (not changed): chunk size 400, overlap 50, top_k 10.

**Method.** A throwaway agent (`react_core`, `groq/openai/gpt-oss-120b`) with only the KB and the instruction "knowledge base first, answer only from retrieved passages, cite the section". It had no language rule. 10 Finnish and 10 English questions. The direct retrieve route (`/v1/vector-indices/{id}/retrieve`) returned 404, so raw passages were not inspected: a retrieval miss cannot be told apart from an LLM miss. Grades: OK, partial, WRONG (wrong or invented value), MISS (said "not in the KB" although it is).

| Id | Question | Correct answer | Default (english slate) | Granite multilingual |
|---|---|---|---|---|
| FI-01 | Full domestic per diem | 54 EUR, 11 § | MISS | OK |
| FI-02 | Hotel breakfast reduces per diem? | No, 13 § guidance | partial | partial |
| FI-03 | When is partial per diem paid | over 6 h, 10 § | OK | partial |
| FI-04 | Per diem in Belgium | 81 EUR, annex | WRONG (54) | WRONG (54) |
| FI-05 | Holiday combined with trip | avoid; special reason and consent, 3 § and 4 § | partial | OK |
| FI-06 | Own car mileage | 55 / 49 c, 6 § | OK | OK |
| FI-07 | Claim deadline | 2 months, 21 § | WRONG ("two weeks") | OK |
| FI-08 | Night travel allowance | 16 EUR, 16 § | OK | OK |
| FI-09 | Per diem cut, two free meals | 50 %, 13 § | WRONG (foreign 35/65 rule) | WRONG (same) |
| FI-10 | Per diem in Sweden | 70 EUR, annex | WRONG (54) | OK |
| EN-01 | Full domestic per diem | 54 EUR | OK | MISS |
| EN-02 | Hotel breakfast | No | OK | OK |
| EN-03 | Partial per diem | over 6 h | OK | WRONG (50 % meal rule) |
| EN-04 | Belgium | 81 EUR | OK | MISS |
| EN-05 | Holiday with trip | as FI-05 | partial | MISS |
| EN-06 | Mileage | 55 / 49 c | OK | OK |
| EN-07 | Claim deadline | 2 months | MISS | OK |
| EN-08 | Night allowance | 16 EUR | OK | OK |
| EN-09 | Two free meals | 50 % | MISS | OK |
| EN-10 | Sweden | 70 EUR | MISS | MISS |

Totals out of 20: default 9 OK, 3 partial, 4 WRONG, 4 MISS; Granite 11 OK, 2 partial, 3 WRONG, 4 MISS. Finnish questions only: default 3 OK / 4 WRONG, Granite 6 OK / 2 WRONG.

**Observations.**
1. Neither configuration is reliable: at most 11 of 20 fully correct.
2. Results vary between runs. FI-01 on the default KB answered 54 EUR (11 §) in a single run and "not in the KB" in the batch.
3. Wrong values, not only misses. Belgium 54 EUR in both configurations (it is 81 EUR), Sweden 54 EUR on the default, claim deadline "two weeks". 54 EUR is the domestic full per diem, so a silent mix-up of domestic and foreign. This supports the decision that country rates come from a tool.
4. Prose rules were missed or confused too (holiday, claim deadline, free meals), so the KB is not dependable for explanations either without more work. This is a risk to the plan, not only to the numbers.
5. Section labels the agent produced were unreliable. Mileage was cited as 13 § (it is 6 §), the claim deadline as 5 §, and several labels were odd (`0 § 10`, `1 §`). Some were right (11 §, 16 §, 10 §). Open design question: how Finnish references are produced reliably. Candidates (untested): an explicit instruction to name the section, a code check of the label against the retrieved text, or taking references for numeric answers from tool output.
6. Language: the spike agent had no language rule. The Granite run's EN-02 answer put an English rendering inside quotation marks as if it were the document text. That breaks the "never translations" requirement, so the agent needs an explicit rule and the demo needs a check for it.
7. On the hotel-breakfast question both runs opened with "Kyllä" and then said there is no reduction. The substance was right, the opening contradicted it.
8. The 13 § application guidance (hotel breakfast, 35 and 65 percent rule) was retrieved in both configurations.
9. The gap between the two configurations is small next to the run-to-run variation, with one run per question. No claim is made that Granite is better.

**Not tested.** Always searching in Finnish. Repeated runs. Changed chunk size. Other countries. The real agent instructions.

**Cleanup.** All throwaway KBs and agents were removed from the instance (checked by listing).
