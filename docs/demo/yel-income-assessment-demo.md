# YEL Income Assessment Agent - Demo Script

For a human presenter. Scenes 1–4 are verified by direct Python data-layer tests and live agent runs (browser chat). Scene 5 (approval flow) is verified live: form renders, all three buttons work, Confirm and Adjust correctly record the income, Escalate correctly suppresses the determination. Where something remains unverified the text says so.

## 1. Audience and goal

**Audience:** YEL underwriters (*YEL-ratkaisija*), entrepreneur account specialists (*Yrittäjäneuvoja*), insurance operations managers at Finnish statutory pension providers — or IBM clients in the broader social insurance and regulated financial services sector.

**Goal:** Show how a watsonx Orchestrate ReAct agent conducts a statutory triennial YEL confirmed work income review: retrieving the entrepreneur profile, benchmarking against Statistics Finland / ETK sector wages, applying the EUR 4,000 statutory transition cap, estimating social security benefit impact, and routing the formal determination through a human-governed approval flow.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real pension system, Kela, or ETK.
- Benefit estimates are illustrative approximations. Real Kela and YTK calculations apply additional rules not modelled here.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy yel-income-assessment`. This imports the tools, the knowledge base, the `yel_issue_decision` flow, and the agent.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name yel_income_assessment`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The `yel_issue_decision` flow renders an approval form in the browser chat UI with three buttons: **Confirm Proposed Income**, **Adjust & Issue**, and **Escalate to Appeals**. The form has been verified live.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **YEL Income Assessment** (YAML name `yel_income_assessment`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name yel_income_assessment` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene, except Scene 5 which continues in the Scene 1 thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `yel_income_assessment`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **YEL Income Assessment** is selectable.
- [ ] No state to reset: all mock data is static Python; no database is modified between runs.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `yel_get_business_profile`, `yel_get_sector_benchmark`, `yel_calculate_income_recommendation`, `yel_estimate_social_benefits`. The knowledge base appears in transcripts as a tool call named `yel_income_policy`. The flow is `yel_issue_decision`.
- **The model varies.** Tool order and wording differ between runs. Quoted outputs below are from observed runs; the agent's phrasing in your run will differ.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 — Transition Cap (ENT-801) | Python data layer test + live browser run. Agent correctly cited YEL-POL-02 and landed at EUR 22k. |
| 2 — Dispute / Part-time (ENT-802) | Python data layer test only. Tool logic verified deterministically. Agent not run live for this case. |
| 3 — Beginner Discount (ENT-803) | Python data layer test only. Tool logic verified deterministically. Agent not run live for this case. |
| 4 — Below Threshold (ENT-804) | Python data layer test only. Tool logic verified deterministically. Agent not run live for this case. |
| 5 — Approval Flow (fresh thread) | Observed live: agent correctly gates on evidence and asks for assessment before calling the flow. |
| 5 — Approval Flow (Scene 1 thread) | Observed live: form renders, all three buttons work. Confirm and Adjust correctly record income. Escalate suppresses determination. Income field label shows proposed value; type or leave blank (Confirm uses proposed automatically). |

---

## Scene 1 — Triennial Review: IT Consultant (Transition Cap)

**Why this scene:** Demonstrates the core review path. The sector median (EUR 46k) is far above the current income (EUR 18k), but the EUR 4,000 statutory cap limits the mandatory increase to EUR 22k. This is the most common point of confusion for entrepreneurs who expect to jump to the full median.

**Prompt (type exactly):**

```
Conduct a YEL income review for IT consultant ENT-801 (current income EUR 18,000/yr, turnover EUR 95,000/yr). Use your tools to retrieve the profile, sector benchmark, and calculate the recommended income. Do NOT call yel_issue_decision — just report your diagnosis and the proposed new confirmed income with reasoning.
```

**Expected behaviour (observed):**

- Agent calls `yel_get_business_profile('ENT-801')` → retrieves Aleksi Mäkinen, NACE J.62, revenue EUR 95k, current income EUR 18k, 45 h/wk.
- Agent calls `yel_get_sector_benchmark('NACE J.62')` → sector median EUR 46,000.
- Agent calls `yel_calculate_income_recommendation('ENT-801')` → recommended income EUR 22,000, transition cap applied, `YEL-POL-02` cited.
- Agent calls `yel_estimate_social_benefits('ENT-801', compare_income=22000)` → shows daily sick allowance rising from EUR 42/day to EUR 51.33/day.
- Agent summarises: current EUR 18k → recommended EUR 22k (+EUR 4k cap); explains why it cannot go to EUR 46k in one review; shows the premium change and the benefit delta.

**Point out:**

- *Tools:* The agent calls all four tools in sequence — profile, benchmark, recommendation, benefits. This is the intended protocol.
- *Transition cap:* The sector median is EUR 46k — 2.5x the current income. The EUR 4,000 cap prevents a shock premium increase. Remaining gap is addressed in future reviews.
- *Policy citation:* The agent cites `YEL-POL-02` for the cap logic.
- *Benefits:* The daily sick allowance delta is illustrative. For a 30-day illness: approximately EUR 280 more with the higher income.

**Fallback:**

- If the agent jumps straight to EUR 46k: ask "What does the tool say about the transition cap?" It should re-cite `YEL-POL-02` and correct itself.
- If tool calls are skipped: start a new conversation and re-send the prompt.

---

## Scene 2 — Contested Case: Bakery Owner (Part-Time Hours, Revenue ≠ Work Input)

**Why this scene:** The trap case. Revenue EUR 140k looks high, but the owner works only 20 h/wk managing logistics while 3 hired employees do the actual production. The sector median must be scaled for part-time hours (20/40 = 50% → EUR 16k target), which is *below* the current income (EUR 32k). No mandatory increase applies.

**Prompt (type exactly):**

```
Artisan bakery owner ENT-802 is contesting a proposed YEL income of EUR 38,000. Retrieve her profile and sector benchmark, then calculate the income recommendation. Do NOT call yel_issue_decision — just report what the correct recommended income should be and why the turnover-based proposal was too high.
```

**Expected behaviour (based on mock data, not observed live for this case):**

- Agent calls `yel_get_business_profile('ENT-802')` → Kaisa Virtanen, NACE C.10, revenue EUR 140k, 20 h/wk, 3 employees, EUR 48k subcontracting.
- Agent calls `yel_get_sector_benchmark('NACE C.10')` → sector median EUR 32k.
- Agent calls `yel_calculate_income_recommendation('ENT-802')` → part-time adjusted target: EUR 32k × (20/40) = EUR 16k. Current income (EUR 32k) > target. No mandatory increase. Recommended income stays at EUR 32k.
- Agent explains: the EUR 38k proposal was based on turnover, which is incorrect under `YEL-POL-01` — the benchmark is owner work input, not revenue.

**Point out:**

- *Revenue ≠ work input:* EUR 140k turnover is driven by 3 employees and raw materials, not solely by the owner.
- *Part-time hours adjustment:* The tool scales the median proportionally. This is the correct statutory method (`YEL-POL-01`).
- *Restraint:* Current income is already above the adjusted target. The agent should correctly say "no mandatory increase" — not propose EUR 38k.

**Be straight:** The agent reads only what is in the mock profile; it cannot verify actual payroll records or invoices. In a real system the underwriter reviews physical documents.

**Fallback:**

- If the agent recommends EUR 38k or higher: ask "What is the part-time hours adjustment in the tool reasoning?" The tool reasoning shows the 20/40 ratio explicitly.
- If the agent calls the flow despite the instruction: model adherence failure. Note it; start a new conversation.

---

## Scene 3 — New Entrepreneur: Startup Founder (Beginner Discount)

**Why this scene:** First-time entrepreneur, 19 months insured. Sector median is high (EUR 46k), cap applies (EUR 14k → EUR 18k), and the 22% beginner discount reduces the premium but NOT the social security benefit base.

**Prompt (type exactly):**

```
New startup founder ENT-803 wants to know their recommended YEL income and whether they qualify for a beginner discount. Retrieve the profile, sector benchmark, and calculate the recommendation. Do NOT call yel_issue_decision — just report the recommended income, whether the beginner discount applies, and what their monthly premium would be.
```

**Expected behaviour (based on mock data, not observed live for this case):**

- Agent calls `yel_get_business_profile('ENT-803')` → Juhani Korhonen, NACE J.62, 19 months insured, EUR 14k current income.
- Agent calls `yel_get_sector_benchmark('NACE J.62')` → sector median EUR 46k.
- Agent calls `yel_calculate_income_recommendation('ENT-803')` → recommended EUR 18k (cap applied), beginner discount applicable.
- Tool reports: standard rate ~24.1%, beginner discount 22% → discounted rate ~18.8%. Monthly premium ~EUR 282.75 (illustrative).
- Agent confirms: discount applies to premium only; benefit base remains EUR 18k.

**Point out:**

- *Beginner discount:* 22% off the premium for the first 48 months — it does not reduce the YEL income or the Kela allowance base. Many first-time entrepreneurs misunderstand this.
- *Transition cap:* Same as Scene 1 — sector median EUR 46k, cap limits mandatory increase to +EUR 4k = EUR 18k.
- *Policy refs:* `YEL-POL-02` for cap, `YEL-POL-03` for the beginner discount and benefit linkage.

**Be straight:** The monthly premium of ~EUR 282.75 is illustrative. Real premiums depend on exact contribution rates (updated annually) and the entrepreneur's date of birth.

**Fallback:**

- If agent says the discount reduces the benefit base: point to `YEL-POL-03` — "Discount applies to premium only."

---

## Scene 4 — Below-Threshold Freelancer (Restraint Case)

**Why this scene:** The red-herring / non-applicability case. Revenue EUR 5,200 is below the statutory YEL minimum threshold (EUR 9,010/yr). The agent must identify this first and stop — not perform a benchmark comparison or propose an income.

**Prompt (type exactly):**

```
Side-hustle freelancer ENT-804 has annual revenue of EUR 5,200 and wants to know if YEL insurance is mandatory. Use your tools to check and report whether YEL is required and what options are available.
```

**Expected behaviour (based on mock data, not observed live for this case):**

- Agent calls `yel_get_business_profile('ENT-804')` → Meri Leinonen, NACE M.74, revenue EUR 5,200, no current YEL.
- Agent calls `yel_get_sector_benchmark('NACE M.74')` → sector median EUR 26k, statutory minimum EUR 9,010.
- Agent calls `yel_calculate_income_recommendation('ENT-804')` → `yel_mandatory: false`; revenue is below the EUR 9,010 threshold.
- Agent reports: YEL is NOT mandatory. Voluntary insurance is available. Cites `YEL-POL-01`.
- Agent does NOT propose an income or call `yel_issue_decision`.

**Point out:**

- *Restraint:* The correct answer is "YEL not required." The agent checks the mandatory threshold before doing any benchmark comparison.
- *Voluntary option:* The agent should mention voluntary YEL is available even below the threshold.

**Be straight:** Only 3 NACE sector benchmarks are loaded. Any entrepreneur in a sector not in the mock data returns a "sector not found" error. Production would query a live ETK API.

**Fallback:**

- If agent proposes an income despite below-threshold: the tool returns `yel_mandatory: false`. The agent instructions say to stop. If it still calls the flow, that is a model adherence failure; start a new conversation.

---

## Scene 5 — Approval Flow (Formal Determination)

> **Thread continuity required.** This scene runs **in the same conversation thread as Scene 1**. Do NOT start a new conversation. If you send this prompt in a fresh thread, the agent correctly asks for the assessment first — that is the right behaviour (observed live), not a bug.

**Setup:** Complete Scene 1 in the browser. Without starting a new conversation, type:

**What to type (same thread as Scene 1):**

```
Issue the formal determination for ENT-801 with the recommended income of EUR 22,000.
```

**Expected behaviour (observed live):**

- Agent calls `yel_issue_decision`, passing `entrepreneur_id='ENT-801'`, `proposed_income_eur=22000`, justification from the prior assessment, and `policy_ref='YEL-POL-02'`.
- A form appears titled **"YEL Confirmed Work Income — Underwriter Review"** showing:
  - Read-only fields: Entrepreneur ID, Proposed YEL Income, Policy Reference, Assessment Reasoning.
  - An input field labelled **"Final Confirmed Income (EUR/yr) — proposed: 22000"** (empty; the label shows the proposed figure).
  - Three buttons: **Confirm Proposed Income**, **Adjust & Issue**, **Escalate to Appeals** (under the ∨ chevron).

**Confirm path (observed live):** Leave the income field blank and click **Confirm Proposed Income** → the flow uses EUR 22,000 (the proposed value) → `yel_issue_decision_record` is called → agent reports verbatim:
```
DECISION ISSUED (CONFIRM). Entrepreneur ENT-801: confirmed YEL income 22,000 EUR/yr. Policy: YEL-POL-02. ...
```

**Adjust path (observed live):** Type a different value (e.g. `20000`) in the income field, click **Adjust & Issue** → `yel_issue_decision_record` is called with the typed value → agent reports:
```
DECISION ISSUED (ADJUST). Entrepreneur ENT-801: confirmed YEL income 20,000 EUR/yr. Policy: YEL-POL-02. ...
```

**Escalate path (observed live):** Click the **∨** chevron next to Confirm → click **Escalate to Appeals** → no income change is issued → agent reports:
```
ESCALATED TO APPEALS REVIEW. No income change has been issued. Case for entrepreneur ENT-801 has been referred to TELK. ...
```

**Point out:**

- *Governance gate:* The agent cannot issue a determination without the underwriter clicking a button. `yel_issue_decision_record` is not attached to the agent — it is only reachable through this flow.
- *Income field:* Leave it blank to confirm the proposed figure; type a different integer to adjust. The flow never records 0.
- *Escalate:* No income record is written. The current confirmed income remains in force until TELK rules.

**Fallback:**

- If prompt sent in fresh thread and agent asks for assessment: correct. Run Scene 1 first in the same thread, then send this prompt.
- If **Escalate to Appeals** is not visible: click the **∨** chevron to expand the additional buttons.
- If income is recorded as 0: this is the old flow version. Redeploy with `python wxodemo.py deploy yel-income-assessment`.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name yel_income_assessment`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **YEL Income Assessment**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched in observed runs |
| Agent recommends EUR 46k for ENT-801 (ignores cap) | Model did not follow tool reasoning list | Ask "What does yel_calculate_income_recommendation say about the transition cap?" |
| Scene 5 in fresh thread: agent asks for assessment | Correct evidence-gating behaviour | Run Scene 1 first in the same thread, then send the Scene 5 prompt |
| Flow records income as 0 | Old flow version without the fallback fix | `python wxodemo.py deploy yel-income-assessment`, retry |
| Number input field shows placeholder 22000 but submits empty | Stale browser cache of old flow | Hard-reload the page (Ctrl+Shift+R), retry |

Not seen live: KB indexing delays after first deploy (wait ~60 s before the first query after a fresh import).

## 8. Things not to say

- **Do not say** the benefit amounts (EUR/day) are accurate Kela figures — they are illustrative approximations from the mock formula.
- **Do not say** "the agent saves X minutes per case" — no measurement has been made.
- **Do not say** scenes 2, 3, and 4 were run live — they were verified by data-layer unit tests only.

## 9. Closing talking points

**What the platform made easy**

- The `@tool` decorator and YAML agent spec made it straightforward to wire statutory calculation logic (Python) to an LLM that can explain steps and handle natural language disputes.
- The approval flow governance pattern (write tool not attached to the agent; only reachable through the flow) is a clean architectural constraint that a fixed rules engine would need to implement separately.

**What was not easy**

- The YAML `instructions` block must be very explicit about step sequence and tool call order; without it the model skips steps or calls the flow prematurely.
- The `number_input_field` DataMap default renders as a placeholder, not a pre-filled value. The fallback had to be moved into the flow scripts.
- Benefit estimates required careful wording to mark them as illustrative throughout.

**When NOT to use an agent**

- For fully-specified cases (full-time entrepreneur, no dispute, benchmark available): a deterministic rules engine is faster, cheaper, and more auditable.
- When the entrepreneur's situation can be fully encoded in a form with well-defined fields: use a workflow, not an agent.

**When an agent might be worth it** (arguments, not measured here): multi-step dispute handling in natural language, generating the written justification for the formal determination, and classifying ambiguous split-role cases that would require extensive branching in a rules engine.

**Open items (still open at the time of writing; see `plans/yel-income-assessment-plan.md`)**

1. Scenes 2, 3, and 4 have not been run live against the deployed agent. Data layer is verified; agent behaviour is untested for those cases.
2. Only 3 NACE sector benchmarks are loaded. Production requires the full ETK/Statistics Finland sector table.
3. The income recommendation uses proportional hours adjustment only. Real YEL assessments also consider specialisation, experience, and market position.

## 10. After the demo

- Undeploy to free instance resources: `python wxodemo.py undeploy yel-income-assessment`.
- Or leave deployed — subsequent deploys upsert existing resources without creating duplicates.
