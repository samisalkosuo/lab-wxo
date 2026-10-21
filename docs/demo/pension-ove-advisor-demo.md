# Partial Early Old-Age Pension Advisor Agent - Demo Script

For a human presenter. **This scenario has not been run against a live WXO instance.**
Tool sequences, agent answers, and flow behaviour described in the scenes below come from
the mock data design and tool code — not from observed runs. Every section that would
normally quote a recorded run says "not verified". Fill in observations after you have
run it live.

## 1. Audience and goal

**Audience:** Pension fund executives, chief customer officers, digital transformation leads, and IT architects in the earnings-related pension sector (TyEL/YEL/JuEL institutions such as Varma, Ilmarinen, Elo, Veritas, Keva).

**Goal:** Demonstrate how a watsonx Orchestrate conversational agent handles complex statutory retirement advisory rules, computes multi-variable pension reductions and continuing employment accruals, and enforces strict governance gates for formal benefit filings.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to live Arek or ETK production registers.
- This scenario has not been run against a live WXO instance. No tool sequences, answer quotes, or run counts can be cited yet. The scenes below describe expected behaviour from the code, not observed behaviour.
- The approval flow form, Approve path, and Reject path have not been browser-verified.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy pension-ove-advisor`. This imports the tools (`ove_get_member_profile`, `ove_get_accrued_pension`, `ove_calculate_reduction`, `ove_simulate_combined_income`), the knowledge base (`pension_ove_policy`), the approval flow (`ove_submit_application`), and the agent (`pension_ove_advisor`).
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name pension_ove_advisor`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The browser needs access to your WXO instance web UI. The approval form (Scene 5) only renders there. It cannot be driven from the CLI or the run API.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **Partial Early Old-Age Pension Advisor** (YAML name `pension_ove_advisor`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name pension_ove_advisor` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. A flow waiting for a click blocks its thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours):
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `pension_ove_advisor`. If not, deploy it (section 2).
- [ ] Reload the browser chat page and confirm **Partial Early Old-Age Pension Advisor** is selectable.
- [ ] No data reset is needed. The mock world is static and read-only.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `ove_get_member_profile`, `ove_get_accrued_pension`, `ove_calculate_reduction`, `ove_simulate_combined_income`, and `ove_submit_application` (the approval flow). The knowledge base appears in transcripts as a tool call named `pension_ove_policy`.
- **The model varies.** Tool order and wording differ between runs.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Vague opening | **Not verified.** Expected from code. |
| 2 Main path 50% OVE (MEM-101) | **Not verified.** Expected from code. Local Python tool calculation verified. |
| 3 Underage refusal (MEM-102) | **Not verified.** Expected from code. Age check verified in unit test. |
| 4 Multi-option comparison (MEM-103) | **Not verified.** Expected from code. Simulation logic verified in unit test. |
| 5 Governed application flow | **Not verified.** Form not browser-tested. |
| 6 Disability conflict restraint (MEM-104) | **Not verified.** Benefit conflict check verified in unit test. |

---

## Scene 1 - Vague opening ("I want to explore partial pension")

This is the messy-input teaching point. The member provides no ID or birth year.

**Prompt (type exactly):**

```
Hi, I am thinking about taking partial pension early while continuing my job. Can you help me?
```

**Expected behaviour (not verified against live instance):**

- The agent should greet the user politely and ask for their **member ID** (e.g. MEM-101) and birth year or target retirement timeframe.
- It should not attempt to calculate numbers without knowing the member's profile.
- It should ask one clear clarifying question at a time.

**Point out:**

- *Graceful disambiguation:* handles vague member inquiries without guessing.
- *Strict evidence baseline:* waits for member identification before querying pension accruals.

---

## Scene 2 - Main path: 50% OVE with continuing salary (Matti Virtanen, MEM-101)

Demonstrates the core calculation: 50% partial draw, permanent 0.4%/month actuarial reduction, life expectancy coefficient, and 1.5%/year ongoing TyEL work accrual.

**Prompt (type exactly):**

```
I turn 62 next month and want to explore taking 50% partial early old-age pension (OVE) while continuing my job. My member ID is MEM-101 and my current monthly salary is 4200 euros.
```

**Expected behaviour (not verified against live instance):**

- Calls `ove_get_member_profile("MEM-101")` and verifies age 62 (born 1964).
- Calls `ove_get_accrued_pension("MEM-101")` retrieving €2,400.00/mo baseline accrual.
- Calls `ove_calculate_reduction("MEM-101", 50, "2026-05-01")` and computes:
  * 23 months before full pension age $\rightarrow$ 9.2% permanent reduction.
  * Life expectancy coefficient: 0.9482.
  * Monthly OVE gross payout: €1,033.16/mo.
- Calls `ove_simulate_combined_income("MEM-101", 50, 4200.0, 24)` and computes:
  * Total combined monthly gross: €5,233.16/mo.
  * Continuing work accrual: 1.5%/year on €4,200/mo = €63.00/mo new pension added per year.
- Cites `OVE-POL-03` explaining that the reduction is permanent for life on the drawn portion.

**Point out:**

- *Accurate actuarial modeling:* seamlessly combines statutory early penalties and continuing employment accruals.
- *Policy grounding:* cites `OVE-POL-03` for the 1.5% TyEL work accrual rule.

---

## Scene 3 - Refusal & age boundary check (Liisa Korhonen, MEM-102)

Demonstrates strict adherence to birth cohort minimum retirement age thresholds.

**Prompt (type exactly):**

```
Can I take 25% OVE starting next month? My member ID is MEM-102 and I am a 59-year-old teacher.
```

**Expected behaviour (not verified against live instance):**

- Calls `ove_get_member_profile("MEM-102")` identifying DOB 1966-08-25 (age 59).
- Calls `ove_calculate_reduction("MEM-102", 25)` which returns `ineligible_underage`.
- Explains that for birth cohort 1966, the statutory minimum OVE age is 62 years 0 months (shortfall of 27 months).
- Cites `OVE-POL-01` and provides the earliest date when an application can be filed.
- Refuses to file an early application.

**Point out:**

- *Regulatory compliance:* prevents invalid or illegal pension filings before statutory age thresholds.
- *Clear policy reference:* cites `OVE-POL-01`.

---

## Scene 4 - Multi-option scenario comparison (Antti Mäkinen, MEM-103)

Demonstrates financial trade-off comparison between 25% and 50% draw percentages alongside reduced work hours (80%).

**Prompt (type exactly):**

```
I want to compare taking 25% vs 50% OVE. My member ID is MEM-103 and I plan to reduce my work hours to 80% with a salary of 2800 euros per month.
```

**Expected behaviour (not verified against live instance):**

- Calls `ove_get_member_profile("MEM-103")` and `ove_get_accrued_pension("MEM-103")` (€3,000/mo baseline).
- Calls `ove_simulate_combined_income` for both 25% and 50% draw options.
- Compares:
  * Option A (25% draw): lower early penalty impact, higher untouched baseline capital.
  * Option B (50% draw): higher immediate monthly cash flow, higher permanent reduction on drawn half.
- Outlines the net combined income including €2,800/mo reduced work salary.

**Point out:**

- *Holistic advisory:* provides clear side-by-side trade-off analysis to empower member decision-making.

---

## Scene 5 - Governed application submission (MEM-101)

Demonstrates human-in-the-loop governance for formal pension filings.

**Prompt (type exactly):**

```
Please submit my formal application for 50% OVE starting 2026-05-01 for member MEM-101.
```

**Expected behaviour (not verified against live instance):**

- Summarizes the election: Member MEM-101, 50% draw, start date 2026-05-01.
- States: "I will now submit your OVE application for formal confirmation."
- Invokes the `ove_submit_application` approval flow.
- The browser chat UI renders the **OVE Application Confirmation** form.
- Upon clicking **Approve Application**, reports the formal registration confirmation and application reference ID verbatim.

**Point out:**

- *Governance boundary:* AI advises and simulates, but formal administrative filing requires human approval.

---

## Scene 6 - Restraint & conflict detection (Eeva Koskinen, MEM-104)

Demonstrates conflict detection when a member is actively receiving a conflicting statutory benefit.

**Prompt (type exactly):**

```
I want to apply for 50% OVE. My member ID is MEM-104.
```

**Expected behaviour (not verified against live instance):**

- Calls `ove_get_member_profile("MEM-104")` discovering active full disability pension (Kuntoutustuki, €1,850/mo).
- Detects the statutory benefit conflict.
- Cites `OVE-POL-02` explaining that Finnish law prohibits concurrent receipt of OVE and full disability pension.
- Refuses to calculate or submit an application.

**Point out:**

- *System integrity:* automatically detects benefit conflicts and prevents unlawful double-claims.

---

## 6. What to say and what not to say

### Things to say

- "This agent demonstrates how complex Finnish statutory pension rules (TyEL/JuEL) can be made understandable and accessible to members."
- "The agent never modifies pension records directly; formal filings always route through an interactive human approval gate."
- "All member profiles, accruals, and calculations run on static, deterministic mock datasets designed for repeatable demos."

### Things NOT to say

- Do not claim this is connected to Arek, Kanta, or live ETK production services.
- Do not claim measured time savings or processing speedups without run benchmarks.
- Do not state that the agent can override statutory cohort age thresholds or pension laws.
