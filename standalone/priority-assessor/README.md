# priority_assessor — Priority Assessor Agent

## Purpose

`priority_assessor` assigns a structured priority level (`Critical`, `High`, `Medium`, `Low`)
to any incoming item — IT incident, manufacturing defect, logistics disruption, citizen
report, or customer complaint — and returns a strict JSON object with the priority,
confidence score, grounded rationale, recommended next action, and whether configured
or default rules were applied.

The agent operates in two modes:

- **Default mode** (no rules supplied): applies built-in common-sense defaults based on
  safety risk, user/customer impact scale, financial exposure, and domain signal words.
- **Configured mode** (rules supplied in the prompt): applies the user's explicit priority
  criteria literally, mapping them to `Critical / High / Medium / Low`.

This makes it a cross-industry demonstration agent — the same agent can prioritise
citizen reports for a city portal, defects for a factory QA team, service desk tickets
for IT operations, or complaints for a customer success team.

## What this agent does

- Accepts any free-form item text (single sentence through full report document).
- Optionally accepts user-supplied priority rules as plain text in any format.
- Returns strictly valid JSON with keys `priority`, `confidence`, `rationale`,
  `next_action`, and `rules_used`.
- Grounds rationale exclusively in facts stated in the item text — never invents
  or hallucinate values.
- Asks one clarifying question when the item provides too little information to
  evaluate above 0.30 confidence.
- Defends against prompt injection: embedded commands inside item text are ignored.

## What this agent does not do

- Does not write, approve, or execute any action on behalf of the user.
- Does not connect to external ticketing, ERP, or CRM systems.
- Does not output conversational text or explanations outside the JSON payload.
- Does not manage or persist priority assignments across sessions.

## Dependencies

None. No knowledge base, no tools, no connections. The agent uses
`groq/openai/gpt-oss-120b`. Verify it is available with:

```bash
orchestrate models list
```

## Sample documents

The `sample-docs/` directory contains realistic example documents for five domains,
two per domain:

| File | Domain | Expected default priority |
|---|---|---|
| `manufacturing_defect_bearing_failure_20250312.md` | Manufacturing | Critical |
| `manufacturing_defect_paint_cosmetic_20250408.md` | Manufacturing | Low |
| `logistics_disruption_cold_chain_pharma_20250519.md` | Logistics | Critical |
| `logistics_disruption_parcel_delay_20250602.md` | Logistics | Low |
| `it_incident_banking_outage_20250715.md` | IT | Critical |
| `it_incident_hr_portal_payslip_20250821.md` | IT | Medium |
| `citizen_report_gas_leak_20250903.md` | Citizen | Critical |
| `citizen_report_overgrown_vegetation_20251004.md` | Citizen | Low |
| `customer_complaint_product_safety_20250614.md` | Customer | Critical |
| `customer_complaint_app_dark_mode_20250709.md` | Customer | Low |

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy priority_assessor

# Or manually:
orchestrate agents import --file standalone/priority-assessor/agent.yaml
orchestrate agents deploy --name priority_assessor
```

Re-running import is safe — it updates in place.

## Teardown

```bash
python wxodemo.py undeploy priority_assessor

# Or manually:
orchestrate agents remove --name priority_assessor --kind native
```

## Known limits

| Limit | Detail |
|---|---|
| Four-level scale only | Priority is always one of Critical / High / Medium / Low, regardless of configured rule labels. User-defined labels (e.g., P1/P2/P3, SEV1/SEV2) are mapped to these four levels in rationale but the `priority` key always uses the canonical names. |
| No persistence | Priority assessments are not stored; each conversation turn is independent. |
| Single-item evaluation | Designed for one item per prompt. Batch ranking across multiple items is not supported in a single turn. |
| LLM-bound accuracy | Confidence scores and rationale quality depend on the model. Downstream consumers should treat confidence < 0.60 as uncertain. |
| Not verified by a live run | The instructions have not been exercised against a live instance. Test default and configured paths, clarification prompts, and prompt injection defence before relying on it in production. |

## Examples

See [`examples.md`](examples.md) for 28 prompts covering all five domains, both modes,
edge cases, and prompt injection defence — including full document text ready to paste.
