# Incident Triage Agent - Demo Script

For a human presenter. Every prompt below was run against the real agent. Quotes of agent output were copied from recorded transcripts; the approval-flow and tool result messages are marked where they come from the code instead. Where something was **not** verified, the text says so.

## 1. Audience and goal

**Audience:** engineers or technical leads who are evaluating watsonx Orchestrate (WXO) and want to see what an agent, a knowledge base, tools and a human-approval flow look like in practice.

**Goal:** show how the platform pieces fit together on a realistic task (production incident triage over mock data).

**What this demo does NOT claim** (decided with the project owner, see section 9):

- It does **not** show that the evaluation "passes". The final-answer check passed in **0 of 15** runs. Only tool selection was consistent (13 of 15 runs).
- All data is a fixed, mock world. Nothing is connected to a real system.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `scripts/deploy-all.ps1` (or `deploy-all.sh`). This imports tools, the runbook knowledge base, the approval flow and the agent.
- **Imported agents are draft until deployed.** The deploy scripts already run `orchestrate agents deploy --name incident_triage`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The browser needs access to your WXO instance web UI. The approval form (scene 4) only renders there. It cannot be driven from the CLI or the run API.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It printed nothing and hung when run non-interactively in this project's shell.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **Incident Triage** (YAML name `incident_triage`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name incident_triage` and reload the page.
3. **Do not use AskOrchestrate.** During testing, a wrong agent selection produced a confusing generic answer that looked like an agent defect. It was not.
4. Start a **new conversation** for each scene. A flow that is waiting for a click blocks its chat thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). In PowerShell, using the values from your own `env.cfg` via variables only, never pasting or printing the key:
  ```powershell
  $env:PYTHONUTF8 = "1"
  # load WXO_API_KEY and WXO_ENV_NAME from env.cfg into variables, then:
  orchestrate env activate $envName --api-key $apiKey
  ```
  (`$env:PYTHONUTF8 = "1"` avoids cp1252 crashes on Windows.)
- [ ] Confirm the agent exists: `orchestrate agents list` should list `incident_triage`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **Incident Triage** is selectable.
- [ ] No data reset is needed. The mock world is static and read-only, `open_ticket` and `execute_remediation` persist nothing. Each scene needs only a fresh conversation.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Killing Python broke auth for later commands. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `list_open_incidents`, `get_incident`, `get_service_health`, `query_logs`, `get_metrics`, `list_recent_deployments`, `open_ticket`, `request_remediation` (the approval flow). The knowledge base appears in transcripts as a tool call named `incident_triage_runbooks`. The flow appears in transcripts as `request_remediation_approval` (its display name).
- **The model varies.** Tool order and wording differ between runs. Quotes below are from specific runs; do not promise exact text.
- **Display quirk:** the agent writes IDs such as `RB-TLS-01` with *non-breaking hyphens* (U+2011) in its answers. It looks identical on screen. It only matters if you copy an ID into a search box or compare text exactly. In this document I typed those IDs with normal hyphens.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Vague opening | 3 evaluation runs (before the instruction fix) and 6 SDK dry-runs (after the fix). Approval form **not** driven. |
| 2 INC-1001 diagnosis | 3 evaluation runs and 1 SDK dry-run (after the fix). |
| 3 INC-1002 red herring | 3 evaluation runs and 1 SDK dry-run (after the fix). |
| 4 Approval, Approve and Reject | Approval prompt reached the form in 3 of 3 SDK dry-runs. **The form, Approve and Reject were verified only by the user's browser test (Sub-Task 4).** I could not drive the form. |
| 5 INC-1004 non-incident | 3 evaluation runs and 1 SDK dry-run (after the fix). |
| 6 Evaluation | Evaluation numbers are from the stored results of the one evaluation run; not re-run. |
| Trace pointer (scene 2) | `orchestrate observability traces search --last 30m` listed `incident_triage` traces. **Trace details in the web UI were not checked** by me. |

The agent's instructions were fixed after the evaluation run (`p99_latency_ms` changed to `latency`), so tool sequences in the evaluation transcripts differ slightly from what you will see now. The SDK dry-runs were done after the fix.

---

## Scene 1 - Vague opening ("checkout is slow")

**Prompt (type exactly):**

```
Hey, checkout is slow. Can you look into it?
```

**Expected behaviour (observed):**

- The agent first calls `list_open_incidents`, then picks INC-1001 (checkout, CRITICAL) without being told the ID, then `get_incident`, `get_service_health`, `query_logs`, `get_metrics` (`latency`), `list_recent_deployments`, and the runbook knowledge base.
- The list it received contained four incidents: INC-1001 (CRITICAL, checkout), INC-1002 (CRITICAL, payments), INC-1003 (MAJOR, auth-gateway), INC-1004 (MINOR, search-service).
- It then goes straight on to **propose a fix** and the approval form appears ("A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete."). It does this without you asking for a fix.
- Across 9 recorded runs (3 evaluation, 6 dry-run): 8 proposed `rollback` of `checkout`, INC-1001, `RB-DEPLOY-01`. **1 dry-run proposed `db_pool_resize` on `payments` but filed it under INC-1001** (it reasoned that checkout was degraded because payments was slow). That is a mismatch with the incident it was filed under. After adding a "Keep incidents separate" section to the agent instructions a further 10-run retest was done; 2 of 10 still showed the mismatch (no measurable improvement; the section is still in the YAML but unproven). Total across all recorded runs: **3 of 19 vague-opening runs show the mismatch**.
- **It never asked a clarifying question in any of the 19 runs**, even though its instructions allow one. Do not promise one.

**Point out:**

- *Tools:* the agent chose to start with a lookup because the input had no incident ID. Point at the tool-call steps in the chat.
- *Knowledge base:* the runbook is retrieved by the agent when it needs it, not pasted into the prompt.
- *Approval flow* (preview): it paused for a human before anything changed.

**What to do at the form:** read the form fields aloud. If it shows checkout / rollback / INC-1001 / RB-DEPLOY-01, click **Reject** (nothing executes) and say "we will do Approve and Reject properly in scene 4". Then start a new conversation.

**Fallback:**

- If the form shows something that does not match (for example `payments` / `db_pool_resize` under INC-1001), click **Reject** and use it as a point: the human gate caught an inconsistent proposal. Do not call it a pass.
- If the agent does ask which incident, answer "the checkout one" and carry on.
- If the agent answers in text only and no form appears, move on; scene 4 covers the form with a different prompt.

---

## Scene 2 - Bad-deployment diagnosis (INC-1001)

**Prompt (type exactly):**

```
Investigate incident INC-1001 on the checkout service. Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and what remediation action you would recommend.
```

The "Do NOT call request_remediation" clause is here only to keep this scene diagnosis-only. Do not use that clause in scene 4.

**Expected behaviour (observed):**

- Tools: `get_incident`, `get_service_health`, `query_logs` (ERROR, checkout), `get_metrics` (`latency`), `list_recent_deployments` (checkout), then the knowledge base. The post-fix dry-run used exactly this sequence.
- The evidence it gathered: p99 latency 2420 ms vs 180 ms baseline (13.4x), 4.2% 504 errors, and deployment DEP-4108 (checkout v2.14.0) completed 13:55 UTC, with the spike starting 14:02 UTC.
- Real answer excerpt (evaluation run 1): "Perform a **rollback** of the checkout service to the previous stable version (**v2.13.2**) to restore normal latency and eliminate the 504 errors. This action follows the procedure described in Runbook **RB-DEPLOY-01**."
- It states a root cause only after several pieces of evidence (the instructions require at least two).

**Point out:**

- *Tools:* each tool returns a bounded, formatted result (logs are capped, metrics summarised). Show one expanded tool result.
- *Knowledge base:* the answer cites one runbook ID. The retrieval returned several chunks of the same runbook; the agent cited only the matching one.
- *Tracing:* the run is recorded as a trace. From a terminal: `orchestrate observability traces search --last 30m` lists recent `incident_triage` traces with their latency (two I saw were about 4.6 s and 9.9 s; do not treat that as typical). Showing the trace *in the web UI* was not verified, so check where it lives in your instance before promising it. Exporting one trace with `orchestrate observability traces export --trace-id <id>` returned a 400 asking for time-range parameters in this CLI version, so I did not use it.

**Fallback:**

- If a `get_metrics` call returns `METRIC_NOT_FOUND` and the agent retries with `latency`, that is a harmless tool error. None occurred in the 13 post-fix dry-runs; the evaluation run had many because of the instruction typo. See section 8: do not present it as a strength.
- If the answer names a different runbook or omits one, re-run once. If it persists, say so and move on.
- If the tool order differs, that is expected. The conclusion (rollback, v2.14.0 deployment) was the same in all 4 runs.

---

## Scene 3 - Red-herring incident (INC-1002)

**Prompt (type exactly):**

```
Investigate incident INC-1002 on the payments service. There was a recent deployment to notification-service - could that be related? Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and recommended action.
```

(Same wording as the evaluation test case, except the dash. The user planting the suspect is realistic, and it is what the evaluation used.)

**Expected behaviour (observed):**

- Tools: `get_incident`, `get_service_health`, `query_logs`, `get_metrics` (`db_connections`), `list_recent_deployments` for `payments`, then for `notification-service`, then the knowledge base. In the post-fix dry-run the agent skipped nothing relevant; it checked both services' deployments.
- Evidence: `ConnectionPoolTimeoutException ... (active=100/100, max=100, queued=38)`, error code `DB_POOL_EXHAUSTED`, 18.5% HTTP 500, and a `db_connections` metric showing the pool 100% saturated with 45 queued requests.
- It found the notification-service deployment DEP-4109 (14:05 UTC) and dismissed it. Real excerpt (evaluation run 1): "A recent deployment to notification-service (14:05 UTC) is unrelated: the runbook explicitly states that deployments to *unrelated* services are red herrings and should not be considered a cause."
- Recommended action: `db_pool_resize` on payments, runbook `RB-DBPOOL-01`. Same in all 4 runs.

**Point out:**

- *Tools:* the agent looked up the deployment you asked about and compared it to the evidence instead of agreeing.
- *Knowledge base:* the dismissal leans on a rule in the runbook text.

**Be straight about one limit:** here you raised the suspect yourself. In the earlier smoke test, where the prompt did not mention the deployment, the agent never looked at notification-service at all. So this scene shows "checks a suspect and dismisses it", not "spots red herrings unprompted".

**Fallback:** if the agent hedges or does not mention notification-service, ask "what about the notification-service deployment?" It then checks it. If it ever blames that deployment, stop and say that is a failure; none was seen in 4 runs.

---

## Scene 4 - Approval flow (Approve path and Reject path)

This scene uses **two fresh conversations**, one for each path. Use the prompt below in both. It was the prompt verified in the browser.

**Prompt (type exactly; no "Do NOT call request_remediation" clause):**

```
There is a critical incident on the checkout service, INC-1001. Logs show an N+1 query regression introduced by a recent deployment. Investigate and propose a fix.
```

**Expected behaviour (observed):**

- In 3 of 3 SDK dry-runs the agent called, in order: `get_incident`, `get_service_health`, `query_logs` (search "N+1"), `query_logs` (WARN, "query"), `list_recent_deployments`, the knowledge base, then the approval flow with `action=rollback`, `service=checkout`, `incident_id=INC-1001`, `runbook_ref=RB-DEPLOY-01` and a justification. The chat then shows: "A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete."
- Note this prompt hands the agent the conclusion ("N+1 ... introduced by a recent deployment"). It did still query logs and deployments, but it did not call `get_metrics` in these runs.

**What the form shows** (from the flow definition and the browser test): a card titled "Remediation Approval Request" with Target Service, Proposed Action, Incident Reference, Runbook Reference, Agent Justification, and two buttons, **Approve** and **Reject**.

### 4a. Approve path

1. Read the five fields aloud (checkout / rollback / INC-1001 / RB-DEPLOY-01 / the justification).
2. Click **Approve**.
3. Expected (browser-verified by the user): `execute_remediation` runs and the agent reports the result. The mock tool's summary text is "Rolled back checkout to previous stable version (v2.13.2). N+1 query regression removed." The exact wording shown in the chat was not recorded, so describe it loosely.

### 4b. Reject path (new conversation)

1. Send the same prompt. Wait for the form.
2. Click **Reject**.
3. Expected (browser-verified): nothing is executed and the agent reports the rejection. The flow's message text is "REJECTED. No remediation was executed. Proposed action 'rollback' on service 'checkout' was declined by the approver. Incident: INC-1001. No infrastructure changes were made." That wording is from the flow code; the verbatim text as rendered in the browser was not captured.

**Point out (this is the key platform feature of the demo):**

- *Approval flow:* the approval gate is a **flow**, not a line in the agent's instructions. The agent is given `request_remediation` only. The tool that actually changes things, `execute_remediation`, is **not** attached to the agent, so it cannot be called directly by the model. Only the flow calls it, only after Approve.
- *Be honest:* the gate is deterministic flow logic. It would work the same behind a script. It is not evidence that an LLM was needed.
- *Tracing:* the flow instance has its own ID, shown in the transcript text ("flow instance ID ...").

**Fallback:**

- Wrong agent in the picker (AskOrchestrate): no form appears and the answer is generic. Switch to **Incident Triage** and start a new conversation. This is the most likely mistake.
- If the form content looks wrong (different service or action), click **Reject** and say why.
- If the form never renders or Approve errors, see section 7. Do not retry endlessly; move to scene 5 and say the approval path was verified separately in a browser test.
- A conversation stuck behind an unanswered form: open a new conversation.

---

## Scene 5 - Non-incident (INC-1004): restraint

**Prompt (type exactly):**

```
Investigate incident INC-1004. Use your tools to find the root cause and whether any action is needed.
```

**Expected behaviour (observed):**

- It concluded no action in all 4 runs (3 evaluation, 1 dry-run). It never called the approval flow and never opened a ticket.
- The tool path varied, so do not claim a fixed sequence: evaluation runs 1 and 2 used `get_incident`, `get_service_health` and the knowledge base; run 3 also called `get_metrics`; the post-fix dry-run used only `get_incident` and `get_service_health` and did **not** consult the knowledge base.
- Real excerpt (post-fix dry-run): "This is an expected, scheduled load-test event that does not require any remediation. No action is needed."
- Evaluation run 1 cited `RB-NOISE-01` ("Scheduled Load Test Noise - No Action Needed") and said: "Monitor the service after the test window; if latency remains elevated or errors appear, reopen the incident and follow the appropriate runbook."

**Point out:**

- *Tools:* the agent stopped as soon as it had enough evidence. Compare the number of tool steps with scene 2.
- *Instructions:* the "do not propose a remediation for a non-incident" rule is in the agent instructions.

**Be straight:** this is an easy case. The incident title itself says "(Scheduled Load Test)" and its summary mentions the test window, so the data gives the answer away.

**Fallback:** if it consults the knowledge base or calls `get_metrics`, fine. If it proposes a remediation, say that is a failure and reject the form. This was not seen in 4 runs.

---

## Scene 6 - Evaluation (honest)

This scene is mostly talking. Do not run the evaluation live: it is slow, and in a non-interactive shell `orchestrate evaluations evaluate` exits with code 1 (a progress-rendering issue) although it writes all result files.

> **Note:** if the `evaluation/incident-triage/results/` folder is missing in your clone, run the evaluation yourself to produce results, or describe the development-run results verbally.

**Show:** if you have run the evaluation on your instance, open `evaluation/incident-triage/results/<timestamp>/summary_metrics.csv`. If not, describe the results from the development run verbally (see talking points below) and say you are quoting stored results from the development instance.

**Say these things plainly:**

- *What the evaluation measured:* 5 test cases x 3 runs = 15 runs, with a simulated user, against the agent **before** the `p99_latency_ms` -> `latency` instruction fix. `tool_match_success` was true in 13 of 15 runs, and `tool_call_recall` was 1.0 in 13 of 15. The two misses are both INC-1004 runs where the test case lists a `get_metrics` call that the agent skipped because it already had a conclusive answer (a too-strict test case). The plan's Open Item 3 says `query_logs`; the test case file `tc_inc1004_search_no_action.json` actually lists `get_incident`, `get_service_health` and `get_metrics`, and `get_metrics` is what runs 1 and 2 did not call.
- *What did not pass:* the final-answer check passed in **0 of 15** runs. Causes found so far: the agent writes IDs with non-breaking hyphens, so exact keyword matches fail, and the expected answers were short one-liners compared with long answers (the second cause is unverified). So the evaluation currently measures tool selection only. **Do not say the agent passes the evaluation.**
- *Not re-run:* the evaluation has not been re-run since the instruction fix, so the tool-precision numbers (between 0.33 and 1.0, lowest on the vague case) include noise from the typo.
- *What was observed about tool use:* the agent chose to skip tools when it already had a conclusive answer (INC-1003, INC-1004). That saved calls but did not change any answer.
- *Vague input:* the agent resolved the vague opening to INC-1001 through `list_open_incidents` and never asked a clarifying question.

**Fallback:** if someone asks "so why use an agent?", the honest answer is the second half of section 9.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name incident_triage`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **Incident Triage**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `orchestrate env activate` (key from `env.cfg` via a variable; never print it) |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Approve click gives a tool error: `execute_remediation() got an unexpected keyword argument 'data'` (status 424) | Bug found in the first browser test; fixed by passing an explicit `input_schema` to the flow's tool node and re-importing | Re-run the deploy. If it reappears, the flow was not re-imported |
| A `METRIC_NOT_FOUND` tool error shows in a trace | The agent asked `get_metrics` for a name the tool does not have. The `p99_latency_ms` cause (a typo in the agent instructions) is fixed, but an evaluation run also guessed `p95_latency_ms` on its own | Harmless, the agent retries. Do not present as a feature |
| Different tool order or wording than this script | LLM variation | Expected. The conclusions matched in the recorded runs |
| Form shows a service/action that does not fit the incident | Seen once in 9 vague-opening runs (`payments`/`db_pool_resize` under INC-1001) | Click **Reject** and point out the human gate |
| Text match fails when you copy or search an ID | The agent writes IDs with non-breaking hyphens (U+2011) | Display quirk only; retype with a normal hyphen |
| Chat page "stuck" after the form | The thread is waiting for a click | Click Approve or Reject, or start a new conversation |
| Evaluation run exits with code 1 | Non-TTY progress rendering | Result files are still written; read them |

Not seen, so not covered here: clean first deploy on a fresh instance. The deploy was only re-run over the existing `techzone1` instance (exit 0, all resources updated).

**Note:** `scripts/smoke_test.py --scenario incident-triage` sends the four diagnosis-only prompts in `evaluation/incident-triage/ground_truth.json` (`smoke_prompts`) to the deployed agent and prints the tools called and the start of each answer. It looks the agent up by name, so no UUID is needed. It does not grade the answers, and its live path has not yet been run against an instance (only `--dry-run` was).

## 8. Things not to say

- **Do not say** the agent "recovers from a wrong metric name" as a strength. The recorded recoveries after `p99_latency_ms` were caused by a typo in the agent's own instructions, now fixed.
- **Do not say** "the agent passes the evaluation".
- **Do not say** the agent always asks a clarifying question.

## 9. Closing talking points

**What the platform made easy**

- Assembling an agent from small, bounded tools plus a knowledge base: import the tools, import the knowledge base, list them in `agent.yaml`.
- A governed human-in-the-loop step: the approval form is a flow, the dangerous tool is not given to the agent, and Approve/Reject both behave as designed (browser-verified).
- Runbook retrieval with citations that the agent surfaced as runbook IDs.
- Scripted re-deploys: re-importing updates resources in place.
- Built-in evaluation tooling and traces for the agent's tool use.

**What was not easy**

- Draft versus live agents (the picker showed only AskOrchestrate until deploy).
- Flow tool nodes: the first browser test failed because the tool node had no explicit input schema.
- Evaluation: the framework needed hand-installed dependencies on Python 3.14, its final-answer check currently passes 0 of 15 runs, the output is tricky to read in a non-TTY shell, and the approval form cannot be driven by the evaluator.
- Text matching of answers is fragile (non-breaking hyphens, long answers versus one-line expectations).
- Auth expiry (2 hours) and Windows encoding quirks in the CLI.

**When NOT to use an agent**

- The workflow is known and fixed, the inputs are well-formed and the rules are stable. A script or a flow is faster, cheaper, deterministic and easier to test.
- Latency or cost matters per request. A script makes no LLM calls; the agent runs took seconds (the two traces I listed were about 4.6 s and 9.9 s) and use an LLM.
- You need the same answer every time for audit or compliance. The agent's tool path varied between runs (INC-1004), and once an action was filed under a mismatched incident (vague opening).
- The risky step needs a guarantee. Put it in a flow or a tool (as done here), never only in instructions.

**When an agent might be worth it** (arguments, not yet measured here): inputs that vary or are vague, the next step depends on what the previous step found, new incident types appear faster than rules can be written, and an explanation in prose is part of the deliverable.

**Open items (still open at the time of writing; see `incident-triage-plan.md`)**

1. The evaluation's final-answer check passes 0 of 15 (non-breaking hyphens, one-liner expectations).
2. The INC-1004 test case is too strict (it expects a `get_metrics` call the agent can legitimately skip; the plan text says `query_logs`, but the test case file lists `get_metrics`).
3. The evaluation has not been re-run since the `p99_latency_ms` -> `latency` fix.
4. Evaluation dependencies were installed by hand into the global Python 3.14; see the README for the documented workaround. A clean install was not tested.

## 10. After the demo

- The SDK dry-runs behind this script started approval-flow instances (the form cannot be answered from the API) that were never answered. They only touch mock data, and they may show up in traces or conversation lists. I did not check how the instance treats them.
- Sub-Task 8 complete. Sub-Task 9 (README update, teardown scripts) is next.


