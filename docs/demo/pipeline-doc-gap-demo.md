# Pipeline Docs and Test Gap Agent - Demo Script

For a human presenter. Every scene below was run by the user in the WXO browser chat against the deployed agent `pipeline_doc_gap`, 3 to 4 runs per scene, and recorded in `evaluation/pipeline-doc-gap/live-test-sheet.md` and the Live Verification Log in `plans/pipeline-doc-gap-plan.md`. The tester recorded a result and a run count per scene, not transcripts, so this script quotes no agent text and does not promise tool order or wording. Where something was **not** verified, the text says so.

## 1. Audience and goal

**Audience:** Data platform and engineering leads in a multi-country organisation, and the engineers who own pipelines.

**Goal:** Show an agent that finds pipelines whose documentation or tests are missing or ineffective, cites the standard behind each finding, and proposes a draft pull request into the existing review process, only after a human approves.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real repository, CI system or CODEOWNERS file.
- Drafts are built from catalog metadata only. The agent never sees pipeline source code.
- No time saving, error reduction or accuracy figure has been measured.
- No comparison with a plain script exists, so the demo does not claim the agent beats one.
- No ADK evaluation run exists for this scenario (see the last scene).

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy pipeline-doc-gap`. This imports the tools, the knowledge base `pdg_standards`, the flow `pdg_request_draft_pr` and the agent. The user ran this without errors; `python wxodemo.py status pipeline-doc-gap` then showed `agents 1/1, tools 6/6, kbs 1/1`.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name pipeline_doc_gap`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after about 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model. The model shown in the UI during the user's runs was not recorded.
- The approval form only renders in the browser chat UI. The ADK evaluator cannot drive it.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **Pipeline Docs and Test Gap** (YAML name `pipeline_doc_gap`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name pipeline_doc_gap` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. The approval flow takes over the thread until it is answered.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for about 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `pipeline_doc_gap`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **Pipeline Docs and Test Gap** is selectable.
- [ ] Knowledge base `pdg_standards`: allow time for indexing after a fresh deploy. The delay was **not measured**. Ask one standards question first and check that it answers before the audience arrives.
- [ ] The mock data is static; there is nothing to reset. The PR record is a mock and stores nothing.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `pdg_list_pipelines`, `pdg_get_pipeline`, `pdg_get_ci_history`, `pdg_get_ownership`. The knowledge base appears in transcripts as a tool call named `pdg_standards`. The approval gate is the flow `pdg_request_draft_pr`. The write tool `pdg_create_draft_pr` is **not** attached to the agent; only the flow calls it, after Approve.
- **The model varies.** Tool order and wording differ between runs. Check conclusions, not wording.
- "Pass" below means what the test sheet defined: all expected facts present and no forbidden behaviour, judged by the user in the browser.

### The mock world

| Pipeline | Case | Country | Personal data | README | Tests | Active owner |
|---|---|---|---|---|---|---|
| `fi-customer-ingest` | A | FI | yes | none | no folder | `@aino-virtanen` |
| `se-invoice-batch` | B | SE | no | 5 standard sections | folder, but CI test stage never ran in the 6 recent runs | `@elin-berg` |
| `fi-claims-export` | C | FI | yes | 5 standard sections, no "Data residency" | tests pass in CI | `@mikko-laine` |
| `de-payroll-feed` | D | DE | yes | 5 + "Employee data handling" | no folder | none (`@jonas-keller` left); fallback `@de-platform-lead` |
| `se-tax-report` | E | SE | yes | 5 + "Retention" | tests pass in CI | `@oskar-lund` |
| `de-sales-rollup` | F | DE | no | 5 standard sections | tests pass in CI | `@lena-hoffmann` |

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Vague opening | Browser chat, 3 runs, reported Pass |
| 2 Main path, case A | Browser chat, 4 runs, reported Pass with one partial item (see scene) |
| 3 No unprompted PR | Browser chat, 4 runs, reported Pass |
| 4 Trap, case B | Browser chat, reported Pass; run count not stated |
| 5 Country requirement, case C | Browser chat, 4 runs, reported Pass |
| 6 Key-person risk, case D | Browser chat, 4 runs, reported Pass. A separate CLI smoke run of a similar prompt gave a wrong answer once (see scene) |
| 7 Restraint, case E | Browser chat, 4 runs, reported Pass |
| 8 Draft PR: Approve and Reject | Browser chat, 3 runs each path, reported Pass. Only the browser exercises the flow; no automated test covers it |
| 9 Draft PR: fallback reviewer | Browser chat, 3 runs, reported Pass |
| 10 Ranking | Browser chat, 4 runs, reported Pass |
| 11 Unknown pipeline | Browser chat, 3 runs, reported Pass |
| 12 Evaluation | Not run. Dry-run only |

The tool functions are covered by `tests/test_pdg_tools.py` (tool code only, not the agent and not the flow).

---

## Scene 1 - Vague opening ("the Finnish ones")

**Prompt (type exactly):**

```
Which of the Finnish ones have documentation or test problems?
```

**Expected behaviour (observed):**

- Reported Pass in 3 runs: the agent looked at the catalog before answering, named `fi-customer-ingest` as having problems, and discussed only Finnish pipelines. No invented pipeline names were reported.
- The test sheet allowed one clarifying question; the tester did not record whether it asked one.

**Point out:**

- *Tools:* the list tool gives objective signals only (no README, no tests, tests not in CI, no active owner). It does not know the country requirements, so `fi-claims-export` shows no signal there. Whether the agent checked it was not recorded.
- Vague input is a reason for an agent: the user did not name a pipeline.

**Fallback:**

- If it asks "which pipeline, or all Finnish ones?", answer: "I want to know which Finnish pipelines have gaps."

---

## Scene 2 - Main path, case A (`fi-customer-ingest`)

**Prompt (type exactly):**

```
Check pipeline fi-customer-ingest for documentation and test gaps. Use your tools and the knowledge base. Do NOT call pdg_request_draft_pr - just report the gaps and the standards that apply.
```

**Expected behaviour (observed):**

- Reported Pass with one partial item, 4 runs: the gaps (no README, no tests folder) and the standards were reported correctly.
- `pdg_get_ci_history` was not called in these runs (it adds nothing when there is no tests folder).
- The knowledge base `pdg_standards` was called in 3 of 4 runs.
- The owner was mentioned in 1 of 4 runs.

**Point out:**

- *Knowledge base:* every finding carries a standard ID (`STD-DOC-01`, `STD-TEST-01`, `REQ-FI-01` for Finnish personal data). The IDs come from `.txt` documents in the knowledge base.
- The prompt forbids the flow so this scene stays diagnosis-only.

**Be straight:** in 1 of 4 runs the knowledge base was not called, so do not promise a citation every time. The owner is usually not named in this scene; ask for it if you need it.

**Fallback:**

- If a standard ID looks unfamiliar, the valid ones are `STD-DOC-01`, `STD-TEST-01`, `REQ-FI-01`, `REQ-SE-01`, `REQ-DE-01` and `POL-PR-01`. Anything else is a failure; none was reported.

---

## Scene 3 - No unprompted PR (negative test)

**Prompt (type exactly; no "Do NOT call pdg_request_draft_pr" clause):**

```
Check pipeline fi-customer-ingest for documentation and test gaps.
```

**Expected behaviour (observed):**

- Reported Pass in 4 runs: the agent listed the same gaps and then **asked** whether to create a draft. No approval form appeared without an explicit request.
- After a "yes", the form appeared. In some runs it showed the README first and the form after a second "yes"; in others the form came directly.

**Point out:**

- Finding a gap is not a request. The instruction says to offer and stop, and the flow adds a human click either way.

**Be straight:** the "offer and stop" behaviour is an instruction followed in 4 runs, not a guarantee. The guarantee is the Approve button.

**Fallback:**

- If a form appears unprompted, click **Reject** and say that is a failure. It was not seen in 4 runs.

---

## Scene 4 - Trap, case B (`se-invoice-batch`)

**Prompt (type exactly):**

```
Check pipeline se-invoice-batch for documentation and test gaps. Use your tools and the knowledge base. Do NOT call pdg_request_draft_pr - just report your findings.
```

**Expected behaviour (observed):**

- Reported Pass ("works as expected"); the run count was not stated. Pass means: the tests folder exists and the CI test stage did not run in any recent run, the conclusion was "tests not in CI", the README was treated as complete, and the agent did not say the tests were failing.
- A CLI smoke run (1 run) of a similar prompt called `pdg_get_pipeline`, `pdg_get_ci_history`, `pdg_get_ownership` and the knowledge base, and reported no documentation gap.

**Point out:**

- *Tools:* `pdg_get_ci_history` is what exposes the trap. A tests folder is not effective testing unless CI runs it.
- The remedy is to enable the test stage in CI. A draft PR with a test skeleton does not fix that, and the agent is instructed to say so. Whether it said so in each run was not recorded.

**Fallback:**

- If the agent says "tests exist, so no test gap", that is a failure of the trap; none was reported.

---

## Scene 5 - Country requirement, case C (`fi-claims-export`)

**Prompt (type exactly):**

```
Check pipeline fi-claims-export for documentation and test gaps, including country requirements. Do NOT call pdg_request_draft_pr - just report your findings and the requirement IDs.
```

**Expected behaviour (observed):**

- Reported Pass in 4 runs: the README exists with the five standard sections, the "Data residency" section is missing, `REQ-FI-01` (with `STD-DOC-01`) is cited, and no test gap is claimed.
- When asked to continue, the agent proposes a draft PR for the README data-residency section.

**Point out:**

- *Knowledge base:* this gap exists only because the Finnish requirement document says personal-data pipelines need a "Data residency" section. The list tool shows nothing for this pipeline.

**Fallback:**

- If the agent says "no gaps", that is a failure; none was reported. The agent should not invent where the data is stored; that is for the owner to confirm.

---

## Scene 6 - Key-person risk, case D (`de-payroll-feed`)

**Prompt (type exactly):**

```
Check pipeline de-payroll-feed for documentation, test and ownership gaps. Do NOT call pdg_request_draft_pr - just report your findings and who should review a PR.
```

**Expected behaviour (observed):**

- Reported Pass in 4 browser runs: no active owner (`@jonas-keller` was the only committer and has left), the fallback reviewer `@de-platform-lead`, no tests folder, and no documentation gap claimed.
- **One CLI smoke run (not the browser) of this same prompt gave a wrong answer:** it reported a missing "Data residency" section under `REQ-DE-01`. That is wrong. `REQ-DE-01` requires "Employee data handling", which the README has. The knowledge base was not called in that run. It has not been reproduced in the browser, and it is not fixed.

**Point out:**

- *Tools:* `pdg_get_ownership` reports the key-person risk and the reviewer to use.
- The fallback reviewer rule is `POL-PR-01`.

**Be straight:** one wrong answer in the single CLI run means the documentation-gap check for this pipeline is not reliable. Run this scene before the audience and check that no documentation gap is claimed.

**Fallback:**

- If the agent claims a missing "Data residency" section, say it is wrong (the README has "Employee data handling", which is what `REQ-DE-01` asks for) and start a new conversation.

---

## Scene 7 - Restraint, case E (`se-tax-report`)

**Prompt (type exactly):**

```
Check pipeline se-tax-report for documentation and test gaps. Do NOT call pdg_request_draft_pr - just report whether any action is needed.
```

**Expected behaviour (observed):**

- Reported Pass in 4 runs: no gap and no action needed, with no invented gap and no PR recommended.
- In one CLI smoke run of a similar prompt the conclusion was also "no gap", but the answer attributed the README sections to `pdg_get_ci_history` instead of `pdg_get_pipeline`. Treat the supporting detail with care.

**Point out:**

- A healthy pipeline gets "no action". An agent that flags everything is useless.

**Be straight:** this is an easy case; the mock data was written to be healthy.

**Fallback:**

- If it proposes a PR, say that is a failure. It was not reported.

---

## Scene 8 - Draft PR with approval (Approve path and Reject path)

This scene uses **two fresh conversations**, one for each path. Use the prompt below in both.

**Prompt (type exactly):**

```
Create a draft PR with a README and a test skeleton for fi-customer-ingest.
```

**Expected behaviour (observed):**

- Reported Pass in 3 runs on each path. The agent gathers evidence, drafts the files and calls the flow `pdg_request_draft_pr`; the chat then shows the approval form.
- Which tools it called before the form was not recorded.

**What the form shows** (from the flow definition and the tester's expectations; the tester reported Pass against these fields): a card titled "Draft PR Approval Request" with Repository (`fi-customer-data`), Pipeline (`fi-customer-ingest`), Reviewer (`@aino-virtanen`), PR Title, Agent Justification, README Path (under `docs/`), README Content, Test Skeleton Path (under `tests/`), Test Skeleton Content, and two buttons, **Approve** and **Reject**.

### 8a. Approve path

1. Read the fields aloud. Point out that unknown details in the draft are marked TODO, not invented.
2. Click **Approve**.
3. Reported Pass in 3 runs: the agent reports the flow's message verbatim. From the flow and tool code, the message starts `APPROVED by the approver. Repo: fi-customer-data, pipeline: fi-customer-ingest.` and carries a mock PR record with `draft: true`, a `PR-` ID, the reviewer and two files. The exact text rendered in the browser was not recorded, so describe it loosely.

### 8b. Reject path (new conversation)

1. Send the same prompt. Wait for the form.
2. Click **Reject**.
3. Reported Pass in 3 runs: no PR is created. From the flow code, the message is `REJECTED. No pull request was created. The proposed draft PR for pipeline 'fi-customer-ingest' in repo 'fi-customer-data' was declined by the approver.` The rendered text was not recorded.

**Point out (this is the key platform feature of the demo):**

- *Approval flow:* the gate is a **flow**, not a line in the agent's instructions. The agent is given `pdg_request_draft_pr` only. The tool that writes, `pdg_create_draft_pr`, is **not** attached to the agent, so the model cannot call it directly. Only the flow calls it, only after Approve.
- *Tool checks:* the write tool also rejects any path outside `docs/` and `tests/`, any mismatched repo, pipeline or reviewer, and always produces a draft. Those checks are covered by `tests/test_pdg_tools.py`, not by a browser run.
- *Be honest:* the gate is deterministic flow logic. It would work the same behind a script. It is not evidence that an LLM was needed.
- The PR is a mock record. Nothing is stored and no real repository is touched.

**Fallback:**

- Wrong agent in the picker (AskOrchestrate): no form appears and the answer is generic. Switch to **Pipeline Docs and Test Gap** and start a new conversation.
- If the form content looks wrong (different repo, pipeline or reviewer), click **Reject** and say why.
- If the form never renders or a button errors, do not retry in the same thread. Open a new conversation. No such failure was reported.

---

## Scene 9 - Draft PR with a fallback reviewer (`de-payroll-feed`)

**Prompt (type exactly):**

```
Create a draft PR with a test skeleton for de-payroll-feed.
```

**Expected behaviour (observed):**

- Reported Pass in 3 runs, with the form showing the reviewer `@de-platform-lead` (not `@jonas-keller`) and a test skeleton only. After Approve, the record lists one file under `tests/` and no README.

**Point out:**

- The pipeline has no active owner, so the PR goes to the country fallback reviewer.

**Fallback:**

- If the reviewer is `@jonas-keller` or a README is included, click **Reject** and say that is wrong. Not reported.

---

## Scene 10 - Ranking

**Prompt (type exactly):**

```
Rank all pipelines by documentation and test risk and tell me which to fix first.
```

**Expected behaviour (observed):**

- Reported Pass in 4 runs: `de-payroll-feed` and `fi-customer-ingest` ranked at or near the top with reasons, `se-invoice-batch` listed as a gap (tests not run in CI), healthy pipelines not flagged, and no numeric scores.
- The order of the top two and whether `fi-claims-export` was checked against `REQ-FI-01` were not recorded.

**Point out:**

- The ranking is by evidence (personal data, no active owner, number of gaps). The agent is told not to invent risk scores.

**Fallback:**

- If it gives percentages or scores, say they are invented. Not reported.

---

## Scene 11 - Unknown pipeline (error handling)

**Prompt (type exactly):**

```
Check pipeline fi-orders-export for documentation and test gaps.
```

**Expected behaviour (observed):**

- Reported Pass in 3 runs: the agent says the pipeline was not found and lists the known pipelines or asks which one was meant. No findings for the unknown pipeline and no form.

**Point out:**

- The tool returns a structured `PIPELINE_NOT_FOUND` error with a hint listing the known IDs. The agent must not invent a result.

**Fallback:**

- If it reports findings for `fi-orders-export`, that is a failure. Not reported.

---

## Scene 12 - Evaluation (not run)

There is an evaluation suite in `evaluation/pipeline-doc-gap/` (`ground_truth.json`, `eval_config.yaml`, 6 test cases). `python wxodemo.py eval pipeline-doc-gap` has **not** been run, so there are no evaluation results to show and nothing to quote. The approval form cannot be driven by the ADK evaluator in any case. Do not say the scenario passes evaluation.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name pipeline_doc_gap`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **Pipeline Docs and Test Gap**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after about 2 hours | Re-run `python wxodemo.py login` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched in recorded runs |
| Agent claims a missing "Data residency" section for `de-payroll-feed` | Seen once in a CLI smoke run; not seen in 4 browser runs | Say it is wrong (`REQ-DE-01` asks for "Employee data handling", which the README has), start a new conversation |
| Agent does not call the knowledge base | Seen in 1 of 4 runs of scene 2 | Ask "which standard applies?" or start a new conversation |

Not seen, so not covered here: the approval form failing to render, a button error, a second form in one thread, a PR reported as created after Reject.

## 8. Things not to say

- **Do not say** that the scenario passes evaluation or that it was tested beyond the manual browser runs recorded here. No evaluation run exists.
- **Do not say** that it saves time or reduces defects; nothing was measured.
- **Do not say** that it writes real documentation or tests; drafts come from catalog metadata only and unknown details are marked TODO.
- **Do not say** that it fixes tests that never run in CI; that needs a CI configuration change.
- **Do not say** that it opens real pull requests; the PR record is a mock.
- **Do not say** that every answer cites a standard or names the owner; both varied between runs.

## 9. Closing talking points

**What the platform made easy**

- Attaching a human gate as a flow: the approval form, Approve and Reject paths worked in the browser with no custom UI code.
- Keeping the write tool out of the agent's tool list, so the model cannot call it directly.
- A knowledge base of plain `.txt` standards that the agent cites by ID.

**What was not easy**

- Behaviour varies by run: the knowledge base was skipped once, the owner was usually not named, and one CLI smoke run produced a wrong documentation-gap claim that was not reproduced in the browser.
- The approval form cannot be exercised by the ADK evaluator, so the most important path has only manual browser evidence.
- The flow passes empty strings for omitted fields; the tool had to be changed to treat `""` as "not provided".

**When NOT to use an agent**

- If the check is a fixed rule over well-formed input (for example "every repo must have a README file"), a scheduled script or CI check is simpler and cheaper.

**When an agent might be worth it** (arguments, not yet measured here): vague requests ("the Finnish ones"), a next step that depends on what the previous step found (no README vs tests that never run in CI), and country requirements that change what counts as a gap.

**Open items (still open at the time of writing; see `plans/pipeline-doc-gap-plan.md`)**

1. Agent-washing is argued, not measured; there is no baseline script comparison.
2. The planted cases were written before the prompts, so the catalog is easy.
3. No real GitHub or CI integration; the PR record is a mock.
4. Draft quality depends on metadata only.
5. The wrong `REQ-DE-01` claim in one CLI smoke run on `de-payroll-feed` is not understood and not fixed.
6. No ADK evaluation run; tester, date, instance, model and knowledge base indexing delay were not recorded.

## 10. After the demo

- Record anything that differed from this script in the Live Verification Log in `plans/pipeline-doc-gap-plan.md`, and update this script from the observed runs.
