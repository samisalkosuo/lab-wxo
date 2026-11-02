# Cloud FinOps Agent

Investigates cloud spend anomalies, identifies idle and over-provisioned resources,
produces rightsizing recommendations, and routes resource changes through a cost-owner
approval flow.

## Tools

| Tool | Kind | Description |
|---|---|---|
| `cf_get_spend_summary` | read | Service-level spend breakdown with prior-period comparison. First tool to call on a bill increase. |
| `cf_list_idle_resources` | read | Lists all resources with low utilisation. Use with `cf_get_resource_utilization` to verify before acting. |
| `cf_get_resource_utilization` | read | 30-day and 7-day CPU/memory/network averages, plus scheduled jobs list. Required before any reclamation proposal. |
| `cf_explain_cost_spike` | read | Root-cause explanation for a spend increase in a named service, including contributing resources. |
| `cf_get_billing_lines` | read | Detailed billing line items. Used to verify reported usage vs. actual telemetry (CF-004 billing error case). |
| `cf_approve_reclaim` | flow | Governance gate — shows proposed reclamation to cost owner. On approval calls `cf_reclaim_resource`. |
| `cf_approve_resize` | flow | Governance gate — shows proposed rightsizing to cost owner. On approval calls `cf_resize_resource`. |

Write tools (`cf_reclaim_resource`, `cf_resize_resource`) are internal — the agent
never calls them directly; only the flows call them after cost-owner approval.

## Knowledge Base

**`cloud_finops_policy`** — four policy documents:

| Document ID | Title |
|---|---|
| CF-POL-01 | Idle Resource Reclamation Policy (30-day window, scheduled-job check) |
| CF-POL-02 | Zombie Resource Handling (missing owner tag + idle) |
| CF-POL-03 | Rightsizing Guidelines (criteria + change-control note) |
| CF-POL-04 | Billing Error Escalation Procedure (do not act — escalate to finance) |

## Mock Data

| Case | User query | Planted situation | Teaches |
|---|---|---|---|
| CF-001 | "Why did our bill spike this month?" | `vm-zombie-01`: running at full cost since 2025-04-10, no owner tag, zero activity | Root-cause investigation, zombie classification |
| CF-002 | "Any idle resources we can reclaim?" | `vm-idle-finance-01` and `vm-idle-dev-03` are genuinely idle; `vm-batch-weekend-01` has a Saturday batch job | Red herring: 7-day window looks idle, 30-day + job calendar says no |
| CF-003 | "Rightsize the database cluster" | `db-cluster-prod-01`: CPU 22%, memory 28%; illustrative saving ~40% | Rightsizing vs. reclamation, governed resize, illustrative label |
| CF-004 | "The billing report says we used 1 000 GPU hours" | Line BL-5001 reports 1 000 GPU hours; telemetry shows 0 | Restraint: flag discrepancy, do not act, escalate to finance |

Account: `acct-001` | Billing period: `2025-05` | Prior period: `2025-04`

## Limitations

- Both approval flows (`cf_approve_reclaim`, `cf_approve_resize`) follow the patterns of
  `flows/incident_triage/request_remediation.py` and
  `flows/hr_onboarding/hr_request_provisioning.py`. Approve and Reject on each form were
  verified in the browser chat UI.
- The agent LLM (`groq/openai/gpt-oss-120b`) and the KB embedding model must exist
  in the target instance.
- KB indexing takes time after import; wait before the first demo query.
- `orchestrate agents deploy` (for chat UI availability) fails on Developer Edition;
  warn and continue.
