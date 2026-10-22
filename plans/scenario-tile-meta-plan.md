# Plan: Add Industry & Function Meta to Scenario Tiles

## Overview

Add two small muted caption lines — **Industry** and **Function** — to each scenario tile on the home page of `docs/demo/presentation.html`. They appear directly under the scenario title (before the description text) using Option A placement. Scoped to scenario tiles only; standalone agent tiles are unchanged.

**Key insight:** The industry, function, and target roles values are **already authored** as HTML strings inside each scenario's overview slide (slide 0, inside the `.fit-card` `.fit-group` elements). The correct approach is to **hoist** these values to the top-level scenario object as plain-text fields, and have the existing overview slide HTML reference those fields — so the data is defined once and reused both in the tile and in the slide.

---

## Sub-Task 1 — Hoist `industry`, `function`, and `roles` to the top-level scenario object in each JS file

**Intent:** Move the industry/function/roles values from being hardcoded inside the slide HTML to being declared once as top-level fields on the scenario object. The slide's `.fit-value` elements then read from those fields. This makes the data single-sourced.

**Expected Outcomes:**
- All 9 scenario objects gain three new top-level fields: `industry`, `function`, `roles` (roles as an array of strings).
- The `.fit-value` HTML inside the overview slide's `.fit-card` is replaced with template references to those fields (e.g. `${scenario.industry}`).
- The rendered slide output is visually identical to what it is today.

**Todo List:**
- [ ] For each scenario file, extract the plain-text industry and function values from the `.fit-value` divs and add them as `industry` and `function` fields on the scenario object (after `description`, before `status`).
- [ ] Extract the `.fit-pill` strings into a `roles` array field on the scenario object.
- [ ] Update each overview slide's `.fit-card` HTML to reference `scenario.industry`, `scenario.function`, and `scenario.roles` instead of repeating the strings inline. For scenarios where the `.fit-value` contains an inline `<span>` sub-note (e.g. incident-triage, hr-onboarding, release-readiness, cloud-finops, pension-ove-advisor, yel-income-assessment), keep that sub-note HTML inside the slide template — the plain `industry` field carries only the primary text.
- [ ] Exact values to use (plain text, no HTML):
  - `incident-triage`: industry = `"Cross-Industry (Cloud & Digital Services)"`, function = `"Site Reliability Engineering (SRE) & IT Operations"`
  - `customer-returns`: industry = `"Retail, E-Commerce & Consumer Goods"`, function = `"Customer Service & Post-Purchase Operations"`
  - `hr-onboarding`: industry = `"Cross-Industry (Workforce & People Operations)"`, function = `"Human Resources (HR Ops) & IT Identity Provisioning"`
  - `release-readiness`: industry = `"Cross-Industry (Software Delivery & Enterprise IT)"`, function = `"Software Delivery, QA & DevSecOps Governance"`
  - `cloud-finops`: industry = `"Cross-Industry (Public & Hybrid Cloud Infrastructure)"`, function = `"Cloud FinOps & Infrastructure Cost Governance"`
  - `travel-request`: industry = `"Public Sector, Higher Education & Regulated Enterprise"`, function = `"Finance, Travel Administration & Expense Governance"`
  - `pension-disability-triage`: industry = `"Finnish Statutory Pension Insurance / Social Security"`, function = `"Disability Claims Management & Occupational Rehabilitation"`
  - `pension-ove-advisor`: industry = `"Finnish Statutory Pension Insurance"`, function = `"Pension Customer Advisory, Actuarial Calculations & Claims Processing"`
  - `yel-income-assessment`: industry = `"Finnish Statutory Pension Insurance (YEL)"`, function = `"YEL Underwriting & Entrepreneur Advisory"`

**Relevant Context:**
- All files in `docs/demo/scenarios/`
- The `.fit-card` block is at approximately lines 26–44 in each file (overview slide render function)
- Some `.fit-value` divs contain inline `<span>` sub-text with `font-size:12px; color:var(--text-muted)` — those are decorative; the plain-text field carries the primary label only
- The `roles` array feeds the `.fit-pills` block; each array entry becomes one `<span class="fit-pill">` element

**Status:** [x] done

---

## Sub-Task 2 — Add `.home-card-meta` CSS class to `presentation.html`

**Intent:** Define a reusable CSS class for the small muted caption text that renders the Industry and Function lines inside a scenario tile.

**Expected Outcomes:** `.home-card-meta` and `.home-card-meta-row` classes exist in the `<style>` block, using 11px font size and `var(--text-muted)` color.

**Todo List:**
- [ ] Insert the following CSS after the `.home-card-title` rule (around line 1099 in `presentation.html`):
  ```css
  .home-card-meta {
    margin-top: 5px;
    margin-bottom: 8px;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .home-card-meta-row {
    font-size: 11px;
    color: var(--text-muted);
    line-height: 1.4;
  }

  .home-card-meta-row strong {
    font-weight: 600;
    color: var(--text-muted);
  }
  ```

**Relevant Context:**
- CSS `<style>` block ends around line 1135 in `presentation.html`
- `.home-card-title` rule is at lines 1094–1099
- `--text-muted` is `#878d96` (dark) / `#697077` (light)

**Status:** [x] done

---

## Sub-Task 3 — Update the home page tile template in `presentation.html`

**Intent:** Render the two new meta lines inside the scenario tile using the now-available top-level `scenario.industry` and `scenario.function` fields.

**Expected Outcomes:** Each scenario tile shows two small muted lines directly under the title+badge row, before the description:
```
Industry: Retail, E-Commerce & Consumer Goods
Function: Customer Service & Post-Purchase Operations
```
Standalone agent tiles are unchanged.

**Todo List:**
- [ ] In the scenario tile template (lines 1517–1535 of `presentation.html`), insert a meta block between `.home-card-header` and `.home-card-desc`:
  ```js
  ${(scenario.industry || scenario.function) ? `
    <div class="home-card-meta">
      ${scenario.industry ? `<div class="home-card-meta-row"><strong>Industry:</strong> ${scenario.industry}</div>` : ''}
      ${scenario.function ? `<div class="home-card-meta-row"><strong>Function:</strong> ${scenario.function}</div>` : ''}
    </div>
  ` : ''}
  ```
- [ ] Verify the standalone agents tile block (lines 1545–1561) is **unchanged**

**Relevant Context:**
- Scenario tile template is at lines 1517–1535 in `presentation.html`
- Standalone agent template is at lines 1545–1561 — leave untouched
- Conditional guard ensures no layout breakage if a future scenario omits the fields

**Status:** [x] done
