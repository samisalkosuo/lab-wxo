# Travel Request Agent - Demo Script

For a human presenter. Every prompt below was run against the real agent, except that the approval form was **not** answered (it cannot be driven from the run API). Quotes of agent output were copied from recorded transcripts; the approval-flow and tool result messages are marked where they come from the code instead. Where something was **not** verified, the text says so.

## 1. Audience and goal

**Audience:** engineers or technical leads who are evaluating watsonx Orchestrate (WXO) and want to see an agent that combines a source document in another language, deterministic tools and a human-approval flow.

**Goal:** show how an employee can ask in free English text whether a business trip may go ahead, and get an outcome (APPROVED, NEEDS APPROVAL or DENIED), reasons with references to the Finnish source document, a reimbursement estimate, and, after a human approves in a flow, a request id that other apps can use. Also give an honest answer to "is this really an agent, or a script with a chat box?" (section 9).

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real system. The employees, cost centres, budgets and the approval-level policy are invented.
- The agent does **not** book trips, pay anything or process expense claims.
- It does **not** read the whole state travel regulation. Only a small subset of the 2026 rates is hand-keyed into the tools (8 countries, a few domestic rates). The PDF is in the knowledge base for explanations and references, not for amounts.
- It does **not** show that the agent beats a plain script. Most of the logic (amounts, thresholds, budget check, request id) is deterministic code. See section 9.
- The approval form (Approve and Reject) has **not** been seen working in a browser. See the verification table.
- The legal status of shipping the PDF is **not** settled (section 9, open items).

## 2. Prerequisites

- The repo (or the packaged zip) has been deployed to your WXO instance with `scripts/deploy-all.ps1` or `deploy-all.sh` (scenario: `travel-request`). This imports the tools, the two knowledge bases, the approval flow and the agent.
- **Imported agents are draft until deployed.** The deploy scripts already run `orchestrate agents deploy --name travel_request`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model. Both knowledge bases use the embedding model `ibm/granite-embedding-278m-multilingual`; the instance must offer that too (it was accepted on `techzone1`; other instances were not tried).
- The browser needs access to your WXO instance web UI. The approval form (scene 8) only renders there.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **travel_request** (YAML name `travel_request`; the agent has no separate display name). If it is missing, the agent is still draft: run `orchestrate agents deploy --name travel_request` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene, except scene 2 where the second prompt goes into the same conversation. A flow that is waiting for a click blocks its chat thread.
5. Write in English. The agent answers in English; the Finnish document references stay in Finnish (for example `Valtion matkustussääntö 2026, 13 §`). That is by design.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). In PowerShell, using the values from your own `env.cfg` via variables only, never pasting or printing the key:
  ```powershell
  $env:PYTHONUTF8 = "1"
  # load WXO_API_KEY and WXO_ENV_NAME from env.cfg into variables, then:
  orchestrate env activate $envName --api-key $apiKey
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `travel_request`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **travel_request** is selectable.
- [ ] No data reset is needed. The mock world is static. From reading the tool code, the request id is derived from the trip data and nothing is stored (a direct call of the tool returned the same kind of id; the flow was not run).
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.
- [ ] Optional smoke check before the demo: `python scripts/smoke_test.py --scenario travel-request` sends the eight diagnosis-only prompts in `evaluation/travel-request/ground_truth.json` and prints the tools called and the start of each answer. It does not grade the answers.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `travel_get_employee_profile`, `travel_get_budget_status`, `travel_get_per_diem_rate`, `travel_estimate_reimbursement`. The knowledge bases appear in transcripts as tool calls named `travel_state_rules` (the Finnish PDF) and `travel_agency_policy` (the English mock policy). The approval flow is `travel_submit_request`; in transcripts it appears under its display name, `submit_travel_request_for_approval`. The tool that issues the id, `travel_issue_request_id`, is **not** attached to the agent; only the flow calls it.
- **The model varies.** Tool order and wording differ between runs. Quotes below are from specific runs; do not promise exact text.
- The prompts for scenes 1, 2 (second prompt), 3, 4, 5 and 6 end with "Do not call travel_submit_request ..." That clause only keeps the agent from starting the approval flow while you present the decision. Runs without it were not compared, so what the agent does without the clause is not known.
- **How the numbers were checked.** The reimbursement amounts are the output of `travel_estimate_reimbursement` for the stated inputs. They were compared with `evaluation/travel-request/ground_truth.json`, whose amounts come from the same tool, not from an independent calculation by hand of the PDF. The agent is instructed to state only numbers from tools.

### What was and was not verified

Unless a row says otherwise, "3 runs" means three runs of the same prompt through the run API (`scripts/smoke_test.py` style, no browser), with the final answers read by me against `ground_truth.json`. Eight prompts were run three times each (24 answers); an earlier build had several wrong outcomes that were fixed by instruction changes, so this evidence covers the **current** configuration only.

| Scene | Verified how |
|---|---|
| 1 Happy path (TR-001) | 3 runs, all APPROVED with 25 EUR. |
| 2 Vague opening and follow-up | First prompt: 4 runs, no tool calls, each asked for the missing facts. Second prompt in the same conversation: 1 run, NEEDS APPROVAL, manager, 361 EUR. The same facts as a single message (TR-002): 3 runs, same result. |
| 3 Policy beats request (TR-005) | 3 runs, all APPROVED with 85 EUR. |
| 4 Holiday week (TR-004) | 3 runs, all NEEDS APPROVAL, manager, 763.3 EUR. |
| 5 Budget forces director (TR-008) | 3 runs, all NEEDS APPROVAL, director, 709 EUR. |
| 6 Rates for 2027 (TR-007) | 3 runs, all APPROVED with no estimate. |
| 7 Reading the Finnish source | 3 runs, all called `travel_state_rules` with a Finnish query and gave the right main point. Details differed between runs (see scene). |
| 8 Approval flow | 1 run reached the flow call with `required_level: manager` and the right trip data. **The form, Approve, Reject, the request id from the flow, and the agent reporting the flow message were NOT verified.** I could not drive the form. |
| 9 Restraint (TR-006) | 3 runs, none called a tool, none issued a decision or an id. |
| Knowledge-base use overall | In the 24 answers the PDF knowledge base was called in 1 and the English policy knowledge base in 8. In the other answers the section numbers came from the tool line items. Scene 7 is the one that reliably uses the PDF. |

---

## Scene 1 - Happy path (TR-001)

**Prompt (type exactly):**

```
I am Aino Virtanen (E-1001). I want to hold a customer meeting in Tampere on Tuesday 14 April 2026. I leave home in the morning and return in the evening, about 8 hours in total. May I go, and how much reimbursement can I expect? Do not call travel_submit_request, just give the decision.
```

**Expected behaviour (observed):**

- The agent calls `travel_get_employee_profile`, `travel_estimate_reimbursement` and `travel_get_budget_status`, in that order (3 of 3 runs), and in all 3 runs also searched `travel_agency_policy`.
- It answers APPROVED with an estimated total of 25 EUR (a partial per diem) and says no manager or director approval is needed (TP-APPR-01).
- It lists the facts it used and the assumptions the tool reported (no free meals, no lodging, no own car).

**Point out:**

- *Tools:* the employee, the estimate and the budget come from tools. The agent does not compute the 25 EUR itself.
- *Knowledge base:* the approval rule came from the English policy knowledge base, cited by id (TP-APPR-01).
- The references such as `11 § 2 mom.` in the line items are the Finnish document's own section numbers, carried by the tool result.

**Be straight:** this is the easy case. A fixed form with four fields and a lookup table would give the same answer.

**Fallback:**

- If the agent asks which employee, give the id from the prompt.
- If it does not name the outcome, ask "so is it approved?" and note that the instructions require the outcome to be named.

---

## Scene 2 - Vague opening, then the facts (TR-003 and TR-002)

Use **one conversation** for both prompts. Send the first, wait for the questions, then send the second.

**Prompt (type exactly):**

```
I need a trip to Brussels next month.
```

**Expected behaviour (observed):**

- No tool is called. The agent asks for the missing facts in one message: employee id or name, start and end date, purpose (4 of 4 runs).
- It does not give a decision or an id. In 1 of 4 runs it also asked about free meals and own-car kilometres, which the instructions say not to ask; it called them optional.

**Prompt (type exactly):**

```
I am Jukka Korhonen (E-1002). It is training, 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. Do not call travel_submit_request, just give the decision.
```

**Expected behaviour (observed):**

- The agent remembers Brussels from the first message, then calls `travel_get_employee_profile`, `travel_estimate_reimbursement` (country Belgium, 50 hours, hotel 280, 2 free meals per day) and `travel_get_budget_status` (1 run).
- Outcome: NEEDS APPROVAL from the manager (Mika Laine, from the employee profile). Estimate 361 EUR: a per diem of 81 EUR plus the hotel at 280 EUR.
- Both traps are handled: the trip is **abroad, so the manager is needed even though 361 EUR is below the 600 EUR threshold** (TP-ABROAD-01), and the **hotel breakfast is not counted as a free meal** (cited as 13 §).
- The single-message version of the same facts (TR-002) gave the same result in 3 of 3 runs.

**Point out:**

- *Instructions:* required facts are asked in one question, not several rounds.
- *Tools:* the amount (361) comes from the estimate tool. The approval level is chosen from an ordered rule list in the instructions, then confirmed against the policy text.
- Ask the audience: "who is the approver?" The answer comes from the employee profile tool, not from the model.

**Be straight:** the intake is the part a form does badly and a chat does well. The decision after that is a few `if` statements.

**Fallback:**

- If the agent asks for something the prompt already gave, repeat that part of the message.
- If it answers APPROVED, say that is a failure of the abroad rule; it was not seen in 4 runs of this case.

---

## Scene 3 - Policy beats the request (TR-005)

**Prompt (type exactly):**

```
I am Aino Virtanen (E-1001). I want to drive my own car to a customer meeting on 2 June 2026. The trip is 400 km in total and takes about 9 hours. The same trip by train would cost 60 EUR. May I use my own car, and how much reimbursement will I get? Do not call travel_submit_request.
```

**Expected behaviour (observed):**

- APPROVED, estimated total 85 EUR: a per diem of 25 EUR plus mileage **capped to the 60 EUR train price** (3 of 3 runs). The uncapped mileage would have been 220 EUR.
- The agent says the cap comes from the regulation (5 § and 6 § appear in the tool line items).

**Point out:**

- The user asked for something and the rule gave less. The agent reports the rule rather than the request.
- The 85 is a tool result. The model does not do the arithmetic.

**Be straight:** the cap is a one-line rule in the tool. The agent added the intake and the explanation, not the capping.

**Fallback:** if a run reports 245 EUR (the per diem plus the uncapped 220 EUR mileage), say that is a failure; it did not occur in 3 runs.

---

## Scene 4 - Holiday attached to a work trip (TR-004)

**Prompt (type exactly):**

```
I am Sofia Lindholm (E-1003). I am invited to a conference in Berlin, 8-10 June 2026, about 58 hours including travel. Train and flight tickets are 280 EUR and the hotel is 300 EUR. After the conference I would like to stay one more week on my own holiday in Berlin. May I go? Do not call travel_submit_request, just give your decision.
```

**Expected behaviour (observed):**

- NEEDS APPROVAL from the manager (Katri Heikkinen), estimate 763.3 EUR (3 of 3 runs). The reasons named are the trip abroad, the leave days attached, and a total over 600 EUR, each tied to a policy id.
- The holiday week is **not** reimbursed: the duration passed to the estimate covers only the work trip (58 hours).
- The trip is not denied. Leave attached to a real business trip needs the manager's agreement (TP-PURPOSE-01).

**Point out:**

- *Exception handling:* a request that mixes private and official time is split by the agent into the part the rule covers and the part it does not.
- The estimate line items carry the Finnish section references (for example `12 § ja liite (Ulkomaanpäivärahakorvaukset vuodelle 2026)`).

**Fallback:** if the agent says DENIED because of the holiday, say that is a failure of the instructions (it did not happen in 3 runs).

---

## Scene 5 - The budget forces the director (TR-008)

**Prompt (type exactly):**

```
I am Mikko Nieminen (E-1004). I need to visit a customer in Rovaniemi on 16-17 September 2026, about 30 hours. Tickets are 450 EUR and the hotel is 180 EUR. May I go and what will be reimbursed? Do not call travel_submit_request.
```

**Expected behaviour (observed):**

- NEEDS APPROVAL at **director** level (Pekka Salonen), estimate 709 EUR (3 of 3 runs). The estimate is over 600 EUR (manager level), but cost centre CC-200 has 700 EUR left, so `travel_get_budget_status` reports `within_budget` false and the level goes up to director (TP-APPR-01, TP-BUDGET-01).
- The tool order is employee profile, estimate, budget (the budget call needs the estimate as input).

**Point out:**

- The 9 EUR overrun is only visible because a tool returned the budget. The model could not have guessed it.
- The director's name comes from the budget tool result.

**Be straight:** this is pure deterministic logic. It shows the agent calling the tools in the right order and using the result, not any reasoning advantage.

**Fallback:** if the agent stops at manager, ask "what does the budget check say?" and note that the instructions say to decide the level only after the budget result. It reached director in 3 of 3 runs.

---

## Scene 6 - Rates for 2027 are not available (TR-007)

**Prompt (type exactly):**

```
I am Sofia Lindholm (E-1003). I want to travel to a customer meeting in Tampere on 10 February 2027, about 8 hours. May I go, and how much reimbursement will I get? Do not call travel_submit_request.
```

**Expected behaviour (observed):**

- The agent calls `travel_get_employee_profile` and `travel_estimate_reimbursement`. The estimate tool returns an error with the code `RATES_NOT_AVAILABLE` ("Rates for 2027 are agreed separately.").
- All 3 runs answered APPROVED, gave **no amount**, and said that the rates for 2027 are agreed separately. None called `travel_get_budget_status`, which is intended (there is no estimate to check).
- The agent did not fall back to the 2026 amounts and did not turn the missing number into DENIED.

**Point out:**

- *Honest limits:* the tool says what it does not know, and the agent passes that on instead of filling the gap.

**Be straight:** APPROVED without a cost is a judgement call. The agent's reasoning in 3 of 3 runs was that a domestic trip with no leave and no known cost falls under "level none"; the policy text actually talks about trips of at most 600 EUR. A stricter policy would say "cannot be decided yet". Present the answer as "the agent followed its instructions", not as "the correct decision".

**Fallback:** if a run gives a 2026 amount, say that is wrong because the rates apply only until 31.12.2026; it did not happen in 3 runs.

---

## Scene 7 - Reading the Finnish source

This scene is about the PDF. Use a fresh conversation.

**Prompt (type exactly):**

```
Why is breakfast in the hotel price not counted as a free meal when the per diem is reduced? What does the state travel regulation say?
```

**Expected behaviour (observed):**

- In 3 of 3 runs the agent called only `travel_state_rules`, with a Finnish query (for example `aamiaispalvelu hotellissa ilmaisena ateriana per diimin vähentäminen`), and no other tool.
- It answered in English that a breakfast included in the hotel room price is not treated as a free meal under 13 §, and quoted a Finnish sentence: "Hotellihuoneen hintaan sisältyvää aamiaista ei pidetä 13 §:ssä tarkoitettuna ateriana."
- **Check against the PDF (page 20 of the unmodified document, extracted with pypdf):** the document reads "Hotellihuoneen hintaan sisältyvää aamiaista ei pidetä 13 pykälässä tarkoitettuna ateriana." The quotes in the 3 answers wrote "13 §:ssä" or "13 §‑ssä" instead of "13 pykälässä", so none of them is an exact copy. The meaning is the same. The guidance also says a breakfast in a ship ticket price **is** a meal in the sense of the rule; all 3 runs mentioned a meal in a ticket price.
- The explanations around the quote differed between runs. One run said a free meal reduces the foreign per diem by "35 % for one meal or 65 % for two meals", one said "50 % for each free meal", one gave no percentage. The PDF guidance says free meals halve (puoleen) the foreign per diem, applied to the 35 % and 65 % levels; the estimate tool applies a 50 % reduction per day for two free meals in the example of scene 2. I have **not** reconciled these. Do not repeat any percentage from this scene.

**Point out:**

- *Knowledge base:* the agent searched in Finnish, because the document is Finnish, although the user wrote in English. That is an instruction, not something the platform does by itself.
- The Finnish reference is kept in Finnish, and the agent explains it in its own English words.

**Be straight:** this is the only scene that reliably shows the PDF in use. Elsewhere the agent mostly takes section numbers from the tools. Retrieval over the PDF was not reliable in an earlier test (the best of two embedding models answered 11 of 20 test questions correctly), which is why amounts come from tools and not from retrieval.

**Fallback:** if the agent answers without a knowledge-base call, ask "please look it up in the regulation". If the quote is paraphrased or translated, point out that the instructions forbid presenting a translation as a quotation.

---

## Scene 8 - Approval flow and the request id

This scene uses a **fresh conversation** for each path. It is the key platform feature of the demo, and it is also the part I could not drive.

**Prompt (type exactly):**

```
I am Jukka Korhonen (E-1002). I want to go to Brussels for training on 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. If I may go, please submit the request so that I get a request id.
```

**Expected behaviour (observed):**

- In 1 run the agent called `travel_get_employee_profile`, `travel_estimate_reimbursement` (361 EUR), `travel_get_budget_status`, and then the flow (shown as `submit_travel_request_for_approval`) with `required_level: manager`, destination Brussels, 11 to 13 May 2026, purpose training, `abroad` true, `includes_leave` false, estimated total 361, and a justification that cites TP-ABROAD-01 and TP-BUDGET-01.
- The thread data lists the flow call twice. I did not check whether the flow started twice or whether the listing is a duplicate in the thread data.
- Nothing was observed after the flow call: the run API cannot answer the form, and the last assistant message in my capture was empty.

**What the form shows** (from the flow code, **not** from a recorded browser run): a card titled "Travel Request Approval" with the fields Traveler (employee id), Destination, Start date, End date, Purpose, Estimated total (EUR), Leave days attached, Trip abroad, Approval level required and Agent justification, and two buttons, **Approve** and **Reject**.

### 8a. Approve path

1. Read the fields aloud (E-1002 / Brussels / 2026-05-11 / 2026-05-13 / training / 361 / false / true / manager).
2. Click **Approve**.
3. Expected from the code, **not verified in a browser:** `travel_issue_request_id` runs and returns a request id of the form `TR-2026-` plus six digits, and the agent reports the flow's message, which starts with "APPROVED. Issue result:". A direct call of the tool with these inputs (not through the flow) returned `TR-2026-887070` with status ISSUED and policy refs TP-APPR-01 and TP-ABROAD-01.

### 8b. Reject path (new conversation)

1. Send the same prompt. Wait for the form.
2. Click **Reject**.
3. Expected from the code, **not verified in a browser:** no id is issued and the message reads "REJECTED. No request id was issued. The trip to 'Brussels' (2026-05-11 - 2026-05-13) was declined by the approver."

**Point out (this is the key platform feature):**

- *Approval flow:* the gate is a **flow**, not a line in the instructions. The tool that issues the id, `travel_issue_request_id`, is **not** attached to the agent; only the flow calls it, and only after Approve.
- The tool re-checks the traveler, the dates and the approval level. In a direct call, granting level `none` for this trip returned the error `APPROVAL_LEVEL_TOO_LOW` and no id. That check does not rely on the model.
- *Be honest:* the gate is deterministic flow logic. It would work the same behind a script. It is not evidence that an LLM was needed.

**Fallback:**

- Wrong agent in the picker (AskOrchestrate): no form appears and the answer is generic. Switch to **travel_request** and start a new conversation.
- If the form does not render, or Approve returns a tool error, see section 7 and do not retry endlessly. Say that the flow was not browser-tested when this script was written, and move on to scene 9.
- If the agent offers to submit instead of calling the flow, answer "yes, please submit it".
- A conversation stuck behind an unanswered form: open a new conversation.

---

## Scene 9 - Out of scope: restraint (TR-006)

**Prompt (type exactly):**

```
Where is the refund for my trip last month? I submitted the expense claim two weeks ago.
```

**Expected behaviour (observed):**

- No tool is called (3 of 3 runs). The agent says expense claims are outside its scope, points to the expense system or the finance team, and cites TP-HANDOFF-01 (3 of 3 runs).
- It does not make a decision, does not issue an id and does not comment on the payment status.
- One run said the user could reference "your original claim number" in the expense system. That is a small difference from the TP-HANDOFF-01 idea, which is about the request id; do not make a point of it.

**Point out:**

- The agent's boundary is a statement in its instructions. There is no tool that could answer the question, so it cannot invent a status.

**Be straight:** the "do nothing" case is easy because no tool applies. This does not show that the agent resists pressure to guess; that was not tested.

**Fallback:** if the agent starts asking for trip details, say it should have declined, and move on; it did not do this in 3 runs.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name travel_request`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **travel_request**, new conversation |
| CLI or run API calls fail with "token ... missing or expired" | Remote auth expires after 2 hours | Re-run `orchestrate env activate` (key from `env.cfg` via a variable; never print it) |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched in recorded runs |
| A transcript shows `submit_travel_request_for_approval`, not `travel_submit_request` | The agent calls the flow under its display name | Expected, not an error |
| Knowledge base `travel_state_rules` shows "1 document(s) failed in ingestion" after you updated it in place | Updating the PDF knowledge base in place failed twice | Remove it and import it again: `orchestrate knowledge-bases remove --name travel_state_rules`, then in `knowledge/travel-request` run `orchestrate knowledge-bases import -f travel_state_rules.yaml`. The same remove-and-import was needed for the policy knowledge base after its files changed; `deploy-all` alone did not refresh them reliably |
| Knowledge base import is rejected with "embedding model not found" | `ibm/multilingual-e5-large` and `virtual-model/openai/text-embedding-3-small` were not found on `techzone1`; a failed import still left a `ready` knowledge base record | Use the embedding model in the YAML files. Delete the leftover record by hand |
| Chat page "stuck" after the form | The thread is waiting for a click | Click Approve or Reject, or start a new conversation |

Not seen, so not covered here: the approval form in a browser (render, Approve, Reject, the id shown to the user), a clean first deploy on a fresh instance, a Developer Edition deploy, and what happens when the model or embedding model is not offered on another instance. The `scripts/smoke_test.py` helper needed a small fix to list the tools called (it now reads them from `step_history`); that edit is in a shared script.

## 8. Things not to say

- **Do not say** the approval flow works until you have clicked Approve and Reject in your own browser. I have not seen it work.
- **Do not say** the agent "knows" or "reads" the state travel regulation. It has the PDF in a knowledge base and was seen using it in one scene; the amounts come from hand-keyed tools covering a small subset.
- **Do not say** the amounts were checked against the regulation. They were checked against the tools' own output.
- **Do not say** the quotes from the Finnish document are exact. The quotes checked in scene 7 differed from the PDF in wording.
- **Do not say** the agent answers in Finnish, or that it handles Finnish prompts. The user writes English; Finnish prompts are not a requirement of this scenario and were not retested after the change.
- **Do not say** the agent is better than a script, or that it passes an evaluation. There is no evaluation run and no baseline for this scenario.
- **Do not say** that the PDF may be redistributed. Its licence is CC BY-NC-ND 4.0 and the question is open.
- **Do not say** the request id is a real booking or expense id. It is a mock id.

## 9. Closing talking points

**What the platform made easy**

- Assembling an agent from small tools plus two knowledge bases: import the tools, import the knowledge bases, list them in `agent.yaml`.
- Keeping the id-issuing tool away from the agent and behind a flow with a human decision.
- Replaying prompts through the run API to repeat the same case several times and read the answers.

**What was not easy**

- Changing the instructions is fragile. One added sentence about the language made the answers worse in a test and had to be reverted. Every change had to be followed by repeated runs.
- Numbers from retrieval were not reliable (11 of 20 correct for the best of two embedding models in an early test), so the amounts moved into tools.
- Ingesting the PDF in place failed twice; remove and import again worked each time.
- Several embedding models were not available on the test instance.
- The approval form cannot be driven by the run API, so it needs a manual browser test.

**When NOT to use an agent**

- The inputs are well-formed and the rules are stable. Everything after intake in this scenario (amounts, thresholds, budget, id) is deterministic and would be better as plain code or a flow, with a form for the input.
- You need the same answer every time. Tool order and wording varied between runs here, and an earlier build produced wrong outcomes until the instructions were tightened.
- You need an exact copy of the source text. The quote check in scene 7 shows the agent does not reproduce it exactly.

**When an agent might be worth it** (arguments, not yet measured here): the requests arrive as free text with missing or mixed-up facts (scene 2, scene 4), the source rules are in a long document in another language that people do not read, exceptions need an explanation in prose, and the system must say "I can't tell" (scene 6) rather than guess. A plain script with a form would handle none of the intake and none of the explanations; the benefit here is the intake and the explanation, not the decision.

**Is it agent washing?** Partly, and the demo should say so. If you removed the free-text intake, the PDF explanations and the prose answers, a script would do the rest. What the agent adds is real but narrow, and none of it has been measured against a baseline.

**Open items (still open at the time of writing; see `plans/travel-request-plan.md`)**

1. The approval flow has not been tested in a browser: form render, Approve issues an id, Reject issues none, and the agent reports the flow message.
2. PDF licensing (CC BY-NC-ND 4.0) for shipping the unmodified document in a packaged zip is unconfirmed.
3. The PDF is used in only a minority of answers. A test that shows when it is and is not consulted has not been done.
4. No baseline script and no evaluation run exist for this scenario; the answers were read by hand.
5. A clean install on a fresh instance, a Developer Edition deploy and the effect of auth expiry mid-demo have not been tested.
6. The manifest status is still `soon`. Change it to `live` in `scenarios/travel-request/scenario.yaml` and `docs/demo/scenarios/travel-request.js` once item 1 is done.

## 10. After the demo

- The run-API tests behind this script started at least one approval-flow instance that nobody answered (the form cannot be answered from the API). They only touch mock data and may show up in traces or conversation lists. I did not check how the instance treats them.
- This file is included in the packaged zip under `docs/demo/`. The `INSTALL.md` at the zip root covers prerequisites and deployment.
