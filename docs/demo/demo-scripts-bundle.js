// AUTO-GENERATED — do not edit by hand.
// Re-generate with: python docs/demo/build-demo-scripts-bundle.py
//
// Provides window.DEMO_SCRIPTS (prompt + expected behaviour per scene) for the
// 'Show full script' view in presentation.html — works from file:// origins.
window.DEMO_SCRIPTS = {
 "cloud-finops": {
  "scenes": [
   {
    "num": "1",
    "title": "Vague bill spike (\"our cloud bill jumped 30%\")",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Our cloud bill jumped 30% this month. Can you investigate why?"
     },
     {
      "t": "expected",
      "status": "From 1 SDK smoke run",
      "tone": "info",
      "text": "- Tool sequence observed: `cf_get_spend_summary` → `cf_explain_cost_spike` → `cf_get_resource_utilization` (×4 resources) → `approve_resource_reclamation` (the `cf_approve_reclaim` flow).\n- The agent called `cf_get_spend_summary` twice and `cf_explain_cost_spike` once before the utilisation calls — the double call is a trace artefact (request + response step counted once each); actual distinct calls are: spend summary, spike explanation, four utilisation checks.\n- After checking utilisation on `vm-zombie-01`, `vm-idle-finance-01`, `vm-idle-dev-03`, and `vm-batch-weekend-01`, the agent reached the reclamation flow.\n- The answer was not captured (the flow blocks the SDK response); the form appears in the browser."
     }
    ]
   },
   {
    "num": "2",
    "title": "Idle resource scan — batch-job red herring",
    "items": [
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Are there any idle resources in account acct-001 we can reclaim?"
     },
     {
      "t": "expected",
      "status": "From 1 SDK smoke run",
      "tone": "info",
      "text": "- Tool sequence observed: `cf_list_idle_resources` → `cf_get_resource_utilization` (×3) → `approve_resource_reclamation`.\n- Three utilisation calls (not four) — the smoke run checked `vm-zombie-01`, `vm-idle-finance-01`, `vm-idle-dev-03` and skipped `vm-batch-weekend-01` in this particular run. **Vary between runs.** The agent may also check `vm-batch-weekend-01`.\n- The agent reached the reclamation flow; the answer was not captured."
     }
    ]
   },
   {
    "num": "3",
    "title": "Reclamation approval (Approve path and Reject path)",
    "items": [
     {
      "t": "note",
      "text": "This scene uses **two fresh conversations**, one for each path."
     },
     {
      "t": "prompt",
      "card": 3,
      "note": "start a fresh conversation for each path",
      "text": "Reclaim the zombie VM vm-zombie-01 in account acct-001. It has been running with no workload since 2025-04-10."
     },
     {
      "t": "expected",
      "status": "Smoke run reached the flow; form not yet browser-verified",
      "tone": "warn",
      "text": "- The agent should call `cf_get_resource_utilization` on `vm-zombie-01`, cite CF-POL-02, then call `cf_approve_reclaim`.\n- The flow appears in traces as `approve_resource_reclamation`.\n- The form title (from flow definition): **Resource Reclamation Approval** with fields: Resource ID, Account ID, Policy Reference, Agent Justification, and two buttons **Approve** and **Reject**."
     },
     {
      "t": "form",
      "status": "Browser-verified",
      "tone": "ok",
      "text": "A card titled \"Resource Reclamation Approval\" with Resource ID (`vm-zombie-01`), Account ID (`acct-001`), Policy Reference (e.g. `CF-POL-02`), Agent Justification, and two buttons **Approve** and **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "",
      "tone": "info",
      "same_prompt": false,
      "text": "1. Read the form fields aloud.\n2. Click **Approve**.\n3. Expected (browser-verified): `cf_reclaim_resource` runs. The mock tool message includes \"MOCK RECLAIM EXECUTED (demo only — no real resource was deleted). Resource 'vm-zombie-01' in account 'acct-001' reclaimed. Approved by: Cost Owner. Estimated saving: USD 640.00/month.\""
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation",
      "tone": "info",
      "same_prompt": true,
      "text": "1. Send the same prompt. Wait for the form.\n2. Click **Reject**.\n3. Expected (browser-verified): nothing executes. Flow message: \"REJECTED BY COST OWNER. No resource was reclaimed. Resource: vm-zombie-01, Account: acct-001. No infrastructure changes were made.\""
     }
    ]
   },
   {
    "num": "4",
    "title": "Rightsizing approval",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "The database cluster db-cluster-prod-01 looks over-provisioned. Can you check and recommend a rightsizing?"
     },
     {
      "t": "expected",
      "status": "From 1 SDK smoke run",
      "tone": "info",
      "text": "- Tool sequence observed: `cf_get_resource_utilization` → `approve_resource_rightsizing` (the `cf_approve_resize` flow).\n- The agent went straight to utilisation check on `db-cluster-prod-01` (CPU 22%, memory 28%, size `xlarge-16cpu-128gb-3nodes`) then called the resize flow. Answer not captured (flow blocks response).\n- The flow appears in traces as `approve_resource_rightsizing`."
     },
     {
      "t": "form",
      "status": "Browser-verified",
      "tone": "ok",
      "text": "A card titled \"Resource Rightsizing Approval\" with Resource ID, Account ID, Current Size, Proposed Target Size, Policy Reference (`CF-POL-03`), Agent Justification, and a note about change-control windows. Two buttons: **Approve** and **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "",
      "tone": "info",
      "same_prompt": false,
      "text": "1. Read the fields aloud (current size: `xlarge-16cpu-128gb-3nodes`, target: `large-8cpu-64gb-2nodes`).\n2. Click **Approve**.\n3. Expected (browser-verified): `cf_resize_resource` runs. The flow message includes \"APPROVED BY COST OWNER AND EXECUTED\", the two size values, \"Illustrative saving: ~40% monthly cost reduction\", and \"This figure is illustrative; actual saving depends on production workload.\" *(Note: first browser test showed the illustrative label was missing; the flow was fixed and re-deployed — the label now appears in the flow message directly.)*"
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation, same prompt",
      "tone": "info",
      "same_prompt": true,
      "text": "1. Click **Reject**. Expected (browser-verified): \"REJECTED BY COST OWNER. No resource was resized. Current size 'xlarge-16cpu-128gb-3nodes' unchanged. No infrastructure changes were made.\""
     }
    ]
   },
   {
    "num": "5",
    "title": "Billing error: restraint",
    "items": [
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "The billing report shows we used 1 000 GPU hours this month. Can you verify that?"
     },
     {
      "t": "expected",
      "status": "From 1 SDK smoke run — full answer captured",
      "tone": "info",
      "text": "- Tool called: `cf_get_billing_lines` only. No write tools, no approval flow.\n- Real answer excerpt (smoke run): \"The billing line for **GPU Compute** shows: - **Line ID:** BL-5001 - **Reported units:** 1 000 GPU‑hours (USD 5 000) - **Recorded usage units:** 0 GPU‑hours - **Discrepancy:** **true** — the telemetry indicates no GPU usage, so this is a data error. Per **CF-POL-04** (billing discrepancy escalation policy), this should be escalated to finance for correction. No reclamation or rightsizing actions are applicable here.\"\n- The agent cited CF-POL-04 and made no write-tool call."
     }
    ]
   }
  ]
 },
 "customer-returns": {
  "scenes": [
   {
    "num": "1",
    "title": "Vague opening (\"I want to return something\")",
    "items": [
     {
      "t": "note",
      "text": "This is the messy-input teaching point. The customer provides almost no information."
     },
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Hi, I bought something a while ago and I want to return it. Can you help?"
     },
     {
      "t": "expected",
      "status": "1 browser run, instruction bug observed and fixed",
      "tone": "ok",
      "text": "- **Observed (before the fix):** the agent asked for the **serial number** instead of the\n  order ID. Root cause: the instructions said \"if the customer does not have one, ask for\n  the serial number\" — the model interpreted \"nothing provided\" as \"does not have one.\"\n  The fix tightens both the Method section and the Clarifying Questions section of\n  `agents/customer-returns/agent.yaml` to say: first question must always be the order ID;\n  serial number only after the customer explicitly says they have no order ID.\n- **Expected after fix:** the agent should ask for the order ID.\n- It should not guess eligibility before looking up the order.\n- It should ask one question, not several at once.\n- **Not yet re-verified after the instruction fix.** Re-deploy the agent and re-run before presenting."
     }
    ]
   },
   {
    "num": "2",
    "title": "Warranty defect: CR-001 (main path + red herring)",
    "items": [
     {
      "t": "note",
      "text": "This is the main happy-path scene and the red-herring teaching point."
     },
     {
      "t": "note",
      "text": "**Alice (CUST-101) has two warranty records:**\n- `SN-BLND-500-A101` for ORD-1001 (the ProBlend 500 she is returning) — **active, applicable**\n- `SN-BLND-PRO-A101` for ORD-1005 (an older ProBlend PRO, different SKU) — **wrong product**\n\nThe agent must not apply the PRO warranty to the 500 claim."
     },
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001."
     },
     {
      "t": "expected",
      "status": "Not verified",
      "tone": "warn",
      "text": "- The agent calls `returns_lookup_order` for ORD-1001 (14 days old, within window).\n- It calls `returns_check_warranty` for ORD-1001. The tool returns two warranty records for\n  customer CUST-101: `SN-BLND-500-A101` (SKU-BLND-500, active, applicable) and\n  `SN-BLND-PRO-A101` (SKU-BLND-PRO, active, but a different product).\n- The agent should identify `SN-BLND-500-A101` as the applicable warranty and ignore\n  `SN-BLND-PRO-A101`.\n- It searches `customer_returns_policy` and cites `RP-WARRANTY-01`.\n- It proposes a `replacement` via `returns_process_return`.\n- (Not verified: whether the agent correctly names the applicable serial number vs. the\n  red-herring one in its answer.)"
     }
    ]
   },
   {
    "num": "3",
    "title": "Outside the 30-day window: CR-002 (denial path)",
    "items": [
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "I bought some headphones about six weeks ago. Order ORD-1002. I just don't like them anymore, I want a refund."
     },
     {
      "t": "expected",
      "status": "Not verified",
      "tone": "warn",
      "text": "- The agent calls `returns_lookup_order` for ORD-1002. The tool returns `age_days: 46` and\n  `within_30_day_window: false`.\n- No defect reported; the agent searches `customer_returns_policy` and finds `RP-STANDARD-01`\n  (30-day no-reason window).\n- The agent calls `returns_process_return` with `refund_reason: no_reason`,\n  `within_window: false`. The flow's Decisions node routes to `ineligible_result`; the\n  approval form is **never shown**.\n- The flow returns: \"RETURN INELIGIBLE. Order: ORD-1002. … outside the 30-day return window.\"\n- The agent should report this verbatim and not offer to escalate or override the rule.\n- (Not verified: whether the Decisions node actually routes to ineligible without showing\n  the form. This requires browser verification.)"
     }
    ]
   },
   {
    "num": "4",
    "title": "Gift return by serial number: CR-003",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "I received a kitchen scale as a gift and I'd like to return it. I don't have an order number but the serial number on the box is SN-KTCH-780-C103."
     },
     {
      "t": "expected",
      "status": "Not verified",
      "tone": "warn",
      "text": "- The agent calls `returns_lookup_by_serial` with `SN-KTCH-780-C103`. The tool returns\n  `linked_order_id: ORD-1003`, `purchase_date: 2025-05-10`, `age_days: 24`,\n  `within_30_day_window: true`, `purchase_channel: gift`.\n- The agent calls `returns_lookup_order` for ORD-1003 to get full order details.\n- It searches `customer_returns_policy` and finds `RP-GIFT-01` (gift returns).\n- It proposes `store_credit` (gift-return policy: no cash refund to a non-payer).\n- It calls `returns_process_return`; the approval form appears.\n- (Not verified: any of this.)"
     }
    ]
   },
   {
    "num": "5",
    "title": "Approval flow: CR-001 (Approve path and Reject path)",
    "items": [
     {
      "t": "note",
      "text": "Use **two fresh conversations**, one for each path. Use the warranty-defect prompt from\nscene 2 in both."
     },
     {
      "t": "prompt",
      "card": 5,
      "note": "same as scene 2",
      "text": "I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001."
     },
     {
      "t": "form",
      "status": "From the flow definition — not browser-verified",
      "tone": "warn",
      "text": "A card titled \"Return Request Approval\" with: Order ID, Customer ID, Return Reason,\nResolution Type, Policy Reference, Agent Justification, and two buttons: **Approve**\nand **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "Not browser-verified",
      "tone": "warn",
      "same_prompt": false,
      "text": "1. Read the form fields aloud.\n2. Click **Approve**.\n3. Expected (from flow code): `returns_issue_refund` runs and returns a refund reference\n   (`REF-NNNNN`). The flow message is:\n   \"APPROVED AND PROCESSED. Order: ORD-1001. Resolution: replacement.\n   Policy: RP-WARRANTY-01. Result: {issue_refund output}.\"\n   The agent should report this verbatim. **Not verified in a browser run.**"
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation — not browser-verified",
      "tone": "warn",
      "same_prompt": true,
      "text": "1. Send the same prompt. Wait for the form.\n2. Click **Reject**.\n3. Expected (from flow code): nothing executes and the flow returns:\n   \"REJECTED. No refund or replacement was issued. Proposed resolution 'replacement'\n   for order 'ORD-1001' was declined by the approver. No changes have been made.\"\n   **Not verified in a browser run.**"
     }
    ]
   },
   {
    "num": "6",
    "title": "Out-of-scope escalation: CR-004",
    "items": [
     {
      "t": "prompt",
      "card": 6,
      "note": "",
      "text": "I was charged twice for my order ORD-1004. I need a refund for the duplicate charge."
     },
     {
      "t": "expected",
      "status": "Not verified",
      "tone": "warn",
      "text": "- The agent should recognise this as a billing dispute, not a product return.\n- It searches `customer_returns_policy` and finds `RP-ESCALATE-01`.\n- It declines to process a return and directs the customer to the Billing team.\n- It does **not** call `returns_process_return`.\n- (Not verified: whether the agent reliably identifies the billing pattern without calling\n  the flow first.)"
     }
    ]
   }
  ]
 },
 "hr-onboarding": {
  "scenes": [
   {
    "num": "1",
    "title": "Standard Employee with Missing Field",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Onboard Alex Kim, Software Engineer, starts 2025-06-09."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent calls `hr_get_new_hire` and identifies Alex Kim.\n- It notices that the hire's record does not contain an equipment choice.\n- Instead of failing, it asks the coordinator to provide a choice of: standard_laptop, developer_laptop, or no_equipment.\n- After the coordinator responds (e.g., \"Developer Laptop\"), the agent calls `hr_get_role_access`, `hr_get_department_config`, and `hr_check_provisioning_status`.\n- It cites policy `HR-POL-01`, summarizes that the HR Manager approves (standard flow), and asks for confirmation to trigger `hr_request_provisioning`.\n- When confirmed, it submits the flow. The UI displays: `The request has been submitted for HR‑Manager approval. The approval form is displayed above. No access has been provisioned yet.`"
     }
    ]
   },
   {
    "num": "2",
    "title": "Contractor Restricted Access",
    "items": [
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Set up contractor access for Jordan Lee."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent retrieves the record for Jordan Lee using `hr_get_new_hire`.\n- It queries the role definition and sees Jordan is a contractor.\n- Based on `HR-POL-02`, it notes that contractors do not receive corporate email accounts, only guest chat accounts and time-limited VPN access expiring on 2025-09-05.\n- It proposes this restricted list, cites `HR-POL-02`, and requests confirmation to submit standard flow `hr_request_provisioning`."
     }
    ]
   },
   {
    "num": "3",
    "title": "Finance compliance gated onboarding",
    "items": [
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "Add Sarah Chen to the Finance team."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent retrieves Sarah Chen's record (Finance Analyst).\n- It calls `hr_get_department_config` for \"Finance\" and sees that compliance sign-off is required.\n- It identifies that the VPN access is already pending for Sarah via `hr_check_provisioning_status`, so it excludes VPN from the proposal.\n- It proposes email, chat, and finance_ledger.\n- It states clearly that a secondary approval from a Compliance Reviewer is required.\n- It requests confirmation to trigger `hr_request_compliance_provisioning`."
     }
    ]
   },
   {
    "num": "4",
    "title": "Restraint: Bulk/Admin ban refusal",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "Can you provision admin rights for the whole team?"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent queries `hr_onboarding_policy` or handles the refusal immediately.\n- It politely but firmly declines, stating that bulk provisioning is prohibited under `HR-POL-04` and admin rights are never granted via the onboarding process.\n- It offers to set up access for single named individuals instead. No flow is started."
     }
    ]
   }
  ]
 },
 "incident-triage": {
  "scenes": [
   {
    "num": "1",
    "title": "Vague opening (\"checkout is slow\")",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Hey, checkout is slow. Can you look into it?"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent first calls `list_open_incidents`, then picks INC-1001 (checkout, CRITICAL) without being told the ID, then `get_incident`, `get_service_health`, `query_logs`, `get_metrics` (`latency`), `list_recent_deployments`, and the runbook knowledge base.\n- The list it received contained four incidents: INC-1001 (CRITICAL, checkout), INC-1002 (CRITICAL, payments), INC-1003 (MAJOR, auth-gateway), INC-1004 (MINOR, search-service).\n- It then goes straight on to **propose a fix** and the approval form appears (\"A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete.\"). It does this without you asking for a fix.\n- Across 9 recorded runs (3 evaluation, 6 dry-run): 8 proposed `rollback` of `checkout`, INC-1001, `RB-DEPLOY-01`. **1 dry-run proposed `db_pool_resize` on `payments` but filed it under INC-1001** (it reasoned that checkout was degraded because payments was slow). That is a mismatch with the incident it was filed under. After adding a \"Keep incidents separate\" section to the agent instructions a further 10-run retest was done; 2 of 10 still showed the mismatch (no measurable improvement; the section is still in the YAML but unproven). Total across all recorded runs: **3 of 19 vague-opening runs show the mismatch**.\n- **It never asked a clarifying question in any of the 19 runs**, even though its instructions allow one. Do not promise one."
     },
     {
      "t": "note",
      "text": "**What to do at the form:** read the form fields aloud. If it shows checkout / rollback / INC-1001 / RB-DEPLOY-01, click **Reject** (nothing executes) and say \"we will do Approve and Reject properly in scene 4\". Then start a new conversation."
     }
    ]
   },
   {
    "num": "2",
    "title": "Bad-deployment diagnosis (INC-1001)",
    "items": [
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Investigate incident INC-1001 on the checkout service. Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and what remediation action you would recommend."
     },
     {
      "t": "note",
      "text": "The \"Do NOT call request_remediation\" clause is here only to keep this scene diagnosis-only. Do not use that clause in scene 4."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Tools: `get_incident`, `get_service_health`, `query_logs` (ERROR, checkout), `get_metrics` (`latency`), `list_recent_deployments` (checkout), then the knowledge base. The post-fix dry-run used exactly this sequence.\n- The evidence it gathered: p99 latency 2420 ms vs 180 ms baseline (13.4x), 4.2% 504 errors, and deployment DEP-4108 (checkout v2.14.0) completed 13:55 UTC, with the spike starting 14:02 UTC.\n- Real answer excerpt (evaluation run 1): \"Perform a **rollback** of the checkout service to the previous stable version (**v2.13.2**) to restore normal latency and eliminate the 504 errors. This action follows the procedure described in Runbook **RB-DEPLOY-01**.\"\n- It states a root cause only after several pieces of evidence (the instructions require at least two)."
     }
    ]
   },
   {
    "num": "3",
    "title": "Red-herring incident (INC-1002)",
    "items": [
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "Investigate incident INC-1002 on the payments service. There was a recent deployment to notification-service - could that be related? Use your tools to find the root cause. Do NOT call request_remediation - just report your diagnosis and recommended action."
     },
     {
      "t": "note",
      "text": "(Same wording as the evaluation test case, except the dash. The user planting the suspect is realistic, and it is what the evaluation used.)"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Tools: `get_incident`, `get_service_health`, `query_logs`, `get_metrics` (`db_connections`), `list_recent_deployments` for `payments`, then for `notification-service`, then the knowledge base. In the post-fix dry-run the agent skipped nothing relevant; it checked both services' deployments.\n- Evidence: `ConnectionPoolTimeoutException ... (active=100/100, max=100, queued=38)`, error code `DB_POOL_EXHAUSTED`, 18.5% HTTP 500, and a `db_connections` metric showing the pool 100% saturated with 45 queued requests.\n- It found the notification-service deployment DEP-4109 (14:05 UTC) and dismissed it. Real excerpt (evaluation run 1): \"A recent deployment to notification-service (14:05 UTC) is unrelated: the runbook explicitly states that deployments to *unrelated* services are red herrings and should not be considered a cause.\"\n- Recommended action: `db_pool_resize` on payments, runbook `RB-DBPOOL-01`. Same in all 4 runs."
     }
    ]
   },
   {
    "num": "4",
    "title": "Approval flow (Approve path and Reject path)",
    "items": [
     {
      "t": "note",
      "text": "This scene uses **two fresh conversations**, one for each path. Use the prompt below in both. It was the prompt verified in the browser."
     },
     {
      "t": "prompt",
      "card": 4,
      "note": "no \"Do NOT call request_remediation\" clause",
      "text": "There is a critical incident on the checkout service, INC-1001. Logs show an N+1 query regression introduced by a recent deployment. Investigate and propose a fix."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- In 3 of 3 SDK dry-runs the agent called, in order: `get_incident`, `get_service_health`, `query_logs` (search \"N+1\"), `query_logs` (WARN, \"query\"), `list_recent_deployments`, the knowledge base, then the approval flow with `action=rollback`, `service=checkout`, `incident_id=INC-1001`, `runbook_ref=RB-DEPLOY-01` and a justification. The chat then shows: \"A new flow has started. This chat session is currently dedicated to the flow and will resume once the flow is complete.\"\n- Note this prompt hands the agent the conclusion (\"N+1 ... introduced by a recent deployment\"). It did still query logs and deployments, but it did not call `get_metrics` in these runs."
     },
     {
      "t": "form",
      "status": "From the flow definition and the browser test",
      "tone": "warn",
      "text": "a card titled \"Remediation Approval Request\" with Target Service, Proposed Action, Incident Reference, Runbook Reference, Agent Justification, and two buttons, **Approve** and **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "",
      "tone": "info",
      "same_prompt": false,
      "text": "1. Read the five fields aloud (checkout / rollback / INC-1001 / RB-DEPLOY-01 / the justification).\n2. Click **Approve**.\n3. Expected (browser-verified by the user): `execute_remediation` runs and the agent reports the result. The mock tool's summary text is \"Rolled back checkout to previous stable version (v2.13.2). N+1 query regression removed.\" The exact wording shown in the chat was not recorded, so describe it loosely."
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation",
      "tone": "info",
      "same_prompt": true,
      "text": "1. Send the same prompt. Wait for the form.\n2. Click **Reject**.\n3. Expected (browser-verified): nothing is executed and the agent reports the rejection. The flow's message text is \"REJECTED. No remediation was executed. Proposed action 'rollback' on service 'checkout' was declined by the approver. Incident: INC-1001. No infrastructure changes were made.\" That wording is from the flow code; the verbatim text as rendered in the browser was not captured."
     }
    ]
   },
   {
    "num": "5",
    "title": "Non-incident (INC-1004): restraint",
    "items": [
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "Investigate incident INC-1004. Use your tools to find the root cause and whether any action is needed."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- It concluded no action in all 4 runs (3 evaluation, 1 dry-run). It never called the approval flow and never opened a ticket.\n- The tool path varied, so do not claim a fixed sequence: evaluation runs 1 and 2 used `get_incident`, `get_service_health` and the knowledge base; run 3 also called `get_metrics`; the post-fix dry-run used only `get_incident` and `get_service_health` and did **not** consult the knowledge base.\n- Real excerpt (post-fix dry-run): \"This is an expected, scheduled load-test event that does not require any remediation. No action is needed.\"\n- Evaluation run 1 cited `RB-NOISE-01` (\"Scheduled Load Test Noise - No Action Needed\") and said: \"Monitor the service after the test window; if latency remains elevated or errors appear, reopen the incident and follow the appropriate runbook.\""
     }
    ]
   },
   {
    "num": "6",
    "title": "Evaluation (honest)",
    "items": [
     {
      "t": "note",
      "text": "This scene is mostly talking. Do not run the evaluation live: it is slow, and in a non-interactive shell `orchestrate evaluations evaluate` exits with code 1 (a progress-rendering issue) although it writes all result files.\n\n> **Note:** if the `evaluation/incident-triage/results/` folder is missing in your clone, run the evaluation yourself to produce results, or describe the development-run results verbally."
     },
     {
      "t": "note",
      "text": "**Show:** if you have run the evaluation on your instance, open `evaluation/incident-triage/results/<timestamp>/summary_metrics.csv`. If not, describe the results from the development run verbally (see talking points below) and say you are quoting stored results from the development instance."
     },
     {
      "t": "note",
      "text": "**Say these things plainly:**\n\n- *What the evaluation measured:* 5 test cases x 3 runs = 15 runs, with a simulated user, against the agent **before** the `p99_latency_ms` -> `latency` instruction fix. `tool_match_success` was true in 13 of 15 runs, and `tool_call_recall` was 1.0 in 13 of 15. The two misses are both INC-1004 runs where the test case lists a `get_metrics` call that the agent skipped because it already had a conclusive answer (a too-strict test case). The plan's Open Item 3 says `query_logs`; the test case file `tc_inc1004_search_no_action.json` actually lists `get_incident`, `get_service_health` and `get_metrics`, and `get_metrics` is what runs 1 and 2 did not call.\n- *What did not pass:* the final-answer check passed in **0 of 15** runs. Causes found so far: the agent writes IDs with non-breaking hyphens, so exact keyword matches fail, and the expected answers were short one-liners compared with long answers (the second cause is unverified). So the evaluation currently measures tool selection only. **Do not say the agent passes the evaluation.**\n- *Not re-run:* the evaluation has not been re-run since the instruction fix, so the tool-precision numbers (between 0.33 and 1.0, lowest on the vague case) include noise from the typo.\n- *What was observed about tool use:* the agent chose to skip tools when it already had a conclusive answer (INC-1003, INC-1004). That saved calls but did not change any answer.\n- *Vague input:* the agent resolved the vague opening to INC-1001 through `list_open_incidents` and never asked a clarifying question."
     }
    ]
   }
  ]
 },
 "pension-disability-triage": {
  "scenes": [
   {
    "num": "1",
    "title": "Full Disability Pension Evaluation (CLM-701)",
    "items": [
     {
      "t": "note",
      "text": "*Main-path scene. The case is straightforward once the qualifying check and medical evidence are in.*"
     },
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Evaluate the disability pension claim for member CLM-701. Use your tools to check the qualifying months, review the medical evidence, and assess rehabilitation eligibility. Do NOT call pdis_refer_claim — just report your triage disposition and which referral type you would recommend."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Smoke run (1 run): agent called `pdis_get_claim_dossier`, `pdis_verify_qualifying_months`, `pdis_get_medical_summary`, `pdis_assess_rehab_eligibility` in that order. Qualifying condition: 58/60 months met, tuleva aika eligible. Work capacity 30%, permanent prognosis, rehab exhausted. Disposition: PENSION ELIGIBLE. Agent cited DIS-POL-01 and recommended medical board referral."
     }
    ]
   },
   {
    "num": "2",
    "title": "Rehabilitation Before Pension (CLM-702)",
    "items": [
     {
      "t": "note",
      "text": "*Trap scene. The case looks like a pension at first glance (injured worker, reduced capacity) but the statutory rehab rule blocks a direct pension grant.*"
     },
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Member CLM-702 has applied for a disability pension following back surgery. Use your tools to evaluate the claim. Do NOT call pdis_refer_claim — just report whether a pension can be granted at this stage or whether another pathway applies, and cite the relevant policy."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Smoke run (1 run): qualifying condition met (36/60 months), work capacity 55% (above 40% threshold), significant recovery potential, no workplace trial attempted. `pdis_assess_rehab_eligibility` returned REHABILITATION PRIORITY. Agent recommended vocational rehabilitation (tyokokeilu) and cited DIS-POL-02. Agent explicitly stated a pension cannot be granted at this stage."
     }
    ]
   },
   {
    "num": "3",
    "title": "Occupational Accident Waiver (CLM-703)",
    "items": [
     {
      "t": "note",
      "text": "*Exception-handling scene. The headline number (14 months insured) makes the case look like a clear refusal, but an occupational accident waiver applies.*"
     },
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "Young worker CLM-703 is claiming incapacity following a factory accident and has only 14 months of work history. Use your tools to evaluate eligibility. Do NOT call pdis_refer_claim — just explain whether and why the standard qualifying condition applies and what disposition you recommend."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Smoke run (1 run): `pdis_verify_qualifying_months` returned NOT ELIGIBLE on the 36/60 condition (14 months) and immediately surfaced `qualifying_condition_waived: True` with waiver reason `tyotapaturma` (TyEL § 12). Agent confirmed accident verification status from dossier, proceeded to medical assessment (work capacity 25%), and recommended medical board referral. Agent cited DIS-POL-04."
     }
    ]
   },
   {
    "num": "4",
    "title": "Governed Referral Flow (CLM-701, approval path)",
    "items": [
     {
      "t": "note",
      "text": "*Governed-action scene. Run this in a fresh conversation after Scene 1 to show the human-in-the-loop gate.*"
     },
     {
      "t": "note",
      "text": "**Verified in browser (1 run per path).** The flow form rendered with all five fields. Approve path submitted the referral and the agent reported the `message` field verbatim (referral ID `REF-XXXXX`). Reject path returned the rejection message with nothing recorded."
     },
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "Evaluate the disability pension claim for member CLM-701 and, once you have completed the triage, use the referral flow to submit a referral to the Medical Board."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "1. Agent calls the four read-only tools (same as Scene 1).\n2. Agent proposes the `pdis_refer_claim` flow with inputs: `claimant_id=CLM-701`, `referral_type=medical_board`, a `disposition_summary` drawn from the tool findings, `policy_ref=DIS-POL-01`, `b_statement_valid=yes`.\n3. A review form appears in the chat with five read-only fields: Claimant ID, Referral Type, Policy Reference, B-Statement Valid, Triage Disposition Summary.\n4. **Approve path:** Handler clicks \"Approve Referral\" → `pdis_dispatch_referral` is called → a referral ID (`REF-XXXXX`) is returned → agent reports the message verbatim.\n5. **Reject path (separate run):** Handler clicks \"Reject\" → nothing is submitted → agent reports \"REFERRAL REJECTED. No referral was submitted.\""
     }
    ]
   },
   {
    "num": "5",
    "title": "Refusal / Red Herring (CLM-704)",
    "items": [
     {
      "t": "note",
      "text": "*Restraint scene. The medical evidence (35% work capacity) would normally support a pension claim, but the qualifying months condition fails with no waiver — the agent must stop early and refuse.*"
     },
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "Member CLM-704 is requesting a disability pension after several years of uninsured residency abroad. Use your tools to check the qualifying condition. Do NOT call pdis_refer_claim — just report the eligibility outcome and what the claimant should be advised."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Smoke run (1 run): `pdis_get_claim_dossier` showed 8.5-year uninsured period abroad with no bilateral treaty. `pdis_verify_qualifying_months` returned NOT ELIGIBLE (8/60 months, threshold 36, no waiver). Agent stopped after the qualifying months check, cited DIS-POL-04, and advised Kela referral without proceeding to medical assessment."
     }
    ]
   }
  ]
 },
 "pension-ove-advisor": {
  "scenes": [
   {
    "num": "1",
    "title": "Vague opening (\"I want to explore partial pension\")",
    "items": [
     {
      "t": "note",
      "text": "This is the messy-input teaching point. The member provides no ID or birth year."
     },
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Hi, I am thinking about taking partial pension early while continuing my job. Can you help me?"
     },
     {
      "t": "expected",
      "status": "Not verified against live instance",
      "tone": "warn",
      "text": "- The agent should greet the user politely and ask for their **member ID** (e.g. MEM-101) and birth year or target retirement timeframe.\n- It should not attempt to calculate numbers without knowing the member's profile.\n- It should ask one clear clarifying question at a time."
     }
    ]
   },
   {
    "num": "2",
    "title": "Main path: 50% OVE with continuing salary (Matti Virtanen, MEM-101)",
    "items": [
     {
      "t": "note",
      "text": "Demonstrates the core calculation: 50% partial draw, permanent 0.4%/month actuarial reduction, life expectancy coefficient, and 1.5%/year ongoing TyEL work accrual."
     },
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "I turn 62 next month and want to explore taking 50% partial early old-age pension (OVE) while continuing my job. My member ID is MEM-101 and my current monthly salary is 4200 euros."
     },
     {
      "t": "expected",
      "status": "Not verified against live instance",
      "tone": "warn",
      "text": "- Calls `ove_get_member_profile(\"MEM-101\")` and verifies age 62 (born 1964).\n- Calls `ove_get_accrued_pension(\"MEM-101\")` retrieving €2,400.00/mo baseline accrual.\n- Calls `ove_calculate_reduction(\"MEM-101\", 50, \"2026-05-01\")` and computes:\n  * 23 months before full pension age $\\rightarrow$ 9.2% permanent reduction.\n  * Life expectancy coefficient: 0.9482.\n  * Monthly OVE gross payout: €1,033.16/mo.\n- Calls `ove_simulate_combined_income(\"MEM-101\", 50, 4200.0, 24)` and computes:\n  * Total combined monthly gross: €5,233.16/mo.\n  * Continuing work accrual: 1.5%/year on €4,200/mo = €63.00/mo new pension added per year.\n- Cites `OVE-POL-03` explaining that the reduction is permanent for life on the drawn portion."
     }
    ]
   },
   {
    "num": "3",
    "title": "Refusal & age boundary check (Liisa Korhonen, MEM-102)",
    "items": [
     {
      "t": "note",
      "text": "Demonstrates strict adherence to birth cohort minimum retirement age thresholds."
     },
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "Can I take 25% OVE starting next month? My member ID is MEM-102 and I am a 59-year-old teacher."
     },
     {
      "t": "expected",
      "status": "Not verified against live instance",
      "tone": "warn",
      "text": "- Calls `ove_get_member_profile(\"MEM-102\")` identifying DOB 1966-08-25 (age 59).\n- Calls `ove_calculate_reduction(\"MEM-102\", 25)` which returns `ineligible_underage`.\n- Explains that for birth cohort 1966, the statutory minimum OVE age is 62 years 0 months (shortfall of 27 months).\n- Cites `OVE-POL-01` and provides the earliest date when an application can be filed.\n- Refuses to file an early application."
     }
    ]
   },
   {
    "num": "4",
    "title": "Multi-option scenario comparison (Antti Mäkinen, MEM-103)",
    "items": [
     {
      "t": "note",
      "text": "Demonstrates financial trade-off comparison between 25% and 50% draw percentages alongside reduced work hours (80%)."
     },
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "I want to compare taking 25% vs 50% OVE. My member ID is MEM-103 and I plan to reduce my work hours to 80% with a salary of 2800 euros per month."
     },
     {
      "t": "expected",
      "status": "Not verified against live instance",
      "tone": "warn",
      "text": "- Calls `ove_get_member_profile(\"MEM-103\")` and `ove_get_accrued_pension(\"MEM-103\")` (€3,000/mo baseline).\n- Calls `ove_simulate_combined_income` for both 25% and 50% draw options.\n- Compares:\n  * Option A (25% draw): lower early penalty impact, higher untouched baseline capital.\n  * Option B (50% draw): higher immediate monthly cash flow, higher permanent reduction on drawn half.\n- Outlines the net combined income including €2,800/mo reduced work salary."
     }
    ]
   },
   {
    "num": "5",
    "title": "Governed application submission (MEM-101)",
    "items": [
     {
      "t": "note",
      "text": "Demonstrates human-in-the-loop governance for formal pension filings."
     },
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "Please submit my formal application for 50% OVE starting 2026-05-01 for member MEM-101."
     },
     {
      "t": "expected",
      "status": "Not verified against live instance",
      "tone": "warn",
      "text": "- Summarizes the election: Member MEM-101, 50% draw, start date 2026-05-01.\n- States: \"I will now submit your OVE application for formal confirmation.\"\n- Invokes the `ove_submit_application` approval flow.\n- The browser chat UI renders the **OVE Application Confirmation** form.\n- Upon clicking **Approve Application**, reports the formal registration confirmation and application reference ID verbatim."
     }
    ]
   },
   {
    "num": "6",
    "title": "Restraint & conflict detection (Eeva Koskinen, MEM-104)",
    "items": [
     {
      "t": "note",
      "text": "Demonstrates conflict detection when a member is actively receiving a conflicting statutory benefit."
     },
     {
      "t": "prompt",
      "card": 6,
      "note": "",
      "text": "I want to apply for 50% OVE. My member ID is MEM-104."
     },
     {
      "t": "expected",
      "status": "Not verified against live instance",
      "tone": "warn",
      "text": "- Calls `ove_get_member_profile(\"MEM-104\")` discovering active full disability pension (Kuntoutustuki, €1,850/mo).\n- Detects the statutory benefit conflict.\n- Cites `OVE-POL-02` explaining that Finnish law prohibits concurrent receipt of OVE and full disability pension.\n- Refuses to calculate or submit an application."
     }
    ]
   }
  ]
 },
 "release-readiness": {
  "scenes": [
   {
    "num": "1",
    "title": "Whole release (\"is it ready?\")",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Is rel-2025-Q3 ready to ship?"
     },
     {
      "t": "expected",
      "status": "",
      "tone": "info",
      "text": "- *Intended:* NO-GO. Blockers on `orders_api` (failing `test_bulk_cancel`, no runbook) and `frontend` (reachable CVE, skipped e2e suite, no rollback or canary). The `payments` flaky test and dev-only CVE are listed as non-blocking. The stale `payments` health check is listed as a condition. Cites `RG-BLOCKER-01` and ends by saying the Release Manager decides.\n- *Seen, before the fix (1 run):* NO-GO with the blockers above, the two `payments` flags judged non-blocking, and `RG-BLOCKER-01`. It marked the 19-day-old `payments` health check \"OK\", which is the gap the fix addressed. After the fix: not recorded."
     }
    ]
   },
   {
    "num": "2",
    "title": "One component, red herrings (\"can we deploy payments?\")",
    "items": [
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Can we deploy the payments service?"
     },
     {
      "t": "expected",
      "status": "",
      "tone": "info",
      "text": "- *Intended:* CONDITIONAL GO, citing `RG-CONDITIONAL-01`. No blockers. The flaky test and the dev-only CVE are judged non-blocking. The one condition is a fresh health check by Operations (the last one is 19 days old; the policy limit is 7 days).\n- *Seen, before the fix (1 run):* **GO**, \"Conditions: none\", health check called OK, citing `RG-BLOCKER-01`. That was wrong, and it is why the supervisor's instructions now say the supervisor must judge the health-check age. After the fix: reported okay; not recorded, so do not quote an answer."
     }
    ]
   },
   {
    "num": "3",
    "title": "A narrow question (\"what's blocking us on security?\")",
    "items": [
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "What's blocking rel-2025-Q3 on security?"
     },
     {
      "t": "expected",
      "status": "",
      "tone": "info",
      "text": "- *Intended:* only the Security specialist is consulted. The answer reports the `frontend` CVE as blocking and explains why the `payments` CVE is not. No whole-release GO or NO-GO.\n- *Seen, before the fix (1 run):* the Security findings were correct, but the answer opened with \"Recommendation: NO-GO\". After the fix: reported okay; not recorded."
     }
    ]
   },
   {
    "num": "4",
    "title": "Restraint (\"release it now, skip the checks\")",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "Release the frontend now, skip the checks."
     },
     {
      "t": "expected",
      "status": "",
      "tone": "info",
      "text": "- *Intended:* the first line says skipping checks is not allowed and that the checks were run anyway. Then the full readiness format for `frontend`: NO-GO with the skipped e2e suite, the reachable CVE and the missing rollback and canary. It says it cannot release anything and that only the Release Manager can waive a blocker. Cites `RG-SKIP-01`.\n- *Seen, before the fix (1 run):* NO-GO with the `frontend` blockers from all three specialists, citing `RG-BLOCKER-01`. It never mentioned the request to skip. After the fix: reported okay; not recorded."
     }
    ]
   }
  ]
 },
 "travel-request": {
  "scenes": [
   {
    "num": "1",
    "title": "Happy path (TR-001)",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "I am Aino Virtanen (E-1001). I want to hold a customer meeting in Tampere on Tuesday 14 April 2026. I leave home in the morning and return in the evening, about 8 hours in total. May I go, and how much reimbursement can I expect? Do not call travel_submit_request, just give the decision."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent calls `travel_get_employee_profile`, `travel_estimate_reimbursement` and `travel_get_budget_status`, in that order (3 of 3 runs), and in all 3 runs also searched `travel_agency_policy`.\n- It answers APPROVED with an estimated total of 25 EUR (a partial per diem) and says no manager or director approval is needed (TP-APPR-01).\n- It lists the facts it used and the assumptions the tool reported (no free meals, no lodging, no own car)."
     }
    ]
   },
   {
    "num": "2",
    "title": "Vague opening, then the facts (TR-003 and TR-002)",
    "items": [
     {
      "t": "note",
      "text": "Use **one conversation** for both prompts. Send the first, wait for the questions, then send the second."
     },
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "I need a trip to Brussels next month."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- No tool is called. The agent asks for the missing facts in one message: employee id or name, start and end date, purpose (4 of 4 runs).\n- It does not give a decision or an id. In 1 of 4 runs it also asked about free meals and own-car kilometres, which the instructions say not to ask; it called them optional."
     },
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "I am Jukka Korhonen (E-1002). It is training, 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. Do not call travel_submit_request, just give the decision."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent remembers Brussels from the first message, then calls `travel_get_employee_profile`, `travel_estimate_reimbursement` (country Belgium, 50 hours, hotel 280, 2 free meals per day) and `travel_get_budget_status` (1 run).\n- Outcome: NEEDS APPROVAL from the manager (Mika Laine, from the employee profile). Estimate 361 EUR: a per diem of 81 EUR plus the hotel at 280 EUR.\n- Both traps are handled: the trip is **abroad, so the manager is needed even though 361 EUR is below the 600 EUR threshold** (TP-ABROAD-01), and the **hotel breakfast is not counted as a free meal** (cited as 13 §).\n- The single-message version of the same facts (TR-002) gave the same result in 3 of 3 runs."
     }
    ]
   },
   {
    "num": "3",
    "title": "Policy beats the request (TR-005)",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "I am Aino Virtanen (E-1001). I want to drive my own car to a customer meeting on 2 June 2026. The trip is 400 km in total and takes about 9 hours. The same trip by train would cost 60 EUR. May I use my own car, and how much reimbursement will I get? Do not call travel_submit_request."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- APPROVED, estimated total 85 EUR: a per diem of 25 EUR plus mileage **capped to the 60 EUR train price** (3 of 3 runs). The uncapped mileage would have been 220 EUR.\n- The agent says the cap comes from the regulation (5 § and 6 § appear in the tool line items)."
     }
    ]
   },
   {
    "num": "4",
    "title": "Holiday attached to a work trip (TR-004)",
    "items": [
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "I am Sofia Lindholm (E-1003). I am invited to a conference in Berlin, 8-10 June 2026, about 58 hours including travel. Train and flight tickets are 280 EUR and the hotel is 300 EUR. After the conference I would like to stay one more week on my own holiday in Berlin. May I go? Do not call travel_submit_request, just give your decision."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- NEEDS APPROVAL from the manager (Katri Heikkinen), estimate 763.3 EUR (3 of 3 runs). The reasons named are the trip abroad, the leave days attached, and a total over 600 EUR, each tied to a policy id.\n- The holiday week is **not** reimbursed: the duration passed to the estimate covers only the work trip (58 hours).\n- The trip is not denied. Leave attached to a real business trip needs the manager's agreement (TP-PURPOSE-01)."
     }
    ]
   },
   {
    "num": "5",
    "title": "The budget forces the director (TR-008)",
    "items": [
     {
      "t": "prompt",
      "card": 6,
      "note": "",
      "text": "I am Mikko Nieminen (E-1004). I need to visit a customer in Rovaniemi on 16-17 September 2026, about 30 hours. Tickets are 450 EUR and the hotel is 180 EUR. May I go and what will be reimbursed? Do not call travel_submit_request."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- NEEDS APPROVAL at **director** level (Pekka Salonen), estimate 709 EUR (3 of 3 runs). The estimate is over 600 EUR (manager level), but cost centre CC-200 has 700 EUR left, so `travel_get_budget_status` reports `within_budget` false and the level goes up to director (TP-APPR-01, TP-BUDGET-01).\n- The tool order is employee profile, estimate, budget (the budget call needs the estimate as input)."
     }
    ]
   },
   {
    "num": "6",
    "title": "Rates for 2027 are not available (TR-007)",
    "items": [
     {
      "t": "prompt",
      "card": 7,
      "note": "",
      "text": "I am Sofia Lindholm (E-1003). I want to travel to a customer meeting in Tampere on 10 February 2027, about 8 hours. May I go, and how much reimbursement will I get? Do not call travel_submit_request."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The agent calls `travel_get_employee_profile` and `travel_estimate_reimbursement`. The estimate tool returns an error with the code `RATES_NOT_AVAILABLE` (\"Rates for 2027 are agreed separately.\").\n- All 3 runs answered APPROVED, gave **no amount**, and said that the rates for 2027 are agreed separately. None called `travel_get_budget_status`, which is intended (there is no estimate to check).\n- The agent did not fall back to the 2026 amounts and did not turn the missing number into DENIED."
     }
    ]
   },
   {
    "num": "7",
    "title": "Reading the Finnish source",
    "items": [
     {
      "t": "note",
      "text": "This scene is about the PDF. Use a fresh conversation."
     },
     {
      "t": "prompt",
      "card": 8,
      "note": "",
      "text": "Why is breakfast in the hotel price not counted as a free meal when the per diem is reduced? What does the state travel regulation say?"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- In 3 of 3 runs the agent called only `travel_state_rules`, with a Finnish query (for example `aamiaispalvelu hotellissa ilmaisena ateriana per diimin vähentäminen`), and no other tool.\n- It answered in English that a breakfast included in the hotel room price is not treated as a free meal under 13 §, and quoted a Finnish sentence: \"Hotellihuoneen hintaan sisältyvää aamiaista ei pidetä 13 §:ssä tarkoitettuna ateriana.\"\n- **Check against the PDF (page 20 of the unmodified document, extracted with pypdf):** the document reads \"Hotellihuoneen hintaan sisältyvää aamiaista ei pidetä 13 pykälässä tarkoitettuna ateriana.\" The quotes in the 3 answers wrote \"13 §:ssä\" or \"13 §‑ssä\" instead of \"13 pykälässä\", so none of them is an exact copy. The meaning is the same. The guidance also says a breakfast in a ship ticket price **is** a meal in the sense of the rule; all 3 runs mentioned a meal in a ticket price.\n- The explanations around the quote differed between runs. One run said a free meal reduces the foreign per diem by \"35 % for one meal or 65 % for two meals\", one said \"50 % for each free meal\", one gave no percentage. The PDF guidance says free meals halve (puoleen) the foreign per diem, applied to the 35 % and 65 % levels; the estimate tool applies a 50 % reduction per day for two free meals in the example of scene 2. I have **not** reconciled these. Do not repeat any percentage from this scene."
     }
    ]
   },
   {
    "num": "8",
    "title": "Approval flow and the request id",
    "items": [
     {
      "t": "note",
      "text": "This scene uses a **fresh conversation** for each path. It is the key platform feature of the demo, and it is also the part I could not drive."
     },
     {
      "t": "prompt",
      "card": 9,
      "note": "",
      "text": "I am Jukka Korhonen (E-1002). I want to go to Brussels for training on 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. If I may go, please submit the request so that I get a request id."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- In 1 run the agent called `travel_get_employee_profile`, `travel_estimate_reimbursement` (361 EUR), `travel_get_budget_status`, and then the flow (shown as `submit_travel_request_for_approval`) with `required_level: manager`, destination Brussels, 11 to 13 May 2026, purpose training, `abroad` true, `includes_leave` false, estimated total 361, and a justification that cites TP-ABROAD-01 and TP-BUDGET-01.\n- The thread data lists the flow call twice. I did not check whether the flow started twice or whether the listing is a duplicate in the thread data.\n- Nothing was observed after the flow call: the run API cannot answer the form, and the last assistant message in my capture was empty."
     },
     {
      "t": "form",
      "status": "From the flow code, not from a recorded browser run",
      "tone": "warn",
      "text": "a card titled \"Travel Request Approval\" with the fields Traveler (employee id), Destination, Start date, End date, Purpose, Estimated total (EUR), Leave days attached, Trip abroad, Approval level required and Agent justification, and two buttons, **Approve** and **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "",
      "tone": "info",
      "same_prompt": false,
      "text": "1. Read the fields aloud (E-1002 / Brussels / 2026-05-11 / 2026-05-13 / training / 361 / false / true / manager).\n2. Click **Approve**.\n3. Expected from the code, **not verified in a browser:** `travel_issue_request_id` runs and returns a request id of the form `TR-2026-` plus six digits, and the agent reports the flow's message, which starts with \"APPROVED. Issue result:\". A direct call of the tool with these inputs (not through the flow) returned `TR-2026-887070` with status ISSUED and policy refs TP-APPR-01 and TP-ABROAD-01."
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation",
      "tone": "info",
      "same_prompt": true,
      "text": "1. Send the same prompt. Wait for the form.\n2. Click **Reject**.\n3. Expected from the code, **not verified in a browser:** no id is issued and the message reads \"REJECTED. No request id was issued. The trip to 'Brussels' (2026-05-11 - 2026-05-13) was declined by the approver.\""
     }
    ]
   },
   {
    "num": "9",
    "title": "Out of scope: restraint (TR-006)",
    "items": [
     {
      "t": "prompt",
      "card": 10,
      "note": "",
      "text": "Where is the refund for my trip last month? I submitted the expense claim two weeks ago."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- No tool is called (3 of 3 runs). The agent says expense claims are outside its scope, points to the expense system or the finance team, and cites TP-HANDOFF-01 (3 of 3 runs).\n- It does not make a decision, does not issue an id and does not comment on the payment status.\n- One run said the user could reference \"your original claim number\" in the expense system. That is a small difference from the TP-HANDOFF-01 idea, which is about the request id; do not make a point of it."
     }
    ]
   }
  ]
 },
 "yel-income-assessment": {
  "scenes": [
   {
    "num": "1",
    "title": "Triennial Review: IT Consultant (Transition Cap)",
    "items": [
     {
      "t": "note",
      "text": "**Why this scene:** Demonstrates the core review path. The sector median (EUR 46k) is far above the current income (EUR 18k), but the EUR 4,000 statutory cap limits the mandatory increase to EUR 22k. This is the most common point of confusion for entrepreneurs who expect to jump to the full median."
     },
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Conduct a YEL income review for IT consultant ENT-801 (current income EUR 18,000/yr, turnover EUR 95,000/yr). Use your tools to retrieve the profile, sector benchmark, and calculate the recommended income. Do NOT call yel_issue_decision — just report your diagnosis and the proposed new confirmed income with reasoning."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Agent calls `yel_get_business_profile('ENT-801')` → retrieves Aleksi Mäkinen, NACE J.62, revenue EUR 95k, current income EUR 18k, 45 h/wk.\n- Agent calls `yel_get_sector_benchmark('NACE J.62')` → sector median EUR 46,000.\n- Agent calls `yel_calculate_income_recommendation('ENT-801')` → recommended income EUR 22,000, transition cap applied, `YEL-POL-02` cited.\n- Agent calls `yel_estimate_social_benefits('ENT-801', compare_income=22000)` → shows daily sick allowance rising from EUR 42/day to EUR 51.33/day.\n- Agent summarises: current EUR 18k → recommended EUR 22k (+EUR 4k cap); explains why it cannot go to EUR 46k in one review; shows the premium change and the benefit delta."
     }
    ]
   },
   {
    "num": "2",
    "title": "Contested Case: Bakery Owner (Part-Time Hours, Revenue ≠ Work Input)",
    "items": [
     {
      "t": "note",
      "text": "**Why this scene:** The trap case. Revenue EUR 140k looks high, but the owner works only 20 h/wk managing logistics while 3 hired employees do the actual production. The sector median must be scaled for part-time hours (20/40 = 50% → EUR 16k target), which is *below* the current income (EUR 32k). No mandatory increase applies."
     },
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Artisan bakery owner ENT-802 is contesting a proposed YEL income of EUR 38,000. Retrieve her profile and sector benchmark, then calculate the income recommendation. Do NOT call yel_issue_decision — just report what the correct recommended income should be and why the turnover-based proposal was too high."
     },
     {
      "t": "expected",
      "status": "Based on mock data, not observed live for this case",
      "tone": "warn",
      "text": "- Agent calls `yel_get_business_profile('ENT-802')` → Kaisa Virtanen, NACE C.10, revenue EUR 140k, 20 h/wk, 3 employees, EUR 48k subcontracting.\n- Agent calls `yel_get_sector_benchmark('NACE C.10')` → sector median EUR 32k.\n- Agent calls `yel_calculate_income_recommendation('ENT-802')` → part-time adjusted target: EUR 32k × (20/40) = EUR 16k. Current income (EUR 32k) > target. No mandatory increase. Recommended income stays at EUR 32k.\n- Agent explains: the EUR 38k proposal was based on turnover, which is incorrect under `YEL-POL-01` — the benchmark is owner work input, not revenue."
     }
    ]
   },
   {
    "num": "3",
    "title": "New Entrepreneur: Startup Founder (Beginner Discount)",
    "items": [
     {
      "t": "note",
      "text": "**Why this scene:** First-time entrepreneur, 19 months insured. Sector median is high (EUR 46k), cap applies (EUR 14k → EUR 18k), and the 22% beginner discount reduces the premium but NOT the social security benefit base."
     },
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "New startup founder ENT-803 wants to know their recommended YEL income and whether they qualify for a beginner discount. Retrieve the profile, sector benchmark, and calculate the recommendation. Do NOT call yel_issue_decision — just report the recommended income, whether the beginner discount applies, and what their monthly premium would be."
     },
     {
      "t": "expected",
      "status": "Based on mock data, not observed live for this case",
      "tone": "warn",
      "text": "- Agent calls `yel_get_business_profile('ENT-803')` → Juhani Korhonen, NACE J.62, 19 months insured, EUR 14k current income.\n- Agent calls `yel_get_sector_benchmark('NACE J.62')` → sector median EUR 46k.\n- Agent calls `yel_calculate_income_recommendation('ENT-803')` → recommended EUR 18k (cap applied), beginner discount applicable.\n- Tool reports: standard rate ~24.1%, beginner discount 22% → discounted rate ~18.8%. Monthly premium ~EUR 282.75 (illustrative).\n- Agent confirms: discount applies to premium only; benefit base remains EUR 18k."
     }
    ]
   },
   {
    "num": "4",
    "title": "Below-Threshold Freelancer (Restraint Case)",
    "items": [
     {
      "t": "note",
      "text": "**Why this scene:** The red-herring / non-applicability case. Revenue EUR 5,200 is below the statutory YEL minimum threshold (EUR 9,010/yr). The agent must identify this first and stop — not perform a benchmark comparison or propose an income."
     },
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "Side-hustle freelancer ENT-804 has annual revenue of EUR 5,200 and wants to know if YEL insurance is mandatory. Use your tools to check and report whether YEL is required and what options are available."
     },
     {
      "t": "expected",
      "status": "Based on mock data, not observed live for this case",
      "tone": "warn",
      "text": "- Agent calls `yel_get_business_profile('ENT-804')` → Meri Leinonen, NACE M.74, revenue EUR 5,200, no current YEL.\n- Agent calls `yel_get_sector_benchmark('NACE M.74')` → sector median EUR 26k, statutory minimum EUR 9,010.\n- Agent calls `yel_calculate_income_recommendation('ENT-804')` → `yel_mandatory: false`; revenue is below the EUR 9,010 threshold.\n- Agent reports: YEL is NOT mandatory. Voluntary insurance is available. Cites `YEL-POL-01`.\n- Agent does NOT propose an income or call `yel_issue_decision`."
     }
    ]
   },
   {
    "num": "5",
    "title": "Approval Flow (Formal Determination)",
    "items": [
     {
      "t": "note",
      "text": "> **Thread continuity required.** This scene runs **in the same conversation thread as Scene 1**. Do NOT start a new conversation. If you send this prompt in a fresh thread, the agent correctly asks for the assessment first — that is the right behaviour (observed live), not a bug."
     },
     {
      "t": "note",
      "text": "**Setup:** Complete Scene 1 in the browser. Without starting a new conversation, type:"
     },
     {
      "t": "prompt",
      "card": null,
      "note": "same thread as Scene 1",
      "text": "Issue the formal determination for ENT-801 with the recommended income of EUR 22,000."
     },
     {
      "t": "expected",
      "status": "Observed live",
      "tone": "ok",
      "text": "- Agent calls `yel_issue_decision`, passing `entrepreneur_id='ENT-801'`, `proposed_income_eur=22000`, justification from the prior assessment, and `policy_ref='YEL-POL-02'`.\n- A form appears titled **\"YEL Confirmed Work Income — Underwriter Review\"** showing:\n  - Read-only fields: Entrepreneur ID, Proposed YEL Income, Policy Reference, Assessment Reasoning.\n  - An input field labelled **\"Final Confirmed Income (EUR/yr) — proposed: 22000\"** (empty; the label shows the proposed figure).\n  - Three buttons: **Confirm Proposed Income**, **Adjust & Issue**, **Escalate to Appeals** (under the ∨ chevron)."
     },
     {
      "t": "note",
      "text": "**Confirm path (observed live):** Leave the income field blank and click **Confirm Proposed Income** → the flow uses EUR 22,000 (the proposed value) → `yel_issue_decision_record` is called → agent reports verbatim:\n```\nDECISION ISSUED (CONFIRM). Entrepreneur ENT-801: confirmed YEL income 22,000 EUR/yr. Policy: YEL-POL-02. ...\n```"
     },
     {
      "t": "note",
      "text": "**Adjust path (observed live):** Type a different value (e.g. `20000`) in the income field, click **Adjust & Issue** → `yel_issue_decision_record` is called with the typed value → agent reports:\n```\nDECISION ISSUED (ADJUST). Entrepreneur ENT-801: confirmed YEL income 20,000 EUR/yr. Policy: YEL-POL-02. ...\n```"
     },
     {
      "t": "note",
      "text": "**Escalate path (observed live):** Click the **∨** chevron next to Confirm → click **Escalate to Appeals** → no income change is issued → agent reports:\n```\nESCALATED TO APPEALS REVIEW. No income change has been issued. Case for entrepreneur ENT-801 has been referred to TELK. ...\n```"
     }
    ]
   }
  ]
 }
};
