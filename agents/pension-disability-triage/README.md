# Disability Pension & Vocational Rehabilitation Triage Agent

Agent name: `pension_disability_triage`

## What it does

Triages Finnish statutory disability pension claims (TyEL/YEL) by systematically
evaluating medical evidence, verifying the 36/60-month qualifying insurance condition
(tulevan ajan ansioedellytys), enforcing the "Rehabilitation before Pension" principle
(kuntoutus ennen eläkettä), and routing eligible cases through a human-in-the-loop
referral flow.

## Tools

| Tool | Purpose | Agent may call? |
|---|---|---|
| `pdis_get_claim_dossier` | Retrieve claimant record, employment history, accident details | Yes |
| `pdis_verify_qualifying_months` | Check 36/60-month insurance condition, waiver, tuleva aika | Yes |
| `pdis_get_medical_summary` | B-statement, diagnosis, work capacity %, prognosis, CMO referral flag | Yes |
| `pdis_assess_rehab_eligibility` | Rehabilitation-before-pension assessment, disposition | Yes |
| `pdis_refer_claim` (flow) | Governed approval flow to submit medical board / rehab / Kela referral | Yes |
| `pdis_dispatch_referral` | Internal write tool — records the approved referral | **No** (flow only) |

## Knowledge base

| KB name | Documents |
|---|---|
| `pension_disability_policy` | DIS-POL-01 (incapacity criteria), DIS-POL-02 (rehab priority), DIS-POL-03 (kuntoutustuki), DIS-POL-04 (qualifying months & exceptions) |

## Mock data

| Claimant | Case | Disposition | Teaches |
|---|---|---|---|
| CLM-701 | Severe MS, 12 years insured, rehab exhausted | `pension_eligible` → medical_board | Full disability pension evaluation, tuleva aika |
| CLM-702 | Back surgery, 7 years insured, recovery potential | `rehab_priority` → vocational_rehab | DIS-POL-02: rehab before pension |
| CLM-703 | Factory accident, 14 months insured | `pension_eligible` → medical_board (waiver) | DIS-POL-04: occupational accident waiver |
| CLM-704 | 8 months insured (gap abroad), no treaty | `deny_tyelonly` → Kela | Red herring / refusal case |

## Approval flow

The `pdis_refer_claim` flow presents the agent's triage summary to the claims handler
for sign-off before any official referral is recorded. Approval triggers
`pdis_dispatch_referral`; rejection returns an explicit "nothing was submitted" message.

Browser verification required (not testable via CLI):
- Form renders with all five fields.
- "Approve Referral" button calls `pdis_dispatch_referral`.
- "Reject" button returns the rejection message with nothing recorded.
- Agent resumes and reports the `message` field verbatim.

## Limitations / not tested

- Clean first-install (no existing resources) on a fresh WXO instance is untested.
- Browser flow form rendering and button behaviour require manual browser verification.
- `orchestrate agents deploy` may fail on Developer Edition (warn and continue).
- KB indexing takes time after import; wait before first knowledge-base query.
- Evaluation tier is `core` (ground_truth.json only); no ADK test_cases/ added.
