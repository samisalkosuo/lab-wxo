# Customer Returns Agent

Conversational agent that handles product return and refund requests. The agent
investigates each case by looking up orders and warranties, consulting the return
policy knowledge base, and routing approved refunds through a governed approval flow.

## Teaching points

- **Agent / flow split:** the agent's open-ended reasoning identifies what to propose;
  the `returns_process_return` flow's Decisions node enforces the deterministic
  eligibility rule (warranty path vs. 30-day window vs. ineligible).
- **Write tool never on the agent:** `returns_issue_refund` is not in the agent's
  tool list. Only the flow calls it after human approval.
- **Red herring:** Alice (CUST-101) has two warranty records — one for her current
  blender (SKU-BLND-500, ORD-1001) and one for an older PRO model (SKU-BLND-PRO,
  ORD-1005). The agent must not apply the PRO warranty to the ORD-1001 claim.

## Tools attached to agent

| Tool | Purpose |
|---|---|
| `returns_lookup_order` | Retrieve order details and age in days |
| `returns_check_warranty` | Check active manufacturer warranty for an order's SKU |
| `returns_get_return_history` | Check whether a return has already been filed |
| `returns_lookup_by_serial` | Find the linked order from a product serial number (gift-return path) |
| `returns_list_orders` | Show all orders in the demo system — convenience tool for users who don't know their order ID |
| `returns_process_return` | Flow: eligibility check → human approval → issue refund (governance gate) |

## Write tool (flow only — not attached to agent)

| Tool | Called by |
|---|---|
| `returns_issue_refund` | `returns_process_return` flow only, after human approval |

## Knowledge base

| KB name | Documents |
|---|---|
| `customer_returns_policy` | RP-WARRANTY-01, RP-STANDARD-01, RP-GIFT-01, RP-ESCALATE-01 |

## Mock data

| Case | Order | Customer | Situation |
|---|---|---|---|
| CR-001 | ORD-1001 | CUST-101 Alice | Blender broke — warranty active, eligible for replacement |
| CR-002 | ORD-1002 | CUST-102 Ben | Headphones disliked — 46 days old, outside 30-day window, denied |
| CR-003 | ORD-1003 | CUST-103 Carol | Kitchen scale received as gift — serial SN-KTCH-780-C103, eligible for store credit |
| CR-004 | ORD-1004 | CUST-104 David | Double charge complaint — billing issue, out of scope, escalate |
| Red herring | ORD-1005 | CUST-101 Alice | PRO blender (different SKU) — warranty exists but wrong product |

## Limitations

- Not tested with a live WXO instance. All data is mock and static.
- The approval form in `returns_process_return` can only be driven by a human in the
  browser chat UI. The CLI smoke test sends diagnosis-only prompts.
- The flow's Decisions node eligibility logic has not been verified in a live browser run.
  Item to re-test: ineligible path (CR-002) does not show the approval form.
- KB indexing delay: after import, wait before the first demo query.
