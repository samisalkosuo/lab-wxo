# Scenario Target Fit & Audience Overview Plan

## Top-Level Overview
Add a dedicated "Target Fit & Audience" card directly below the challenge callout banner on Slide 1 (Overview) for each of the 6 demo scenarios in `presentation.html` and `docs/demo/scenarios/*.js`. This metadata specifies where and for whom the scenario is a good fit, covering **Industry** (e.g. specific vertical or explicitly "Cross-Industry"), **Function** (business / operational function), and most common **Target Roles**. The home catalog page tiles remain untouched.

---

## Sub-Tasks

### Sub-Task 1: Add Fit Card Styling to Presentation Template
- **Intent**: Define clean, theme-aligned CSS classes in `docs/demo/presentation.html` for rendering the Target Fit card (industry, function, roles pills/badges) with responsive grid layout and dark-theme contrast.
- **Expected Outcomes**:
  - CSS styles added for `.fit-card`, `.fit-group`, `.fit-label`, `.fit-value`, `.fit-pills`, and `.fit-pill`.
  - Consistent typography, badge colors, and spacing matching IBM Carbon-inspired theme variables in `presentation.html`.
- **Todo List**:
  1. Inspect CSS section of [`docs/demo/presentation.html`](docs/demo/presentation.html) around line 680 (near `.callout-banner`).
  2. Add styles for `.fit-card` and its sub-elements supporting multi-column layout for Industry, Function, and Roles.
- **Relevant Context**: [`docs/demo/presentation.html`](docs/demo/presentation.html)
- **Status**: [x] done

---

### Sub-Task 2: Add Target Fit to Incident Triage Overview Slide
- **Intent**: Update Slide 1 of Incident Triage scenario with target fit information.
- **Expected Outcomes**:
  - Fit card placed directly under `.callout-banner` in [`docs/demo/scenarios/incident-triage.js`](docs/demo/scenarios/incident-triage.js).
  - Industry: `Cross-Industry` (Any organization operating cloud / microservice workloads).
  - Function: `Site Reliability Engineering (SRE) & IT Operations`.
  - Roles: `Site Reliability Engineer (SRE)`, `Incident Commander`, `DevOps Engineer`, `IT Operations Manager`.
- **Todo List**:
  1. Edit slide 1 `render()` template in [`docs/demo/scenarios/incident-triage.js`](docs/demo/scenarios/incident-triage.js) to insert `.fit-card` below `.callout-banner`.
- **Relevant Context**: [`docs/demo/scenarios/incident-triage.js`](docs/demo/scenarios/incident-triage.js)
- **Status**: [x] done

---

### Sub-Task 3: Add Target Fit to Customer Returns Overview Slide
- **Intent**: Update Slide 1 of Customer Returns scenario with target fit information.
- **Expected Outcomes**:
  - Fit card placed directly under `.callout-banner` in [`docs/demo/scenarios/customer-returns.js`](docs/demo/scenarios/customer-returns.js).
  - Industry: `Retail, E-Commerce & Consumer Goods`.
  - Function: `Customer Service & Post-Purchase Operations`.
  - Roles: `Customer Support Agent`, `Support Lead / Supervisor`, `E-Commerce Operations Specialist`, `Store / Customer Experience Manager`.
- **Todo List**:
  1. Edit slide 1 `render()` template in [`docs/demo/scenarios/customer-returns.js`](docs/demo/scenarios/customer-returns.js) to insert `.fit-card` below `.callout-banner`.
- **Relevant Context**: [`docs/demo/scenarios/customer-returns.js`](docs/demo/scenarios/customer-returns.js)
- **Status**: [x] done

---

### Sub-Task 4: Add Target Fit to Release Readiness Overview Slide
- **Intent**: Update Slide 1 of Release Readiness scenario with target fit information.
- **Expected Outcomes**:
  - Fit card placed directly under `.callout-banner` in [`docs/demo/scenarios/release-readiness.js`](docs/demo/scenarios/release-readiness.js).
  - Industry: `Cross-Industry` (Software development, SaaS, enterprise digital products).
  - Function: `Software Delivery, Quality Assurance (QA) & DevSecOps`.
  - Roles: `Release Manager`, `QA Lead / Test Architect`, `Security Compliance Officer`, `DevOps / Engineering Lead`.
- **Todo List**:
  1. Edit slide 1 `render()` template in [`docs/demo/scenarios/release-readiness.js`](docs/demo/scenarios/release-readiness.js) to insert `.fit-card` below `.callout-banner`.
- **Relevant Context**: [`docs/demo/scenarios/release-readiness.js`](docs/demo/scenarios/release-readiness.js)
- **Status**: [x] done

---

### Sub-Task 5: Add Target Fit to Cloud FinOps Overview Slide
- **Intent**: Update Slide 1 of Cloud FinOps scenario with target fit information.
- **Expected Outcomes**:
  - Fit card placed directly under `.callout-banner` in [`docs/demo/scenarios/cloud-finops.js`](docs/demo/scenarios/cloud-finops.js).
  - Industry: `Cross-Industry` (Any enterprise running public or hybrid cloud infrastructure).
  - Function: `Cloud Financial Operations (FinOps) & Infrastructure Engineering`.
  - Roles: `FinOps Practitioner / Analyst`, `Cloud Solutions Architect`, `Engineering Budget Owner`, `IT Infrastructure Lead`.
- **Todo List**:
  1. Edit slide 1 `render()` template in [`docs/demo/scenarios/cloud-finops.js`](docs/demo/scenarios/cloud-finops.js) to insert `.fit-card` below `.callout-banner`.
- **Relevant Context**: [`docs/demo/scenarios/cloud-finops.js`](docs/demo/scenarios/cloud-finops.js)
- **Status**: [x] done

---

### Sub-Task 6: Add Target Fit to HR Onboarding Overview Slide
- **Intent**: Update Slide 1 of HR Onboarding scenario with target fit information.
- **Expected Outcomes**:
  - Fit card placed directly under `.callout-banner` in [`docs/demo/scenarios/hr-onboarding.js`](docs/demo/scenarios/hr-onboarding.js).
  - Industry: `Cross-Industry` (Organizations managing employee lifecycle & IT provisioning).
  - Function: `Human Resources (HR Operations) & Identity / IT Provisioning`.
  - Roles: `HR Operations Coordinator`, `IT Access & Identity Administrator`, `Hiring Manager`, `HR Compliance Officer`.
- **Todo List**:
  1. Edit slide 1 `render()` template in [`docs/demo/scenarios/hr-onboarding.js`](docs/demo/scenarios/hr-onboarding.js) to insert `.fit-card` below `.callout-banner`.
- **Relevant Context**: [`docs/demo/scenarios/hr-onboarding.js`](docs/demo/scenarios/hr-onboarding.js)
- **Status**: [x] done

---

### Sub-Task 7: Add Target Fit to Travel Request Overview Slide
- **Intent**: Update Slide 1 of Travel Request scenario with target fit information.
- **Expected Outcomes**:
  - Fit card placed directly under `.callout-banner` in [`docs/demo/scenarios/travel-request.js`](docs/demo/scenarios/travel-request.js).
  - Industry: `Public Sector, Higher Education & Regulated Enterprise` (Organizations with statutory travel regulations and per-diem rules).
  - Function: `Finance, Travel Administration & Corporate Governance`.
  - Roles: `Travel Coordinator / Expense Administrator`, `Department Manager / Cost-Center Approver`, `Finance Manager`, `Compliance Officer`.
- **Todo List**:
  1. Edit slide 1 `render()` template in [`docs/demo/scenarios/travel-request.js`](docs/demo/scenarios/travel-request.js) to insert `.fit-card` below `.callout-banner`.
- **Relevant Context**: [`docs/demo/scenarios/travel-request.js`](docs/demo/scenarios/travel-request.js)
- **Status**: [x] done

---

### Sub-Task 8: Verification & Visual Polish
- **Intent**: Verify that all 6 overview slides render correctly in the presentation deck without visual regression, overflowing elements, or console errors.
- **Expected Outcomes**:
  - Slide 1 of each scenario displays the fit card properly positioned directly below the challenge callout banner.
  - Home catalog view is unaffected and retains its clean scenario tile grid.
  - Sidebar slide count, navigation, and other slide templates continue to work seamlessly.
- **Todo List**:
  1. Review HTML / JavaScript syntax across all modified files.
  2. Verify consistency of tags, styles, and role chips across all 6 scenarios.
- **Relevant Context**: [`docs/demo/presentation.html`](docs/demo/presentation.html), [`docs/demo/scenarios/*.js`](docs/demo/scenarios/)
- **Status**: [x] done
