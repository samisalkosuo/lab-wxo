# Disability Pension & Vocational Rehabilitation Triage - Plan

> Scenario 8 in the presentation sidebar.
> Scenario id: `pension-disability-triage` | Package: `pension_disability` | Sidebar position: 8 | Status: `soon`

## Top-Level Overview

**Goal.** Demonstrate an intelligent claims triage and decision-support agent for Finnish statutory earnings-related pension institutions (TyEL/YEL/JuEL providers). The agent assists pension case handlers and medical review officers in processing **Disability Pension Claims** (*Työkyvyttömyyseläke* and temporary *Kuntoutustuki*). It systematically enforces the statutory **"Rehabilitation before Pension"** principle (*Kuntoutus ensin*), verifies the mandatory 36/60-month qualifying employment condition (*tulevan ajan ansioedellytys*), detects statutory waiting-period exceptions, and prepares medical board referral packages through a human-in-the-loop approval flow.

**Why it passes the agent-washing test.** Disability claim dossiers arrive with complex, unstructured medical B-statements (*B-lääkärinlausunto*), employer duty-to-accommodate reports, and fragmented earnings records. The assessment cannot follow a naive linear script because the path branches dynamically: an applicant with residual work capacity must be guided to vocational rehabilitation (*ammatillinen kuntoutus*, työkokeilu); an applicant with an occupational accident bypasses standard contribution waiting windows; an applicant with insufficient insured months requires statutory continuation options. The agent extracts evidence, evaluates eligibility, and recommends a triage disposition, while the formal referral of the medical dossier to the Chief Medical Officer (*Asiantuntijalääkäri*) is governed by an approval flow.

**Target Fit & Audience.**
- **Industry:** Finnish Statutory Pension Insurance / Social Security Authorities (*Työeläkeyhtiöt & Keva*).
- **Function:** Disability Claims Management & Occupational Rehabilitation (*Työkyvyttömyyseläke- ja kuntoutusasiat*).
- **Target Roles:** Disability Claims Handler (*Eläkeratkaisija*), Occupational Rehabilitation Specialist (*Kuntoutusasiantuntija*), Medical Case Coordinator (*Lääketieteellinen sihteeri*), Claims Team Lead.

**Key design decisions.**

| Decision | Rationale |
|---|---|
| Read tools on agent: `pdis_get_claim_dossier`, `pdis_verify_qualifying_months`, `pdis_assess_rehab_eligibility`, `pdis_get_medical_summary` | Prefixed `pdis_` for instance uniqueness; bounded, domain-specific read tools. |
| Write tool `pdis_dispatch_referral` behind approval flow | Submitting an official referral to the Medical Board / Chief Medical Officer requires claims handler sign-off. |
| Flow name: `pdis_refer_claim` | Governed approval flow with dual-action form (Refer to CMO / Refer to Vocational Rehab / Deny). |
| Knowledge base name: `pension_disability_policy` | 4 `.txt` policy files (`DIS-POL-01` to `DIS-POL-04`) detailing statutory medical thresholds and rehab subsidy rules. |
| Static mock world | 4 comprehensive claims cases covering full disability, rehab priority, workplace accident waiver, and contribution gap. |

**Mock world.**

| Case | Claimant / Query | Planted situation | Teaches |
|---|---|---|---|
| DIS-001 | "Evaluate disability claim for member CLM-701 (chronic severe neurological condition)" | Insured for 12 years, 58/60 contribution months met. Medical statement B confirms full permanent loss of work capacity (< 40% capacity). Prior rehab measures exhausted. | Straightforward full disability pension evaluation, validation of future period (*tuleva aika*) condition, direct medical board referral. |
| DIS-002 | "Member CLM-702 applying for disability pension following back surgery" | Insured 7 years, 36/60 months met. Medical report indicates significant recovery potential with modified ergonomic duties. No workplace trial attempted. | Statutory "Rehabilitation before pension" rule (`DIS-POL-02`): Agent prioritizes vocational rehabilitation (*työeläkekuntoutus* / työkokeilu) over early retirement. |
| DIS-003 | "Young worker CLM-703 claiming incapacity following a factory accident (only 14 months of work history)" | Insured only 14 months (fails standard 36-month condition). However, injury arose directly from a verified occupational accident (*työtapaturma*). | Statutory exception handling (`DIS-POL-04`): Waiting period waived for work-related accidents; agent validates accident documentation and approves eligibility check. |
| DIS-004 | "Member CLM-704 requesting disability pension after 4 years of uninsured residency abroad" | Member has only 8 contribution months in the last 60 months (fails the 36/60 rule). No bilateral social security treaty applies. | Red herring / clear refusal: Agent detects missing qualifying insurance months, explains lack of *tuleva aika* coverage, and provides information on Kela national disability pension. |

---

## Sub-Tasks

### Sub-Task 1: Mock data and read-only tools
- **Intent**: Create static Python datasets and `@tool` functions for claim dossiers, insurance periods, medical summaries, and vocational rehab assessments.
- **Expected Outcomes**:
  - `tools/pension_disability/data/` with `claimants.py`, `medical_dossiers.py`, `insurance_periods.py`.
  - `tools/pension_disability/pension_disability.py` containing `pdis_get_claim_dossier`, `pdis_verify_qualifying_months`, `pdis_assess_rehab_eligibility`, `pdis_get_medical_summary`.
  - `tools/pension_disability/requirements.txt` with `ibm-watsonx-orchestrate==2.18.2`.
  - Local Python test suite validating cases DIS-001 through DIS-004.
- **Relevant Context**: [`tools/incident_triage/incident_triage.py`](tools/incident_triage/incident_triage.py)
- **Status**: `[ ] pending`

### Sub-Task 2: Disability & rehabilitation policy knowledge base
- **Intent**: Author knowledge base YAML and plain text policy documents with stable document identifiers.
- **Expected Outcomes**:
  - `knowledge/pension-disability-triage/pension_disability_policy.yaml`.
  - `knowledge/pension-disability-triage/policies/`:
    - `DIS-POL-01-incapacity-criteria.txt`: Full vs. partial disability definitions, B-statement requirements, prognosis periods.
    - `DIS-POL-02-rehabilitation-priority.txt`: Statutory "Rehabilitation before Pension" mandate, workplace trials, retraining subsidies.
    - `DIS-POL-03-temporary-kuntoutustuki.txt`: Temporary cash rehabilitation allowance rules and treatment plan requirements.
    - `DIS-POL-04-qualifying-months-and-exceptions.txt`: 36/60-month rule, *tuleva aika* provisions, occupational accident waivers.
- **Relevant Context**: [`knowledge/customer-returns/customer_returns_policy.yaml`](knowledge/customer-returns/customer_returns_policy.yaml)
- **Status**: `[ ] pending`

### Sub-Task 3: Medical board referral flow
- **Intent**: Author a human-in-the-loop flow allowing the claims handler to review the triaged summary and authorize formal referral to the Medical Board / Chief Medical Officer or Vocational Rehab Unit.
- **Expected Outcomes**:
  - `flows/pension_disability/refer_medical_board.py` with Pydantic inputs and interactive review form.
  - Internal write tool `pdis_dispatch_referral` called strictly upon form approval.
- **Relevant Context**: [`flows/incident_triage/request_remediation.py`](flows/incident_triage/request_remediation.py)
- **Status**: `[ ] pending`

### Sub-Task 4: Agent YAML, README and manifest
- **Intent**: Configure the ReAct agent, instructions, evidence citation constraints, and scenario manifest.
- **Expected Outcomes**:
  - `agents/pension-disability-triage/agent.yaml` with clinical triage protocol, required evidence checks, and citation rules.
  - `agents/pension-disability-triage/README.md`.
  - `scenarios/pension-disability-triage/scenario.yaml` manifest.
- **Relevant Context**: [`agents/cloud-finops/agent.yaml`](agents/cloud-finops/agent.yaml)
- **Status**: `[ ] pending`

### Sub-Task 5: Ground truth and smoke evaluation
- **Intent**: Author ground truth checklist covering all 4 claim cases with diagnosis-only `smoke_prompts`.
- **Expected Outcomes**:
  - `evaluation/pension-disability-triage/ground_truth.json` with 4 case definitions and `smoke_prompts`.
- **Relevant Context**: [`evaluation/incident-triage/ground_truth.json`](evaluation/incident-triage/ground_truth.json)
- **Status**: `[ ] pending`

### Sub-Task 6: Demo walkthrough script and interactive slides
- **Intent**: Author demo walkthrough script and presentation slide matching sidebar position 8.
- **Expected Outcomes**:
  - `docs/demo/pension-disability-triage-demo.md`.
  - `docs/demo/scenarios/pension-disability-triage.js` with `.fit-card` (Industry: Finnish Statutory Pension / Työeläke, Function: Disability Claims & Occupational Health, Roles: Disability Claims Handler, Rehabilitation Specialist, Medical Reviewer).
  - Registered script tag in `docs/demo/presentation.html`.
- **Relevant Context**: [`docs/demo/scenarios/release-readiness.js`](docs/demo/scenarios/release-readiness.js), [`docs/demo/presentation.html`](docs/demo/presentation.html)
- **Status**: `[ ] pending`

### Sub-Task 7: Validation and dry-run smoke testing
- **Intent**: Validate scenario consistency and verify dry-run smoke prompts.
- **Expected Outcomes**:
  - `python wxodemo.py validate pension-disability-triage` passes with `OK`.
  - `python wxodemo.py smoke pension-disability-triage --dry-run` displays valid prompt sequences.
- **Relevant Context**: [`src/wxodemo/validate.py`](src/wxodemo/validate.py)
- **Status**: `[ ] pending`
