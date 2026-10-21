# Partial Early Old-Age Pension Advisor (OVE) Agent

An expert pension advisory agent for Finnish statutory earnings-related pension schemes (TyEL/JuEL/YEL/MYEL). The agent helps members explore taking a 25% or 50% **Partial Early Old-Age Pension** (*Osittainen varhennettu vanhuuseläke - OVE*), calculates statutory early reductions, simulates ongoing employment with 1.5% annual pension accrual, and files official applications through a human-governed approval flow.

## Tools

| Tool | Permission | Purpose |
|---|---|---|
| `ove_get_member_profile` | Read-only | Retrieves member DOB, birth cohort, employment, and active pension benefits. |
| `ove_get_accrued_pension` | Read-only | Fetches current total accrued earnings-related pension baseline. |
| `ove_calculate_reduction` | Read-only | Calculates 0.4%/mo actuarial penalty and life expectancy coefficient adjustment. |
| `ove_simulate_combined_income` | Read-only | Simulates combined monthly gross income and new 1.5%/yr TyEL work accrual. |
| `ove_submit_application` | Flow | Human-in-the-loop approval flow for formal OVE application submission. |

## Knowledge Base

- **`pension_ove_policy`**:
  - `OVE-POL-01`: Statutory cohort minimum age thresholds (1958–1967+).
  - `OVE-POL-02`: 25% and 50% draw rules, irreversibility, and disability pension exclusions.
  - `OVE-POL-03`: Permanent 0.4%/month reduction and continuing work 1.5% annual accrual.
  - `OVE-POL-04`: Life expectancy coefficient (*elinaikakerroin*) and progressive taxation guidance.

## Mock Data

| Member ID | Name | Birth Year | Status & Planted Context |
|---|---|---|---|
| `MEM-101` | Matti Virtanen | 1964 | Age 62, €2,400/mo accrued pension. Happy path 50% OVE with full-time salary continuation. |
| `MEM-102` | Liisa Korhonen | 1966 | Age 59, teacher. Under cohort minimum age threshold (62y required). |
| `MEM-103` | Antti Mäkinen | 1963 | Age 63, project manager. Multi-option simulation (25% vs 50% draw, 80% work hours). |
| `MEM-104` | Eeva Koskinen | 1962 | Age 63. Actively receiving full disability pension (Kuntoutustuki) — statutory conflict. |

## Known Limitations

- Stateless mock execution (does not connect to live Arek/ETK pension registers).
- Calculations use standard statutory formulas without voluntary individual pension contributions.
