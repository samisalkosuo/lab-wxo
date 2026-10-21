# YEL Income Assessment — Agent README

Demo scenario for statutory YEL (Yrittäjien eläkelaki) confirmed work income
triennial reviews in the Finnish self-employed pension insurance sector.

---

## Overview

The **YEL Income Assessment** agent assists YEL underwriters (*YEL-ratkaisija*)
and self-employed entrepreneurs (*yrittäjät*) in conducting the statutory
triennial review of a self-employed person's confirmed work income
(*YEL-työtulo*) under the 2023 YEL reform.

The agent evaluates the entrepreneur's sector median wage benchmark from
Statistics Finland / ETK, applies the statutory EUR 4,000 per-year transition
cap (*korotuskatto*), models the impact on Kela social security benefits, and
routes the formal administrative determination (*valituskelpoinen päätös*)
through the `yel_issue_decision` approval flow.

---

## Tools

| Tool | Attached to agent | Purpose |
|---|---|---|
| `yel_get_business_profile` | ✅ | Fetch entrepreneur profile: sector, revenue, current income, hours, employees |
| `yel_get_sector_benchmark` | ✅ | Fetch Statistics Finland / ETK sector median wage and statutory thresholds |
| `yel_calculate_income_recommendation` | ✅ | Apply statutory rules: median, hours ratio, EUR 4,000 cap, beginner discount |
| `yel_estimate_social_benefits` | ✅ | Estimate sickness allowance, parental allowance, unemployment allowance, pension accrual |
| `yel_issue_decision_record` | ❌ (flow only) | Write the formal determination record — called only by `yel_issue_decision` flow |

The `yel_issue_decision` flow is the governance gate. The agent calls the flow;
the flow presents the proposal to the underwriter for sign-off before issuing
any formal record.

---

## Knowledge Base

| Document ID | File | Content |
|---|---|---|
| `YEL-POL-01` | `YEL-POL-01-confirmed-income-definition.txt` | Wage-replacement principle, mandatory threshold (EUR 9,010/yr), evidence rules |
| `YEL-POL-02` | `YEL-POL-02-transition-cap-and-review.txt` | 2023 reform triennial review cycle, EUR 4,000 transition cap |
| `YEL-POL-03` | `YEL-POL-03-social-security-linkage.txt` | Kela benefit linkage, 22 % beginner discount |
| `YEL-POL-04` | `YEL-POL-04-right-of-reply-and-appeals.txt` | Right of reply (kuuleminen), appeals to TELK, formal decision requirements |

---

## Mock World

| Case | Entrepreneur | Situation | Teaches |
|---|---|---|---|
| ENT-801 | Aleksi Mäkinen, IT consultant | Full-time (45 h/wk), revenue EUR 95k, current income EUR 18k, sector median EUR 46k | Transition cap: increase capped at EUR 22k (+EUR 4k), not full median |
| ENT-802 | Kaisa Virtanen, bakery owner | Revenue EUR 140k but works only 20 h/wk managing; 3 staff do production | Part-time hours reduce benchmark target; dispute resolution: owner input ≠ turnover |
| ENT-803 | Juhani Korhonen, startup founder | 19 months insured, revenue EUR 28k, beginner period | Beginner 22 % discount; cap applied (EUR 14k → EUR 18k) |
| ENT-804 | Meri Leinonen, freelance photographer | Revenue EUR 5,200 (below EUR 9,010 threshold) | Red herring / non-applicability: YEL not mandatory |

---

## Limitations (not tested live)

- The approval flow (`yel_issue_decision`) has not been run in a browser UI.
  The Confirm / Adjust & Issue / Escalate buttons have not been clicked in a live WXO instance.
- The agent has not been deployed or smoke-tested against a live WXO instance.
- The beginner discount applies to the premium only; the benefit base uses the
  full income. This is a policy rule, not a demo simplification.
- Benefit estimates are illustrative approximations (2024/2025 figures).
  Actual Kela amounts differ based on individual circumstances and income ceilings.
- Only four entrepreneur profiles are loaded. Other IDs return a NOT_FOUND error.
- The tool recommendation logic uses a proportional hours adjustment.
  Real YEL assessments also consider specialisation, experience, and market position.
