# Disability Pension & Vocational Rehabilitation Triage Agent - Demo Script

For a human presenter. The scenario has been deployed and the smoke prompts have passed
on a live WXO instance. The approval flow (Approve and Reject paths) has been verified
in the browser chat UI. Tool sequences are from local Python testing (all 4 cases, all
error paths); agent output wording varies by run and has not been quoted verbatim.

## 1. Audience and goal

**Audience:** Finnish pension institution claims handlers (Eläkeratkaisija),
occupational rehabilitation specialists (Kuntoutusasiantuntija), medical case
coordinators, and claims team leads at TyEL/Keva providers.

**Goal:** Show how an AI agent can systematically triage a disability pension
application — checking the qualifying insurance condition, evaluating medical
evidence, enforcing the "Rehabilitation before Pension" statutory rule, and
routing the case through a governed approval flow — while keeping the claims
handler in control of every official action.

**What this demo does NOT claim:**

- All data is a fixed, static mock world. No connection to Arek, Keva systems, or any real pension platform.
- Agent output wording varies between runs; the expected behaviour below describes what the tools return, not verbatim agent quotes.
- No timing claims (case processing speed, staff hours saved) are made. No numbers were measured.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy pension-disability-triage`. This imports the tools, the knowledge base, the `pdis_refer_claim` flow, and the agent.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name pension_disability_triage`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `groq/openai/gpt-oss-120b`. The instance must offer that model.
- The knowledge base (`pension_disability_policy`) requires indexing time after import. Wait several minutes before your first KB query.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **Disability Pension & Vocational Rehabilitation Triage** (YAML name `pension_disability_triage`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name pension_disability_triage` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. Conversation history from a previous scene may confuse the agent.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `pension_disability_triage`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **Disability Pension & Vocational Rehabilitation Triage** is selectable.
- [ ] The mock data is static — no reset needed between cases.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `pdis_get_claim_dossier`, `pdis_verify_qualifying_months`, `pdis_get_medical_summary`, `pdis_assess_rehab_eligibility`. The knowledge base appears in transcripts as a tool call named `pension_disability_policy`. The flow is `pdis_refer_claim` (browser only).
- **The model varies.** Tool order and wording differ between runs. The tool behaviours below are from local Python testing; agent wording has not been observed.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Full disability — CLM-701 | Tool outputs verified locally (Python). Smoke prompt sent to live agent (1 run). |
| 2 Rehab-first — CLM-702 | Tool outputs verified locally (Python). Smoke prompt sent to live agent (1 run). |
| 3 Occupational accident waiver — CLM-703 | Tool outputs verified locally (Python). Smoke prompt sent to live agent (1 run). |
| 4 Governed referral flow | Approve and Reject paths verified in browser chat UI (1 run each). |
| 5 Refusal / red herring — CLM-704 | Tool outputs verified locally (Python). Smoke prompt sent to live agent (1 run). |

---

## Scene 1 - Full Disability Pension Evaluation (CLM-701)

*Main-path scene. The case is straightforward once the qualifying check and medical evidence are in.*

**Prompt (type exactly):**

```
Evaluate the disability pension claim for member CLM-701. Use your tools to check the qualifying months, review the medical evidence, and assess rehabilitation eligibility. Do NOT call pdis_refer_claim — just report your triage disposition and which referral type you would recommend.
```

**Expected behaviour (observed):**

- Smoke run (1 run): agent called `pdis_get_claim_dossier`, `pdis_verify_qualifying_months`, `pdis_get_medical_summary`, `pdis_assess_rehab_eligibility` in that order. Qualifying condition: 58/60 months met, tuleva aika eligible. Work capacity 30%, permanent prognosis, rehab exhausted. Disposition: PENSION ELIGIBLE. Agent cited DIS-POL-01 and recommended medical board referral.

**Point out:**

- *Tools:* Four read-only tools called in order — dossier, qualifying months, medical summary, rehab assessment. No write action triggered.
- *Knowledge base:* Agent should cite DIS-POL-01 (incapacity criteria) and DIS-POL-02 (rehab measures exhausted).
- *Completeness:* The agent must not skip the rehab check even in an obvious case. CMO referral is mandatory per DIS-POL-01.

**Fallback:**

- If the agent skips the rehab eligibility check, note it as a limitation and ask: "Can you also run the rehabilitation eligibility assessment to confirm all steps were covered?"

---

## Scene 2 - Rehabilitation Before Pension (CLM-702)

*Trap scene. The case looks like a pension at first glance (injured worker, reduced capacity) but the statutory rehab rule blocks a direct pension grant.*

**Prompt (type exactly):**

```
Member CLM-702 has applied for a disability pension following back surgery. Use your tools to evaluate the claim. Do NOT call pdis_refer_claim — just report whether a pension can be granted at this stage or whether another pathway applies, and cite the relevant policy.
```

**Expected behaviour (observed):**

- Smoke run (1 run): qualifying condition met (36/60 months), work capacity 55% (above 40% threshold), significant recovery potential, no workplace trial attempted. `pdis_assess_rehab_eligibility` returned REHABILITATION PRIORITY. Agent recommended vocational rehabilitation (tyokokeilu) and cited DIS-POL-02. Agent explicitly stated a pension cannot be granted at this stage.

**Point out:**

- *Statutory rule:* This is the "Rehabilitation before Pension" principle (kuntoutus ennen eläkettä). The agent enforces it because the tool data encodes the condition: work capacity > 40%, recovery potential = significant, rehab measures not exhausted.
- *What makes it a trap:* An untrained handler might see "reduced work capacity + B-statement" and proceed directly to pension evaluation. The agent must stop and redirect to rehabilitation.
- *Policy citation:* DIS-POL-02 should be cited.

**Be straight:** If the agent does grant a pension rather than recommending rehab, note this as a model reliability issue. The tool data is correct; the agent's reasoning is what varies between runs.

**Fallback:**

- If the agent incorrectly recommends a pension: "The tool shows work capacity at 55% with significant recovery potential and no workplace trial. Does DIS-POL-02 apply here?"

---

## Scene 3 - Occupational Accident Waiver (CLM-703)

*Exception-handling scene. The headline number (14 months insured) makes the case look like a clear refusal, but an occupational accident waiver applies.*

**Prompt (type exactly):**

```
Young worker CLM-703 is claiming incapacity following a factory accident and has only 14 months of work history. Use your tools to evaluate eligibility. Do NOT call pdis_refer_claim — just explain whether and why the standard qualifying condition applies and what disposition you recommend.
```

**Expected behaviour (observed):**

- Smoke run (1 run): `pdis_verify_qualifying_months` returned NOT ELIGIBLE on the 36/60 condition (14 months) and immediately surfaced `qualifying_condition_waived: True` with waiver reason `tyotapaturma` (TyEL § 12). Agent confirmed accident verification status from dossier, proceeded to medical assessment (work capacity 25%), and recommended medical board referral. Agent cited DIS-POL-04.

**Point out:**

- *Red herring:* The 14-month figure invites a quick refusal decision. The agent must read the waiver flag before concluding ineligibility.
- *Accident verification:* The agent instructions require explicit confirmation of accident documentation before accepting a waiver. Point this out — it is a safety check against fraud.
- *Policy citation:* DIS-POL-04 (qualifying months & exceptions) should be cited.

**Be straight:** The waiver flag is deterministic mock data. This proves the tool works — it does not prove the agent will always catch the waiver in a real messy dossier.

**Fallback:**

- If the agent concludes "not eligible" without catching the waiver: ask "Does the tool result show any waiver flag or statutory exception for this case?"

---

## Scene 4 - Governed Referral Flow (CLM-701, approval path)

*Governed-action scene. Run this in a fresh conversation after Scene 1 to show the human-in-the-loop gate.*

**Verified in browser (1 run per path).** The flow form rendered with all five fields. Approve path submitted the referral and the agent reported the `message` field verbatim (referral ID `REF-XXXXX`). Reject path returned the rejection message with nothing recorded.

**Prompt (type exactly):**

```
Evaluate the disability pension claim for member CLM-701 and, once you have completed the triage, use the referral flow to submit a referral to the Medical Board.
```

**Expected behaviour (observed):**

1. Agent calls the four read-only tools (same as Scene 1).
2. Agent proposes the `pdis_refer_claim` flow with inputs: `claimant_id=CLM-701`, `referral_type=medical_board`, a `disposition_summary` drawn from the tool findings, `policy_ref=DIS-POL-01`, `b_statement_valid=yes`.
3. A review form appears in the chat with five read-only fields: Claimant ID, Referral Type, Policy Reference, B-Statement Valid, Triage Disposition Summary.
4. **Approve path:** Handler clicks "Approve Referral" → `pdis_dispatch_referral` is called → a referral ID (`REF-XXXXX`) is returned → agent reports the message verbatim.
5. **Reject path (separate run):** Handler clicks "Reject" → nothing is submitted → agent reports "REFERRAL REJECTED. No referral was submitted."

**Point out:**

- The form is the governance gate. Nothing is recorded until the claims handler explicitly approves.
- `pdis_dispatch_referral` is not on the agent's tool list — it can only be called through the flow after the button click.
- Approval and rejection are two separate browser paths; you need two separate conversations to show both.

**Fallback:**

- If the flow form does not appear: check `orchestrate tools list` for `pdis_refer_claim` and re-run `wxodemo deploy`. Show Scene 1 as the diagnostic fallback.

---

## Scene 5 - Refusal / Red Herring (CLM-704)

*Restraint scene. The medical evidence (35% work capacity) would normally support a pension claim, but the qualifying months condition fails with no waiver — the agent must stop early and refuse.*

**Prompt (type exactly):**

```
Member CLM-704 is requesting a disability pension after several years of uninsured residency abroad. Use your tools to check the qualifying condition. Do NOT call pdis_refer_claim — just report the eligibility outcome and what the claimant should be advised.
```

**Expected behaviour (observed):**

- Smoke run (1 run): `pdis_get_claim_dossier` showed 8.5-year uninsured period abroad with no bilateral treaty. `pdis_verify_qualifying_months` returned NOT ELIGIBLE (8/60 months, threshold 36, no waiver). Agent stopped after the qualifying months check, cited DIS-POL-04, and advised Kela referral without proceeding to medical assessment.

**Point out:**

- *Red herring:* A non-specialist handler might see "35% work capacity" in the dossier and assume a pension applies. The qualifying months check is the statutory gate that blocks this — and the agent enforces it.
- *Restraint:* The right answer here is to do less, not more. Proceeding to full medical assessment is wasteful and misleading.
- *Policy citation:* DIS-POL-04 should be cited.

**Be straight:** If the agent does proceed to a full medical assessment despite the qualifying months failure, point this out as a limitation.

**Fallback:**

- If the agent proceeds beyond the qualifying months check: "Given that the qualifying condition failed with no waiver, is there a policy reason to continue the medical assessment?"

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name pension_disability_triage`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **Disability Pension & Vocational Rehabilitation Triage**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched the tool data |
| Flow form does not appear | Flow not imported, or agent tried to call write tool directly | Check `orchestrate tools list` for `pdis_refer_claim`; re-run `wxodemo deploy` |
| Agent recommends pension for CLM-702 without rehab | LLM reasoning failure | Prompt: "Does DIS-POL-02 apply here given the recovery potential shown by the tool?" |

Not seen, so not covered here: KB indexing failures, multi-turn conversation drift across scenes.

## 8. Things not to say

- **Do not say** "the agent processes claims faster than a human" — no timing was measured.
- **Do not say** "the agent always enforces the rehabilitation rule" — model behaviour varies between runs; 1 smoke run per prompt was conducted.
- **Do not say** "this is connected to Arek or any real Finnish pension system" — all data is mock.

## 9. Closing talking points

**What the platform made easy**

- Attaching four deterministic domain tools to a ReAct agent with a single YAML file — no LLM fine-tuning needed for tool use.
- The KB-backed policy citation pattern: the agent references stable document IDs (DIS-POL-01 through DIS-POL-04) without those IDs being hard-coded into the instructions.
- The approval flow gate: `pdis_dispatch_referral` is completely unreachable by the agent; the platform enforces least-privilege by design.

**What was not easy**

- Ensuring the agent reliably stops after the qualifying months check for CLM-704 (without also checking medical evidence unnecessarily) depends on the LLM following the instructions literally. This requires rehearsal.
- The "rehabilitation before pension" rule (CLM-702) is a negative-result case — the agent must say "no pension yet" — and LLMs sometimes try to be helpful by offering pension options anyway.

**When NOT to use an agent**

- When every incoming case has fully structured, machine-readable inputs and the decision tree is fixed. A rules engine or decision table handles that more reliably than a ReAct loop.
- When the approval flow form must be presented in a native case-management system (Arek, etc.) rather than the WXO chat UI.

**When an agent might be worth it** (arguments, not yet measured here): When dossiers arrive as unstructured text — free-form B-statements, handwritten employer reports, incomplete submissions — and a handler must decide which statutory check to prioritise. The agent can extract the salient facts, apply the statutory priority order, and surface the policy citation without the handler navigating multiple systems manually.

**Open items (still open at the time of writing; see `plans/pension-disability-triage-plan.md`)**

1. LLM reliability across multiple runs has not been measured (1 smoke run per case). Rehearse before a live demo.
2. No ADK test_cases/ or eval_config.yaml have been added (evaluation tier is `core`).

## 10. After the demo

- If you used `python wxodemo.py deploy pension-disability-triage` to set up, run `python wxodemo.py undeploy pension-disability-triage` to clean up all imported resources.
- The mock data is static — no database cleanup is needed.
