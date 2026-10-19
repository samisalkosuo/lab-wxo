# Travel Request Agent

Decides whether an employee's planned business trip may go ahead. The user writes in English. The agent answers **APPROVED**, **NEEDS APPROVAL** (manager or director) or **DENIED**, with reasons, an estimated reimbursement, and, after a human approves, a **request id** that other apps or agents can use for booking and expense claims. It does not book trips, process expense claims or pay anything.

The source of the state travel rules is a Finnish document, *Valtion matkustussääntö 2026*. The agent searches it with Finnish queries and cites it in Finnish (for example `Valtion matkustussääntö 2026, 13 §`). It never presents a translation of the document as a quotation. The approval levels come from a short **fictional** agency policy written in English for this demo.

## Files

- `agent.yaml` -- agent definition
- `../../tools/travel_request/travel_request.py` -- Python tool package (5 tools, one of them internal)
- `../../tools/travel_request/data/` -- mock employees, budgets, hand-keyed 2026 rates, approval rules
- `../../knowledge/travel-request/` -- the two knowledge bases and the PDF
- `../../flows/travel_request/travel_submit_request.py` -- approval flow
- `../../evaluation/travel-request/ground_truth.json` -- smoke prompts and expected outcomes

## Tools attached (4 tools, 1 flow)

| Tool | Kind | Purpose |
|---|---|---|
| `travel_get_employee_profile` | Python | Grade, manager and cost center for an employee id or name |
| `travel_get_budget_status` | Python | Compares an estimated cost with the remaining 2026 budget of a cost center |
| `travel_get_per_diem_rate` | Python | Foreign per diem for a country (small hand-keyed subset of the annex) |
| `travel_estimate_reimbursement` | Python | Deterministic estimate: per diem, free-meal reduction, own-car mileage with the cheapest-mode cap, tickets, lodging |
| `travel_submit_request` | Flow | Approval form, then issues the request id on Approve |

**Not attached:** `travel_issue_request_id` is called only by the `travel_submit_request` flow after a human approves. It also re-checks the traveler, the estimate and the approval level against the mock data and refuses leisure trips and 2027 trips.

## Knowledge bases

| Name | Content | Language |
|---|---|---|
| `travel_state_rules` | `VM_2025_63.pdf`, *Valtion matkustussääntö 2026* (Valtiovarainministeriön julkaisuja 2025:63), unmodified | Finnish |
| `travel_agency_policy` | Six fictional policy documents: TP-AUTH-01, TP-APPR-01, TP-BUDGET-01, TP-PURPOSE-01, TP-ABROAD-01, TP-HANDOFF-01 (`.txt`) | English |

Both use the embedding model `ibm/granite-embedding-278m-multilingual`. See the plan for why.

Amounts and thresholds are not read from the knowledge bases. They come from the tools. The PDF is there so the agent can explain and cite the rules.

### Source attribution

*Valtion matkustussääntö 2026*, Valtiovarainministeriön julkaisuja 2025:63, Ministry of Finance, Finland. URN: https://urn.fi/URN:ISBN:978-952-367-397-7. Licence: CC BY-NC-ND 4.0. The PDF is shipped unmodified. The rates keyed into `tools/travel_request/data/rates.py` are a small subset, valid until 31.12.2026 per the document. Whether shipping the PDF in this repo and in the scenario zip is acceptable has not been confirmed (open item 1 in the plan).

## Mock data

| Employee | Name | Manager | Cost center | Remaining budget |
|---|---|---|---|---|
| E-1001 | Aino Virtanen | Mika Laine | CC-100 | 8000 EUR |
| E-1002 | Jukka Korhonen | Mika Laine | CC-100 | 8000 EUR |
| E-1003 | Sofia Lindholm | Katri Heikkinen | CC-300 | 5000 EUR (director Leena Rantanen) |
| E-1004 | Mikko Nieminen | Katri Heikkinen | CC-200 | 700 EUR (director Pekka Salonen) |

Approval rule (fictional, TP-APPR-01): none for a domestic trip with no leave, at most 600 EUR and enough budget; manager for a trip abroad, attached leave or 600-2500 EUR; director over 2500 EUR or when the budget is not enough. The mock "today" is `2026-03-02`; no tool uses it yet.

## Deploy

```powershell
$env:PYTHONUTF8 = "1"
.\scripts\deploy-all.ps1 -Scenario travel-request
```

Or this agent alone (tools, knowledge bases and the flow must already be imported):

```powershell
orchestrate agents import -f agents/travel-request/agent.yaml
orchestrate agents deploy --name travel_request
```

`agents import` creates a draft. The chat UI shows only deployed agents.

**Re-importing the PDF knowledge base.** In two attempts, updating `travel_state_rules` in place failed ingestion ("1 document(s) failed in ingestion"), while removing it first and importing it fresh succeeded. The first-ever import also failed once and succeeded on the second try after removal. The cause is unknown. If it fails: `orchestrate knowledge-bases remove --name travel_state_rules`, then import again from `knowledge/travel-request/`. A failed import can leave a KB record behind, so check `orchestrate knowledge-bases list`.

## Smoke test

```powershell
python scripts/smoke_test.py --scenario travel-request
```

The smoke prompts are diagnosis only (they tell the agent not to call the flow). The run API cannot answer the approval form.

## What was and was not verified

Verified by running (instance `techzone1`):

- The tools, directly in Python: 38 checks pass (rates, caps, 2027 refusal, country aliases, write-tool refusals).
- The 8 smoke prompts against the deployed agent, 3 times in a row on the final configuration: all 24 answers passed an automatic check of the outcome word, the expected amount, the tools called and "English answer". That check is crude (string matching). A manual read of the answers found no wrong amounts or wrong outcomes in those 24, but the wording varies between runs.
- The agent calls the approval flow with the expected arguments when asked for a request id (1 run in Finnish on an earlier configuration, 1 run in English on the final one; arguments read from the thread, not judged beyond that). The form itself was **not** answered.

Not verified:

- **The approval flow in the browser:** form rendering, Approve issuing an id, Reject issuing none, the agent repeating the `message` field. Nothing about this has been seen.
- **Retrieval quality on the Finnish PDF.** In an earlier spike (one run per question, 20 questions) the best configuration answered 11 correctly, 2 partly, 3 wrong and 4 missed. The final agent mostly relies on tools, but its explanations and section citations still depend on retrieval. Section numbers beyond those carried in tool output were not systematically checked.
- **Quotations from the Finnish document.** The agent is told not to translate or put its own wording in quotation marks. In 24 answers no translated quotation was spotted, but this was not exhaustively checked.
- **Other countries.** Only the keyed subset exists: Belgium, Germany, Sweden, Estonia, United States, United Kingdom, France, Norway. Other countries return a "not available" result.
- A clean first install on a fresh instance, agent deploy on a Developer Edition, and long-running behaviour.

## Known limitations

- **Instruction changes are fragile.** One added language sentence made Finnish answers worse in an earlier round and was reverted. Re-run the repeated smoke test after every change to `agent.yaml`.
- **Small rate subset.** The tools carry a hand-keyed part of the 2026 rates only. Some real rules are not modelled: the 15 h / 5 h exception for short foreign trips, meal allowance, night travel allowance, travel day compensation.
- **Mileage assumes no earlier kilometres this year** (the 55 c / 49 c switch at 5000 km).
- **2027 trips:** the tools refuse to estimate (the document says 2027 rates are agreed separately). The agent should still give a decision. This worked in the final 3 runs; earlier configurations sometimes answered DENIED.
- **Approval levels are fictional.** They are invented for this demo.
- **Embedding model availability.** `ibm/multilingual-e5-large` and `virtual-model/openai/text-embedding-3-small` were not available on the test instance.
