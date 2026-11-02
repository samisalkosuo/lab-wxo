# Maintenance Field Assistant (`field_maintenance`)

A single agent for maintenance technicians. The technician describes a problem in plain words;
the agent finds the asset, checks the evidence in a **mock Maximo**, points to the right
procedure and safety steps in a knowledge base, and drafts a work log. The log is written
only after the technician approves it in a form.

## Maximo is mocked

All data is fictional and static. Field names follow IBM Maximo (`ASSETNUM`, `WONUM`,
`WORKTYPE`, `STATUS`, `FAILURECODE`, `PMNUM`, `ITEMNUM`) and the tools return business-level
results, not raw API calls. In real life only the bodies of the tools in
`tools/field_maintenance/field_maintenance.py` would change (Maximo REST/OSLC calls instead of
reading `data/`). **No connection to a real Maximo was built or tested.**

## Why this is an agent and not a flowchart

- The input is messy ("cooling pump on line 2 is vibrating and hot"). The asset must be resolved
  first, and sometimes a clarifying question is needed.
- The next step depends on what the last one found: a repeat failure adds a follow-up request,
  an open work order means no duplicate, a confined-space job means stop and ask for a permit.
- The combinations of history, hazard and parts cannot be drawn in advance.
- The one fixed part, the write to Maximo, is deterministic and sits in a flow with a human gate.

## Tools on the agent

| Name | Kind | Purpose |
|---|---|---|
| `mx_find_asset` | read-only tool | Match a loose description to candidate assets (ranked, `ambiguous` flag) |
| `mx_get_asset` | read-only tool | Asset record: location, status, criticality, hazard class |
| `mx_get_work_order_history` | read-only tool | Closed work orders, failure codes, repeat failures |
| `mx_list_open_work_orders` | read-only tool | Open work orders (avoid duplicates) |
| `mx_get_pm_schedule` | read-only tool | PM schedule and overdue flag |
| `mx_check_spares` | read-only tool | Spare part stock, bin and expected date |
| `mx_get_meter_readings` | read-only tool | Vibration, temperature, current vs warning/alarm levels |
| `mx_submit_work_log` | flow (approval gate) | Shows the draft; on Submit calls `mx_write_work_log`, on Reject writes nothing |

`mx_write_work_log` is **not** attached to the agent. Only the flow calls it. It also checks in
code that a given `WONUM` belongs to the asset, is open, and exists.

## Knowledge base: `field_maintenance_procedures`

Plain `.txt` documents (the built-in KB does not accept markdown), fictional demo content,
not real safety guidance.

| ID | Document |
|---|---|
| `SOP-PUMP-01` | Pump vibration, noise or heat - bearing inspection |
| `SOP-LOTO-01` | Lockout/tagout |
| `SOP-ELEC-01` | Electrical panel and motor circuit work |
| `SOP-CONF-01` | Confined space entry and permit |
| `POL-WORKLOG-01` | Work log standard, duplicate work orders, repeat-failure rule |
| `POL-STOP-01` | Safety steps cannot be skipped |

## Mock plant

| Asset | What is planted |
|---|---|
| `PUMP-L2-03` | Vibration and bearing temperature above alarm; `BRG-WEAR` twice in 6 months; coupling insert out of stock |
| `PUMP-L2-04` | Standby pump, readings normal, one old unrelated seal leak (red herring) |
| `MTR-CV-04` | Open work order `WO-11002` already covers the trip fault; PM overdue; current above alarm |
| `TNK-12` | Hazard class `confined_space` |
| `BLR-01`, `BLR-02`, `BLR-03` | Three boiler room assets, so "something is wrong in the boiler room" is ambiguous |
| `PNL-L2-01`, `CMP-01` | Fill out the plant |

## Limitations

- Static data: results do not change between calls and nothing is persisted by the write tool.
- Asset search is a simple keyword match over demo data, not Maximo search.
- Readings are a fixed snapshot with a short trend, not a live feed.
- The approval form needs a browser test; the ADK evaluator cannot click it.
- One ADK evaluation run exists (1 of 5 test cases succeeded). The test cases were edited afterwards and have not been re-run. See Scene 6 in [`docs/demo/field-maintenance-demo.md`](../../docs/demo/field-maintenance-demo.md).
