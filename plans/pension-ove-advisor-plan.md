# Partial Early Old-Age Pension Advisor (OVE) - Plan

> Scenario 7 in the presentation sidebar.
> Scenario id: `pension-ove-advisor` | Package: `pension_ove` | Sidebar position: 7 | Status: `soon`

## Top-Level Overview

**Goal.** Demonstrate an expert pension advisory agent for Finnish statutory earnings-related pension institutions (TyEL/YEL/JuEL providers like Varma, Ilmarinen, Elo, Veritas, Keva). The agent guides members through evaluating a **Partial Early Old-Age Pension** (*Osittainen varhennettu vanhuuseläke - OVE*), calculating 25% vs 50% early withdrawal options, applying the permanent 0.4%/month actuarial reduction (*varhennusvähennys*), simulating ongoing work earnings with continuing 1.5% annual pension accrual, and routing a formal OVE application through a human-governed approval flow.

**Why it passes the agent-washing test.** Inquiries from members approaching retirement age are unstructured and involve multiple personal variables: birth year/cohort (determining the lowest statutory OVE age threshold), choice of 25% or 50% draw percentage, planned future monthly salary, and expected retirement timeline. The agent conducts progressive discovery, disambiguates member scenarios, cross-references pension laws and life expectancy coefficients (*elinaikakerroin*), and computes custom simulations. The deterministic and legally binding step (locking in the OVE election and generating an official pension decision) is strictly routed through an approval flow.

**Target Fit & Audience.**
- **Industry:** Finnish Statutory Pension Insurance / Earnings-Related Pension Funds (*Työeläkeala*).
- **Function:** Pension Advisory, Customer Service & Benefit Calculations (*Eläkeneuvonta ja -laskenta*).
- **Target Roles:** Pension Advisory Specialist (*Eläkeneuvoja*), Customer Service Officer, Benefits Operations Lead.

**Key design decisions.**

| Decision | Rationale |
|---|---|
| Read tools on agent: `ove_get_member_profile`, `ove_get_accrued_pension`, `ove_calculate_reduction`, `ove_simulate_combined_income` | Prefixed `ove_` for WXO instance uniqueness; focused, bounded toolset under the 8-tool target. |
| Write tool `ove_create_application_record` behind an approval flow | Never attached directly to agent; formal submission requires member verification and sign-off. |
| Flow name: `ove_submit_application` | Governed flow with interactive Approve / Reject form for formal application filing. |
| Knowledge base name: `pension_ove_policy` | 4 `.txt` policy files (`OVE-POL-01` to `OVE-POL-04`) with symptom $\rightarrow$ procedure structure and stable document IDs. |
| Static mock world | 4 deterministic member cases with varied birth cohorts, salary plans, and planted constraints. |

**Mock world.**

| Case | Member query | Planted situation | Teaches |
|---|---|---|---|
| OVE-001 | "I turn 62 next month and want to take 50% OVE while continuing my full-time job. What will my monthly income look like?" | Age 62 (born 1964), accrued pension €2,400/mo, 24 months before target retirement age (64y). 50% draw = €1,200 baseline minus 9.6% reduction (€1,084.80/mo OVE) + continuing salary €4,200/mo. | Standard 50% OVE calculation, actuarial penalty formula, continuing 1.5% accrual explanation. |
| OVE-002 | "Can I take 25% OVE now? I'm 59 years old and working as a teacher." | Born 1966. Minimum OVE age for cohort 1966 is 62 years. Currently under age threshold (ineligible). | Strict eligibility boundary enforcement, clear policy citation (`OVE-POL-01`), constructive future timeline guidance. |
| OVE-003 | "Should I take 25% or 50% OVE? I plan to cut my working hours to 80% (salary €2,800/mo)." | Age 63 (born 1963), accrued pension €3,000/mo, 12 months early. Comparison: 25% draw (€714/mo net OVE) vs 50% draw (€1,428/mo net OVE) + reduced work income. | Multi-option comparison simulation, trade-off analysis, life-long reduction impact. |
| OVE-004 | "I am already receiving a disability pension (kuntoutustuki) and want to apply for OVE." | Member actively receives full temporary disability pension. Statutory rule: OVE cannot be granted concurrently with disability pension. | Red herring / conflict detection: agent identifies conflicting active benefit from profile and explains statutory restriction (`OVE-POL-02`). |

---

## Sub-Tasks

### Sub-Task 1: Mock data and read-only tools
- **Intent**: Build static Python mock data and `@tool` functions for member profiles, accrued earnings, actuarial reduction calculations, and combined income simulation.
- **Expected Outcomes**:
  - `tools/pension_ove/data/` with `members.py`, `accruals.py`, `cohort_tables.py`.
  - `tools/pension_ove/pension_ove.py` containing `ove_get_member_profile`, `ove_get_accrued_pension`, `ove_calculate_reduction`, `ove_simulate_combined_income`.
  - `tools/pension_ove/requirements.txt` with `ibm-watsonx-orchestrate==2.18.2`.
  - Direct local Python unit test script verifying calculations against OVE-001 to OVE-004.
- **Relevant Context**: [`tools/incident_triage/incident_triage.py`](tools/incident_triage/incident_triage.py)
- **Status**: `[x] done` — tools implemented with mock members, accruals, cohort tables, and verified with local Python tests.

### Sub-Task 2: OVE policy knowledge base
- **Intent**: Create knowledge base YAML configuration and plain text policy files (`.txt`) with stable document identifiers.
- **Expected Outcomes**:
  - `knowledge/pension-ove-advisor/pension_ove_policy.yaml`.
  - `knowledge/pension-ove-advisor/policies/`:
    - `OVE-POL-01-cohort-age-limits.txt`: Lowest OVE eligibility age brackets by birth cohort (1958–1967+).
    - `OVE-POL-02-draw-percentages-and-rules.txt`: 25% and 50% draw rules, irreversibility, concurrent pension restrictions (disability/old-age).
    - `OVE-POL-03-actuarial-reduction-and-accrual.txt`: 0.4%/month permanent reduction formula, post-OVE 1.5% annual work accrual.
    - `OVE-POL-04-taxation-and-life-expectancy.txt`: Life expectancy coefficient (*elinaikakerroin*) application and taxation principles.
- **Relevant Context**: [`knowledge/customer-returns/customer_returns_policy.yaml`](knowledge/customer-returns/customer_returns_policy.yaml)
- **Status**: `[x] done` — KB YAML and 4 policy documents created with stable identifiers and symptoms $\rightarrow$ procedure structure.

### Sub-Task 3: Governed application approval flow
- **Intent**: Author a human-in-the-loop approval flow that allows the member or advisor to formally submit an OVE election after reviewing the simulated reduction and amounts.
- **Expected Outcomes**:
  - `flows/pension_ove/submit_ove_application.py` using Pydantic input models and dual-outcome approval form (Approve / Reject).
  - Internal write tool `ove_create_application_record` called only upon form approval.
- **Relevant Context**: [`flows/incident_triage/request_remediation.py`](flows/incident_triage/request_remediation.py)
- **Status**: `[x] done` — flow `ove_submit_application` implemented with Approve and Reject paths.

### Sub-Task 4: Agent YAML, README and manifest
- **Intent**: Configure the native ReAct agent, detailed instructions, evidence citation rules, and scenario manifest.
- **Expected Outcomes**:
  - `agents/pension-ove-advisor/agent.yaml` with systematic advice methodology, required tool calling sequence, and strict policy citations.
  - `agents/pension-ove-advisor/README.md`.
  - `scenarios/pension-ove-advisor/scenario.yaml` manifest.
- **Relevant Context**: [`agents/cloud-finops/agent.yaml`](agents/cloud-finops/agent.yaml)
- **Status**: `[x] done` — agent instructions, README, and manifest configured with status `live`.

### Sub-Task 5: Ground truth and smoke evaluation
- **Intent**: Author ground truth checklist covering all 4 mock cases with diagnosis-only `smoke_prompts`.
- **Expected Outcomes**:
  - `evaluation/pension-ove-advisor/ground_truth.json` with 4 case definitions and `smoke_prompts`.
- **Relevant Context**: [`evaluation/incident-triage/ground_truth.json`](evaluation/incident-triage/ground_truth.json)
- **Status**: `[x] done` — ground truth with 4 cases and 4 smoke prompts created.

### Sub-Task 6: Demo walkthrough script and interactive slides
- **Intent**: Author demo walkthrough script and presentation slide matching sidebar position 7.
- **Expected Outcomes**:
  - `docs/demo/pension-ove-advisor-demo.md`.
  - `docs/demo/scenarios/pension-ove-advisor.js` with `.fit-card` (Industry: Finnish Statutory Pension / Työeläke, Function: Pension Advisory & Benefit Calculation, Roles: Pension Advisor, Benefits Specialist).
  - Registered script tag in `docs/demo/presentation.html`.
- **Relevant Context**: [`docs/demo/scenarios/customer-returns.js`](docs/demo/scenarios/customer-returns.js), [`docs/demo/presentation.html`](docs/demo/presentation.html)
- **Status**: `[x] done` — 6-scene demo script and 6-slide presentation created with matching prompts.

### Sub-Task 7: Validation and dry-run smoke testing
- **Intent**: Validate scenario consistency and verify dry-run smoke prompts.
- **Expected Outcomes**:
  - `python wxodemo.py validate pension-ove-advisor` passes with `OK`.
  - `python wxodemo.py smoke pension-ove-advisor --dry-run` displays valid prompt sequences.
- **Relevant Context**: [`src/wxodemo/validate.py`](src/wxodemo/validate.py)
- **Status**: `[x] done` — validation passes and smoke dry-run confirms all 4 prompts.
