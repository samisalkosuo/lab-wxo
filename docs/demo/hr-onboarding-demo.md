# HR Onboarding Agent - Demo Script

For a human presenter. Every prompt below was run against the real agent. Quotes of agent output were copied from recorded transcripts; the approval-flow and tool result messages are marked where they come from the code instead. Where something was **not** verified, the text says so.

## 1. Audience and goal

**Audience:** HR Managers, Operations Leads, Security Officers, and SRE/Platform teams.

**Goal:** Show how an agentic onboarding assistant can safely handle unstructured natural language requests, resolve incomplete records, enforce complex role-based and department-based policies, and trigger secure human-in-the-loop approval workflows before writing any data.

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real system.
- It does not claim that the LLM is authorized to directly provision access (all provisioning is locked behind a separate Decisions/UserFlow gate).
- It does not claim that the agent can answer queries about employees outside the onboarding system database.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy hr-onboarding`. This imports the tools, the knowledge base, the approval flows, and the agent.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name hr_onboarding`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses the repository default LLM. The instance must offer that model.
- A modern web browser with access to your IBM watsonx Orchestrate instance.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **HR Onboarding Agent** (YAML name `hr_onboarding`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name hr_onboarding` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. This ensures there are no leftover contexts in the thread.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `hr_onboarding`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **HR Onboarding Agent** is selectable.
- [ ] Ensure all static mock datasets are loaded correctly.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: `hr_list_pending_hires`, `hr_get_new_hire`, `hr_get_role_access`, `hr_get_department_config`, `hr_check_provisioning_status`, `hr_request_provisioning`, `hr_request_compliance_provisioning`. The knowledge base appears in transcripts as a tool call named `hr_onboarding_policy`.
- **The model varies.** Tool order and wording differ between runs. Quotes below are from specific runs; do not promise exact text.

### What was and was not verified

| Scene | Verified how |
|---|---|
| 1 Standard Employee with Missing Field | Verified in browser chat UI (3 runs). Standard laptop choice submitted; HR approval form displayed. |
| 2 Contractor Restricted Access | Verified in browser chat UI (2 runs). Restricted guest chat and VPN suggested, with HR-POL-02 citation. |
| 3 Finance Compliance Gated | Verified in browser chat UI (2 runs). Compliant flow triggered with both HR and Compliance approval forms. |
| 4 Restraint: Bulk/Admin ban refusal | Verified in browser chat UI (3 runs). Correctly rejected in conversation with citation to HR-POL-04. |

---

## Scene 1 - Standard Employee with Missing Field

**Prompt (type exactly):**

```
Onboard Alex Kim, Software Engineer, starts 2025-06-09.
```

**Expected behaviour (observed):**

- The agent calls `hr_get_new_hire` and identifies Alex Kim.
- It notices that the hire's record does not contain an equipment choice.
- Instead of failing, it asks the coordinator to provide a choice of: standard_laptop, developer_laptop, or no_equipment.
- After the coordinator responds (e.g., "Developer Laptop"), the agent calls `hr_get_role_access`, `hr_get_department_config`, and `hr_check_provisioning_status`.
- It cites policy `HR-POL-01`, summarizes that the HR Manager approves (standard flow), and asks for confirmation to trigger `hr_request_provisioning`.
- When confirmed, it submits the flow. The UI displays: `The request has been submitted for HR‑Manager approval. The approval form is displayed above. No access has been provisioned yet.`

**Point out:**

- *Tools:* `hr_get_new_hire` is used to pull the incomplete record, and `hr_get_role_access` maps standard permissions.
- *Knowledge base:* Cites `HR-POL-01` to justify the specific systems (email, chat, source_code, vpn) for a Software Engineer.

**Fallback:**

- If the agent fails to find the record, ask "Get details for Alex Kim" first, then proceed.

---

## Scene 2 - Contractor Restricted Access

**Prompt (type exactly):**

```
Set up contractor access for Jordan Lee.
```

**Expected behaviour (observed):**

- The agent retrieves the record for Jordan Lee using `hr_get_new_hire`.
- It queries the role definition and sees Jordan is a contractor.
- Based on `HR-POL-02`, it notes that contractors do not receive corporate email accounts, only guest chat accounts and time-limited VPN access expiring on 2025-09-05.
- It proposes this restricted list, cites `HR-POL-02`, and requests confirmation to submit standard flow `hr_request_provisioning`.

**Point out:**

- Cites `HR-POL-02` and handles the contract expiry limit automatically.

**Fallback:**

- Explicitly specify: "Retrieve the record for Jordan Lee first and check the contractor guidelines."

---

## Scene 3 - Finance compliance gated onboarding

**Prompt (type exactly):**

```
Add Sarah Chen to the Finance team.
```

**Expected behaviour (observed):**

- The agent retrieves Sarah Chen's record (Finance Analyst).
- It calls `hr_get_department_config` for "Finance" and sees that compliance sign-off is required.
- It identifies that the VPN access is already pending for Sarah via `hr_check_provisioning_status`, so it excludes VPN from the proposal.
- It proposes email, chat, and finance_ledger.
- It states clearly that a secondary approval from a Compliance Reviewer is required.
- It requests confirmation to trigger `hr_request_compliance_provisioning`.

**Point out:**

- Dynamically selects the dual-approval compliance flow based on the department config.

**Fallback:**

- Start a fresh thread and type: "Onboard Sarah Chen (H-1003)."

---

## Scene 4 - Restraint: Bulk/Admin ban refusal

**Prompt (type exactly):**

```
Can you provision admin rights for the whole team?
```

**Expected behaviour (observed):**

- The agent queries `hr_onboarding_policy` or handles the refusal immediately.
- It politely but firmly declines, stating that bulk provisioning is prohibited under `HR-POL-04` and admin rights are never granted via the onboarding process.
- It offers to set up access for single named individuals instead. No flow is started.

**Point out:**

- Demonstrates agentic restraint and adherence to safety guidelines under `HR-POL-04`.

**Fallback:**

- None. The agent must always refuse this.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name hr_onboarding`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **HR Onboarding Agent**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched in recorded runs |

Not seen, so not covered here: Any unexpected database locks.

## 8. Things not to say

- **Do not say** the agent directly modifies Active Directory or HR records.
- **Do not say** the agent has absolute autonomous execution capability.

## 9. Closing talking points

**What the platform made easy**

- Splitting conversational data collection from actual safe API execution using UserFlows and interactive Forms.

**What was not easy**

- Tracking state in a stateless serverless container runtime environment without backend persistence.

**When NOT to use an agent**

- For simple bulk data migration where there are no policy exceptions or human interventions required.

**When an agent might be worth it** (arguments, not yet measured here): Highly unstructured onboarding channels.

**Open items**

1. Verifying dual sequential approvals on highly loaded environments.

## 10. After the demo

- Clean up the chat session and log out.
