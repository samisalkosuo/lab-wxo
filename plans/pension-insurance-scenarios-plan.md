# Finnish Pension Insurance Scenarios — Master Plan

> Overview and link index for the 3 Finnish Statutory Earnings-Related Pension Insurance (TyEL/YEL/JuEL) demo scenarios.

## Individual Scenario Plans

The detailed sub-tasks, mock data specifications, knowledge base policies, approval flows, and demo walkthrough plans are split into dedicated plan files:

1. **[`plans/pension-ove-advisor-plan.md`](pension-ove-advisor-plan.md)** (Scenario 7)
   - **ID:** `pension-ove-advisor` | **Package:** `pension_ove`
   - **Topic:** Partial Early Old-Age Pension (*Osittainen varhennettu vanhuuseläke - OVE*), 25% vs 50% draw options, 0.4%/mo actuarial penalty, 1.5% ongoing work accrual, and application sign-off flow.

2. **[`plans/pension-disability-triage-plan.md`](pension-disability-triage-plan.md)** (Scenario 8)
   - **ID:** `pension-disability-triage` | **Package:** `pension_disability`
   - **Topic:** Disability Pension (*Työkyvyttömyyseläke* & *Kuntoutustuki*) triage, statutory "Rehabilitation before Pension" (*kuntoutus ensin*) mandate, 36/60 contribution months check, and medical board referral flow.

3. **[`plans/yel-income-assessment-plan.md`](yel-income-assessment-plan.md)** (Scenario 9)
   - **ID:** `yel-income-assessment` | **Package:** `yel_income`
   - **Topic:** Entrepreneur YEL Confirmed Work Income (*YEL-työtulo*) triennial reviews, sector median wage benchmarks, €4,000 transition ceiling, social safety net impact modeling, and administrative resolution approval flow.

---

## Build Execution Order

Each scenario will be implemented following the standard 7-step build lifecycle from `wxo-scenario-authoring`:
1. Mock data and read-only Python tools
2. Knowledge base policy documents (`.txt`)
3. Human-governed approval flow & write tool
4. Native ReAct Agent YAML & README
5. Manifest & Ground Truth evaluation checklist
6. Demo walkthrough markdown & presentation slide
7. Validation (`python wxodemo.py validate <id>`) and smoke dry-run
