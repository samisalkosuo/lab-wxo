# Entrepreneur YEL Confirmed Work Income Review - Plan

> Scenario 9 in the presentation sidebar.
> Scenario id: `yel-income-assessment` | Package: `yel_income` | Sidebar position: 9 | Status: `soon`

## Top-Level Overview

**Goal.** Demonstrate an entrepreneur pension and social security advisory agent for Finnish statutory pension institutions (TyEL/YEL providers). The agent assists YEL underwriters (*YEL-ratkaisija*) and self-employed entrepreneurs (*yrittäjät*) in conducting statutory triennial **YEL Confirmed Work Income Reviews** (*YEL-työtulon tarkistus*). It evaluates the business's sector median wage benchmarks (ETK / Statistics Finland data), applies the statutory €4,000 transition adjustment cap (*korotuskatto*), analyzes the direct impact of YEL income on social security safety nets (sickness allowance, parental benefits, unemployment security, future pension), and issues an official administrative determination via a human-governed approval flow.

**Why it passes the agent-washing test.** YEL income determinations are among the most contested and nuanced processes in the Finnish pension sector. Entrepreneurs present complex, multi-faceted business situations: seasonal fluctuations, split roles (e.g. part-time software development and part-time manual labor), holding company dividends vs. active operational hours, and subcontracting cost deductions. A simple algorithmic lookup cannot handle the natural language dispute or evaluate the reasonableness of self-reported work input. The agent dialogues with the user, assesses realistic wage equivalents, models social benefit repercussions, and prepares a balanced proposal. The formal issuance of a legally appealable administrative decision (*valituskelpoinen päätös*) is strictly routed through an approval flow.

**Target Fit & Audience.**
- **Industry:** Finnish Statutory Pension Insurance / Self-Employed Social Insurance (*YEL-vakuutus*).
- **Function:** YEL Underwriting, Entrepreneur Advisory & Insurance Policy Management (*YEL-vakuutuspalvelut*).
- **Target Roles:** YEL Underwriter / Case Handler (*YEL-ratkaisija*), Entrepreneur Account Specialist (*Yrittäjäneuvoja*), Insurance Operations Supervisor.

**Key design decisions.**

| Decision | Rationale |
|---|---|
| Read tools on agent: `yel_get_business_profile`, `yel_get_sector_benchmark`, `yel_calculate_income_recommendation`, `yel_estimate_social_benefits` | Prefixed `yel_` for WXO uniqueness; compact, highly relevant financial calculation tools. |
| Write tool `yel_issue_decision_record` behind an approval flow | Formal statutory decisions require underwriter sign-off before official dispatch. |
| Flow name: `yel_issue_decision` | Governed flow with dual-action form (Confirm Proposed Income / Adjust & Issue / Escalate to Appeals). |
| Knowledge base name: `yel_income_policy` | 4 `.txt` policy files (`YEL-POL-01` to `YEL-POL-04`) detailing YEL legislation guidelines and transition caps. |
| Static mock world | 4 distinct entrepreneur profiles with varied turnovers, sector benchmarks, and dispute cases. |

**Mock world.**

| Case | Entrepreneur / Query | Planted situation | Teaches |
|---|---|---|---|
| YEL-001 | "Evaluate YEL income review for IT Consultant ENT-801 (current työtulo €18,000/yr, turnover €95,000/yr)" | Full-time sole proprietor in software consulting (sector median €46,000/yr). Prior income was €18,000/yr. Statutory €4,000 review cap restricts mandatory adjustment to €22,000/yr. | Application of statutory €4,000 transition ceiling (`YEL-POL-02`), calculation of new monthly YEL premium and increased daily sickness allowance. |
| YEL-002 | "Artisan bakery owner ENT-802 contesting proposed €38,000 YEL income" | High revenue (€140,000) but heavily reliant on raw ingredients and 3 hired bakery assistants; owner works 20h/wk managing logistics. True managerial wage equivalent is €26,000/yr. | Disambiguating turnover from owner's personal work input, clarifying hours and subcontracting expenses, adjusting recommendation to realistic wage level. |
| YEL-003 | "New startup founder ENT-803 inquiring about minimum YEL income and beginner discount" | First-time entrepreneur within first 48 months of operation. Qualified for statutory 22% beginner discount (*aloittavan yrittäjän alennus*). | Early-stage entrepreneur rules (`YEL-POL-03`), 22% discount calculation, explanation of statutory minimum floor (€9,010/yr). |
| YEL-004 | "Side-hustle freelancer ENT-804 with €5,200 annual revenue asking if YEL is mandatory" | Freelancer earning €5,200/yr (below the statutory YEL minimum threshold of €9,010/yr in 2024/2025). | Red herring / clear non-applicability: Agent identifies that income is below the mandatory YEL insurance threshold and explains voluntary insurance vs. non-obligation. |

---

## Sub-Tasks

### Sub-Task 1: Mock data and read-only tools
- **Intent**: Create static Python datasets and `@tool` functions for business profiles, sector wage statistics, income recommendation algorithms, and social benefit estimators.
- **Expected Outcomes**:
  - `tools/yel_income/data/` with `businesses.py`, `sector_benchmarks.py`, `benefit_formulas.py`.
  - `tools/yel_income/yel_income.py` containing `yel_get_business_profile`, `yel_get_sector_benchmark`, `yel_calculate_income_recommendation`, `yel_estimate_social_benefits`.
  - `tools/yel_income/requirements.txt` with `ibm-watsonx-orchestrate==2.18.2`.
  - Local Python test suite validating cases YEL-001 through YEL-004.
- **Relevant Context**: [`tools/incident_triage/incident_triage.py`](tools/incident_triage/incident_triage.py)
- **Status**: `[ ] pending`

### Sub-Task 2: YEL policy knowledge base
- **Intent**: Author knowledge base YAML and plain text policy documents with stable document identifiers.
- **Expected Outcomes**:
  - `knowledge/yel-income-assessment/yel_income_policy.yaml`.
  - `knowledge/yel-income-assessment/policies/`:
    - `YEL-POL-01-confirmed-income-definition.txt`: Value of work input definition, replacement wage principle, turnover vs. wage.
    - `YEL-POL-02-transition-cap-and-review.txt`: 2023 YEL reform rules, triennial review cycle, statutory €4,000 maximum increase cap.
    - `YEL-POL-03-social-security-linkage.txt`: Linkage to Kela sickness allowance, parental benefits, YTK/unemployment funds, beginner 22% discount.
    - `YEL-POL-04-right-of-reply-and-appeals.txt`: Opportunity to be heard (*kuuleminen*), acceptable evidence, appeal to TELK (Eläketurvalautakunta).
- **Relevant Context**: [`knowledge/customer-returns/customer_returns_policy.yaml`](knowledge/customer-returns/customer_returns_policy.yaml)
- **Status**: `[ ] pending`

### Sub-Task 3: Income determination approval flow
- **Intent**: Author a human-in-the-loop flow allowing the YEL underwriter to review the assessment, adjust the work input value, and authorize the formal administrative decision.
- **Expected Outcomes**:
  - `flows/yel_income/issue_income_decision.py` with Pydantic inputs and underwriter decision form.
  - Internal write tool `yel_issue_decision_record` called strictly upon underwriter approval.
- **Relevant Context**: [`flows/incident_triage/request_remediation.py`](flows/incident_triage/request_remediation.py)
- **Status**: `[ ] pending`

### Sub-Task 4: Agent YAML, README and manifest
- **Intent**: Configure the ReAct agent, instructions, evidence citation rules, and scenario manifest.
- **Expected Outcomes**:
  - `agents/yel-income-assessment/agent.yaml` with structured review protocol, mandatory tool usage sequence, and policy citation rules.
  - `agents/yel-income-assessment/README.md`.
  - `scenarios/yel-income-assessment/scenario.yaml` manifest.
- **Relevant Context**: [`agents/cloud-finops/agent.yaml`](agents/cloud-finops/agent.yaml)
- **Status**: `[ ] pending`

### Sub-Task 5: Ground truth and smoke evaluation
- **Intent**: Author ground truth checklist covering all 4 entrepreneur cases with diagnosis-only `smoke_prompts`.
- **Expected Outcomes**:
  - `evaluation/yel-income-assessment/ground_truth.json` with 4 case definitions and `smoke_prompts`.
- **Relevant Context**: [`evaluation/incident-triage/ground_truth.json`](evaluation/incident-triage/ground_truth.json)
- **Status**: `[ ] pending`

### Sub-Task 6: Demo walkthrough script and interactive slides
- **Intent**: Author demo walkthrough script and presentation slide matching sidebar position 9.
- **Expected Outcomes**:
  - `docs/demo/yel-income-assessment-demo.md`.
  - `docs/demo/scenarios/yel-income-assessment.js` with `.fit-card` (Industry: Finnish Statutory Pension / Työeläke & YEL, Function: YEL Underwriting & Entrepreneur Advisory, Roles: YEL Underwriter, Entrepreneur Specialist, Compliance Officer).
  - Registered script tag in `docs/demo/presentation.html`.
- **Relevant Context**: [`docs/demo/scenarios/cloud-finops.js`](docs/demo/scenarios/cloud-finops.js), [`docs/demo/presentation.html`](docs/demo/presentation.html)
- **Status**: `[ ] pending`

### Sub-Task 7: Validation and dry-run smoke testing
- **Intent**: Validate scenario consistency and verify dry-run smoke prompts.
- **Expected Outcomes**:
  - `python wxodemo.py validate yel-income-assessment` passes with `OK`.
  - `python wxodemo.py smoke yel-income-assessment --dry-run` displays valid prompt sequences.
- **Relevant Context**: [`src/wxodemo/validate.py`](src/wxodemo/validate.py)
- **Status**: `[ ] pending`
