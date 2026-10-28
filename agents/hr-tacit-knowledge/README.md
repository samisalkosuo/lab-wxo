# HR Tacit Knowledge — Scenario README

Scenario ID: `hr-tacit-knowledge`  
Status: `soon` (not yet deployed; Sub-Task 8 required)  
Plan: [`plans/hr-tacit-knowledge-plan.md`](../../plans/hr-tacit-knowledge-plan.md)

---

## What This Scenario Shows

Tacit knowledge in an HR shared-services team — workarounds, "why we do it this way",
stale intranet pages — is captured from work that already happens (tickets, chat threads,
documents) with minimal extra effort from the expert. New hires and role-changers get
answers with article citations from a conversational agent.

**Two agents, least privilege:**

| Agent | Audience | Does | Does NOT have |
|---|---|---|---|
| `hr_tk_curator` | Expert / content owner | Triages harvested items, scans for PII, finds placement, drafts articles, routes for review | Learner tools, any write tool |
| `hr_tk_guide` | New hire / role-changer | Answers questions from the KB, cites the article ID, routes gaps to the right expert | Draft, PII, publish tools |

---

## Why an Agent (Not a Script)

Fixed parts are NOT agentic and are not claimed to be:
- PII detection is deterministic regex + term lists (in [`tools/hr_tk/pii.py`](../../tools/hr_tk/pii.py))
- Publishing is a flow + write tool

The agent is justified for the open-ended parts:
- What counts as tacit knowledge in a mixed batch is a judgment call (workaround vs routine vs near-duplicate)
- The next step depends on what the KB search finds (new / update / duplicate / ignore)
- Learner questions are vague and may need a clarifying question; whether the KB covers it decides between answering and routing
- The decision tree cannot be drawn in advance

---

## Tools

### Curator tools (attached to `hr_tk_curator`)

| Tool | Purpose |
|---|---|
| `hr_tk_list_new_artifacts` | List all harvested items waiting for review |
| `hr_tk_get_artifact` | Retrieve the full text of one artifact |
| `hr_tk_scan_pii` | Scan text for PII (deterministic: regex + known names) |
| `hr_tk_find_related_articles` | Search the KB article index by topic keywords |
| `hr_tk_find_expert` | Find the right expert for a topic |

### Guide tools (attached to `hr_tk_guide`)

| Tool | Purpose |
|---|---|
| `hr_tk_get_employee_profile` | Retrieve a learner's role, desk, and tenure |
| `hr_tk_find_expert` | Shared with curator — find the right expert |

### Write tools (NOT attached to any agent — flow-only)

| Tool | Called by | Purpose |
|---|---|---|
| `hr_tk_publish_article` | `hr_tk_review_draft`, `hr_tk_answer_gap` | Create or update a KB article (governance enforced in code) |
| `hr_tk_notify_expert` | `hr_tk_answer_gap` | Mock notification to an expert (simulated, not delivered) |

---

## Flows

| Flow | Triggers | Purpose |
|---|---|---|
| `hr_tk_review_draft` | Curator after drafting | Shows draft to expert; Confirm publishes, Reject discards |
| `hr_tk_answer_gap` | Guide after learner confirms | Asks expert to answer an uncovered question; Submit creates a draft article |

Both flows call write tools ONLY on the confirm/submit path. The reject/decline path never
calls a write tool.

---

## Knowledge Base

Name: `hr_tk_knowledge`  
Path: `knowledge/hr-tacit-knowledge/`  
Articles: `HR-TK-ART-01` to `HR-TK-ART-06`

**Planted conflicts (intentional, for the demo):**

| Article | Planted stale fact | Used in |
|---|---|---|
| `HR-TK-ART-01` | Payroll cutoff stated as 18th (real: 22nd) | TK-003 |
| `HR-TK-ART-04` | Form HR-22 / 10 days (real: e-form PR-1 / 5 days) | TK-002 |
| `HR-TK-ART-02` | Superseded by ART-03 (red herring for TK-004) | TK-004 |
| `HR-TK-ART-05` | Sweden position-change (different-country red herring) | TK-002 |

---

## Demo Cases

| ID | Entry | What it teaches |
|---|---|---|
| TK-001 | Curator: "Review the newly harvested items" | Triage a mixed batch; draft one new article; expert review |
| TK-002 | Same batch, A-105 | Identify a contradiction; propose an UPDATE (not a duplicate) |
| TK-003 | Curator: expert pastes the sample document | PII redaction; detect conflict with ART-01; draft + review |
| TK-004 | Guide: new hire asks about employment certificates | Answer from current article (ART-03); ignore superseded ART-02 |
| TK-005 | Guide: new hire asks about work permit letter | KB does not cover it; route to the right expert |
| TK-006 | Curator: expert rejects the draft | Nothing published on Reject |

---

## Real vs Mock

| Item | Status | Notes |
|---|---|---|
| Harvested artifacts | **Mock data** | Static files in `tools/hr_tk/data/artifacts.py` |
| KB articles | **Static** | 6 pre-seeded articles in `knowledge/hr-tacit-knowledge/articles/` |
| Expert notification | **Simulated** | `hr_tk_notify_expert` returns simulated: true, delivered: false |
| Expert assignment in flow | **Unverified** | Flow runs as the initiator; `assign_to` a named user requires a real tenant |
| Editable draft field | **Unverified** | `text_input_field(single_line=False)` is documented; browser behaviour not tested |
| Publishing makes article searchable | **Not real** | `hr_tk_publish_article` returns the article text but does NOT write to disk; re-import needed |
| Guide in Teams / Slack | **Not tested** | Deployment option |
| Document upload | **Pasted text only** | Expert pastes the document in chat (TK-003); file upload routes not tried |

---

## TK-003 Sample Document

File: [`docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt`](../../docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt)

The expert pastes this text into the curator chat. The document contains:
- Useful tacit knowledge: the payroll-hold sequence for retroactive leave corrections
- PII planted on purpose: names, emails, national IDs, phone numbers, salary amounts
- A conflict with ART-01: the document says the payroll cutoff is the 22nd; ART-01 says the 18th

The curator should: redact the PII, draft a new article and flag an update to ART-01.

---

## Limitations

- The PII scanner uses regex + a fixed name list. It does not use general NER. Sensitive-term
  redaction may leave awkward text; the agent must rewrite the lesson in general terms.
  The `hr_tk_publish_article` re-check is the safety net.
- Keyword matching in `hr_tk_find_related_articles` is tuned to this mock data set. A close
  paraphrase with different vocabulary might not match.
- The tool ID counter (`articles.next_article_id()`) counts the seeded set, so two publishes
  in the same session both get HR-TK-ART-07. Acceptable for a static demo.
- Scheduled harvesting is not built. See the plan Open Items.
