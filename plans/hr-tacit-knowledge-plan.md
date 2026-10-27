# HR Tacit Knowledge Capture & Guide - Plan

> Scenario id: `hr-tacit-knowledge` | Resource prefix: `hr_tk_` (user decision) | Status: `soon` until verified in the browser.
> Conventions: skills `wxo-scenario-authoring`, `wxo-adk`, `scenario-demo-docs`. Closest reference in shape: `hr-onboarding` (read tools + KB + governed flows), `release-readiness` (more than one agent).
> Prefix check: no existing `scenarios/*/scenario.yaml` or `tools/` name starts with `hr_tk_`. The existing `hr_` names belong to `hr-onboarding` and must not be reused. Re-run the check before the first import.

## Top-Level Overview

**Goal.** Tacit knowledge in an HR shared-services team (workarounds, "why we do it this way", stale intranet pages) is captured from work that already happens, with minimal extra effort from the expert, and is delivered to new employees and role-changers through an agentic chat.

**Two sides, two agents (least privilege).**

| Agent | Audience | Does | Does NOT have |
|---|---|---|---|
| `hr_tk_curator` | Expert / content owner | Triages harvested items, scans for PII, finds where the content belongs (new, update, duplicate, ignore), drafts the article, asks "is this correct?", starts the review flow. Also takes a document the expert drops in. | Learner tools, any write tool |
| `hr_tk_guide` | New hire / role-changer | Answers questions from the KB for the learner's role and tenure, cites the article ID, routes a gap to the right expert. | Draft, PII and publish tools |

**Agent-washing check.** Summarising one transcript into one article is a single LLM call and is not an agent use case. The agent is justified only for the parts the repo guidance names:
- What counts as tacit knowledge in a mixed batch is a judgment call with no fixed rule (a workaround vs routine chatter vs a near-duplicate).
- The next step depends on what the KB search finds: create, update a contradicted article, merge as duplicate, or ignore.
- Learner questions are vague and may need a clarifying question; whether the KB covers the question decides between answering and routing.
- The decision tree cannot be drawn in advance.
The fixed parts are not agentic and are not claimed to be: PII detection is deterministic code, publishing is a flow plus a write tool.

**Flow of the whole loop.**
1. Harvest: mock tickets, chat threads and repository documents arrive as `artifacts`. Nobody asks the expert to write anything.
2. Curator triages the batch, scans for PII, finds placement, drafts.
3. Expert is notified (mock) and reviews in a flow: confirm, edit, or reject. This is the "is this correct?" step.
4. Publish (mock write) after confirmation. The publish tool re-checks PII in code.
5. Learner asks a question; guide answers with a citation, or routes the gap to an expert whose answer becomes a new draft (back to step 2).

## What is real and what is not (state this in the demo)

| Item | Status in this repo | Evidence / reason |
|---|---|---|
| Harvest from tickets, Slack/Teams, document repository | **Mock data only** | Every scenario here uses static read-only mock data; no external services (skill section 1). A real deployment needs integrations. |
| Expert notification by email/Slack/Teams | **Mock** (`hr_tk_notify_expert` returns a message, sends nothing) | No verified outbound push in the ADK docs found. The scheduler docs state user notifications are not yet supported and scheduled runs must not need user interaction. |
| Scheduled harvesting | **Not built**; described as a deployment option | ADK scheduler exists but only for runs without user interaction. At most it could stage drafts. Not tested. |
| Publishing makes the article searchable live | **Not real** | Python tools are stateless and the documented way to change a built-in KB is to re-import it (`orchestrate knowledge-bases import`). `hr_tk_publish_article` returns a reference and the final text; approved drafts are added under `knowledge/` and picked up on the next deploy/re-import. SharePoint/OneDrive/Box connector sync exists in the ADK; not evaluated here. |
| Guide in Teams or Slack | **Not tested**; deployment option | Channel integrations for Slack and Teams are documented. |
| Editable draft in the review form | **Unverified** | ADK `text_input_field(single_line=False, default=DataMap)` is documented; no existing flow in this repo uses an editable field. Must be tested in the browser chat UI. |
| Review assigned to the expert | **Unverified** | ADK `userflow().assign_to(UserAssignmentPolicy.USER, ...)` is documented; needs a real tenant user. The demo may run it as flow initiator and say so. |
| Document drop-in | **Pasted text, no file upload** | The expert pastes the document text in chat (Sub-Task 6). File upload routes were not tried. |

## Governance (decided in code, not in prompts)

| Rule | Where enforced |
|---|---|
| No PII in a published article | `hr_tk_scan_pii` is deterministic (regex + term lists). `hr_tk_publish_article` runs the same check again and returns `PII_REMAINING` if anything is left. |
| Only a confirmed draft is published | Flow only. Reject path never calls the write tool. Write tools are not attached to either agent (skill rule 5). |
| Article must have source, author (role label), verified date and status | `hr_tk_publish_article` rejects drafts missing these (`MISSING_METADATA`). |
| Update must name an existing article | Publish tool rejects `update` of an unknown ID (`ARTICLE_NOT_FOUND`). |
| Superseded articles are not cited as current | Search tool returns status; guide instructions say cite only `current`; the red herring case tests it. |
| Harvest scope and consent | Only designated channels/queues in the mock set; slides must say employees can opt out. Not enforced technically. |

## Mock World

Everything fictional and static. Emails use `example.com`, IDs are invented, dates are explicit ISO dates (no relative dates, same rule as `hr-onboarding`).

### Harvested artifacts (static)
Each has: `artifact_id`, source (`ticket` | `chat` | `repository`), date, author role, text. Roughly 8 to 10 items, referenced by the cases below.

### Seeded KB articles (static, stable IDs)
`HR-TK-ART-01` ... about 5 to 6 articles, each with status (`current` or `superseded`), owner role, last-verified date. One article states the leave-correction payroll cutoff as the 18th (stale). One superseded article is the red herring for Case 4.

### Experts and employees
A small expert directory (name, role label, topics) and a few learner profiles (role, start date, tenure) so the guide can tailor answers.

### Demo cases

| ID | Entry | Planted situation | Red herring | Teaches |
|---|---|---|---|---|
| TK-001 | Curator: "Review the new harvested items" | Batch of 4: a ticket resolution with an undocumented workaround, a routine chat, a near-duplicate of a seeded article, a noise item | Routine chat looks helpful but is covered by `HR-TK-ART-0x` | Judge what is worth keeping; ignore the rest; draft one article; expert reviews |
| TK-002 | Curator: same batch view, another item | A chat thread says a form/process changed; it contradicts a `current` article | A similar article for a different country | Propose an update to the named article, not a duplicate |
| TK-003 | Curator: expert drops in the sample document | Useful procedure plus personal data (see "Sample upload document") | The document's cutoff statement (22nd) conflicts with the stale article (18th) | Agent places it (one new article + flag the conflicting existing one), redacts PII automatically, asks "is this correct?"; publish refuses if PII remains |
| TK-004 | Guide: new hire asks a process question | A `current` article answers it | A `superseded` article with a different answer | Answer for the learner's role, cite the current article ID |
| TK-005 | Guide: new hire asks something the KB lacks | Expert directory names a peer for the topic | none | Route to the expert; expert's answer becomes a draft (flow) |
| TK-006 | Curator: expert rejects a draft | Review flow, Reject | none | Nothing is published |

Exactly these six cases. Verify the ground truth against real runs before claiming anything in the demo.

## Sample upload document (done)

File: [`docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.md`](../docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.md)

A personal-notes document by a fictional senior HR specialist about correcting a retroactive leave start date without triggering an automatic overpayment-recovery letter. It is built to exercise Case TK-003.

| Property | Content |
|---|---|
| Useful tacit knowledge | Open the payroll hold first, then change the date, then ask for a manual repayment schedule (split over up to three periods needs no manager approval), then call the employee before any letter arrives. Plus: the payroll cutoff is the 22nd, the intranet page still says the 18th. |
| PII planted on purpose | Employee names, employee IDs, a personal email, a mobile number, a national ID number, salary and overpayment amounts, and a named employee on medical leave after surgery (sensitive category). All fictional (`example.com`, invented numbers). |
| Placement test | New article for the hold-first sequence; the cutoff statement conflicts with the stale seeded article, so the agent should also flag an update to that article. |
| What the expert should see | Draft with PII removed or generalised, a short "what I found" summary, and one question: is this correct? |

Format note: the file is Markdown because plan mode can only write text files. Sub-Task 6 added an identical `.txt` copy. No upload route is used: the expert pastes the text into the chat (user decision), so no `.docx` was made.

## Tools

Names must stay unique across the whole instance. All use the `hr_tk_` prefix.

**Curator (read, attached), 5:** `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`.
**Guide (read, attached), 3:** `hr_tk_get_employee_profile`, `hr_tk_find_expert`, plus the KB `hr_tk_knowledge`. (`hr_tk_find_expert` is shared; one tool, two agents.)
**Write, NOT attached to any agent, called only by flows:** `hr_tk_publish_article`, `hr_tk_notify_expert`.
**Flows attached to agents:** `hr_tk_review_draft` (curator), `hr_tk_answer_gap` (guide).

Tool output is bounded and deterministic: tools take keys (artifact id, topic, employee id) and return capped, summarised results; errors are objects with a hint. Copy the import fallback pattern from `tools/hr_onboarding/hr_onboarding.py`.

## Flows

| Flow | Pattern | Notes |
|---|---|---|
| `hr_tk_review_draft` | Input: draft (title, body, source ids, placement, article id if update, PII scan summary). User activity form: draft body in a multi-line editable field, three outcomes: Confirm, Reject (separate buttons), edit then Confirm. Conditions branch, tool node `hr_tk_publish_article`, result scripts. | Reference: `flows/hr_onboarding/hr_request_provisioning.py`. Editable field and expert assignment are the two new, unverified parts. Re-test Confirm and Reject in the browser. |
| `hr_tk_answer_gap` | Input: question, expert id, learner role. Form shown to the expert with the question and a multi-line answer field; on submit a draft is created and handed to the same publish path. | Learner is told the question was routed; the answer is not claimed to be live until published. |

## Knowledge Base

Name `hr_tk_knowledge`, folder `knowledge/hr-tacit-knowledge/`, `.txt` documents only (markdown not supported), each with a stable ID `HR-TK-ART-nn` and a header block: title, status, owner role, last verified, applies to. Symptoms first, then procedure (skill rule 8). Text and structured data (cutoff dates, thresholds) must not contradict each other except where a case plants the conflict on purpose (documented in `ground_truth.json`).

## Sub-Tasks

Process one at a time; the user checks each before the next.

### Sub-Task 1: Scaffold and mock world
- **Intent**: Create the scenario skeleton and the static mock data all later work depends on.
- **Expected Outcomes**: `python wxodemo.py new-scenario hr-tacit-knowledge --name "HR Tacit Knowledge" --description "..."` has run; mock data files for artifacts, articles, experts, employees exist and cover cases TK-001 to TK-006.
- **Todo List**:
  1. Re-check name uniqueness for `hr_tk_*` across `scenarios/*/scenario.yaml` and `tools/`.
  2. Run the scaffold command. It creates `scenarios/hr-tacit-knowledge/scenario.yaml`, `agents/hr-tacit-knowledge/agent.yaml`, `evaluation/hr-tacit-knowledge/ground_truth.json`, the demo markdown and a placeholder slide file, and registers the script tag.
  3. Add a second agent entry for the guide (scaffold creates one agent; the plan needs two, as `release-readiness` does).
  4. Write mock data under `tools/hr_tk/data/`.
- **Relevant Context**: `scenarios/hr-onboarding/scenario.yaml`, `scenarios/release-readiness/scenario.yaml` (multi-agent), `src/wxodemo/scaffold.py`, `tools/hr_onboarding/data/`.
- **Status**: [x] done
- **Built / checked**:
  - Name check: only this plan file contained `hr_tk` / `hr-tacit` before scaffolding.
  - Scaffold ran (`--agent-name hr_tk_curator`; sidebar position 10): `scenarios/hr-tacit-knowledge/scenario.yaml`, `agents/hr-tacit-knowledge/agent.yaml`, `evaluation/hr-tacit-knowledge/ground_truth.json`, `docs/demo/hr-tacit-knowledge-demo.md`, `docs/demo/scenarios/hr-tacit-knowledge.js`, script tag in `presentation.html`.
  - Second agent stub `hr_tk_guide` at `agents/hr-tacit-knowledge-guide/agent.yaml` and added to the manifest `agents` list (instructions are still TODO; Sub-Task 5).
  - Mock data in `tools/hr_tk/data/`: `artifacts.py` (A-101..A-106), `articles.py` (HR-TK-ART-01..06 metadata), `experts.py` (X-101..X-104), `employees.py` (learners L-201, L-202). Imported and counted directly with Python (6/6/4/2); no unit tests written yet.
- **Mock data to case map** (for later sub-tasks):
  - TK-001: A-101 (ticket with workaround, no KB article; expert X-103), A-102 (routine, covered by ART-03), A-103 (near-duplicate of ART-03), A-104 (noise).
  - TK-002: A-105 contradicts ART-04 (form HR-22 / 10 days is stale; real: e-form PR-1 / 5 days; expert X-104). ART-05 (Sweden) is the similar-but-different-country red herring.
  - TK-003: sample upload document vs ART-01 (cutoff 18th is stale; real: 22nd). Expert X-101 is the document author.
  - TK-004: learner L-201 (Finland desk) asks about employment certificates; ART-03 is current, ART-02 is the superseded red herring.
  - TK-005: a question the KB does not cover (visa/work permit letter); expert X-102 is listed for it.
  - TK-006: reject path of the review flow, using any draft.
- **Finding to handle in Sub-Task 7**: `wxodemo smoke` sends every prompt to a single agent (`smoke_agent`, else the first agent; `src/wxodemo/smoke.py`). It cannot drive both agents. Plan: `smoke_agent: hr_tk_guide` for the diagnosis-only prompts (TK-004, TK-005 routing question), and say in the demo script that the curator cases are not covered by smoke. No change to the CLI.

### Sub-Task 2: Read tools and deterministic PII scan
- **Intent**: Build the read-only tools and the PII/placement logic that must hold in code.
- **Expected Outcomes**: Five curator tools plus employee profile; `hr_tk_scan_pii` detects every PII item planted in the sample document and in the mock artifacts; direct Python tests pass.
- **Todo List**:
  1. Implement tools in `tools/hr_tk/hr_tk.py` with the `@tool` functions and import fallback.
  2. Implement `hr_tk_scan_pii` (emails, phones, national IDs, employee IDs, amounts, name list, sensitive terms) returning findings with a suggested redaction.
  3. Implement `hr_tk_find_related_articles` returning candidates with status and a similarity hint, without live search state.
  4. Test each tool directly, including the sample document text.
- **Relevant Context**: `tools/hr_onboarding/hr_onboarding.py`, `tests/`.
- **Status**: [x] done
- **Built / checked**:
  - `tools/hr_tk/pii.py`: deterministic scanner (e-mail, national ID, phone and "extension NNNN", employee ID `E-nnnnn`, money amounts, sensitive health terms, known fictional people). Pure function, no state. Sub-Task 4's publish tool should import `pii.scan` and refuse when `clean` is false.
  - `tools/hr_tk/hr_tk.py`: six read tools. Curator: `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`. Guide: `hr_tk_get_employee_profile`, `hr_tk_find_expert` (shared). Bounded output (3 candidates, 3 experts, 10 artifacts, 25 findings, 8000 chars), structured errors with hints, explicit ISO dates only.
  - `tests/test_hr_tk_tools.py`: 18 tests, all pass. Tools are called through `.fn` because `@tool` returns a `PythonTool` wrapper (calling the wrapper directly raised `TypeError`).
  - Sample document scan: 13 findings (3 names, 2 employee IDs, 1 e-mail, 2 phones incl. the extension, 2 sensitive terms, 2 amounts, 1 national ID); the redacted copy re-scans clean. All six mock artifacts scan clean.
  - Related-article matching per case (verified by the tests): A-101 and A-104 match nothing; A-103 matches only ART-03; A-105 matches only ART-04 (Finland); the sample document matches only ART-01; A-102 returns ART-03 current plus ART-02 flagged superseded.
- **Changes made while testing (matching quality)**: first run matched too loosely (A-101 returned the probation articles, the sample document returned a superseded article). Fixes: whole-word matching, minimum score of 4 (at least two topic hits), and removing generic topics ("form", "manager", "email") from `data/articles.py`.
- **Known limits (state in the demo)**:
  - PII scan is rules plus a fixed name list. It does not do general name recognition. Sensitive-term redaction leaves awkward text ("went on [SENSITIVE_DETAIL] after [SENSITIVE_DETAIL]"); the agent must rewrite the lesson in general terms, which a prompt cannot guarantee. The publish tool's re-check is the safety net.
  - Matching is keyword based, so it is tuned to this mock set. A text that is a close paraphrase with different vocabulary would not match.
  - Not verified on a live instance: how the LLM uses these tools (Sub-Task 8).
- **Repo state to know about**: `python wxodemo.py validate` currently reports 3 demo problems for `hr-tacit-knowledge` (template placeholder, AUTHOR NOTE, prompt count 2 vs 0). They are all in the scaffolded demo script/slides and are resolved in Sub-Task 9. Until then `tests/test_cli.py::test_real_repo_validates_and_dry_runs_cleanly` fails because it validates every scenario. All other tests pass (274). Ruff: the new test file is clean; the new tool files have the same kinds of line-length/import-style warnings as `tools/hr_onboarding` (not fixed, to match repo convention).

### Sub-Task 3: Knowledge base articles
- **Intent**: Seed the KB the guide answers from and the curator compares against.
- **Expected Outcomes**: `knowledge/hr-tacit-knowledge/hr_tk_knowledge.yaml` and about 5 to 6 `.txt` articles, including the stale cutoff article and one superseded red herring.
- **Todo List**: Write articles with stable IDs; align with mock data; document planted conflicts for ground truth.
- **Relevant Context**: `knowledge/hr-onboarding/`.
- **Status**: [x] done
- **Built / checked**:
  - `knowledge/hr-tacit-knowledge/hr_tk_knowledge.yaml` (name `hr_tk_knowledge`) plus six `.txt` files in `articles/`, `HR-TK-ART-01` to `-06`. Each has a header block (status, owner role, last verified, applies to), then SYMPTOMS, PROCEDURE, OUTCOME (or NOTE for the superseded one), following the `hr-onboarding` policy format.
  - The KB description says benefits enrolment and visas are not covered; this is what lets the guide route TK-005 instead of answering.
  - Planted on purpose (record in `ground_truth.json`): ART-01 states the leave-correction cutoff as the 18th (real value is the 22nd, from the sample document); ART-04 states form HR-22 and 10 working days for Finland (real: e-form PR-1 and 5 working days, from artifact A-105); ART-02 is superseded by ART-03; ART-05 (Sweden) is the different-country look-alike.
  - Three new tests in `tests/test_hr_tk_tools.py` (21 pass in total): KB yaml lists exactly the six articles in `data/articles.py`; each file's header matches the metadata (status, owner, verified date, scope, superseded pointer); key facts in the text agree with the structured data; the articles contain no PII by the scanner.
  - Nothing here was imported to a live KB yet; indexing and retrieval quality are checked in Sub-Task 8. The built-in KB takes `.txt` only, which is why these are not markdown.
- **Not done / for later**: the manifest `knowledge_bases` entry is added in Sub-Task 7; the agents' `knowledge_base` fields in Sub-Task 5. Approved drafts will be written to `knowledge/hr-tacit-knowledge/articles/` by hand or script on re-import (the publish tool cannot change the live KB; see the real-vs-mock table).

### Sub-Task 4: Write tools and flows
- **Intent**: Add the governed write path.
- **Expected Outcomes**: `hr_tk_publish_article` and `hr_tk_notify_expert` (not attached to agents) with in-code rules from the Governance table; flows `hr_tk_review_draft` and `hr_tk_answer_gap`.
- **Todo List**: Implement tools; build flows from the `hr_onboarding` flow pattern; add the editable multi-line field and expert assignment; test Confirm and Reject in the browser chat UI (the evaluator cannot drive forms).
- **Relevant Context**: `flows/hr_onboarding/hr_request_provisioning.py`, ADK docs pages `tools/flows/user_activities_node` and `tools/flows/multi_user`.
- **Status**: [x] done in code; browser test deferred to Sub-Task 8
- **Built / checked**:
  - `tools/hr_tk/hr_tk.py`: two write tools, both marked RESTRICTED and attached to no agent.
    - `hr_tk_publish_article(action, title, body, source_ids, author_role, verified_date, status, approver, article_id, applies_to)`. Rules in code: `INVALID_ACTION`; update of an unknown or empty ID returns `ARTICLE_NOT_FOUND`; update of a superseded article returns `ARTICLE_SUPERSEDED` (hint names the successor); `MISSING_METADATA` for empty title, body, sources, author role or approver, a non-ISO date, or status other than `current`; `PII_REMAINING` if `pii.scan` on title plus body is not clean (the error does not echo the values). On success it returns the article ID (next free `HR-TK-ART-nn` for `new`), the target file path, the final text, and `live_in_kb: false` with a next step.
    - `hr_tk_notify_expert(expert_id, subject, message)`: mock; returns `simulated: true, delivered: false`. `EXPERT_NOT_FOUND` and `EMPTY_MESSAGE` errors.
  - `flows/hr_tk/hr_tk_review_draft.py` (flow `hr_tk_review_draft`): read-only display fields (action, article, title, why here, sources, PII removed), an editable multi-line `text_input_field` pre-filled from the draft via a `DataMap` default, `Confirm` submit button and a separate `Reject` button, a conditions branch, tool node `hr_tk_publish_article`, result scripts. The flow fixes `status` to `current` and `approver` to the label "Expert reviewer". Result message says the article is NOT searchable until the KB is re-imported.
  - `flows/hr_tk/hr_tk_answer_gap.py` (flow `hr_tk_answer_gap`): tool node `hr_tk_notify_expert`, then a form showing the question with a required multi-line answer field and a regex-checked date field, buttons `Submit answer` and `Decline`, then `hr_tk_publish_article` as a `new` article. Decline records "declined" and never reaches the publish node.
  - `tests/test_hr_tk_tools.py`: 48 tests pass (27 new). They cover each publish rule, the sample document (raw is refused, the redacted text is accepted), the notify mock, and source-level checks of the flows: names, every required tool argument is mapped and none is invented, status and approver are fixed in the flow, and the non-confirm branch is `default=True`. Whole suite: 304 pass, 1 fails (`test_real_repo_validates_and_dry_runs_cleanly`, the accepted red state until Sub-Task 9).
  - The `record_answered` script text was run in plain Python with stand-in objects; it builds the expected body.
- **Not verified (important)**:
  - The flow modules cannot be imported offline: loading them needs a valid WXO token, so `Flow` building was **not** executed, only `py_compile` (passes). Real-flow import happens at deploy (Sub-Task 8). The `hr_onboarding` flows have the same limit.
  - Reading the edited value back from the form (`flow.nodes['review_form'].output.final_body`) follows `flows/yel_income/issue_income_decision.py`, which reads a number field the same way. The editable text field with a `DataMap` default is documented but unverified in this repo (Open Item 3).
  - Review is assigned to the flow initiator (default). `assign_to` for a named expert is not configured (Open Item 2). In the `hr_tk_answer_gap` demo one person plays both learner and expert.
  - Confirm, Reject, edit-then-Confirm and Decline have not been clicked in a browser.
- **Design note**: `hr_tk_answer_gap` has no separate "is this correct?" step: the expert writes the answer, so Submit is the confirmation, and the publish tool still checks personal data and metadata. If the demo needs a second look, call the review flow afterwards (not built).
- **Known limit**: the tool picks the next article ID by counting the seeded set, so two publishes in a row both get `HR-TK-ART-07`. Fine for a static demo where the KB is re-imported between publishes; say so if it comes up.

### Sub-Task 5: Agents and README
- **Intent**: Define both agents and their instructions.
- **Expected Outcomes**: `agents/hr-tacit-knowledge/` for the curator and a second agent folder for the guide; instructions follow `agents/hr-onboarding/agent.yaml` structure (method, evidence standard, one item at a time, how to propose, clarifying question rule, what not to do, report flow results verbatim, cite article IDs).
- **Todo List**: Write instructions; list tools per agent; README with tools table, KB, mock data table, limitations and the "real vs mock" table above.
- **Relevant Context**: `agents/hr-onboarding/agent.yaml`, `agents/release-readiness/` if present.
- **Status**: [x] done (instructions written, not run)
- **Built / checked**:
  - `agents/hr-tacit-knowledge/agent.yaml` (`hr_tk_curator`): tools `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`, flow `hr_tk_review_draft`; KB `hr_tk_knowledge`. No write tool.
  - `agents/hr-tacit-knowledge-guide/agent.yaml` (`hr_tk_guide`): tools `hr_tk_get_employee_profile`, `hr_tk_find_expert`, flow `hr_tk_answer_gap`; KB `hr_tk_knowledge`. No write, draft or PII tool.
  - Both load as YAML; names match the manifest.
  - `agents/hr-tacit-knowledge/README.md`: why an agent (and where it is not), tools table per agent, write tools, KB, case table, real-vs-mock table, limitations.
- **Decisions to check in Sub-Task 8** (the instructions say this; whether the model follows them is unobserved):
  - Curator shows one line per item (decision plus reason), then drafts the first new or update item and opens the form without asking, because the form is the expert's check.
  - Curator has the KB so it can read the full text of an article before writing an UPDATE. If it cannot retrieve that text it must not open the form.
  - Curator scans the exact title and body it passes to the flow and rewrites sensitive details in general terms. The publish tool's PII check is the safety net.
  - Guide answers only from retrieved passages. For an uncovered question it names the expert, asks the learner, then starts `hr_tk_answer_gap`.
  - Guide calls the profile tool only when the question depends on who is asking (Open Item 5).
- **Open from this step**: none. The document route was decided in Sub-Task 6 (pasted text).
- **Repo state**: `validate` now reports 4 extra problems (curator lists a KB the scenario does not own; guide lists 3 tools and a KB the scenario does not own). They exist because the manifest still has `tools: []`, `knowledge_bases: []` and `flows: []`; Sub-Task 7 fixes them. `tests/test_discovery.py::test_real_repo_scenarios_validate_clean` now fails too, besides `test_cli.py::test_real_repo_validates_and_dry_runs_cleanly`. Everything else passes (303).

### Sub-Task 6: Sample upload document in a usable format
- **Intent**: Provide the same sample document in a format the upload route accepts.
- **Expected Outcomes**: `.docx` and `.txt` copies of the existing Markdown sample with identical content, validated.
- **Todo List**: Decide the route (Open Item 1); create the copies in Agent mode (office tools are restricted to text files in Plan mode); run `office_read` validate and outline on the `.docx`.
- **Relevant Context**: `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.md`.
- **Status**: [x] done (scope changed by user decision)
- **Decision (user)**: no upload route. The expert pastes the document text into the chat, so Open Item 1 is closed by avoiding it. No `.docx` was made, so no `office_read` check applies.
- **Built / checked**:
  - `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt`: plain-text copy of the `.md`; the SHA-256 of both files is identical (`5F3FB619...A9AD`), so the content is the same byte for byte. The `.txt` is the one to open and copy from in the demo; the `.md` stays as the reference.
  - `agents/hr-tacit-knowledge/agent.yaml`: document method now says the expert pastes the text; with no text it asks for it; the source ID is the document title.
  - `agents/hr-tacit-knowledge/README.md`: case TK-003 and the limitations updated.
- **Consequences to state in the demo**: pasting is manual (a small extra step, not zero effort). A real deployment would use a file or repository connector; that was not built or tested. The pasted text is about 2,500 characters and goes through the chat to the model; the scan tool takes up to 8,000.
- **Not verified**: how the model handles a pasted block of that size with the instructions (Sub-Task 8). Whether the model scans the exact paste or a paraphrase is unobserved; the publish tool's PII check is the safety net.

### Sub-Task 7: Manifest, ground truth, validate
- **Intent**: Make the scenario deployable and checkable.
- **Expected Outcomes**: Manifest lists real names, `attached` excludes the two write tools; `ground_truth.json` has six cases and `smoke_prompts` (diagnosis only, no approval form); `python wxodemo.py validate hr-tacit-knowledge` prints `OK`.
- **Todo List**: Fill manifest from the scaffold stub; write ground truth from the Mock World table; run validate.
- **Relevant Context**: `scenarios/incident-triage/scenario.yaml`, `evaluation/hr-onboarding/ground_truth.json`.
- **Status**: [x] done, except `validate` printing `OK` (blocked on Sub-Task 9 by user decision)
- **Built / checked**:
  - `scenarios/hr-tacit-knowledge/scenario.yaml`: `smoke_agent: hr_tk_guide`; one tool package `tools/hr_tk` with 8 `names` and 6 `attached` (the two write tools `hr_tk_publish_article` and `hr_tk_notify_expert` are left out of `attached`); KB `hr_tk_knowledge`; flows `hr_tk_review_draft` and `hr_tk_answer_gap`. `status` stays `soon`.
  - `evaluation/hr-tacit-knowledge/ground_truth.json`: six cases (TK-001 to TK-006) with the agent that owns each, the expected decision per item, the expected draft fields, red herrings and key tools. Notes record the planted conflicts, that the curator cases are browser-only and outside smoke, and that published articles are not searchable. Written before any live run and says so.
  - `smoke_prompts`: two guide prompts, TK-004 (superseded article red herring) and TK-005 (uncovered visa question). The TK-005 prompt asks "who should I ask?" so it can be answered without the flow. Both are diagnosis-only.
  - `validate`: the manifest, tool-name, KB, flow-name and agent-ownership checks now pass. 3 problems remain, all in the scaffolded demo script and slides (placeholder, AUTHOR NOTE, prompt count 2 vs 0). That is the red state the user accepted until Sub-Task 9.
  - `smoke hr-tacit-knowledge --dry-run`: prints the two prompts for agent `hr_tk_guide`; nothing sent.
  - `deploy hr-tacit-knowledge --dry-run`: order is tools, KB, flows, agents; the two agents are imported and deployed. Nothing deployed.
  - Name check: no other scenario manifest contains `hr_tk_`, and no tool file outside `tools/hr_tk` defines an `hr_tk_` function.
  - Tests: 304 pass, 1 fails (`test_cli.py::test_real_repo_validates_and_dry_runs_cleanly`, the accepted red state). `test_discovery.py` is green again.
- **Limits to remember**: smoke covers the guide only; no smoke prompt reaches the curator, and none can reach a form. ground_truth `expected_pii_counts_in_source` holds for this one document.

### Sub-Task 8: Deploy and run
- **Intent**: Observe real behaviour before writing demo claims.
- **Expected Outcomes**: Deployed to the user's own instance; each case run several times; results recorded honestly.
- **Todo List**: `python wxodemo.py deploy hr-tacit-knowledge`; wait for KB indexing; run smoke; run the browser flows (Confirm, Reject, edit then Confirm, the document drop-in); record failures.
- **Relevant Context**: skill sections 7 and 8, `src/wxodemo/smoke.py`.
- **Status**: [-] in progress. Deploy and guide smoke done; curator cases and every browser click still to do (user).
- **Observed so far (user's instance 'techzone1'; one deploy, three smoke passes)**:
  - `login`: environment active. `deploy hr-tacit-knowledge`: all steps `[ok]` (tool package `hr_tk`, KB, both flows, both agents imported and deployed), 2 min 3 s. **Both flows imported without error**, which the offline work could not show. Import success does not show the forms render or the buttons work.
  - `status`: `deployed`, agents 2/2, tools 10/10 (8 tools + 2 flows), KBs 1/1.
  - KB `hr_tk_knowledge`: index status `ready`, 6 documents, checked after the deploy and before the smoke run.
  - Smoke, agent `hr_tk_guide`, 3 passes x 2 prompts = 6 runs, all status `completed`:
    - TK-004 (certificate, Finland desk): 3 of 3 answered from HR-TK-ART-03 with the right steps (portal, category Certificates, short or long form, 3 working days, not the shared mailbox) and cited HR-TK-ART-03 with last-verified 2025-02-18. 0 of 3 gave the superseded process as the answer. Tools in all 3: `hr_tk_get_employee_profile`, then the KB. The profile call was not needed for this question, so the guide did **call a tool the answer did not depend on** (Open Item 5: over-calling observed, harmless here).
    - TK-005 (visa letter): 3 of 3 said the KB has no article, named Marit Solberg, Mobility and Immigration Specialist, ID X-102, and offered to route the question; none started the flow. Tools in all 3: KB, then `hr_tk_find_expert`.
  - Only the first 600 characters of each answer are shown by the smoke command; the end of each answer was not read. The console shows some characters garbled by the terminal encoding (quotes, hyphens in IDs); this is display only and was not checked in the stored thread.
- **Not observed yet**:
  - Curator cases TK-001, TK-002, TK-003, TK-006: smoke cannot reach the curator. Nothing about how the curator behaves has been seen.
  - Any form: review form rendering, editable draft field pre-fill, Confirm, edit then Confirm, Reject; answer form, Submit answer, Decline; the flow result message reported verbatim.
  - TK-005 after the learner agrees (the `hr_tk_answer_gap` call).
  - Whether the curator reads the full text of an article before an UPDATE, and whether it scans the exact title and body it passes to the flow.
  - Nothing here supports a claim of accuracy beyond these six runs.
- **Curator, first browser session (read from `wxodemo export-chats`; one chat thread, three turns; the export folder is git-ignored)**:
  - Turn 1, prompt `Review the newly harvested items from 2025-06-10 to 2025-06-11.`: the four-item summary came before any draft. A-101 NEW, A-104 IGNORE as expected. **A-102 was labelled DUPLICATE of HR-TK-ART-03, not IGNORE** (the ground truth says IGNORE; both mean "no draft"). It stopped after the summary and did **not** open the review form by itself, although the instructions say to.
  - Turn 2 (user typed `scan PII of A-101`): `hr_tk_scan_pii` ran on the artifact; reported clean.
  - Turn 3 (user typed `review A-101`): tools were `hr_tk_find_expert`, then the flow `hr_tk_review_draft`; the form task "Is this correct?" started and the agent's reply was `[Response processed]`. **`hr_tk_scan_pii` was not called in this turn on the draft**, so the instruction "scan the exact title and body before the flow" was not followed here (the scan in turn 2 was on the source text).
  - Flow input the agent sent (from the trace): action `new`, source `A-101`, author role `Benefits Specialist`, verified date `2025-06-10`, pii_summary `0 personal data found`. The body contains the LE-3 form, the 30-day window, the "mid-month joiner" option and the medical declaration after 30 days. It does **not** contain the instruction "do not wait for the 1st of the next month". It adds a step A-101 does not state ("Verify the employee's actual start date in the HRIS").
  - **The model wrote Unicode look-alikes**: non-breaking hyphens (U+2011) in `LE-3` and `mid-month`, and a narrow no-break space (U+202F) in `30 days`. A plain-text search for `LE-3` or `30 days` does not match them. This would carry into a published article and the ground truth `mentions` checks.
  - **Reported by the user, and it matches the trace**: the form rendered, and the editable "Article text" field was **pre-filled with the full draft** (the same text as the body in the trace). So the editable field with a `DataMap` default works for pre-fill (Open Item 3, partly closed). Edit-then-Confirm, Confirm and Reject were not yet reported.
  - The user typed `scan PII of A-101` and `review A-101` themselves, so the curator was never observed going from the summary to the form on its own. That behaviour from the instructions is **not yet observed**. The scan in turn 2 was on the source artifact, not on the finished draft.
- **Second browser session: the flow call failed (user report plus trace)**:
  - Two chats typed `review A-101` (about 14:02 and 14:03 UTC) ended with the agent saying the authentication token had expired and asking for a new token. The trace shows the call to the flow tool `review_knowledge_draft` returned `status_code 400, {"message":"token has expired"}`. The agent only relayed it.
  - The same flow call worked at 13:53 UTC in the first session, so the draft and the flow code were not the cause. Whose token expired is **not established**; the likely candidate is the browser chat session. No fix was made. Retry after reloading the chat or signing in again.
  - Instruction gap to consider after the retry: the agent asked the user for "a new valid token". The curator and guide instructions do not say what to do when a flow call fails with an error; they should state the error plainly and not ask for credentials.
- **Third browser session: edit then Confirm, publish reported as refused (user report plus trace plus offline check)**:
  - `edit A-101` only made the agent ask what to change. `Show me article draft I can edit` opened the form. After the user edited and pressed Confirm, the trace shows the flow ran `task.tool.hr_tk_publish_article` (`POST.runPython`, HTTP 200, about 240 ms) and then `Format Confirmed Result`. The agent reported: nothing published, "the publish step refused the article (it still contained disallowed content)".
  - The flow message was "CONFIRMED BY EXPERT, BUT THE PUBLISH TOOL REFUSED. NOTHING WAS PUBLISHED. Tool result: None". So the flow script read `str(flow.nodes['hr_tk_publish_article'].output)` and got `None`. **The refusal reason was never visible.** The agent's words "disallowed content" are its own guess; no error code appears in the trace. The trace spans carry no tool input or output, so the real return value was not seen.
  - Offline check: `hr_tk_publish_article` called directly with the metadata the agent sent (action `new`, source `A-101`, role `Benefits Specialist`, date `2025-06-10`, status `current`, approver `Expert reviewer`) and the unedited draft text, look-alike characters included, returns `status: success` and article ID `HR-TK-ART-07`. What the user typed into the field is not in any trace, so an edit that adds personal-data-like text cannot be ruled out, but nothing observed shows it.
  - **This is the same unexplained empty read recorded in `plans/hr-onboarding-plan.md` (Sub-Task 6, live runs 1 and 2):** `str(flow.nodes[<tool node>].output)` gave `None` there too, although Incident Triage uses the same pattern. Cause not established in either scenario.
  - **Consequence for this scenario:** with the current script, a successful publish is reported as a refusal, and a real refusal would also be reported without its reason. The "published" flag cannot be trusted until the read is fixed. No code was changed yet.
  - Not yet observed: Confirm without an edit; Reject; the curator opening the form by itself after the summary; a scan of the finished draft before the flow.


### Sub-Task 9: Demo script and slides
- **Intent**: Write the demo from real runs.
- **Expected Outcomes**: `docs/demo/hr-tacit-knowledge-demo.md` and `docs/demo/scenarios/hr-tacit-knowledge.js` with identical prompts, a Target Fit card (Industry: Cross-Industry; Function: HR Shared Services and Knowledge Management; Roles: HR Specialist (expert), HR Operations Lead, People Experience Manager, New Hire / Role-changer), the real-vs-mock table, and a "verified / not verified" section filled only from runs.
- **Todo List**: Use the `scenario-demo-docs` templates; run `validate`; open the presentation from `file://`.
- **Relevant Context**: `docs/demo/hr-onboarding-demo.md`, `docs/demo/scenarios/hr-onboarding.js`.
- **Status**: [ ] pending

## Open Items

1. **Upload route for the sample document.** CLOSED by user decision in Sub-Task 6: the expert pastes the text into the chat. The three upload routes (`file_upload_field` in a form, `chat_with_docs`, a `WXOFile` tool parameter) were not tried and are listed as not verified.
2. **Expert assignment.** `assign_to` needs a real tenant user; otherwise the flow runs as the initiator and the demo says so.
3. **Editable draft field** in a flow form (documented, untested in this repo).
4. **Two agents in one scenario manifest**: confirm the scaffold and `validate` handle a second agent entry the way `release-readiness` does.
5. **Guide with both KB and tools**: confirm the guide uses the KB for article text and the profile tool for role/tenure without over-calling.

## Not Verified / Not Done by This Plan
- Any real connector to tickets, Slack, Teams, repositories, email.
- Scheduled harvesting.
- Live publish into the KB without a re-import.
- Guide delivered through Slack or Teams.
- Clean first install on a fresh instance (open in the skill for all scenarios).
- Any quality or accuracy numbers: no evaluation run is planned (`tier: core`).
