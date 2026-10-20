# Customer Returns Agent - Demo Script

For a human presenter. **This scenario has not been run against a live WXO instance.**
Tool sequences, agent answers, and flow behaviour described in the scenes below come from
the mock data design and tool code — not from observed runs. Every section that would
normally quote a recorded run says "not verified". Fill in observations after you have
run it live.

## 1. Audience and goal

**Audience:** business stakeholders, IT architects, or technical leads evaluating watsonx
Orchestrate and wanting to see how a conversational agent handles messy, ambiguous customer
input against a policy knowledge base with a governed write path.

**Goal:** show how the agent/flow split works: the agent's open-ended reasoning handles vague
input and policy lookup; a Decisions-node flow enforces the deterministic eligibility rule and
requires human approval before any refund is issued.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real system.
- This scenario has not been run against a live WXO instance. No tool sequences, answer
  quotes, or run counts can be cited yet. The scenes below describe expected behaviour
  from the code, not observed behaviour.
- The approval flow form, Approve path, and ineligible path (Decisions node) have not been
  browser-verified.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy customer-returns`.
  This imports the tools, the knowledge base (`customer_returns_policy`), the approval flow
  (`returns_process_return`) and the agent (`customer_returns`).
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs
  `orchestrate agents deploy --name customer_returns`. If you imported by hand, run that
  command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The browser needs access to your WXO instance web UI. The approval form (scene 4) only
  renders there. It cannot be driven from the CLI or the run API.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell.
  It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in
   `env.cfg`) and go to the chat.
2. In the agent picker choose **Customer Returns** (YAML name `customer_returns`). If it is
   missing, the agent is still draft: run `orchestrate agents deploy --name customer_returns`
   and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer
   that looks like an agent defect.
4. Start a **new conversation** for each scene. A flow waiting for a click blocks its thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours):
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `customer_returns`.
  If not, deploy it (section 2).
- [ ] Reload the browser chat page and confirm **Customer Returns** is selectable.
- [ ] No data reset is needed. The mock world is static and read-only; `returns_issue_refund`
  persists nothing. Each scene needs only a fresh conversation.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or
  re-run `python wxodemo.py login`.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `returns_lookup_order`, `returns_check_warranty`,
  `returns_get_return_history`, `returns_lookup_by_serial`, `returns_process_return`
  (the approval flow). The knowledge base appears in transcripts as a tool call named
  `customer_returns_policy`. The flow appears as `Process Return Request` (its display name).
- `returns_issue_refund` is **not** in the tool list above because it is not attached to the
  agent. Only the flow calls it. If you see it as an agent tool chip, something is wrong.
- **The model varies.** Tool order and wording will differ between runs.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Vague opening | 1 browser run. Instruction bug found: agent asked for serial number instead of order ID. Agent instructions fixed (see section 7). Re-deploy required before using this scene. |
| 2 Warranty defect (CR-001) | **Not verified.** Expected from code. Red-herring behaviour (wrong SKU warranty) not observed. |
| 3 Outside window denied (CR-002) | **Not verified.** Ineligible flow path not browser-verified. |
| 4 Gift return by serial (CR-003) | **Not verified.** Serial lookup and gift-return path not observed. |
| 5 Approval flow (Approve and Reject) | **Not verified.** Form not browser-tested. |
| 6 Billing escalation (CR-004) | **Not verified.** Restraint / escalation path not observed. |

---

## Scene 1 - Vague opening ("I want to return something")

This is the messy-input teaching point. The customer provides almost no information.

**Prompt (type exactly):**

```
Hi, I bought something a while ago and I want to return it. Can you help?
```

**Expected behaviour (1 browser run, instruction bug observed and fixed):**

- **Observed (before the fix):** the agent asked for the **serial number** instead of the
  order ID. Root cause: the instructions said "if the customer does not have one, ask for
  the serial number" — the model interpreted "nothing provided" as "does not have one."
  The fix tightens both the Method section and the Clarifying Questions section of
  `agents/customer-returns/agent.yaml` to say: first question must always be the order ID;
  serial number only after the customer explicitly says they have no order ID.
- **Expected after fix:** the agent should ask for the order ID.
- It should not guess eligibility before looking up the order.
- It should ask one question, not several at once.
- **Not yet re-verified after the instruction fix.** Re-deploy the agent and re-run before presenting.

**Point out:**

- *Vague input:* the agent handles an incomplete request without crashing or guessing.
- *One question at a time:* the instructions require asking only for what is not yet known.

**Fallback:**

- If the agent still asks for the serial number first (fix not yet deployed, or fix did not
  hold), answer with the order ID anyway: "I have order number ORD-XXXX." The agent should
  then proceed normally.
- If the agent asks multiple questions at once, answer the order-ID question and ignore the rest.
- If the agent produces an eligibility decision without the order ID, that is a failure; restart.

---

## Scene 2 - Warranty defect: CR-001 (main path + red herring)

This is the main happy-path scene and the red-herring teaching point.

**Alice (CUST-101) has two warranty records:**
- `SN-BLND-500-A101` for ORD-1001 (the ProBlend 500 she is returning) — **active, applicable**
- `SN-BLND-PRO-A101` for ORD-1005 (an older ProBlend PRO, different SKU) — **wrong product**

The agent must not apply the PRO warranty to the 500 claim.

**Prompt (type exactly):**

```
I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001.
```

**Expected behaviour (not verified):**

- The agent calls `returns_lookup_order` for ORD-1001 (14 days old, within window).
- It calls `returns_check_warranty` for ORD-1001. The tool returns two warranty records for
  customer CUST-101: `SN-BLND-500-A101` (SKU-BLND-500, active, applicable) and
  `SN-BLND-PRO-A101` (SKU-BLND-PRO, active, but a different product).
- The agent should identify `SN-BLND-500-A101` as the applicable warranty and ignore
  `SN-BLND-PRO-A101`.
- It searches `customer_returns_policy` and cites `RP-WARRANTY-01`.
- It proposes a `replacement` via `returns_process_return`.
- (Not verified: whether the agent correctly names the applicable serial number vs. the
  red-herring one in its answer.)

**Point out:**

- *Red herring:* two warranty records, only one matches. Point at the agent's reasoning.
- *Knowledge base:* the citation of `RP-WARRANTY-01` comes from KB retrieval, not from the
  agent's training data.
- *Flow gate:* the approval form appears before anything is issued.

**Fallback:**

- If the agent applies the PRO warranty (wrong SKU), point it out as a failure. The agent
  instructions warn about this; it is an open item.
- If the agent asks for the serial number before calling `returns_check_warranty`, provide
  `SN-BLND-500-A101` and continue.

---

## Scene 3 - Outside the 30-day window: CR-002 (denial path)

**Prompt (type exactly):**

```
I bought some headphones about six weeks ago. Order ORD-1002. I just don't like them anymore, I want a refund.
```

**Expected behaviour (not verified):**

- The agent calls `returns_lookup_order` for ORD-1002. The tool returns `age_days: 46` and
  `within_30_day_window: false`.
- No defect reported; the agent searches `customer_returns_policy` and finds `RP-STANDARD-01`
  (30-day no-reason window).
- The agent calls `returns_process_return` with `refund_reason: no_reason`,
  `within_window: false`. The flow's Decisions node routes to `ineligible_result`; the
  approval form is **never shown**.
- The flow returns: "RETURN INELIGIBLE. Order: ORD-1002. … outside the 30-day return window."
- The agent should report this verbatim and not offer to escalate or override the rule.
- (Not verified: whether the Decisions node actually routes to ineligible without showing
  the form. This requires browser verification.)

**Point out:**

- *Decisions node:* the eligibility check is in the flow, not in the agent's instructions.
  The agent cannot bypass it.
- *Honest denial:* the agent correctly declines and cites the policy document.

**Be straight:** the 46-day age is explicit in the tool output, so the denial is easy. The
agent does not need to reason; it just reads `within_30_day_window: false`.

**Fallback:**

- If the form appears (it should not for this case), click **Reject** and note that the
  ineligible path did not trigger as expected.
- If the agent tries to override the denial with policy text, that is a failure; note it.

---

## Scene 4 - Gift return by serial number: CR-003

**Prompt (type exactly):**

```
I received a kitchen scale as a gift and I'd like to return it. I don't have an order number but the serial number on the box is SN-KTCH-780-C103.
```

**Expected behaviour (not verified):**

- The agent calls `returns_lookup_by_serial` with `SN-KTCH-780-C103`. The tool returns
  `linked_order_id: ORD-1003`, `purchase_date: 2025-05-10`, `age_days: 24`,
  `within_30_day_window: true`, `purchase_channel: gift`.
- The agent calls `returns_lookup_order` for ORD-1003 to get full order details.
- It searches `customer_returns_policy` and finds `RP-GIFT-01` (gift returns).
- It proposes `store_credit` (gift-return policy: no cash refund to a non-payer).
- It calls `returns_process_return`; the approval form appears.
- (Not verified: any of this.)

**Point out:**

- *No order ID needed:* the serial-number lookup path is the teaching point for this scene.
- *Policy distinction:* gift returns get store credit, not cash — the KB drove that choice.

**Fallback:**

- If the agent asks for the order ID despite the customer saying they don't have one,
  say "I don't have the order number, only the serial number on the box" and re-provide it.

---

## Scene 5 - Approval flow: CR-001 (Approve path and Reject path)

Use **two fresh conversations**, one for each path. Use the warranty-defect prompt from
scene 2 in both.

**Prompt (type exactly; same as scene 2):**

```
I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001.
```

**What the form shows (from the flow definition — not browser-verified):**

A card titled "Return Request Approval" with: Order ID, Customer ID, Return Reason,
Resolution Type, Policy Reference, Agent Justification, and two buttons: **Approve**
and **Reject**.

### 5a. Approve path (not browser-verified)

1. Read the form fields aloud.
2. Click **Approve**.
3. Expected (from flow code): `returns_issue_refund` runs and returns a refund reference
   (`REF-NNNNN`). The flow message is:
   "APPROVED AND PROCESSED. Order: ORD-1001. Resolution: replacement.
   Policy: RP-WARRANTY-01. Result: {issue_refund output}."
   The agent should report this verbatim. **Not verified in a browser run.**

### 5b. Reject path (new conversation — not browser-verified)

1. Send the same prompt. Wait for the form.
2. Click **Reject**.
3. Expected (from flow code): nothing executes and the flow returns:
   "REJECTED. No refund or replacement was issued. Proposed resolution 'replacement'
   for order 'ORD-1001' was declined by the approver. No changes have been made."
   **Not verified in a browser run.**

**Point out (this is the key platform feature of the demo):**

- *Approval flow:* the gate is a **flow**, not a line in the agent's instructions. The
  agent is given `returns_process_return` only. The tool that actually issues the refund,
  `returns_issue_refund`, is **not** attached to the agent. Only the flow calls it, only
  after Approve.
- *Decisions node:* the eligibility rule lives in the flow, not in the agent. The agent
  cannot propose a refund for an ineligible order and have the flow pass it through.
- *Be honest:* the gate is deterministic flow logic. It would work the same behind a script.

**Fallback:**

- Wrong agent in the picker (AskOrchestrate): no form appears. Switch to **Customer Returns**
  and start a new conversation.
- If the form does not appear, or Approve errors, see section 7. Move on; note the failure.
- A conversation stuck behind an unanswered form: open a new conversation.

---

## Scene 6 - Out-of-scope escalation: CR-004

**Prompt (type exactly):**

```
I was charged twice for my order ORD-1004. I need a refund for the duplicate charge.
```

**Expected behaviour (not verified):**

- The agent should recognise this as a billing dispute, not a product return.
- It searches `customer_returns_policy` and finds `RP-ESCALATE-01`.
- It declines to process a return and directs the customer to the Billing team.
- It does **not** call `returns_process_return`.
- (Not verified: whether the agent reliably identifies the billing pattern without calling
  the flow first.)

**Point out:**

- *Restraint:* the agent knows its scope. A fixed script would also reject this, but the
  agent identified it from unstructured text.
- *No flow triggered:* compare with scenes 2 and 4 where the flow appeared.

**Be straight:** the order note for ORD-1004 says "Customer reports a double charge on their
statement", which is an easy tell. Do not claim the agent detected a subtle signal.

**Fallback:**

- If the agent tries to look up the order and proposes a return, that is a failure; note it.
- If the agent escalates to the wrong team, correct it and point to `RP-ESCALATE-01`.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name customer_returns`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **Customer Returns**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. This script has no recorded runs to compare against yet |
| Agent asks for serial number instead of order ID on first vague message | Instruction ambiguity: model read "nothing provided" as "does not have one." Seen in 1 browser run. Fixed in agent.yaml — re-deploy required. | Re-deploy: `python wxodemo.py deploy customer-returns`. If it persists after re-deploy, give the order ID in your reply and continue. |
| Form shows unexpected fields or does not appear | Flow not imported, or the agent was imported before the flow | Re-run `python wxodemo.py deploy customer-returns` |
| Agent applies the wrong warranty (SKU-BLND-PRO instead of SKU-BLND-500) | Red-herring trap; agent instructions warn about this but it has not been tested live | Note as open item; click Reject if the form appears |
| Ineligible path still shows the approval form (CR-002) | Decisions-node expression not evaluated as expected | Click Reject and note the failure |
| Chat thread stuck after the form | Thread is waiting for a click | Click Approve or Reject, or open a new conversation |

Not seen, so not covered here: any live run on a WXO instance. Everything in this list
except the generic items (auth, AskOrchestrate, UTF-8) is anticipated from the code, not
observed.

## 8. Things not to say

- **Do not say** the agent handles these cases correctly. It has not been tested live.
- **Do not say** the approval form has been verified. It has not been browser-tested.
- **Do not say** the agent never applies the wrong warranty. The red-herring case is an
  open item.
- **Do not say** the Decisions node ineligible path (CR-002) works as designed. It has not
  been browser-verified.

## 9. Closing talking points

**What the platform made easy**

- Assembling an agent from small, bounded tools plus a knowledge base: import the tools,
  import the knowledge base, list them in `agent.yaml`.
- A governed human-in-the-loop step: the approval form is a flow, the write tool is not
  given to the agent, and the Decisions node enforces eligibility before the form appears.
- Serial-number lookup as a fallback for customers without an order ID.
- Policy retrieval with citations: the KB drove which document the agent cited.

**What was not easy**

- The scenario has not been deployed to a live instance, so none of the above has been
  verified end-to-end.
- The red-herring (two warranties for the same customer, different SKUs) is a known fragile
  point: agent instructions warn about it, but instructions alone do not guarantee correctness.
- The Decisions node expression has not been tested in a real flow import; syntax issues
  may appear only at runtime.
- KB indexing delay: after import, wait before the first demo query.

**When NOT to use an agent**

- The workflow is fixed and the inputs are well-formed. A flow with Decisions nodes handles
  the eligibility rule correctly and without an LLM.
- Latency or cost matters per request. The agent runs cost LLM calls and take seconds.
- You need the same answer every time. The agent's KB retrieval and tool path may vary
  between runs.

**When an agent might be worth it** (arguments, not yet measured here): customer input is
always vague and incomplete, the next step depends on what the previous step found (warranty
vs. no-reason vs. gift), and a natural-language explanation is part of the deliverable.

**Open items (still open at the time of writing; see `plans/customer-returns-plan.md`)**

1. Scenario not yet deployed to a live WXO instance. All scenes are unverified.
2. Red-herring warranty case (CR-001): agent must not apply SKU-BLND-PRO warranty to
   ORD-1001. Not tested live.
3. Decisions-node ineligible path (CR-002): must skip the approval form. Not browser-verified.
4. Approval flow form (CR-001 Approve and Reject paths): not browser-tested.
5. Flow Decisions-node expression syntax: not verified in a real import.

## 10. After the demo

- Once you have run scenes live, update every "not verified" note with the observed
  behaviour, the number of runs, and any failures seen.
- Set `status: live` in `scenarios/customer-returns/scenario.yaml` (already done) and in
  `docs/demo/scenarios/customer-returns.js` only after you have observed the key paths.
- Run `python wxodemo.py validate customer-returns` after updating the script to confirm
  prompts in this file match the slides exactly.
