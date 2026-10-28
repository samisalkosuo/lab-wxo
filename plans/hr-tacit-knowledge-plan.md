# HR Tacit Knowledge Capture & Guide - Plan

> Scenario id: `hr-tacit-knowledge` | Resource prefix: `hr_tk_` (user decision) | Status: **`live`** — all nine sub-tasks complete.
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

Format note: the file is Markdown because plan mode can only write text files. Sub-Task 6 adds an identical `.txt` copy. No upload route is used: the expert pastes the text into the chat (user decision), so no `.docx` is needed.

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
  2. Run the scaffold command with `--agent-name hr_tk_curator`. It creates `scenarios/hr-tacit-knowledge/scenario.yaml`, `agents/hr-tacit-knowledge/agent.yaml`, `evaluation/hr-tacit-knowledge/ground_truth.json`, the demo markdown and a placeholder slide file, and registers the script tag.
  3. Add a second agent stub `hr_tk_guide` at `agents/hr-tacit-knowledge-guide/agent.yaml` and add it to the manifest `agents` list (same pattern as `release-readiness`). Instructions are written in Sub-Task 5.
  4. Write mock data under `tools/hr_tk/data/`: `artifacts.py` (A-101..A-106), `articles.py` (HR-TK-ART-01..06 metadata), `experts.py` (X-101..X-104), `employees.py` (learners L-201, L-202).
- **Relevant Context**: `scenarios/hr-onboarding/scenario.yaml`, `scenarios/release-readiness/scenario.yaml` (multi-agent), `src/wxodemo/scaffold.py`, `tools/hr_onboarding/data/`.
- **Mock data to case map** (wire the data to the right cases):
  - TK-001: A-101 (ticket with workaround, no KB article; expert X-103), A-102 (routine chat, covered by ART-03), A-103 (near-duplicate of ART-03), A-104 (noise).
  - TK-002: A-105 contradicts ART-04 (form HR-22 / 10 days is stale; real: e-form PR-1 / 5 days; expert X-104). ART-05 (Sweden) is the similar-but-different-country red herring.
  - TK-003: sample upload document vs ART-01 (cutoff 18th is stale; real: 22nd). Expert X-101 is the document author.
  - TK-004: learner L-201 (Finland desk) asks about employment certificates; ART-03 is current, ART-02 is the superseded red herring.
  - TK-005: a question the KB does not cover (visa/work permit letter); expert X-102 is listed for it.
  - TK-006: reject path of the review flow, using any draft.
- **Note for Sub-Task 7**: `wxodemo smoke` sends every prompt to a single agent (`smoke_agent`, else the first agent). Set `smoke_agent: hr_tk_guide` in the manifest for the diagnosis-only prompts (TK-004, TK-005 routing question). The curator cases are not covered by smoke; say so in the demo script.
- **Status**: [ ] pending

### Sub-Task 2: Read tools and deterministic PII scan
- **Intent**: Build the read-only tools and the PII/placement logic that must hold in code.
- **Expected Outcomes**: Five curator tools plus employee profile; `hr_tk_scan_pii` detects every PII item planted in the sample document and in the mock artifacts; direct Python tests pass.
- **Todo List**:
  1. Implement `tools/hr_tk/pii.py`: deterministic scanner (e-mail, national ID, phone and "extension NNNN", employee ID `E-nnnnn`, money amounts, sensitive health terms, known fictional names). Pure function, no state. Returns `{"clean": bool, "findings": [...]}` with suggested redactions.
  2. Implement the six read tools in `tools/hr_tk/hr_tk.py` with `@tool` and the import fallback from `tools/hr_onboarding/hr_onboarding.py`. Curator: `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`. Guide: `hr_tk_get_employee_profile`, `hr_tk_find_expert` (shared). Cap all outputs (3 candidates, 3 experts, 10 artifacts, 25 findings, 8000 chars). Return structured errors with hints, explicit ISO dates only.
  3. Implement `hr_tk_find_related_articles` with whole-word keyword matching and a minimum score (at least two topic hits) to avoid over-matching. Remove generic topics ("form", "manager", "email") from article topic lists.
  4. Write `tests/test_hr_tk_tools.py`. Call tools through `.fn` (the `@tool` wrapper returns a `PythonTool`; calling the wrapper directly raises `TypeError`). Verify: sample document scan finds all planted PII; redacted copy re-scans clean; all mock artifacts scan clean; related-article matches are correct per case (A-101 and A-104 → nothing; A-103 → ART-03 only; A-105 → ART-04 only; sample document → ART-01 only; A-102 → ART-03 current + ART-02 superseded).
- **Relevant Context**: `tools/hr_onboarding/hr_onboarding.py`, `tests/`.
- **Known limits to state in the demo**:
  - PII scan is rules plus a fixed name list, not general NER. Sensitive-term redaction leaves awkward text; the agent must rewrite the lesson in general terms. The publish tool's re-check is the safety net.
  - Keyword matching is tuned to this mock set; a close paraphrase with different vocabulary would not match.
- **Status**: [ ] pending

### Sub-Task 3: Knowledge base articles
- **Intent**: Seed the KB the guide answers from and the curator compares against.
- **Expected Outcomes**: `knowledge/hr-tacit-knowledge/hr_tk_knowledge.yaml` and six `.txt` articles, including the stale cutoff article and one superseded red herring; tests confirm header metadata, key facts, and PII-free content.
- **Todo List**:
  1. Write `knowledge/hr-tacit-knowledge/hr_tk_knowledge.yaml` (name `hr_tk_knowledge`). Include a KB description that explicitly says benefits enrolment and visas are not covered — this is what lets the guide route TK-005 instead of answering.
  2. Write six `.txt` files in `knowledge/hr-tacit-knowledge/articles/`, IDs `HR-TK-ART-01` to `-06`. Use the `hr-onboarding` format: header block (status, owner role, last verified, applies to), then SYMPTOMS, PROCEDURE, OUTCOME. Superseded articles use NOTE instead of OUTCOME.
  3. Plant these conflicts deliberately (record them in `ground_truth.json` in Sub-Task 7): ART-01 states the leave-correction cutoff as the 18th (real: 22nd); ART-04 states form HR-22 and 10 working days for Finland (real: e-form PR-1 and 5 working days); ART-02 is superseded by ART-03; ART-05 (Sweden) is the different-country look-alike for TK-002.
  4. Add three tests to `tests/test_hr_tk_tools.py`: KB yaml lists exactly the six articles in `data/articles.py`; each file's header matches metadata; key facts agree with structured data; articles contain no PII by the scanner.
- **Relevant Context**: `knowledge/hr-onboarding/`.
- **Note**: the manifest `knowledge_bases` entry is added in Sub-Task 7; the agents' `knowledge_base` fields are set in Sub-Task 5. Approved drafts are written to `knowledge/hr-tacit-knowledge/articles/` and picked up on the next re-import; the publish tool cannot change the live KB.
- **Status**: [ ] pending

### Sub-Task 4: Write tools and flows
- **Intent**: Add the governed write path.
- **Expected Outcomes**: `hr_tk_publish_article` and `hr_tk_notify_expert` (not attached to any agent) with all in-code governance rules; flows `hr_tk_review_draft` and `hr_tk_answer_gap`; tests cover every publish rule and each flow's source structure.
- **Todo List**:
  1. Add two write tools to `tools/hr_tk/hr_tk.py`, both marked RESTRICTED and attached to no agent:
     - `hr_tk_publish_article(action, title, body, source_ids, author_role, verified_date, status, approver, article_id, applies_to)`. Rules: `INVALID_ACTION`; update of an unknown or empty ID → `ARTICLE_NOT_FOUND`; update of a superseded article → `ARTICLE_SUPERSEDED` (hint names the successor); empty title, body, sources, author role, or approver, a non-ISO date, or status other than `current` → `MISSING_METADATA`; `pii.scan` on title+body not clean → `PII_REMAINING` (do not echo values). On success: return the article ID (next free `HR-TK-ART-nn` for `new`), the target file path, the final text, and `live_in_kb: false` with a next step.
     - `hr_tk_notify_expert(expert_id, subject, message)`: mock; returns `simulated: true, delivered: false`. Errors: `EXPERT_NOT_FOUND`, `EMPTY_MESSAGE`.
  2. Write `flows/hr_tk/hr_tk_review_draft.py` (flow `hr_tk_review_draft`): read-only display fields (action, article, title, why here, sources, PII removed), an editable multi-line `text_input_field` pre-filled from the draft body via a `DataMap` default, `Confirm` submit button and a separate `Reject` button, a conditions branch, tool node `hr_tk_publish_article`, result scripts. Fix `status` to `current` and `approver` to `"Expert reviewer"` in the flow. Result message must say the article is NOT searchable until the KB is re-imported. **Important**: before coding the result script, read `plans/hr-onboarding-plan.md` Sub-Task 6 for the known `None`-read problem with `str(flow.nodes[<tool node>].output)` — investigate an alternative before repeating that pattern.
  3. Write `flows/hr_tk/hr_tk_answer_gap.py` (flow `hr_tk_answer_gap`): tool node `hr_tk_notify_expert`, then a form with the question (read-only), a required multi-line answer field, a regex-checked date field, `Submit answer` and `Decline` buttons; `Submit answer` path calls `hr_tk_publish_article` as a `new` article; `Decline` path records "declined" and never reaches the publish node.
  4. Add tests to `tests/test_hr_tk_tools.py`: each publish rule; sample document raw → refused; redacted text → accepted; notify mock; flow source checks (names match manifest, every required tool argument is mapped, no invented arguments, status and approver are fixed in the flow, non-confirm branch is `default=True`).
- **Relevant Context**: `flows/hr_onboarding/hr_request_provisioning.py`, `flows/yel_income/issue_income_decision.py` (reads a form field output the same way), `plans/hr-onboarding-plan.md` Sub-Task 6 (documents the `None`-read problem).
- **Known limits**:
  - Flow modules cannot be imported offline; only `py_compile` is feasible. Real import happens at deploy (Sub-Task 8). Same constraint applies to `hr_onboarding` flows.
  - The `DataMap` default for an editable text field is documented but unverified in this repo. Confirm it renders and pre-fills in the browser during Sub-Task 8.
  - Review is assigned to the flow initiator (default). `assign_to` for a named expert is not configured (Open Item 2).
  - The tool picks the next article ID by counting the seeded set, so two publishes in a row both get `HR-TK-ART-07`. Acceptable for a static demo; say so if it comes up.
- **Status**: [ ] pending

### Sub-Task 5: Agents and README
- **Intent**: Define both agents and their instructions.
- **Expected Outcomes**: `agents/hr-tacit-knowledge/agent.yaml` for the curator and `agents/hr-tacit-knowledge-guide/agent.yaml` for the guide; instructions follow `agents/hr-onboarding/agent.yaml` structure; README documents both agents.
- **Todo List**:
  1. Write `agents/hr-tacit-knowledge/agent.yaml` (`hr_tk_curator`): tools `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`, flow `hr_tk_review_draft`; KB `hr_tk_knowledge`. No write tool. Instructions: show one-line triage per item (decision + reason), then draft the first NEW or UPDATE item and open the review form without asking (the form is the expert's check); scan the exact title and body before the flow; if the full text of an article cannot be retrieved for an UPDATE, do not open the form; report flow results verbatim; on a flow error, state the error plainly and stop — do not ask for credentials.
  2. Write `agents/hr-tacit-knowledge-guide/agent.yaml` (`hr_tk_guide`): tools `hr_tk_get_employee_profile`, `hr_tk_find_expert`, flow `hr_tk_answer_gap`; KB `hr_tk_knowledge`. No write, draft, or PII tool. Instructions: answer only from retrieved KB passages; cite the article ID; cite only articles with status `current`; for an uncovered question name the expert, confirm with the learner, then start `hr_tk_answer_gap`; call the profile tool only when the question depends on who is asking (role or tenure).
  3. Write `agents/hr-tacit-knowledge/README.md`: why an agent (and where it is not), tools table per agent, write tools, KB, case table, real-vs-mock table, limitations. Include the sample document paste route for TK-003.
- **Relevant Context**: `agents/hr-onboarding/agent.yaml`, `agents/release-readiness/` (multi-agent structure).
- **Status**: [ ] pending

### Sub-Task 6: Sample upload document in a usable format
- **Intent**: Provide the sample document in a format usable in the demo.
- **Expected Outcomes**: `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt` exists as an exact plain-text copy of the `.md`.
- **Todo List**:
  1. Write `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt` as an exact plain-text copy of the `.md`. The `.txt` is the file to open and copy from in the demo; the `.md` is the reference.
  2. Confirm `agents/hr-tacit-knowledge/agent.yaml` states the document method: expert pastes the text; if no text is provided the agent asks for it; the source ID is the document title.
- **Relevant Context**: `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.md`.
- **Decision (closed)**: no upload route. Open Item 1 is closed by avoiding it. No `.docx` needed.
- **Consequences to state in the demo**: pasting is manual. A real deployment would use a file or repository connector. The pasted text is about 2,500 characters; the scan tool cap is 8,000.
- **Status**: [ ] pending

### Sub-Task 7: Manifest, ground truth, validate
- **Intent**: Make the scenario deployable and checkable.
- **Expected Outcomes**: `scenarios/hr-tacit-knowledge/scenario.yaml` lists real names with write tools excluded from `attached`; `evaluation/hr-tacit-knowledge/ground_truth.json` has six cases and smoke prompts; `python wxodemo.py validate hr-tacit-knowledge` prints `OK` (3 demo-script problems are the accepted red state until Sub-Task 9).
- **Todo List**:
  1. Fill `scenarios/hr-tacit-knowledge/scenario.yaml`: `smoke_agent: hr_tk_guide`; one tool package `tools/hr_tk` with 8 `names` and 6 `attached` (exclude `hr_tk_publish_article` and `hr_tk_notify_expert`); KB `hr_tk_knowledge`; flows `hr_tk_review_draft` and `hr_tk_answer_gap`. Keep `status: soon`.
  2. Write `evaluation/hr-tacit-knowledge/ground_truth.json`: six cases (TK-001 to TK-006) with owning agent, expected decision per item, expected draft fields, red herrings, key tools. Record the planted conflicts. Note that curator cases are browser-only and outside smoke, and that published articles are not searchable until re-import.
  3. Add two `smoke_prompts`: TK-004 (employment certificate, Finland desk, superseded red herring) and TK-005 (visa letter, "who should I ask?" — must be answerable without starting a flow).
  4. Run `python wxodemo.py validate hr-tacit-knowledge`. Expect OK on manifest, tool-name, KB, flow-name, and agent-ownership checks. The 3 demo-script problems (placeholder, AUTHOR NOTE, prompt count) stay until Sub-Task 9.
  5. Run `smoke hr-tacit-knowledge --dry-run` and `deploy hr-tacit-knowledge --dry-run`; confirm output looks right.
  6. Run the full test suite; confirm only `test_real_repo_validates_and_dry_runs_cleanly` fails (the accepted red state).
- **Relevant Context**: `scenarios/incident-triage/scenario.yaml`, `evaluation/hr-onboarding/ground_truth.json`.
- **Status**: [ ] pending

### Sub-Task 8: Deploy and run
- **Intent**: Observe real behaviour before writing demo claims.
- **Expected Outcomes**: Deployed to the user's own instance; each of the six cases run at least once; results recorded honestly; the `None`-read problem in the review flow confirmed or ruled out before Sub-Task 9.
- **Todo List**:
  1. `python wxodemo.py deploy hr-tacit-knowledge`; wait for KB indexing (`status` shows KB `ready`, 6 documents).
  2. `python wxodemo.py smoke hr-tacit-knowledge` (3 passes); record the tools called and whether TK-004 cites ART-03 (not ART-02); whether TK-005 names the right expert without starting the flow.
  3. In the browser, open the curator agent. Run TK-001 ("Review the newly harvested items"): verify triage summary, then whether the agent opens the review form on its own after the summary or waits for a follow-up prompt. Adjust instructions after observing.
  4. Confirm the editable "Article text" field is pre-filled with the draft body.
  5. Click Confirm (without editing): record whether the publish result is read correctly or returns `None`. If `None` appears, diagnose and fix the result script before proceeding.
  6. Click Reject: verify nothing is published.
  7. Run TK-002 (contradicted article), TK-003 (pasted sample document), TK-005 in the guide (route question, then start the answer-gap flow), TK-006 (reject path).
  8. Record all failures honestly. Do not write claims in the demo script about behaviour not observed.
- **Relevant Context**: skill sections 7 and 8, `src/wxodemo/smoke.py`, `plans/hr-onboarding-plan.md` Sub-Task 6 (the `None`-read problem).
- **Lessons from the previous attempt** (known problems to anticipate):
  - `str(flow.nodes[<tool node>].output)` returned `None` after Confirm; the refusal reason was never visible. Diagnose this before assuming publish works.
  - The model wrote Unicode look-alikes (non-breaking hyphens U+2011, narrow no-break spaces U+202F) in draft bodies. A plain-text search for `LE-3` or `30 days` does not match them. Record if it recurs.
  - The curator did not go from the triage summary to the review form on its own; it waited for a follow-up prompt.
  - The curator scanned the source artifact, not the finished draft, so the PII-scan-before-flow instruction was not followed.
  - Guide over-called `hr_tk_get_employee_profile` on TK-004 (harmless, but unnecessary). Note if it recurs.
  - A flow call returned `token has expired` after about 10 minutes; reload the browser session if this happens.
- **Status**: [x] complete

### Sub-Task 9: Demo script and slides
- **Intent**: Write the demo from real runs.
- **Expected Outcomes**: `docs/demo/hr-tacit-knowledge-demo.md` and `docs/demo/scenarios/hr-tacit-knowledge.js` with identical prompts, a Target Fit card (Industry: Cross-Industry; Function: HR Shared Services and Knowledge Management; Roles: HR Specialist (expert), HR Operations Lead, People Experience Manager, New Hire / Role-changer), the real-vs-mock table, and a "verified / not verified" section filled only from runs.
- **Todo List**: Use the `scenario-demo-docs` templates; run `validate`; open the presentation from `file://`.
- **Relevant Context**: `docs/demo/hr-onboarding-demo.md`, `docs/demo/scenarios/hr-onboarding.js`.
- **Status**: [x] complete — demo script rewritten from six browser-verified runs; `status: live` set in manifest and slides; `validate` → `[ok]`; bundle rebuilt.

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
