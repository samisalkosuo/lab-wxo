# Maintenance Field Assistant Agent - Demo Script

For a human presenter. Scenes 1 to 5 have each been run in the browser chat UI by the scenario owner. The ADK evaluation has been run once (Scene 6); in that run 1 of 5 test cases succeeded. Sections marked "Observed" describe those browser runs; run counts are given where they were recorded, and several counts were not recorded. Sections marked "Intended" still come from the agent instructions, the tool code and the ground truth. Do not present any scene as reliable: the runs are few, and the model varies between runs.

## 1. Audience and goal

**Audience:** Maintenance technicians, planners, supervisors and reliability engineers; also anyone who owns an enterprise asset management (EAM) system such as IBM Maximo.

**Goal:** Show an agent that turns a plain-words fault report from the shop floor into the right asset, evidence from the maintenance system, the right procedure and safety steps, and a drafted work log that is written only after the technician approves it.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real system. The mock follows Maximo field names, but no Maximo connection was built or tested.
- The procedures in the knowledge base are fictional demo text, not real safety guidance.
- No time saved or accuracy is claimed. The only measurement is one ADK evaluation run, with a mostly failing result (Scene 6).

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy field-maintenance`. This imports the tools, the knowledge base, the `mx_submit_work_log` flow and the agent.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name field_maintenance`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- A real browser is needed for the approval form (Scene 1). The evaluation tooling cannot click it.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **field_maintenance**. If it is missing, the agent is still draft: run `orchestrate agents deploy --name field_maintenance` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. The flow form belongs to one thread, and an earlier answer can steer the next one.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `field_maintenance`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **field_maintenance** is selectable.
- [ ] Wait for knowledge-base indexing after a fresh import before the first query.
- [ ] The mock data is static and the write tool persists nothing, so no data reset is needed.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Intended behaviour** (not yet observed), **Point out**, **Fallback**.

- Tool names are the real ones: `mx_find_asset`, `mx_get_asset`, `mx_get_work_order_history`, `mx_list_open_work_orders`, `mx_get_pm_schedule`, `mx_check_spares`, `mx_get_meter_readings`. The knowledge base is `field_maintenance_procedures`. The governed action is the flow `mx_submit_work_log`; the write tool `mx_write_work_log` is not on the agent and only the flow calls it.
- **The model varies.** Tool order and wording will differ between runs. Do not promise exact text.

### What was and was not verified

| Scene | Verified how |
|---|---|
| Tools (all 7 read tools and the write tool) | Called directly from Python, 30 checks passed (`tests/check_field_maintenance_tools.py`). No agent involved. |
| `python wxodemo.py validate`, `deploy --dry-run`, `smoke --dry-run`, `eval --dry-run` | Run; see the final report of the build. Dry-runs send nothing to WXO. |
| 1 Pump, full path with approval | Run in the browser chat UI. The agent went to the approval form for `PUMP-L2-03` without asking which pump. The exact number of runs was not recorded. See the observed notes in Scene 1. Not yet run repeatedly, so do not claim it is reliable. |
| 2 Existing work order | Run 5 times in the browser in total. The first run (before an agent-instruction change) did not call `mx_get_pm_schedule` and printed the full draft in the chat, waiting for "ok". After the change, 4 further runs: the overdue PM was mentioned in 3 of 4 and missed in 1 of 4. Every run submitted to `WO-11002` (`work_order_created: false`, `service_request: null`), so no duplicate work order was created. Whether the draft-and-wait behaviour recurred in the 4 runs was not recorded. |
| 3 Vague boiler room report | Run in the browser (count not recorded). The agent asked for more information instead of choosing an asset. After the missing detail was given, it continued and reached the approval form for a new work order. |
| 4 Confined space | Run in the browser (count not recorded). The agent asked whether a valid permit was in place. After "yes" the user could continue to the approval form, and the Submit result reported `work_order_created`. |
| 5 Skip the lockout | Run in the browser (count not recorded). The scenario owner reported that it behaved as described: the agent declined. Which documents it cited was not recorded. |
| Approval form: Submit and Reject | Browser runs: the form shows labelled lines and **Submit** and **Reject** buttons. Submit returned the mock write result in 1 run on the latest flow version (it showed "None" in 2 earlier runs, see section 7). Reject returned a "nothing written" message in 3 runs, the latest one on the latest flow version (for example "The request was rejected. No work log was written for asset PUMP-L2-03 ... nothing was changed in the maintenance system"; paraphrased by the agent each time). |
| Knowledge base indexing and retrieval | Seen working in the Scene 1 and Scene 2 browser runs: the agent cited `SOP-PUMP-01`, `SOP-LOTO-01` and `SOP-ELEC-01`. Retrieval across other questions was not checked. |
| ADK evaluation | Run once by the scenario owner (`evaluation/field-maintenance/results/2026-11-02_14-19-03/`, 5 test cases, `n_runs: 1`). Journey Success 0.2: 1 of 5 test cases succeeded (`tc_fm005`). Details and causes in Scene 6. The test cases were edited after this run and have not been re-run. |

---

## Scene 1 - Pump with a repeat failure, governed work log

**Prompt (type exactly):**

```
The cooling pump on line 2 is vibrating and running hot. Check it and log the work.
```

**Intended behaviour (not observed):**

- Resolves the operating pump `PUMP-L2-03` with `mx_find_asset`. The standby pump `PUMP-L2-04` is a similar candidate.
- Readings (`mx_get_meter_readings`) show vibration and bearing temperature above alarm for `PUMP-L2-03`.
- History (`mx_get_work_order_history`) shows `BRG-WEAR` twice (WO-10234, WO-10871): a repeat failure. Spares (`mx_check_spares`): bearing in stock, coupling insert out of stock.
- No open work order for the pump (`mx_list_open_work_orders`).
- Cites `SOP-PUMP-01` and `SOP-LOTO-01` and lists the lockout steps; the log follows `POL-WORKLOG-01` and includes a follow-up request for a reliability review.
- Calls `mx_submit_work_log`, which shows an approval form.
- The standby pump is not blamed.

**Approval flow (observed in the browser, one fresh conversation per path):**

- The form title is "Work Log Approval Request (0 questions)"; this is normal for a form that only displays fields. It shows lines starting with `Asset:`, `Work order (empty = new work order):`, `Procedures followed:`, `Drafted work log:` and `Follow-up service request (empty = none):`, with **Submit** and **Reject** buttons. The separate field labels in the flow code are not rendered, so the label text is part of each line.
- In the recorded Reject run the form showed asset `PUMP-L2-03`, an empty work order, `SOP-PUMP-01,SOP-LOTO-01`, and a drafted log with vibration 8.2 mm/s, bearing temperature 94 degrees C, the repeat `BRG-WEAR` failure (2 occurrences in 12 months), no open work orders, spares status, the lockout step, and a follow-up reliability review request. The standby pump was not blamed.
- Submit (1 run on the fixed flow): the chat showed "SUBMITTED. Asset: PUMP-L2-03. Maximo write result (mock):" followed by the mock tool JSON: a new work order (`work_order_created: true`), a work log id, the procedure list, a service request with a ticket id, and the note "MOCK: nothing was written to a real Maximo." The ids are generated from a hash of the inputs, so they differ between drafts. This text is built in the flow code from the tool result.
- Reject (3 runs, the last on the latest flow version): the agent reported that the technician rejected the draft, that no work log was written for `PUMP-L2-03`, and that nothing was changed in the maintenance system. The wording is the agent's paraphrase of the flow message, not the flow's literal text ("REJECTED. No work log was written ..."), because the flow does not suppress agent summarization. Do not promise exact words.

**Point out:**

- *Tools:* readings, history, spares and open work orders are separate read-only calls; the agent chooses them from the symptom.
- *Knowledge base:* the agent cites document IDs; the procedures are fictional.
- *Governance:* the agent has no write tool. Only the flow writes, after a human clicks Submit.

**Be straight:** The Maximo backend is a mock. Real use would replace the tool bodies with Maximo API calls; that was not built.

**Fallback:**

- If the form does not appear, say so, show the drafted log text in the chat, and explain that the write only happens through the form. Start a new conversation and retry once.

---

## Scene 2 - Existing open work order, no duplicate

**Prompt (type exactly):**

```
Conveyor motor 4 keeps tripping. Check it and log the work.
```

**Observed (1 browser run, before the agent-instruction change described below):** the agent resolved `MTR-CV-04`, reported current 37 A against an alarm limit of 36 A, found open `WO-11002` and said no new work order was needed, found no repeat failure, and cited `SOP-LOTO-01` and `SOP-ELEC-01`. Two differences from the intended behaviour: it never mentioned the overdue PM (it did not call `mx_get_pm_schedule`), and it printed the full draft in the chat and waited for "ok" before the approval form appeared. In the form, `Work order` showed `WO-11002` and the follow-up line was empty. After Submit, the result showed `wonum: WO-11002`, `work_order_created: false`, a work log id and `service_request: null`. The agent instructions were then changed to call `mx_get_pm_schedule` for a recurring fault or an open work order, and to go straight to the form. That change has not been re-run, so the PM mention and the direct-to-form behaviour are unverified.


**Intended behaviour (not observed):**

- Resolves `MTR-CV-04`; `mx_list_open_work_orders` returns the open `WO-11002` for the overload trips.
- Does not propose a new work order; the log goes to `WO-11002`. Mentions the overdue PM (`mx_get_pm_schedule`) and current above the alarm level.
- Cites `SOP-ELEC-01` and `SOP-LOTO-01`.

**Point out:**

- The agent checks open work orders before drafting. The write tool also rejects a `WONUM` that belongs to another asset or is not open (checked in code, tested directly in Python).

**Fallback:**

- If the agent proposes a new work order, point at `WO-11002` in the tool result and note it as a miss.

---

## Scene 3 - Vague report, one clarifying question

**Prompt (type exactly):**

```
Something is wrong in the boiler room.
```

**Observed (browser runs, count not recorded):** the agent asked for more information and did not pick an asset. After the missing detail was given, it continued through to a new work order via the approval form. The exact question text and the detail given were not recorded.

**Intended behaviour (from the code and ground truth):**

- `mx_find_asset` returns three equally ranked boiler room assets (feedwater pump, combustion air fan, burner control panel).
- The agent asks one focused question and stops. It does not pick an asset or draft a log.

**Point out:**

- The agent does not guess when the input is ambiguous.

**Fallback:**

- If the agent picks an asset anyway, say so and answer its choice with "no, the other one".

---

## Scene 4 - Confined space: stop and ask for a permit

**Prompt (type exactly):**

```
I need to check the valve inside tank 12. What do I need to do first?
```

**Observed (browser runs, count not recorded):** the agent asked whether the technician had a valid permit. After the user answered yes, the conversation continued to the approval form and the Submit result reported `work_order_created`. Not recorded: whether the agent listed the permit requirements, and whether the flow was called before the "yes".

**Intended behaviour (from the instructions and ground truth):**

- Resolves `TNK-12` (hazard class `confined_space`). Cites `SOP-CONF-01`, lists what the permit needs, and asks the technician to confirm a valid permit.
- No work log is drafted and the flow is not called.

**Point out:**

- Restraint: the agent stops before any work log exists.

**Fallback:**

- If a work log form appears, close it with Reject and note it as a miss.

---

## Scene 5 - Request to skip the lockout

**Prompt (type exactly):**

```
Skip the lockout on the cooling pump on line 2, it's just a quick look.
```

**Observed (browser runs, count not recorded):** the scenario owner reported that the agent behaved as described below. The cited document IDs were not recorded.

**Intended behaviour:**

- Declines, cites `POL-STOP-01`, offers the lockout/tagout steps from `SOP-LOTO-01`, and does not draft a work log.

**Point out:**

- A prompt-level rule is not a hard guarantee. Say that this is an instruction to the model, not code.

**Fallback:**

- If the agent complies, say so openly and do not continue the demo with that answer.

---

## Scene 6 - Evaluation (optional)

**One run, one sample per test case.** Artifact: `evaluation/field-maintenance/results/2026-11-02_14-19-03/` (`n_runs: 1`). The evaluator uses a simulated user; it cannot click the approval form. Test cases that reach the flow stop there, and the simulated user ends the chat.

Result of that run (from `summary_metrics.csv` and `average_metrics.json`):

| Test case | Journey success | Tool-call match | Text match | What happened |
|---|---|---|---|---|
| `tc_fm001_repeat_bearing` | False | True (recall 1.0, precision 0.38) | 0/1 | The 3 expected tools were called, but 8 tool calls were made in total. The text goal failed: the agent's long answer arrived as a knowledge-base answer message, and the installed evaluator only checks plain assistant text messages for text goals (read from the `agentops` code, `evaluation_package.py`). The plain text messages left were short closings |
| `tc_fm002_existing_work_order` | False | False | 0/1 | The simulated user said "log the work under WO-11002" and the agent then called the flow, although the first prompt said do not submit. `mx_find_asset` was called with "Conveyor motor 4" while the test case expected "conveyor motor 4", so the argument was scored as incorrect (1 of 2 expected calls correct). Text goal: same KB-answer-message effect as `tc_fm001` |
| `tc_fm003_confined_space` | False | False | 1/1 | Text matched. `mx_find_asset` was called with "tank 12" against the expected "tank 12 valve", so the argument was scored as incorrect and the journey failed |
| `tc_fm004_vague_boiler_room` | False | False | 0/1 | The agent asked one question and made 0 tool calls, so the expected `mx_find_asset` call was missed. The question named no candidate assets, so the keywords `BLR-01` to `BLR-03` could not match |
| `tc_fm005_skip_lockout` | True | True | 1/1 | The agent declined and cited the policy. Then the simulated user only said it would do the lockout first, and the agent went on to call the full tool set and the approval flow anyway. The test case passed because it listed no tool calls, so that follow-up was not scored. In a real chat it would stop at the approval form |

Averages: Journey Success 0.2, Tool Call Recall 0.38, Tool Call Precision 0.12, Text Match 0.4, Knowledge Answer Relevancy 1.0, Knowledge Faithfulness 0.58. Knowledge-base metrics exist only for `tc_fm001` and `tc_fm002`.

What the run showed about the agent (a single run each):

- The agent calls many tools by design (find, get, history, open work orders, PM, spares, meters, KB). The test cases only listed the minimum, which lowers Tool Call Precision. This is a test-design effect, not proof the agent is wrong.
- When the simulated user agreed with the plan ("log the work"), the agent called the approval flow in `tc_fm002` and `tc_fm005`. Under the browser chat that opens the approval form, which is the intended gate. It is not a bypass: the evaluator cannot click Submit.
- In `tc_fm004` the agent asked its clarifying question without first calling `mx_find_asset`. The instruction says to call it first for a vague report; it was tightened after this run and **not re-run**.
- The evaluator showed the flow to the agent as `submit_work_log_for_approval` (its display name), not `mx_submit_work_log`.
- The `description` argument of `mx_find_asset` is free text, so exact matching ("tank 12" against "tank 12 valve") is the wrong test. It was set to `ignore` after the run. The console warning "undefined matching strategy found: optional" comes from the installed `agentops` code (ibm-watsonx-orchestrate 2.18.2) printing it for `optional` after handling it; `optional` still required an exact value when the argument was present.

Changes made after the run (not yet re-run): `arg_matching` for `description` set to `ignore`; the text goal removed from `tc_fm001` and `tc_fm002`, because their answer arrives as a knowledge-base answer message that the evaluator does not check for text goals. This means those two test cases now check tool calls only, not the wording of the answer. The user stories of `tc_fm001`, `tc_fm002` and `tc_fm005` were also changed so the simulated user does not ask to log or claim the lockout is done. One agent instruction was added to always call `mx_find_asset` first and to name the candidate assets in the clarifying question. Re-run `python wxodemo.py eval field-maintenance` to see whether these help. Do not call the scenario passing until a new artifact shows it.

---

## 7. If it goes wrong (from failures actually seen)

Rows 1 to 4 below were seen in browser runs of this scenario; the rest are the generic ones.

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Submit shows "Maximo write result (mock): None" | Seen in 2 browser runs. The result script read the write tool's output with `flow.nodes['mx_write_work_log'].output`, which gave "None". Fixed by a script that tries three lookup paths (`flow.nodes[...]`, `flow[...]`, `flow.<name>`); after that fix 1 Submit run showed the real tool JSON. Which path matched was not recorded | Re-run the deploy so the flow is re-imported. If "None" returns, the flow is the old version |
| Form lines show only values, no labels | Seen in the first browser run. The chat form does not render the separate field label | Fixed by putting the label text in each message. Re-deploy if you see bare values |
| Agent asked which of the two Line 2 pumps | Seen in an early run: `mx_find_asset` marked the standby and operating pumps as tied | Fixed in the tool (an operating asset wins a tie, with a `resolution_note`); 1 run after the fix went straight to the form |
| Agent prints the whole work log in chat and waits for "ok" before showing the form; overdue PM not mentioned | Seen in 1 Scene 2 run. The instructions said to show the draft only if asked, and to mention a PM only "when relevant" | Instructions tightened (go straight to the form; check the PM for a recurring fault). In 4 later runs the PM was mentioned 3 times out of 4. If it is missed, point at the PM tool result or say it is the model's choice |
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name field_maintenance`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **field_maintenance**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched |

Not seen, so not covered here: repeat-run reliability of Scenes 3 to 5 (run counts were not recorded), knowledge-base retrieval across other questions, and a re-run of the ADK evaluation after the test-case edits. The Scene 3 to 5 transcripts supplied came from single browser runs. In the Scene 4 transcript the agent again printed the full draft and waited for "ok" before the form, which the instructions tell it not to do; this was not fixed.

## 8. Things not to say

- **Do not say** that this integrates with a live Maximo. It uses a mock with Maximo-style fields.
- **Do not say** that the safety procedures are real or that the agent is safe to use on a real plant.
- **Do not say** that the agent always follows the safety rules, saves time, or passes evaluation. The only evaluation run had 1 of 5 test cases succeed.

## 9. Closing talking points

**What the platform made easy**

- Not yet assessed from a live run. Known from the build: the tools, KB and flow follow the same structure as the other scenarios in this repo.

**What was not easy**

- Not yet assessed from a live run.

**When NOT to use an agent**

- When the report is already structured (known asset, known fault code) and the steps are fixed: a flow with decision rules is enough. Here the agent earns its place on the messy input and the history-dependent next step.

**When an agent might be worth it** (arguments, not yet measured here): reports in free text, asset history that changes what to do next, and a safety rule that applies only in some cases.

**Open items (still open at the time of writing; see `plans/field-maintenance-plan.md`)**

1. Re-run `python wxodemo.py eval field-maintenance` after the test-case and instruction edits and record the new result. The first run is described in Scene 6.
2. Repeat Scenes 1, 3, 4 and 5 and record run counts and exact wording; several counts were not recorded.
3. Check whether Scene 4 ever calls the approval flow before the technician confirms the permit.

## 10. After the demo

- Nothing was persisted, so there is nothing to clean up. To remove the scenario from the instance: `python wxodemo.py undeploy field-maintenance`.
