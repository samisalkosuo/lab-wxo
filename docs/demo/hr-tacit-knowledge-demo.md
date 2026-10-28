# HR Tacit Knowledge Agent - Demo Script

For a human presenter. All six scenes were verified in the browser chat UI during Sub-Task 8 of `plans/hr-tacit-knowledge-plan.md`. "Expected behaviour (observed)" rows describe what actually happened across multiple browser runs, not predictions. Where the agent varied between runs, both behaviours are noted.

## 1. Audience and goal

**Audience:** HR operations leaders, people experience managers, or technical evaluators who want to see how tacit knowledge capture and a governed publish flow work together in practice.

**Goal:** show a two-agent architecture — a curator that triages artefacts and drafts articles with PII scanning and expert review, and a guide that answers new-hire questions with citations and routes gaps back to experts.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real HR system, ticketing system, or messaging platform.
- PII detection uses deterministic regex and a fixed name list — it is not a general NER model. It will miss names not in the list and may leave awkward phrasing after redaction; the agent must rewrite those passages.
- Published articles are NOT written to disk and are NOT searchable until the KB is re-imported after the demo run. The agent says so in the flow result.
- No efficiency numbers have been measured. Do not claim time saved or quality improvement.
- Expert assignment (`assign_to` a named user in the flow) requires a real tenant user and has not been configured. The form runs as the flow initiator.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy hr-tacit-knowledge`. This imports the tools, the knowledge base (`hr_tk_knowledge`, 5 articles), the two flows (`hr_tk_review_draft`, `hr_tk_answer_gap`) and both agents (`hr_tk_curator`, `hr_tk_guide`).
- **KB indexing takes time.** After `deploy`, wait until `python wxodemo.py status hr-tacit-knowledge` shows the KB as `ready` before running guide scenes TK-004 and TK-005.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy` for both agents. If you imported by hand, run it manually and reload the chat page.
- **Remote auth expires after 2 hours.** Re-activate before the demo.
- The agents use `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The review form (scenes 1–3, 6) and the answer-gap form (scene 5, follow-up) render only in the browser chat UI. They cannot be driven from the CLI or the run API.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser and go to the chat.
2. **Curator scenes (TK-001, TK-002, TK-003, TK-006):** in the agent picker choose **HR Tacit Knowledge Curator** (YAML name `hr_tk_curator`).
3. **Guide scenes (TK-004, TK-005):** choose **HR Tacit Knowledge Guide** (YAML name `hr_tk_guide`).
4. **Do not use AskOrchestrate.** A wrong selection produces a confusing generic answer.
5. Start a **new conversation** for each scene. A flow waiting for a click blocks its thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment: `python wxodemo.py login`
- [ ] Confirm both agents exist: `orchestrate agents list` should show `hr_tk_curator` and `hr_tk_guide`.
- [ ] Reload the browser chat page and confirm both agents are selectable.
- [ ] No data reset is needed. The mock world is static and read-only. Each scene needs only a fresh conversation.
- [ ] Have the sample document open and ready to copy: `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt` (for scene 3).
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour (observed)**, **Point out**, **Fallback**.

- Tool names are the real ones: `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`, `hr_tk_get_employee_profile`. The review flow appears as `hr_tk_review_draft`; the answer-gap flow as `hr_tk_answer_gap`. The knowledge base appears in transcripts as `hr_tk_knowledge`.
- The write tools `hr_tk_publish_article` and `hr_tk_notify_expert` should **not** appear as agent tool calls — they are called by the flows only. If they appear as direct agent calls, that is a governance failure.
- **The model varies.** Tool order and wording differ between runs. The curator does not always proceed automatically from triage to draft; a follow-up prompt may be needed.
- **Form title shows "(0 questions)"** — this is normal. The `message_output_field` fields (used to display the draft body and metadata) are not counted as "questions" by the platform.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 TK-001 Batch triage | Verified in browser chat UI (multiple runs) |
| 2 TK-002 Contradiction | Verified in browser chat UI |
| 3 TK-003 Document drop-in | Verified in browser chat UI |
| 4 TK-004 Guide citation | Verified in browser chat UI |
| 5 TK-005 Guide gap routing | Verified in browser chat UI |
| 6 TK-006 Expert reject | Verified in browser chat UI (click Reject after TK-001) |

Smoke prompts TK-004 and TK-005 (guide-side only) can be sent via `python wxodemo.py smoke hr-tacit-knowledge`. Curator scenes (TK-001 to TK-003, TK-006) require the browser and cannot be driven through the run API.

---

## Scene 1 - TK-001: Batch Triage (Curator)

**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**

**Prompt (type exactly):**

```
Review the newly harvested items.
```

**Expected behaviour (observed):**

- The curator calls `hr_tk_list_new_artifacts` and receives artefacts A-101 through A-104.
- Produces a triage summary: A-101 NEW (undocumented workaround for retroactive role-change salary corrections), A-102 DUPLICATE/IGNORE (employment certificate chat, covered by ART-03), A-103 DUPLICATE (near-duplicate of ART-03), A-104 IGNORE (meeting reminder noise).
- For A-101: calls `hr_tk_get_artifact`, `hr_tk_find_related_articles` (returns nothing for role-change/salary), `hr_tk_scan_pii` (returns `clean: true` because A-101 uses role labels not names), `hr_tk_find_expert` — then either opens `hr_tk_review_draft` immediately or waits for a follow-up prompt.
- The review form opens with a title like **"Article Review"**, metadata fields (article type, source artifact, author role, placement summary), and the draft body shown in a read-only display field.
- The form title shows "(0 questions)" — this is expected; display fields are not counted as input questions.
- On Confirm, the agent reports verbatim from the flow result: **"CONFIRMED AND RECORDED. Article (new): 'Handling Retroactive Role-Change Salary Corrections ...'"** with the article ID and a note that the article is not searchable until re-import.
- **Observed variation:** the curator sometimes waits after triage and does not draft automatically. If so, type: "Please draft an article for A-101."

**Point out:**

- *Tools called:* `hr_tk_list_new_artifacts`, `hr_tk_get_artifact`, `hr_tk_scan_pii`, `hr_tk_find_related_articles`, `hr_tk_find_expert`, then `hr_tk_review_draft` flow.
- *Red herrings:* A-102 and A-103 both look useful but are covered by HR-TK-ART-03. If the curator drafts a new article for either, that is a misclassification — see Fallback.
- *After clicking Confirm:* the agent reports the `message` field verbatim (observed). The `live_in_kb: false` note appears because the KB only becomes searchable after re-import.

**Fallback:**

- If the curator drafts A-102 or A-103 as new, explain that it found ART-03 as a near-duplicate and should have classified it as DUPLICATE. This is a known limitation of keyword matching.
- If the form does not appear, check the browser console for flow errors. Auth expiry or a stale flow import can cause this. Reload and re-authenticate.

---

## Scene 2 - TK-002: Contradiction Detection (Curator)

**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**

**Prompt (type exactly):**

```
Review the newly harvested items. Focus on ticket A-105.
```

**Expected behaviour (observed):**

- The curator fetches A-105 (ticket SHR-4490: Finland position-change form changed from HR-22 to e-form PR-1, processing time 10 days → 5 days).
- Calls `hr_tk_find_related_articles` with keywords around "position change Finland" — returns HR-TK-ART-04 (Finland, current) and possibly HR-TK-ART-05 (Sweden).
- Identifies A-105 as an UPDATE to HR-TK-ART-04 (not a new article, not an update to ART-05).
- Drafts a correction for ART-04, scans for PII, opens the review form with `article_id: HR-TK-ART-04`.

**Point out:**

- *Red herring:* HR-TK-ART-05 covers the same topic for Sweden. The curator must identify that A-105 is about Finland and propose an update to ART-04 (Finland), not ART-05 (Sweden).
- *Tool used for disambiguation:* `hr_tk_find_related_articles` returns both articles; the agent reads `applies_to` and the title to distinguish countries.

**Be straight:** If the curator mis-targets ART-05, that is a known LLM limitation — it needs to read the article titles closely. The Fallback nudge is reliable in practice.

**Fallback:**

- If the curator proposes ART-05 instead of ART-04: "That article covers Sweden. A-105 is about Finland — which article should be updated?" The agent corrects to ART-04.

---

## Scene 3 - TK-003: Document Drop-in with PII (Curator)

**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**

**Before this scene:** open `docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt` and have the full text ready to paste.

**Prompt (type exactly):**

```
I have some personal notes about correcting retroactive leave start dates. Can you turn this into a KB article? Here are my notes: [paste the full contents of docs/demo/hr-tk-sample/expert-notes-retroactive-leave-dates.txt]
```

**Expected behaviour (observed):**

- The curator treats the pasted text as an artefact, calls `hr_tk_scan_pii` on the text — returns `clean: false` with findings: emails, national IDs (format `DDMMYY-NNNC`), employee IDs (E-48291, E-51034, E-49900, E-47711), phone numbers (+358...), salary amounts (€1,240.00, €980.50, €38,400, €320.00), health terms (surgery, sick leave, medical leave), and known names (Kaisa Mäkinen, Tero Virtanen, Sanna Lehtinen, Eero Salonen, Maarit Virtanen).
- Rewrites the draft replacing PII with general terms ("the employee", role labels, generic dates).
- Re-scans the cleaned draft — returns `clean: true`.
- Calls `hr_tk_find_related_articles` with retroactive leave keywords — returns HR-TK-ART-01. The curator flags the conflict: the document says cutoff is the **22nd** while ART-01 states the **18th**.
- Opens the review form with the cleaned draft and the conflict note.

**Point out:**

- *PII scan in code:* click through the tool call to show the findings list — emails, IDs, health terms. Point out that this happens in code (deterministic regex), not in the LLM response.
- *Conflict detection:* the document says 22nd; ART-01 says 18th. The curator flags this as a contradiction.
- *Document is about 2,500 characters — well under the 8,000-character tool cap.*
- *The publish tool is a safety net:* even if the agent scans source text instead of the finished draft, `hr_tk_publish_article` re-checks PII and refuses with `PII_REMAINING` if any remains.

**Be straight:** The PII scanner uses regex plus a fixed name list. It will miss names not in the list. A real deployment would use a general NER service (e.g. Microsoft Presidio) instead.

**Fallback:**

- If the publish tool refuses with `PII_REMAINING`, explain that the safety net worked as designed — the tool re-checks PII independently of the agent. In a real run you would edit the draft body before confirming.

---

## Scene 4 - TK-004: Guide Answers from Current Article (Guide)

**Agent: HR Tacit Knowledge Guide (`hr_tk_guide`)**

**Prompt (type exactly):**

```
I'm Emilia Saarinen, new HR Coordinator at the Finland desk. How do I get an employment certificate for an employee who needs it for a bank?
```

**Expected behaviour (observed):**

- The guide may call `hr_tk_get_employee_profile` to fetch Emilia's profile (role: HR Coordinator, desk: Finland, tenure: 2 months). This is optional — the procedure is the same regardless of role.
- Searches `hr_tk_knowledge` for the employment certificate procedure.
- Answers with the procedure from HR-TK-ART-03 (current): ESS > My Documents > Certificates > Employment Certificate; select language; submit; 3 working days.
- Cites **HR-TK-ART-03** in the answer. Does NOT cite HR-TK-ART-02 (superseded legacy process) as current guidance.
- **Observed variation:** the guide sometimes calls `hr_tk_get_employee_profile` even when the question is role-independent. This is harmless and demonstrates the guide's context-awareness; note it if it recurs.

**Point out:**

- *Red herring:* HR-TK-ART-02 (superseded) covers the same topic with the old paper-form process. The guide checks the STATUS field and cites only the current article.
- *Article citation:* the guide says "according to HR-TK-ART-03" or equivalent. Article ID visible in the response.

**Be straight:** If the guide over-calls `hr_tk_get_employee_profile` on every question, note it: the guide's instructions direct it to use the profile to tailor answers, which occasionally produces unnecessary calls.

**Fallback:**

- If the guide cites ART-02: "Can you check the status of that article?" The guide corrects to ART-03.

---

## Scene 5 - TK-005: Guide Routes a KB Gap to an Expert (Guide)

**Agent: HR Tacit Knowledge Guide (`hr_tk_guide`)**

**Prompt (type exactly):**

```
An employee is asking for a work permit support letter from HR. I've never handled this before. Who should I ask about this?
```

**Expected behaviour (observed):**

- The guide searches `hr_tk_knowledge`. The KB description explicitly excludes visa and work permit documentation — no results match.
- Calls `hr_tk_find_expert` with a topic around "work permit letter visa documentation".
- Returns expert Janne Korhonen (X-102, HR Operations Lead) whose topics include visa documentation and international mobility.
- Tells the learner: the KB does not cover this topic; suggests routing to Janne Korhonen.
- **Asks for confirmation** before starting `hr_tk_answer_gap`. Does NOT start the flow immediately.
- If the learner types "Yes, please route it to Janne", the guide starts `hr_tk_answer_gap`, which shows a form for the expert to provide an answer or decline.

**Point out:**

- *Restraint behaviour:* the guide has the flow available but asks first. This is the key governance behaviour — the learner confirms before the flow starts.
- *What happens next (if you confirm):* the guide starts `hr_tk_answer_gap`, which notifies the expert (simulated — `delivered: false`) and shows a form. Submit answer → new KB draft is created. Decline → nothing is recorded.
- **The smoke prompt ends at the initial recommendation** (before confirmation). Drive the follow-up interactively.

**Be straight:** Expert notification is simulated (`hr_tk_notify_expert` returns `delivered: false`). In a real deployment this would send a Teams message or email.

**Fallback:**

- If the guide starts the flow without asking, say: "The agent started the flow proactively — in production we would want a confirmation step." Show the flow form as a demonstration of the architecture.

---

## Scene 6 - TK-006: Governance — Expert Rejects the Draft (Browser only)

**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**

**No copy prompt — this scene continues from Scene 1 or 2.** After the review form appears in the browser, click **Reject** instead of Confirm.

**Expected behaviour (observed):**

- The flow takes the default (non-confirm) branch (conditions node: `default=True`).
- The flow returns `decision: 'rejected'`.
- The curator reports: **"REJECTED BY EXPERT. Nothing was published."** (verbatim from the flow result field).
- `hr_tk_publish_article` is NOT called. No article is written.

**Point out:**

- *Governance holds in code:* the Reject path is the conditions default. The publish tool is unreachable on this path regardless of what the agent says.
- *Contrast with Confirm:* Confirm calls the tool and returns the article text with `live_in_kb: false` and the re-import note.

**Fallback:**

- If the curator reports a successful publish after Reject, that is a flow bug. Check the conditions branch (the `default` flag on the publish path). This has not been observed in any browser run.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name hr_tk_curator` (or `hr_tk_guide`), reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select the right agent, start a new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours | Re-run `python wxodemo.py login` |
| `token has expired` in the flow | Browser session idle for ~10 minutes | Reload the browser page and re-authenticate |
| Flow form does not appear | Flow not imported, or import failed | Check `orchestrate tools list` for `hr_tk_review_draft`; re-import if missing |
| "Internal error" on flow confirm | `import json as _json` inside a flow script node — `__import__` is blocked by the platform | Fixed in the current codebase: flow uses string-search instead of `json.loads` |
| Form title shows "(0 questions)" | `message_output_field` fields are not counted as questions by the platform | Expected behaviour — the draft is displayed correctly |
| `PII_REMAINING` from publish tool | Curator scanned source text, not the final draft | The safety net worked. Explain: the tool re-checks PII independently. |
| Curator waits after triage instead of drafting | LLM varies — does not always proceed automatically | Type: "Please draft an article for A-101 (or A-105)" |
| `UnicodeEncodeError ... charmap` from CLI | cp1252 console encoding on Windows | `$env:PYTHONUTF8 = "1"` |

Not seen, so not covered here: form rendering on mobile or non-Chromium browsers; multi-tenant auth issues; KB indexing failures.

## 8. Things not to say

- **Do not say** the PII scan is comprehensive or catches everything. It uses regex and a fixed name list; it misses names not in the list.
- **Do not say** published articles are immediately searchable. The agent explicitly says re-import is needed.
- **Do not say** expert notification is delivered. `hr_tk_notify_expert` returns `delivered: false` in this demo.
- **Do not say** any efficiency number (time saved, % reduction). None have been measured.

## 9. Closing talking points

**What the platform made easy**

- The flow-as-governance-gate pattern: the publish tool is never on the agent — only the flow calls it, after a human clicks Confirm. This took a few lines of flow code, not a complex policy engine.
- Two agents with different least-privilege tool sets, sharing one KB and one expert-directory tool, from the same tool package.
- Deterministic validation in the publish tool (PII re-check, metadata rules) that runs independently of the LLM — the safety net holds even when the agent makes a drafting mistake.

**What was not easy**

- Flow script nodes do not allow `import` statements (the platform blocks `__import__`). Any Python work inside a script node must use only built-in string operations. This caused several "internal error" crashes before the root cause was found; the fix was to replace `json.loads(...)` with a string-search for the JSON field.
- Template syntax (`{flow.input.draft_body}`) in a `message_output_field` crashes the platform when the body contains literal `{` or `}` characters (common in JSON-formatted KB content). The fix is an outer `init_preview` script that replaces those characters before rendering.
- `text_input_field` with `required=True` combined with a DataMap default triggers a validation error on Confirm because the platform treats a DataMap-populated field as still empty for required validation. The fix was to remove the `text_input_field` entirely and display the draft body as a read-only `message_output_field`.
- Keyword matching in `hr_tk_find_related_articles` is tuned to this mock data set. A close paraphrase with different vocabulary could miss a match that a human would catch.

**When NOT to use an agent**

- For a fixed batch job that always runs the same steps (for example: "every Monday, export all closed tickets from ServiceNow and append them to a SharePoint folder"). That is a scheduled ETL job, not an agent.
- For PII detection itself — that is deterministic code. The agent is justified only for the judgment layer on top.

**When an agent might be worth it:** the batch of artefacts is always mixed; the placement decision (NEW vs UPDATE vs DUPLICATE) depends on what the KB search returns; the learner's question is always different; the full decision tree cannot be drawn in advance.

## 10. After the demo

- Start a new conversation before the next scene or repeat run.
- The mock world is static — no cleanup needed.
- If you made real edits in the review form and want to reset, there is nothing to reset; the publish tool does not write to disk.
- To rebuild the script bundle after editing this file: `python docs/demo/build-demo-scripts-bundle.py`.
