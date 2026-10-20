# HR Onboarding Agent

Conversational agent that helps an HR coordinator onboard **one new hire at a time**. It finds the
hire's record, asks only for the fields that are missing, reads the role-access matrix and the
department rules, and proposes the systems to grant. Access is granted only by one of two
human-approval flows. All people, systems and policies are fictional.

## Teaching points

- **Deterministic part in tools, open part in the agent:** the role -> systems matrix and the
  department rules are code (`hr_get_role_access`, `hr_get_department_config`). The agent handles
  messy intake, interpreting policy prose, and declining forbidden requests. This is not a claim that
  the agent beats a script; the lookup itself is a script.
- **Write tool never on the agent:** `hr_provision_access` is not in the agent's tool list. Only the two
  flows call it, after human approval.
- **The flow fixes the approval path:** the flows set `approval_path` and the approver records
  themselves. The agent only chooses *which* flow, and the write tool re-checks that choice in code.
- **Restraint:** a bulk or admin request is declined with a policy citation; no flow starts.
- **Red herring:** a Software Engineer gets no production access, although a Site Reliability Engineer in
  the same department does.

## Tools attached to the agent

| Tool | Purpose |
|---|---|
| `hr_list_pending_hires` | Hires starting in an explicit ISO date range (capped at 10) |
| `hr_get_new_hire` | One hire record plus `missing_fields`; returns candidates when a name is ambiguous |
| `hr_get_role_access` | Systems a role may and may not be granted, policy ids |
| `hr_get_department_config` | Whether compliance sign-off is required, and which flow to use |
| `hr_check_provisioning_status` | Per-system status for a hire (not_requested / pending / granted) |
| `hr_request_provisioning` | Flow: HR Manager approves -> grant access (departments without a compliance gate) |
| `hr_request_compliance_provisioning` | Flow: HR Manager, then Compliance Reviewer, both approve -> grant access (Finance) |

## Write tool (flows only, not attached to the agent)

| Tool | Called by |
|---|---|
| `hr_provision_access` | `hr_request_provisioning` and `hr_request_compliance_provisioning`, after human approval |

It refuses in code: bulk or empty hire ids, role or department not matching the record, admin-like
systems, systems outside the role's list, an invalid approval path, a missing HR Manager approval,
a compliance-gated department on the standard path or without a Compliance Reviewer, and a record that
is still incomplete. The compliance flow used for a department without a gate succeeds and adds a note.

## Knowledge base

| KB name | Documents |
|---|---|
| `hr_onboarding_policy` | HR-POL-01 role access, HR-POL-02 contractors, HR-POL-03 compliance approval, HR-POL-04 bulk and admin ban, HR-POL-05 onboarding checklist |

Plain `.txt` files (the built-in KB does not take Markdown).

## Mock data

| Case | Input | Record | Situation |
|---|---|---|---|
| HR-001 | "Onboard Alex Kim, Software Engineer, starts 2025-06-09" | `H-1001`, Engineering | Equipment choice missing -> one clarifying question. Software Engineer has no production access. Standard flow. |
| HR-002 | "Set up contractor access for Jordan Lee" | `H-1002`, contractor, Engineering, end date 2025-09-05 | Only chat (guest) and time-limited VPN; no email (HR-POL-02). |
| HR-003 | "Add Sarah Chen to the Finance team" | `H-1003`, Finance Analyst, Finance | Compliance-gated flow (HR Manager, then Compliance Reviewer). VPN already `pending`, so the agent leaves it out of the request. |
| HR-004 | "Can you provision admin rights for the whole team?" | none | Declined, cites HR-POL-04, no flow. |

Dates are explicit ISO dates; the data never depends on today's date.

## Limitations

- **Not deployed and not tested against a live WXO instance.** The tools were exercised directly in
  Python; the flows were built and serialized offline; the agent instructions have not been run.
- The approval forms can only be answered by a human in the browser chat UI. The CLI smoke test sends
  diagnosis-only prompts and cannot approve or reject.
- Both flows are untested in a browser. The two-step compliance flow is new in this repo.
- Approvers are fixed role labels ("HR Manager", "Compliance Reviewer"); the forms do not capture who
  approved.
- The hire record is never updated: a value the coordinator supplies (for example the equipment
  choice) is passed into the flow only.
- KB indexing takes time after import; retrieval quality for these documents has not been checked.
- Status stays `soon` until both flows are verified in a browser (Approve and Reject each).
