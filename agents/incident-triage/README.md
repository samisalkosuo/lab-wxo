# Incident Triage Agent

Diagnoses active production incidents by correlating service health, logs, metrics, and
deployment history against the `incident_triage_runbooks` knowledge base. Routes every
proposed remediation through a mandatory human-approval flow (`request_remediation`)
before anything is executed on the target service.

## Files

- `agent.yaml` -- agent definition
- `../../tools/incident_triage/incident_triage.py` -- Python tool package (8 tools)
- `../../knowledge/incident-triage/incident_triage_runbooks.yaml` -- knowledge base
- `../../flows/incident_triage/request_remediation.py` -- remediation approval flow

## Tools attached (8)

| Tool | Kind | Purpose |
|---|---|---|
| `list_open_incidents` | Python | Overview of active incidents |
| `get_incident` | Python | Full details for one incident |
| `get_service_health` | Python | Current health status of a service |
| `query_logs` | Python | Recent log entries for a service |
| `get_metrics` | Python | Key performance metrics for a service |
| `list_recent_deployments` | Python | Recent deployments (context for regressions) |
| `open_ticket` | Python | Log a formal follow-up ticket |
| `request_remediation` | Flow | Human-approval gate before any execution |

**Not attached:** `execute_remediation` is called only by the `request_remediation` flow
after a human approves. Attaching it directly would bypass the governance gate.

## Knowledge base

`incident_triage_runbooks` -- six runbooks covering bad deployment rollback (RB-DEPLOY-01),
DB connection pool exhaustion (RB-DBPOOL-01), TLS certificate renewal (RB-TLS-01),
load-test noise (RB-NOISE-01), escalation policy (RB-ESC-01), and post-incident notes
(RB-POST-01).

## Deploy

```powershell
# From repo root (imports everything in dependency order, then promotes agents to live):
$env:PYTHONUTF8 = "1"
.\scripts\deploy-all.ps1
```

```bash
bash scripts/deploy-all.sh
```

Or deploy this agent alone (prerequisites -- tools, knowledge base, flow -- must already be imported):

```powershell
orchestrate agents import -f agents/incident-triage/agent.yaml
orchestrate agents deploy --name incident_triage
```

**Note:** `orchestrate agents import` creates the agent as a draft. The chat UI only shows live agents. `orchestrate agents deploy --name incident_triage` promotes it to live. The deploy scripts run this step automatically.

## Demo script

See [`docs/demo/incident-triage-demo.md`](../../docs/demo/incident-triage-demo.md) for the human-readable demo: exact prompts, expected agent behaviour per scene, the approval-flow walkthrough, fallback notes, and closing talking points.

## Smoke test (ADK run API)

`orchestrate chat ask` hangs in non-interactive shells. Use the ADK Python client instead:

```python
from ibm_watsonx_orchestrate.client.api_client import APIClient
from ibm_watsonx_orchestrate.client.runs import RunsClient, CreateRunRequest
from ibm_watsonx_orchestrate.client.threads import ThreadsClient

client = APIClient()
runs = RunsClient(client)
threads = ThreadsClient(client)

run = runs.create_run(CreateRunRequest(
    agent_id="incident_triage",
    input="What open incidents are there? Triage them all."
))
# Poll run.id for status, then read thread messages.
```

See `scripts/smoke_test.py` for a complete example (`python scripts/smoke_test.py --scenario incident-triage`; it finds the agent by name and reads its prompts from `evaluation/incident-triage/ground_truth.json`).

## Browser test (approval flow)

The approval form only renders in the watsonx Orchestrate browser chat UI.

1. Open the browser chat and select the **Incident Triage** agent.
2. Type: `There is a checkout service incident INC-1001. Logs show an N+1 query regression. Investigate and propose a fix.`
3. The agent should diagnose and call `request_remediation`.
4. A "Remediation Approval Request" card should appear with Approve / Reject buttons.
5. **Approve path:** Click **Approve** -> agent reports the execution result verbatim.
6. **Reject path:** Start a fresh conversation, repeat, click **Reject** -> agent reports "REJECTED. No remediation was executed."

See `incident-triage-plan.md` Sub-Task 4 notes for the full step-by-step verification checklist.

## Mock incidents

| ID | Service | Root cause | Expected action |
|---|---|---|---|
| INC-1001 | checkout | Bad deployment (N+1 query) | rollback |
| INC-1002 | payments | DB connection pool exhaustion | db_pool_resize |
| INC-1003 | auth-gateway | Expired TLS certificate | certificate_rotation |
| INC-1004 | search-service | Scheduled load test (self-resolving) | no_action |

## Known limitations

- **Evaluation final-answer check: 0 of 15 runs pass.** Tool selection is consistent (13 of 15 runs), but the overall `is_success` metric fails because the agent uses non-breaking hyphens (U+2011) in runbook IDs and produces longer answers than the one-sentence expected responses.
- **Wrong incident in approval requests (3 of 19 vague-opening runs).** On "Hey, checkout is slow...", the agent occasionally files `request_remediation` with `service=payments, incident_id=INC-1001` (mismatched). The human gate prevents execution; the instruction-level fix was ineffective. Proper fix: validate service/incident consistency inside the flow.
- **No clean-instance install tested.** Re-install over `techzone1` was verified; first install from scratch was not.
