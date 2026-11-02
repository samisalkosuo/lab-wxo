# Cloud FinOps Agent - Demo Script

For a human presenter. Smoke prompts CF-001 through CF-004 were run once against the deployed agent (1 SDK run each via `python wxodemo.py smoke cloud-finops`). Tool sequences below are from that run. The approval forms (scenes 3 and 4) were also verified in the browser chat UI (Approve and Reject).

## 1. Audience and goal

**Audience:** engineers, cloud architects, or FinOps practitioners evaluating watsonx Orchestrate (WXO) and wanting to see how an agent, a knowledge base, tools, and a human-approval flow work together on a realistic cost-management task.

**Goal:** show how the platform pieces fit on a Cloud FinOps task: a vague cost complaint drives a progressive investigation, the agent cites policy documents, surfaces a red herring, routes reclamation and rightsizing through approval flows, and refuses to act on a billing error.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real cloud account.
- No cost savings or time figures are claimed. The 40% rightsizing figure in the mock data is explicitly labelled "illustrative" throughout.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy cloud-finops`. This imports the tools, the knowledge base (`cloud_finops_policy`), the two approval flows (`cf_approve_reclaim`, `cf_approve_resize`) and the agent (`cloud_finops`).
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name cloud_finops`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The browser needs access to your WXO instance web UI. Both approval forms (scenes 3 and 4) only render there. They cannot be driven from the CLI or the run API.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **Cloud FinOps** (YAML name `cloud_finops`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name cloud_finops` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. A flow waiting for a click blocks its chat thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `cloud_finops`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **Cloud FinOps** is selectable.
- [ ] No data reset needed. The mock world is static and read-only; the write tools persist nothing across conversations.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `cf_get_spend_summary`, `cf_list_idle_resources`, `cf_get_resource_utilization`, `cf_explain_cost_spike`, `cf_get_billing_lines`. The knowledge base appears in transcripts as a tool call named `cloud_finops_policy`. The flows appear in traces as `approve_resource_reclamation` and `approve_resource_rightsizing` (their display names).
- **The model varies.** Tool order and wording differ between runs. Sequences below are from 1 SDK smoke run each; do not promise exact text.
- **Display quirk:** the smoke run shows each tool name twice in the tools list — the ADK trace records both the request and the response step. The actual unique tools called are the de-duplicated set.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Vague bill spike | 1 SDK smoke run (CF-001-smoke). Tool sequence recorded. Answer not captured by smoke runner (flow blocks the response). |
| 2 Idle resource scan | 1 SDK smoke run (CF-002-smoke). Tool sequence recorded; answer not captured. |
| 3 Reclamation approval | Smoke run + browser-verified. Form rendered correctly. Approve executed `cf_reclaim_resource` and reported result. Reject reported no changes made. |
| 4 Rightsizing approval | Smoke run + browser-verified. Form rendered correctly. Approve executed `cf_resize_resource`; initial flow message omitted the illustrative label (fixed — flow re-deployed). Reject reported no changes made. |
| 5 Billing error restraint | 1 SDK smoke run (CF-004-smoke). Full answer captured — cites CF-POL-04, no write action. |

---

## Scene 1 - Vague bill spike ("our cloud bill jumped 30%")

**Prompt (type exactly):**

```
Our cloud bill jumped 30% this month. Can you investigate why?
```

**Expected behaviour (from 1 SDK smoke run):**

- Tool sequence observed: `cf_get_spend_summary` → `cf_explain_cost_spike` → `cf_get_resource_utilization` (×4 resources) → `approve_resource_reclamation` (the `cf_approve_reclaim` flow).
- The agent called `cf_get_spend_summary` twice and `cf_explain_cost_spike` once before the utilisation calls — the double call is a trace artefact (request + response step counted once each); actual distinct calls are: spend summary, spike explanation, four utilisation checks.
- After checking utilisation on `vm-zombie-01`, `vm-idle-finance-01`, `vm-idle-dev-03`, and `vm-batch-weekend-01`, the agent reached the reclamation flow.
- The answer was not captured (the flow blocks the SDK response); the form appears in the browser.

**Point out:**

- *Progressive investigation:* the agent didn't jump to a conclusion — it went spend summary → biggest mover → root cause → four individual resource checks.
- *Knowledge base:* the agent should cite CF-POL-02 (Zombie Resource Handling) when describing `vm-zombie-01`.
- *Approval flow* (preview): the agent paused for a human before any resource change.

**Fallback:**

- If the agent asks which service to investigate, answer "the compute costs" and carry on.
- If the form appears immediately in the browser, click **Reject** and say "we will do Approve and Reject in scene 3". Start a new conversation.

---

## Scene 2 - Idle resource scan — batch-job red herring

**Prompt (type exactly):**

```
Are there any idle resources in account acct-001 we can reclaim?
```

**Expected behaviour (from 1 SDK smoke run):**

- Tool sequence observed: `cf_list_idle_resources` → `cf_get_resource_utilization` (×3) → `approve_resource_reclamation`.
- Three utilisation calls (not four) — the smoke run checked `vm-zombie-01`, `vm-idle-finance-01`, `vm-idle-dev-03` and skipped `vm-batch-weekend-01` in this particular run. **Vary between runs.** The agent may also check `vm-batch-weekend-01`.
- The agent reached the reclamation flow; the answer was not captured.

**Point out:**

- *Red herring:* point out that `vm-batch-weekend-01` has a 7-day CPU of only 1.8% (looks idle) but a 30-day average of 14.3% driven by Saturday batch jobs. If the agent skips it in this run, ask "what about vm-batch-weekend-01?" and it will check.
- *Knowledge base:* the agent should cite CF-POL-01 (Idle Resource Reclamation Policy) for the 30-day window requirement.

**Be straight:** the agent's decision to check or skip `vm-batch-weekend-01` varies. The tool itself has a hard guard that refuses to reclaim it regardless; point that out if the agent proposes it.

**Fallback:**

- If the agent recommends reclaiming `vm-batch-weekend-01`, that is a reasoning miss. The `cf_reclaim_resource` write tool has a hard code guard that will block it anyway. Note what happened, click Reject on the form, and carry on.
- Ask "what about vm-batch-weekend-01?" to prompt the agent to check it explicitly.

---

## Scene 3 - Reclamation approval (Approve path and Reject path)

This scene uses **two fresh conversations**, one for each path.

**Prompt (type exactly; start a fresh conversation for each path):**

```
Reclaim the zombie VM vm-zombie-01 in account acct-001. It has been running with no workload since 2025-04-10.
```

**Expected behaviour (smoke run reached the flow; form browser-verified):**

- The agent should call `cf_get_resource_utilization` on `vm-zombie-01`, cite CF-POL-02, then call `cf_approve_reclaim`.
- The flow appears in traces as `approve_resource_reclamation`.
- The form title (from flow definition): **Resource Reclamation Approval** with fields: Resource ID, Account ID, Policy Reference, Agent Justification, and two buttons **Approve** and **Reject**.

**What the form shows** (browser-verified):
A card titled "Resource Reclamation Approval" with Resource ID (`vm-zombie-01`), Account ID (`acct-001`), Policy Reference (e.g. `CF-POL-02`), Agent Justification, and two buttons **Approve** and **Reject**.

### 3a. Approve path

1. Read the form fields aloud.
2. Click **Approve**.
3. Expected (browser-verified): `cf_reclaim_resource` runs. The mock tool message includes "MOCK RECLAIM EXECUTED (demo only — no real resource was deleted). Resource 'vm-zombie-01' in account 'acct-001' reclaimed. Approved by: Cost Owner. Estimated saving: USD 640.00/month."

### 3b. Reject path (new conversation)

1. Send the same prompt. Wait for the form.
2. Click **Reject**.
3. Expected (browser-verified): nothing executes. Flow message: "REJECTED BY COST OWNER. No resource was reclaimed. Resource: vm-zombie-01, Account: acct-001. No infrastructure changes were made."

**Point out:**

- *Approval flow:* `cf_reclaim_resource` is **not** attached to the agent; only the flow calls it after Approve. Reject truly executes nothing.
- *Be honest:* the gate is deterministic flow logic. It works the same behind a script.

**Fallback:**

- Wrong agent in the picker (AskOrchestrate): no form appears. Switch to **Cloud FinOps**, new conversation.
- If the form never renders: see section 7. Move on and say the form did not render.
- A conversation stuck behind an unanswered form: open a new conversation.

---

## Scene 4 - Rightsizing approval

**Prompt (type exactly):**

```
The database cluster db-cluster-prod-01 looks over-provisioned. Can you check and recommend a rightsizing?
```

**Expected behaviour (from 1 SDK smoke run):**

- Tool sequence observed: `cf_get_resource_utilization` → `approve_resource_rightsizing` (the `cf_approve_resize` flow).
- The agent went straight to utilisation check on `db-cluster-prod-01` (CPU 22%, memory 28%, size `xlarge-16cpu-128gb-3nodes`) then called the resize flow. Answer not captured (flow blocks response).
- The flow appears in traces as `approve_resource_rightsizing`.

**What the form shows** (browser-verified):
A card titled "Resource Rightsizing Approval" with Resource ID, Account ID, Current Size, Proposed Target Size, Policy Reference (`CF-POL-03`), Agent Justification, and a note about change-control windows. Two buttons: **Approve** and **Reject**.

### 4a. Approve path

1. Read the fields aloud (current size: `xlarge-16cpu-128gb-3nodes`, target: `large-8cpu-64gb-2nodes`).
2. Click **Approve**.
3. Expected (browser-verified): `cf_resize_resource` runs. The flow message includes "APPROVED BY COST OWNER AND EXECUTED", the two size values, "Illustrative saving: ~40% monthly cost reduction", and "This figure is illustrative; actual saving depends on production workload." *(Note: first browser test showed the illustrative label was missing; the flow was fixed and re-deployed — the label now appears in the flow message directly.)*

**Point out:**

- *Illustrative label:* the saving figure says "illustrative" in the flow message. Do not claim it as a real forecast.
- *CF-POL-03* note: the agent should mention the change-control window for database clusters.

### 4b. Reject path (new conversation, same prompt)

1. Click **Reject**. Expected (browser-verified): "REJECTED BY COST OWNER. No resource was resized. Current size 'xlarge-16cpu-128gb-3nodes' unchanged. No infrastructure changes were made."

**Fallback:** same as scene 3.

---

## Scene 5 - Billing error: restraint

**Prompt (type exactly):**

```
The billing report shows we used 1 000 GPU hours this month. Can you verify that?
```

**Expected behaviour (from 1 SDK smoke run — full answer captured):**

- Tool called: `cf_get_billing_lines` only. No write tools, no approval flow.
- Real answer excerpt (smoke run): "The billing line for **GPU Compute** shows: - **Line ID:** BL-5001 - **Reported units:** 1 000 GPU‑hours (USD 5 000) - **Recorded usage units:** 0 GPU‑hours - **Discrepancy:** **true** — the telemetry indicates no GPU usage, so this is a data error. Per **CF-POL-04** (billing discrepancy escalation policy), this should be escalated to finance for correction. No reclamation or rightsizing actions are applicable here."
- The agent cited CF-POL-04 and made no write-tool call.

**Point out:**

- *Restraint:* the right answer is "do nothing and escalate". One tool call, cites CF-POL-04, no flow invoked.
- *Knowledge base:* CF-POL-04 (Billing Error Escalation Procedure) grounded the decision.
- *Compare with scene 1:* scene 1 also touched GPU spend but reached a different conclusion because the investigation revealed a billing discrepancy, not a real usage spike.

**Be straight:** this is the easiest case — the billing line has an explicit `discrepancy: true` flag. It tests whether the agent reads the flag and cites CF-POL-04 rather than acting. It did in the one run.

**Fallback:** if the agent proposes any resource action, that is a reasoning miss. The write tools don't have a guard against billing errors — only the agent's policy grounding prevents action. Note it and move on.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name cloud_finops`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **Cloud FinOps**, new conversation |
| Flow deployment fails: "No module named 'cf_approve_reclaim.cf_approve_reclaim'" | Missing `__init__.py` in flow folder — fixed in this repo | Re-deploy; the `__init__.py` files are present |
| Approve on rightsize form shows no illustrative label | First deploy had this bug — fixed; flow re-deployed | Re-deploy if you cloned before the fix |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. Check whether the conclusions matched |
| Agent recommends reclaiming `vm-batch-weekend-01` | Agent missed the scheduled-job check | `cf_reclaim_resource` has a hard guard that blocks it; point it out |
| Smoke runner shows each tool name twice | ADK trace records request + response as separate steps | Expected; de-duplicate to get the actual call count |

## 8. Things not to say

- **Do not say** the 40% rightsizing saving is real or guaranteed. It is explicitly labelled "illustrative" in the mock tool code.
- **Do not say** the agent "always" catches the `vm-batch-weekend-01` red herring. The smoke run skipped that resource in one pass; vary between runs.

## 9. Closing talking points

**What the platform made easy**

- Assembling an agent from small, bounded read-only tools plus a knowledge base: import the tools, import the KB, list them in `agent.yaml`.
- Two governed human-in-the-loop steps (`cf_approve_reclaim` and `cf_approve_resize`): each write tool is not attached to the agent; the flow calls it only after Approve.
- Policy grounding: in the smoke run on CF-004, the agent retrieved and cited CF-POL-04 without being told which document to look up.
- Scripted re-deploys: re-importing updates resources in place (all six deploy steps returned `[ok]`).

**What was not easy**

- Flow folders need `__init__.py` — without it the ADK flow importer fails with "not a package". Not obvious from the docs; found during the first deploy attempt.
- Draft vs. live agents (the picker shows only AskOrchestrate until `orchestrate agents deploy` runs).
- KB indexing takes time after import; the first demo query may be slow.
- Auth expiry (2 hours) and Windows encoding quirks in the CLI.

**When NOT to use an agent**

- The workflow is known and fixed, the inputs are well-formed, the rules are stable. A script or a flow is faster, cheaper, deterministic and easier to test.
- You need the same answer every time for audit or compliance.
- The risky step needs a guarantee. Put it in a flow or a tool (as done here), never only in instructions.

**When an agent might be worth it** (arguments; the smoke run supports tool selection but not full end-to-end outcomes): inputs that are vague or vary (the user says "our bill jumped" without knowing which service), the next step depends on what the previous step found, and policy documents change often enough that hardcoding rules into a script is brittle.

**Open items**

1. The smoke run checked only 3 of 4 idle-resource candidates in CF-002; whether the agent reliably catches `vm-batch-weekend-01` across multiple runs is untested.
2. Clean first-install re-import safety is untested repo-wide.

## 10. After the demo

- No persistent state changes: the write tools log a mock message but do not change any data structure.
- Both approval flows are browser-verified. If you re-deploy from scratch, re-test both Approve and Reject paths to confirm the forms render correctly.
