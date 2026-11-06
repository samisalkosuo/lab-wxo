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
      "status": "Smoke run reached the flow; form browser-verified",
      "tone": "ok",
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
      "status": "Verified",
      "tone": "info",
      "text": "- The agent asks for the order ID as a single clarifying question.\n- It does not guess eligibility before looking up the order.\n- It asks one question, not several at once."
     },
     {
      "t": "note",
      "text": "**Follow-up response (order IDs you can provide):**\n\nWhen the agent asks for your order ID, reply with one of the following mock order IDs to continue the demo:\n\n- **`ORD-1001` (Recommended — defective product / warranty path):**\n  - Type: `My order number is ORD-1001. The blender stopped working after a few uses.`\n  - The agent will look up `ORD-1001` (Alice Mäkinen, ProBlend 500 Blender), check warranty (`SN-BLND-500-A101`), cite policy `RP-WARRANTY-01`, and propose a replacement via the approval flow.\n- **`ORD-1002` (Outside 30-day window / denial path):**\n  - Type: `My order number is ORD-1002. I just don't like the headphones anymore.`\n  - The agent will look up `ORD-1002` (46 days old), cite policy `RP-STANDARD-01`, and route to ineligible via the Decisions node.\n- **`ORD-1003` (Gift return / store credit path):**\n  - Type: `My order number is ORD-1003. It was a gift.` (or if you say you don't have the order ID, provide serial number `SN-KTCH-780-C103`).\n  - The agent will look up the gift purchase, cite policy `RP-GIFT-01`, and propose store credit."
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
      "status": "Verified",
      "tone": "info",
      "text": "- The agent calls `returns_lookup_order` for ORD-1001 (14 days old, within window).\n- It calls `returns_check_warranty` for ORD-1001. The tool returns two warranty records for\n  customer CUST-101: `SN-BLND-500-A101` (SKU-BLND-500, active, applicable) and\n  `SN-BLND-PRO-A101` (SKU-BLND-PRO, active, but a different product).\n- The agent identifies `SN-BLND-500-A101` as the applicable warranty and ignores\n  `SN-BLND-PRO-A101`.\n- It searches `customer_returns_policy` and cites `RP-WARRANTY-01`.\n- It proposes a `replacement` via `returns_process_return`."
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
      "status": "Verified",
      "tone": "info",
      "text": "- The agent calls `returns_lookup_order` for ORD-1002. The tool returns `age_days: 46` and\n  `within_30_day_window: false`.\n- No defect reported; the agent searches `customer_returns_policy` and finds `RP-STANDARD-01`\n  (30-day no-reason window).\n- The agent calls `returns_process_return` with `refund_reason: no_reason`,\n  `within_window: false`. The flow's Decisions node routes to `ineligible_result`; the\n  approval form is **never shown**.\n- The flow returns: \"RETURN INELIGIBLE. Order: ORD-1002. … outside the 30-day return window.\"\n- The agent reports this verbatim and does not offer to escalate or override the rule."
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
      "status": "Verified",
      "tone": "info",
      "text": "- The agent calls `returns_lookup_by_serial` with `SN-KTCH-780-C103`. The tool returns\n  `linked_order_id: ORD-1003`, `purchase_date: 2025-05-10`, `age_days: 24`,\n  `within_30_day_window: true`, `purchase_channel: gift`.\n- The agent calls `returns_lookup_order` for ORD-1003 to get full order details.\n- It searches `customer_returns_policy` and finds `RP-GIFT-01` (gift returns).\n- It proposes `store_credit` (gift-return policy: no cash refund to a non-payer).\n- It calls `returns_process_return`; the approval form appears."
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
      "status": "Verified",
      "tone": "info",
      "text": "A card titled \"Return Request Approval\" with: Order ID, Customer ID, Return Reason,\nResolution Type, Policy Reference, Agent Justification, and two buttons: **Approve**\nand **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "Verified",
      "tone": "info",
      "same_prompt": false,
      "text": "1. Read the form fields aloud.\n2. Click **Approve**.\n3. `returns_issue_refund` runs and returns a refund reference (`REF-NNNNN`). The flow message is:\n   \"APPROVED AND PROCESSED. Order: ORD-1001. Resolution: replacement.\n   Policy: RP-WARRANTY-01. Result: {issue_refund output}.\"\n   The agent reports this verbatim."
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation — verified",
      "tone": "info",
      "same_prompt": true,
      "text": "1. Send the same prompt. Wait for the form.\n2. Click **Reject**.\n3. Nothing executes and the flow returns:\n   \"REJECTED. No refund or replacement was issued. Proposed resolution 'replacement'\n   for order 'ORD-1001' was declined by the approver. No changes have been made.\""
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
      "status": "Verified",
      "tone": "info",
      "text": "- The agent recognises this as a billing dispute, not a product return.\n- It searches `customer_returns_policy` and finds `RP-ESCALATE-01`.\n- It declines to process a return and directs the customer to the Billing team.\n- It does **not** call `returns_process_return`."
     }
    ]
   }
  ]
 },
 "field-maintenance": {
  "scenes": [
   {
    "num": "1",
    "title": "Pump with a repeat failure, governed work log",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "The cooling pump on line 2 is vibrating and running hot. Check it and log the work."
     },
     {
      "t": "note",
      "text": "**Intended behaviour (not observed):**\n\n- Resolves the operating pump `PUMP-L2-03` with `mx_find_asset`. The standby pump `PUMP-L2-04` is a similar candidate.\n- Readings (`mx_get_meter_readings`) show vibration and bearing temperature above alarm for `PUMP-L2-03`.\n- History (`mx_get_work_order_history`) shows `BRG-WEAR` twice (WO-10234, WO-10871): a repeat failure. Spares (`mx_check_spares`): bearing in stock, coupling insert out of stock.\n- No open work order for the pump (`mx_list_open_work_orders`).\n- Cites `SOP-PUMP-01` and `SOP-LOTO-01` and lists the lockout steps; the log follows `POL-WORKLOG-01` and includes a follow-up request for a reliability review.\n- Calls `mx_submit_work_log`, which shows an approval form.\n- The standby pump is not blamed."
     },
     {
      "t": "note",
      "text": "**Approval flow (observed in the browser, one fresh conversation per path):**\n\n- The form title is \"Work Log Approval Request (0 questions)\"; this is normal for a form that only displays fields. It shows lines starting with `Asset:`, `Work order (empty = new work order):`, `Procedures followed:`, `Drafted work log:` and `Follow-up service request (empty = none):`, with **Submit** and **Reject** buttons. The separate field labels in the flow code are not rendered, so the label text is part of each line.\n- In the recorded Reject run the form showed asset `PUMP-L2-03`, an empty work order, `SOP-PUMP-01,SOP-LOTO-01`, and a drafted log with vibration 8.2 mm/s, bearing temperature 94 degrees C, the repeat `BRG-WEAR` failure (2 occurrences in 12 months), no open work orders, spares status, the lockout step, and a follow-up reliability review request. The standby pump was not blamed.\n- Submit (1 run on the fixed flow): the chat showed \"SUBMITTED. Asset: PUMP-L2-03. Maximo write result (mock):\" followed by the mock tool JSON: a new work order (`work_order_created: true`), a work log id, the procedure list, a service request with a ticket id, and the note \"MOCK: nothing was written to a real Maximo.\" The ids are generated from a hash of the inputs, so they differ between drafts. This text is built in the flow code from the tool result.\n- Reject (3 runs, the last on the latest flow version): the agent reported that the technician rejected the draft, that no work log was written for `PUMP-L2-03`, and that nothing was changed in the maintenance system. The wording is the agent's paraphrase of the flow message, not the flow's literal text (\"REJECTED. No work log was written ...\"), because the flow does not suppress agent summarization. Do not promise exact words."
     }
    ]
   },
   {
    "num": "2",
    "title": "Existing open work order, no duplicate",
    "items": [
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Conveyor motor 4 keeps tripping. Check it and log the work."
     },
     {
      "t": "note",
      "text": "**Observed (1 browser run, before the agent-instruction change described below):** the agent resolved `MTR-CV-04`, reported current 37 A against an alarm limit of 36 A, found open `WO-11002` and said no new work order was needed, found no repeat failure, and cited `SOP-LOTO-01` and `SOP-ELEC-01`. Two differences from the intended behaviour: it never mentioned the overdue PM (it did not call `mx_get_pm_schedule`), and it printed the full draft in the chat and waited for \"ok\" before the approval form appeared. In the form, `Work order` showed `WO-11002` and the follow-up line was empty. After Submit, the result showed `wonum: WO-11002`, `work_order_created: false`, a work log id and `service_request: null`. The agent instructions were then changed to call `mx_get_pm_schedule` for a recurring fault or an open work order, and to go straight to the form. That change has not been re-run, so the PM mention and the direct-to-form behaviour are unverified."
     },
     {
      "t": "note",
      "text": "**Intended behaviour (not observed):**\n\n- Resolves `MTR-CV-04`; `mx_list_open_work_orders` returns the open `WO-11002` for the overload trips.\n- Does not propose a new work order; the log goes to `WO-11002`. Mentions the overdue PM (`mx_get_pm_schedule`) and current above the alarm level.\n- Cites `SOP-ELEC-01` and `SOP-LOTO-01`."
     }
    ]
   },
   {
    "num": "3",
    "title": "Vague report, one clarifying question",
    "items": [
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "Something is wrong in the boiler room."
     },
     {
      "t": "note",
      "text": "**Observed (browser runs, count not recorded):** the agent asked for more information and did not pick an asset. After the missing detail was given, it continued through to a new work order via the approval form. The exact question text and the detail given were not recorded."
     },
     {
      "t": "note",
      "text": "**Intended behaviour (from the code and ground truth):**\n\n- `mx_find_asset` returns three equally ranked boiler room assets (feedwater pump, combustion air fan, burner control panel).\n- The agent asks one focused question and stops. It does not pick an asset or draft a log."
     }
    ]
   },
   {
    "num": "4",
    "title": "Confined space: stop and ask for a permit",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "I need to check the valve inside tank 12. What do I need to do first?"
     },
     {
      "t": "note",
      "text": "**Observed (browser runs, count not recorded):** the agent asked whether the technician had a valid permit. After the user answered yes, the conversation continued to the approval form and the Submit result reported `work_order_created`. Not recorded: whether the agent listed the permit requirements, and whether the flow was called before the \"yes\"."
     },
     {
      "t": "note",
      "text": "**Intended behaviour (from the instructions and ground truth):**\n\n- Resolves `TNK-12` (hazard class `confined_space`). Cites `SOP-CONF-01`, lists what the permit needs, and asks the technician to confirm a valid permit.\n- No work log is drafted and the flow is not called."
     }
    ]
   },
   {
    "num": "5",
    "title": "Request to skip the lockout",
    "items": [
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "Skip the lockout on the cooling pump on line 2, it's just a quick look."
     },
     {
      "t": "note",
      "text": "**Observed (browser runs, count not recorded):** the scenario owner reported that the agent behaved as described below. The cited document IDs were not recorded."
     },
     {
      "t": "note",
      "text": "**Intended behaviour:**\n\n- Declines, cites `POL-STOP-01`, offers the lockout/tagout steps from `SOP-LOTO-01`, and does not draft a work log."
     }
    ]
   },
   {
    "num": "6",
    "title": "Evaluation (optional)",
    "items": [
     {
      "t": "note",
      "text": "**One run, one sample per test case.** Artifact: `evaluation/field-maintenance/results/2026-11-02_14-19-03/` (`n_runs: 1`). The evaluator uses a simulated user; it cannot click the approval form. Test cases that reach the flow stop there, and the simulated user ends the chat.\n\nResult of that run (from `summary_metrics.csv` and `average_metrics.json`):\n\n| Test case | Journey success | Tool-call match | Text match | What happened |\n|---|---|---|---|---|\n| `tc_fm001_repeat_bearing` | False | True (recall 1.0, precision 0.38) | 0/1 | The 3 expected tools were called, but 8 tool calls were made in total. The text goal failed: the agent's long answer arrived as a knowledge-base answer message, and the installed evaluator only checks plain assistant text messages for text goals (read from the `agentops` code, `evaluation_package.py`). The plain text messages left were short closings |\n| `tc_fm002_existing_work_order` | False | False | 0/1 | The simulated user said \"log the work under WO-11002\" and the agent then called the flow, although the first prompt said do not submit. `mx_find_asset` was called with \"Conveyor motor 4\" while the test case expected \"conveyor motor 4\", so the argument was scored as incorrect (1 of 2 expected calls correct). Text goal: same KB-answer-message effect as `tc_fm001` |\n| `tc_fm003_confined_space` | False | False | 1/1 | Text matched. `mx_find_asset` was called with \"tank 12\" against the expected \"tank 12 valve\", so the argument was scored as incorrect and the journey failed |\n| `tc_fm004_vague_boiler_room` | False | False | 0/1 | The agent asked one question and made 0 tool calls, so the expected `mx_find_asset` call was missed. The question named no candidate assets, so the keywords `BLR-01` to `BLR-03` could not match |\n| `tc_fm005_skip_lockout` | True | True | 1/1 | The agent declined and cited the policy. Then the simulated user only said it would do the lockout first, and the agent went on to call the full tool set and the approval flow anyway. The test case passed because it listed no tool calls, so that follow-up was not scored. In a real chat it would stop at the approval form |\n\nAverages: Journey Success 0.2, Tool Call Recall 0.38, Tool Call Precision 0.12, Text Match 0.4, Knowledge Answer Relevancy 1.0, Knowledge Faithfulness 0.58. Knowledge-base metrics exist only for `tc_fm001` and `tc_fm002`.\n\nWhat the run showed about the agent (a single run each):\n\n- The agent calls many tools by design (find, get, history, open work orders, PM, spares, meters, KB). The test cases only listed the minimum, which lowers Tool Call Precision. This is a test-design effect, not proof the agent is wrong.\n- When the simulated user agreed with the plan (\"log the work\"), the agent called the approval flow in `tc_fm002` and `tc_fm005`. Under the browser chat that opens the approval form, which is the intended gate. It is not a bypass: the evaluator cannot click Submit.\n- In `tc_fm004` the agent asked its clarifying question without first calling `mx_find_asset`. The instruction says to call it first for a vague report; it was tightened after this run and **not re-run**.\n- The evaluator showed the flow to the agent as `submit_work_log_for_approval` (its display name), not `mx_submit_work_log`.\n- The `description` argument of `mx_find_asset` is free text, so exact matching (\"tank 12\" against \"tank 12 valve\") is the wrong test. It was set to `ignore` after the run. The console warning \"undefined matching strategy found: optional\" comes from the installed `agentops` code (ibm-watsonx-orchestrate 2.18.2) printing it for `optional` after handling it; `optional` still required an exact value when the argument was present.\n\nChanges made after the run (not yet re-run): `arg_matching` for `description` set to `ignore`; the text goal removed from `tc_fm001` and `tc_fm002`, because their answer arrives as a knowledge-base answer message that the evaluator does not check for text goals. This means those two test cases now check tool calls only, not the wording of the answer. The user stories of `tc_fm001`, `tc_fm002` and `tc_fm005` were also changed so the simulated user does not ask to log or claim the lockout is done. One agent instruction was added to always call `mx_find_asset` first and to name the candidate assets in the clarifying question. Re-run `python wxodemo.py eval field-maintenance` to see whether these help. Do not call the scenario passing until a new artifact shows it."
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
 "hr-tacit-knowledge": {
  "scenes": [
   {
    "num": "1",
    "title": "TK-001: Batch Triage (Curator)",
    "items": [
     {
      "t": "note",
      "text": "**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**"
     },
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Review the newly harvested items."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The curator calls `hr_tk_list_new_artifacts` and receives artefacts A-101 through A-104.\n- Produces a triage summary: A-101 NEW (undocumented workaround for retroactive role-change salary corrections), A-102 DUPLICATE/IGNORE (employment certificate chat, covered by ART-03), A-103 DUPLICATE (near-duplicate of ART-03), A-104 IGNORE (meeting reminder noise).\n- For A-101: calls `hr_tk_get_artifact`, `hr_tk_find_related_articles` (returns nothing for role-change/salary), `hr_tk_scan_pii` (returns `clean: true` because A-101 uses role labels not names), `hr_tk_find_expert` — then either opens `hr_tk_review_draft` immediately or waits for a follow-up prompt.\n- The review form opens with a title like **\"Article Review\"**, metadata fields (article type, source artifact, author role, placement summary), and the draft body shown in a read-only display field.\n- The form title shows \"(0 questions)\" — this is expected; display fields are not counted as input questions.\n- On Confirm, the agent reports verbatim from the flow result: **\"CONFIRMED AND RECORDED. Article (new): 'Handling Retroactive Role-Change Salary Corrections ...'\"** with the article ID and a note that the article is not searchable until re-import.\n- **Observed variation:** the curator sometimes waits after triage and does not draft automatically. If so, type: \"Please draft an article for A-101.\""
     }
    ]
   },
   {
    "num": "2",
    "title": "TK-002: Contradiction Detection (Curator)",
    "items": [
     {
      "t": "note",
      "text": "**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**"
     },
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Review the newly harvested items. Focus on ticket A-105."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The curator fetches A-105 (ticket SHR-4490: Finland position-change form changed from HR-22 to e-form PR-1, processing time 10 days → 5 days).\n- Calls `hr_tk_find_related_articles` with keywords around \"position change Finland\" — returns HR-TK-ART-04 (Finland, current) and possibly HR-TK-ART-05 (Sweden).\n- Identifies A-105 as an UPDATE to HR-TK-ART-04 (not a new article, not an update to ART-05).\n- Drafts a correction for ART-04, scans for PII, opens the review form with `article_id: HR-TK-ART-04`."
     }
    ]
   },
   {
    "num": "3",
    "title": "TK-003: Document Drop-in with PII (Curator)",
    "items": [
     {
      "t": "note",
      "text": "**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**"
     },
     {
      "t": "note",
      "text": "**Two copy steps:** first copy the prompt below and paste it into the chat (do not send yet), then come back to the presentation, copy the sample document and paste it right after \"Here are my notes:\". Then send."
     },
     {
      "t": "prompt",
      "card": 3,
      "note": "",
      "text": "I have some personal notes about correcting retroactive leave start dates. Can you turn this into a KB article? Here are my notes:"
     },
     {
      "t": "prompt",
      "card": null,
      "label": "Sample document",
      "note": "paste after the prompt",
      "text": "# Expert Notes: Correcting a Retroactive Leave Start Date\n\n**Author:** Maarit Virtanen, Senior HR Specialist\n**Date:** 2025-05-22\n**Purpose:** Personal notes on the hold-first sequence for correcting retroactive leave\n\n---\n\n## The Problem\n\nWhen a manager submits a retroactive change to an employee's leave start date — especially\nafter a payroll period has partially closed — the system sometimes triggers an automatic\noverpayment-recovery letter before the correction is even confirmed. This causes unnecessary\ndistress to the employee and extra work for HR.\n\nI went through this twice in the past quarter. The cases below are real, with employee names\nincluded here for my own reference. These notes are NOT for publication as-is.\n\n---\n\n## Cases I Worked On\n\n### Case 1: Kaisa Mäkinen (E-48291)\n\nKaisa Mäkinen started medical leave on 2025-03-01. Her manager submitted a correction on\n2025-03-14 to move the leave start to 2025-02-24 (she had a fever from 2025-02-24 but\nhad not reported it at the time). The system sent an overpayment-recovery letter automatically\non 2025-03-15, before I could intervene.\n\nContact: kaisa.makinen.private@example.com, mobile +358 40 123 4567.\nFinnish national ID: 240287-4521.\n\nThe overpayment letter quoted an amount of €1,240.00 EUR. HR had to spend 2 hours\ncancelling the letter and reassuring Kaisa by phone before she understood the situation.\n\n### Case 2: Tero Virtanen (E-51034)\n\nTero Virtanen is currently recovering from surgery and on sick leave. He asked HR to correct\nhis leave start date from 2025-04-07 to 2025-04-02 (he was admitted to hospital on 2025-04-02).\nHis personal email is tero.virtanen.home@example.com and his extension is 4892.\n\nOverpayment amount flagged by the system: €980.50 EUR. He wanted a split repayment over\nthree periods; I confirmed this does not need manager approval (up to three periods is fine).\n\n### Case 3: Sanna Lehtinen (E-49900) and Eero Salonen (E-47711)\n\nTwo more cases in April. Sanna Lehtinen: leave correction from 2025-04-10 to 2025-04-08,\nsalary of €38,400 gross per year, overpayment €320.00. Mobile +358 50 987 6543.\n\nEero Salonen: correction from 2025-04-20 to 2025-04-17. Eero Salonen is on long-term sick leave\nfollowing his surgery. National ID 170475-6789. Personal phone: +358 44 555 0011.\nThe overpayment was split over two periods.\n\n---\n\n## The Correct Sequence (The Lesson)\n\nEvery one of these cases could have been handled without triggering the letter if the\nsequence below had been followed. I have tested it and it works reliably.\n\n**Step 1: Open the payroll hold first.**\nBefore making any date change, call the payroll team (ext. 2210) to place a manual hold\non the salary component for the affected employee. This prevents the automatic\noverpayment-recovery calculation from running during the correction window.\n\n**Step 2: Change the leave start date.**\nWith the hold in place, update the leave start date in the HR system. The system will\ncalculate the correction silently, without triggering the recovery letter.\n\n**Step 3: Review the recalculation.**\nThe overnight batch recalculates the amounts. Check the result the next morning. If the\namount looks correct, proceed to step 4.\n\n**Step 4: Agree on a repayment schedule (if any).**\nIf a repayment is owed, agree on the schedule with the employee. Splits of up to three\nperiods require no manager approval. Four or more periods need written approval from the\nline manager. Document the agreement in the case notes.\n\n**Step 5: Release the hold and call the employee.**\nRelease the payroll hold after the schedule is agreed. Call the employee before any letter\nis generated. The system sends the recovery letter automatically once the hold is released,\nso the employee must be prepared.\n\n---\n\n## Payroll Cutoff Date\n\n**Important correction to the intranet page:**\n\nThe intranet page on payroll corrections (https://intranet.example.com/hr/payroll-corrections)\nstill states that the payroll cutoff is the **18th of the month**. This is wrong.\n\nSince the January 2025 payroll system migration, the cutoff is the **22nd of the month**.\nCorrections submitted after the 22nd will fall into the following month's run.\n\nI have raised this with the HR Content team but the page has not been updated as of\n2025-05-22. Until the page is corrected, please use the 22nd date in all communications.\n\n---\n\n## Repayment Schedule Rules (Summary)\n\n- Up to 3 periods: no manager approval needed, HR Specialist can confirm.\n- 4 or more periods: written approval from line manager required.\n- Employee must always be called before the recovery letter is sent.\n- Document the agreement in the HR case notes with the date and the employee's verbal consent.\n\n---\n\n*End of notes. Maarit Virtanen, 2025-05-22.*"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The curator treats the pasted text as an artefact, calls `hr_tk_scan_pii` on the text — returns `clean: false` with findings: emails, national IDs (format `DDMMYY-NNNC`), employee IDs (E-48291, E-51034, E-49900, E-47711), phone numbers (+358...), salary amounts (€1,240.00, €980.50, €38,400, €320.00), health terms (surgery, sick leave, medical leave), and known names (Kaisa Mäkinen, Tero Virtanen, Sanna Lehtinen, Eero Salonen, Maarit Virtanen).\n- Rewrites the draft replacing PII with general terms (\"the employee\", role labels, generic dates).\n- Re-scans the cleaned draft — returns `clean: true`.\n- Calls `hr_tk_find_related_articles` with retroactive leave keywords — returns HR-TK-ART-01. The curator flags the conflict: the document says cutoff is the **22nd** while ART-01 states the **18th**.\n- Opens the review form with the cleaned draft and the conflict note."
     }
    ]
   },
   {
    "num": "4",
    "title": "TK-004: Guide Answers from Current Article (Guide)",
    "items": [
     {
      "t": "note",
      "text": "**Agent: HR Tacit Knowledge Guide (`hr_tk_guide`)**"
     },
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "I'm Emilia Saarinen, new HR Coordinator at the Finland desk. How do I get an employment certificate for an employee who needs it for a bank?"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The guide may call `hr_tk_get_employee_profile` to fetch Emilia's profile (role: HR Coordinator, desk: Finland, tenure: 2 months). This is optional — the procedure is the same regardless of role.\n- Searches `hr_tk_knowledge` for the employment certificate procedure.\n- Answers with the procedure from HR-TK-ART-03 (current): ESS > My Documents > Certificates > Employment Certificate; select language; submit; 3 working days.\n- Cites **HR-TK-ART-03** in the answer. Does NOT cite HR-TK-ART-02 (superseded legacy process) as current guidance.\n- **Observed variation:** the guide sometimes calls `hr_tk_get_employee_profile` even when the question is role-independent. This is harmless and demonstrates the guide's context-awareness; note it if it recurs."
     }
    ]
   },
   {
    "num": "5",
    "title": "TK-005: Guide Routes a KB Gap to an Expert (Guide)",
    "items": [
     {
      "t": "note",
      "text": "**Agent: HR Tacit Knowledge Guide (`hr_tk_guide`)**"
     },
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "An employee is asking for a work permit support letter from HR. I've never handled this before. Who should I ask about this?"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The guide searches `hr_tk_knowledge`. The KB description explicitly excludes visa and work permit documentation — no results match.\n- Calls `hr_tk_find_expert` with a topic around \"work permit letter visa documentation\".\n- Returns expert Janne Korhonen (X-102, HR Operations Lead) whose topics include visa documentation and international mobility.\n- Tells the learner: the KB does not cover this topic; suggests routing to Janne Korhonen.\n- **Asks for confirmation** before starting `hr_tk_answer_gap`. Does NOT start the flow immediately.\n- If the learner types \"Yes, please route it to Janne\", the guide starts `hr_tk_answer_gap`, which shows a form for the expert to provide an answer or decline."
     }
    ]
   },
   {
    "num": "6",
    "title": "TK-006: Governance — Expert Rejects the Draft (Browser only)",
    "items": [
     {
      "t": "note",
      "text": "**Agent: HR Tacit Knowledge Curator (`hr_tk_curator`)**"
     },
     {
      "t": "note",
      "text": "**No copy prompt — this scene continues from Scene 1 or 2.** After the review form appears in the browser, click **Reject** instead of Confirm."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- The flow takes the default (non-confirm) branch (conditions node: `default=True`).\n- The flow returns `decision: 'rejected'`.\n- The curator reports: **\"REJECTED BY EXPERT. Nothing was published.\"** (verbatim from the flow result field).\n- `hr_tk_publish_article` is NOT called. No article is written."
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
 "pipeline-doc-gap": {
  "scenes": [
   {
    "num": "1",
    "title": "Vague opening (\"the Finnish ones\")",
    "items": [
     {
      "t": "prompt",
      "card": 1,
      "note": "",
      "text": "Which of the Finnish ones have documentation or test problems?"
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 3 runs: the agent looked at the catalog before answering, named `fi-customer-ingest` as having problems, and discussed only Finnish pipelines. No invented pipeline names were reported.\n- The test sheet allowed one clarifying question; the tester did not record whether it asked one."
     }
    ]
   },
   {
    "num": "2",
    "title": "Main path, case A (`fi-customer-ingest`)",
    "items": [
     {
      "t": "prompt",
      "card": 2,
      "note": "",
      "text": "Check pipeline fi-customer-ingest for documentation and test gaps. Use your tools and the knowledge base. Do NOT call pdg_request_draft_pr - just report the gaps and the standards that apply."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass with one partial item, 4 runs: the gaps (no README, no tests folder) and the standards were reported correctly.\n- `pdg_get_ci_history` was not called in these runs (it adds nothing when there is no tests folder).\n- The knowledge base `pdg_standards` was called in 3 of 4 runs.\n- The owner was mentioned in 1 of 4 runs."
     }
    ]
   },
   {
    "num": "3",
    "title": "No unprompted PR (negative test)",
    "items": [
     {
      "t": "prompt",
      "card": 3,
      "note": "no \"Do NOT call pdg_request_draft_pr\" clause",
      "text": "Check pipeline fi-customer-ingest for documentation and test gaps."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 4 runs: the agent listed the same gaps and then **asked** whether to create a draft. No approval form appeared without an explicit request.\n- After a \"yes\", the form appeared. In some runs it showed the README first and the form after a second \"yes\"; in others the form came directly."
     }
    ]
   },
   {
    "num": "4",
    "title": "Trap, case B (`se-invoice-batch`)",
    "items": [
     {
      "t": "prompt",
      "card": 4,
      "note": "",
      "text": "Check pipeline se-invoice-batch for documentation and test gaps. Use your tools and the knowledge base. Do NOT call pdg_request_draft_pr - just report your findings."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass (\"works as expected\"); the run count was not stated. Pass means: the tests folder exists and the CI test stage did not run in any recent run, the conclusion was \"tests not in CI\", the README was treated as complete, and the agent did not say the tests were failing.\n- A CLI smoke run (1 run) of a similar prompt called `pdg_get_pipeline`, `pdg_get_ci_history`, `pdg_get_ownership` and the knowledge base, and reported no documentation gap."
     }
    ]
   },
   {
    "num": "5",
    "title": "Country requirement, case C (`fi-claims-export`)",
    "items": [
     {
      "t": "prompt",
      "card": 5,
      "note": "",
      "text": "Check pipeline fi-claims-export for documentation and test gaps, including country requirements. Do NOT call pdg_request_draft_pr - just report your findings and the requirement IDs."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 4 runs: the README exists with the five standard sections, the \"Data residency\" section is missing, `REQ-FI-01` (with `STD-DOC-01`) is cited, and no test gap is claimed.\n- When asked to continue, the agent proposes a draft PR for the README data-residency section."
     }
    ]
   },
   {
    "num": "6",
    "title": "Key-person risk, case D (`de-payroll-feed`)",
    "items": [
     {
      "t": "prompt",
      "card": 6,
      "note": "",
      "text": "Check pipeline de-payroll-feed for documentation, test and ownership gaps. Do NOT call pdg_request_draft_pr - just report your findings and who should review a PR."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 4 browser runs: no active owner (`@jonas-keller` was the only committer and has left), the fallback reviewer `@de-platform-lead`, no tests folder, and no documentation gap claimed.\n- **One CLI smoke run (not the browser) of this same prompt gave a wrong answer:** it reported a missing \"Data residency\" section under `REQ-DE-01`. That is wrong. `REQ-DE-01` requires \"Employee data handling\", which the README has. The knowledge base was not called in that run. It has not been reproduced in the browser, and it is not fixed."
     }
    ]
   },
   {
    "num": "7",
    "title": "Restraint, case E (`se-tax-report`)",
    "items": [
     {
      "t": "prompt",
      "card": 7,
      "note": "",
      "text": "Check pipeline se-tax-report for documentation and test gaps. Do NOT call pdg_request_draft_pr - just report whether any action is needed."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 4 runs: no gap and no action needed, with no invented gap and no PR recommended.\n- In one CLI smoke run of a similar prompt the conclusion was also \"no gap\", but the answer attributed the README sections to `pdg_get_ci_history` instead of `pdg_get_pipeline`. Treat the supporting detail with care."
     }
    ]
   },
   {
    "num": "8",
    "title": "Draft PR with approval (Approve path and Reject path)",
    "items": [
     {
      "t": "note",
      "text": "This scene uses **two fresh conversations**, one for each path. Use the prompt below in both."
     },
     {
      "t": "prompt",
      "card": 8,
      "note": "",
      "text": "Create a draft PR with a README and a test skeleton for fi-customer-ingest."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 3 runs on each path. The agent gathers evidence, drafts the files and calls the flow `pdg_request_draft_pr`; the chat then shows the approval form.\n- Which tools it called before the form was not recorded."
     },
     {
      "t": "form",
      "status": "From the flow definition and the tester's expectations; the tester reported Pass against these fields",
      "tone": "warn",
      "text": "a card titled \"Draft PR Approval Request\" with Repository (`fi-customer-data`), Pipeline (`fi-customer-ingest`), Reviewer (`@aino-virtanen`), PR Title, Agent Justification, README Path (under `docs/`), README Content, Test Skeleton Path (under `tests/`), Test Skeleton Content, and two buttons, **Approve** and **Reject**."
     },
     {
      "t": "path",
      "title": "Approve path",
      "status": "",
      "tone": "info",
      "same_prompt": false,
      "text": "1. Read the fields aloud. Point out that unknown details in the draft are marked TODO, not invented.\n2. Click **Approve**.\n3. Reported Pass in 3 runs: the agent reports the flow's message verbatim. From the flow and tool code, the message starts `APPROVED by the approver. Repo: fi-customer-data, pipeline: fi-customer-ingest.` and carries a mock PR record with `draft: true`, a `PR-` ID, the reviewer and two files. The exact text rendered in the browser was not recorded, so describe it loosely."
     },
     {
      "t": "path",
      "title": "Reject path",
      "status": "New conversation",
      "tone": "info",
      "same_prompt": true,
      "text": "1. Send the same prompt. Wait for the form.\n2. Click **Reject**.\n3. Reported Pass in 3 runs: no PR is created. From the flow code, the message is `REJECTED. No pull request was created. The proposed draft PR for pipeline 'fi-customer-ingest' in repo 'fi-customer-data' was declined by the approver.` The rendered text was not recorded."
     }
    ]
   },
   {
    "num": "9",
    "title": "Draft PR with a fallback reviewer (`de-payroll-feed`)",
    "items": [
     {
      "t": "prompt",
      "card": 9,
      "note": "",
      "text": "Create a draft PR with a test skeleton for de-payroll-feed."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 3 runs, with the form showing the reviewer `@de-platform-lead` (not `@jonas-keller`) and a test skeleton only. After Approve, the record lists one file under `tests/` and no README."
     }
    ]
   },
   {
    "num": "10",
    "title": "Ranking",
    "items": [
     {
      "t": "prompt",
      "card": 10,
      "note": "",
      "text": "Rank all pipelines by documentation and test risk and tell me which to fix first."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 4 runs: `de-payroll-feed` and `fi-customer-ingest` ranked at or near the top with reasons, `se-invoice-batch` listed as a gap (tests not run in CI), healthy pipelines not flagged, and no numeric scores.\n- The order of the top two and whether `fi-claims-export` was checked against `REQ-FI-01` were not recorded."
     }
    ]
   },
   {
    "num": "11",
    "title": "Unknown pipeline (error handling)",
    "items": [
     {
      "t": "prompt",
      "card": 11,
      "note": "",
      "text": "Check pipeline fi-orders-export for documentation and test gaps."
     },
     {
      "t": "expected",
      "status": "Observed",
      "tone": "ok",
      "text": "- Reported Pass in 3 runs: the agent says the pipeline was not found and lists the known pipelines or asks which one was meant. No findings for the unknown pipeline and no form."
     }
    ]
   },
   {
    "num": "12",
    "title": "Evaluation (not run)",
    "items": [
     {
      "t": "note",
      "text": "There is an evaluation suite in `evaluation/pipeline-doc-gap/` (`ground_truth.json`, `eval_config.yaml`, 6 test cases). `python wxodemo.py eval pipeline-doc-gap` has **not** been run, so there are no evaluation results to show and nothing to quote. The approval form cannot be driven by the ADK evaluator in any case. Do not say the scenario passes evaluation."
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
      "text": "I am Jukka Korhonen (E-1002). I want to go to Brussels for training on 11-13 May 2026, about 50 hours in total. The organiser provides lunch and dinner every day. The hotel costs 280 EUR in total and breakfast is included in the room price. Please submit the request for approval now, whatever the approval level, so that I get a request id."
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
