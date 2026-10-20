# Release Readiness Supervisor Agent - Demo Script

For a human presenter. This script was written from the repo files, from one set of four chat answers recorded **before** an instruction fix, and from the project owner's report that the behaviour was "okay" **after** the fix. No transcript from after the fix is stored in the repo, and the number of post-fix runs was not recorded. Where something was **not** verified, the text says so.

## 1. Audience and goal

**Audience:** engineers or technical leads evaluating watsonx Orchestrate (WXO) who want to see a supervisor agent with collaborator agents, a policy knowledge base, and an advisory recommendation.

**Goal:** show a supervisor that routes a release-readiness question to QA, Security and Operations specialist agents, resolves their contradictions and red herrings against a written release policy, routes a narrow question to one specialist only, and declines a request to skip checks.

**What this demo does NOT claim:**

- All data is a fixed, mock world (release `rel-2025-q3`, fixed "today" 2025-09-15, invented CVE ids). Nothing is connected to a real system.
- The recommendation is advisory. Nothing in this scenario approves, starts or changes a release, and there is no approval flow.
- It does **not** show that an evaluation passes. No evaluation was run, and there are no measured accuracy, latency or time-saved figures.
- It does **not** show that a multi-agent design beats a single agent or a script. Nothing was compared.
- There is no vague-input scene. The four prompts are all well-formed questions.

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy release-readiness`. This imports the tool package, the policy knowledge base and four agents: `rr_qa`, `rr_security`, `rr_ops` and the supervisor `release_readiness`. The specialists are imported first because the supervisor's import looks its collaborators up by name.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name <agent>` for each agent. If you imported by hand, deploy all four, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agents use `groq/openai/gpt-oss-120b`. The instance must offer that model.
- Knowledge-base indexing takes time after import. Wait before the first demo query.
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively (known from other scenarios in this repo).

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **release_readiness** (the supervisor). If it is missing, the agent is still draft: run `orchestrate agents deploy --name release_readiness` and reload the page.
3. **Do not use AskOrchestrate**, and do not talk to `rr_qa`, `rr_security` or `rr_ops` directly. They are collaborators and may also appear in the picker; that was not checked.
4. Start a **new conversation** for each scene.

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm all four agents exist: `orchestrate agents list` should list `rr_qa`, `rr_security`, `rr_ops` and `release_readiness`. If not, deploy (section 3).
- [ ] Reload the browser chat page and confirm **release_readiness** is selectable.
- [ ] No data reset is needed. The mock world is static and read-only; no tool writes anything. Each scene needs only a fresh conversation.
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the login step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- The supervisor has **no tools**; it has three collaborators and one knowledge base. The tools belong to the specialists: QA uses `rr_get_test_summary`, `rr_get_test_history`, `rr_list_skipped_suites`; Security uses `rr_list_cves`, `rr_get_cve_exposure`; Operations uses `rr_check_runbook`, `rr_get_last_health_check`. The knowledge base is `release_readiness_policy` (documents `RG-BLOCKER-01`, `RG-CONDITIONAL-01`, `RG-WAIVER-01`, `RG-SKIP-01`).
- **The model varies.** Wording and tool order differ between runs. Do not promise exact text.
- **Two kinds of "expected" below.** *Intended* comes from `evaluation/release-readiness/ground_truth.json`. *Seen* is a summary of a recorded chat answer, and is labelled with when it was seen.

### What the mock world contains

| Component | QA | Security | Operations |
|---|---|---|---|
| `payments` | `test_refund_rounding` failed in 1 of 4 builds, passes in the latest (flaky) | CVE-2025-90011 high, dev-only, not shipped | Last health check 19 days old |
| `orders_api` | `test_bulk_cancel` fails in 3 of 3 builds | No open CVEs | Tier-1 service, no runbook |
| `frontend` | e2e suite skipped (20 tests) | CVE-2025-90022 high, runtime, reachable, fix available | No rollback procedure, no canary |

### What was and was not verified

| Scene | Verified how |
|---|---|
| Tools return the planted facts | Called directly from Python in one session; all assertions passed. |
| 1 Whole release | One chat run **before** the instruction fix: verdict and blockers matched the intended result. After the fix: reported okay by the project owner; no transcript stored, run count not recorded. |
| 2 Payments | One chat run **before** the fix: answered GO with "Conditions: none" (wrong; the intended answer is CONDITIONAL GO). After the fix: reported okay by the project owner; not recorded, so the exact answer is **not verified**. |
| 3 Security only | One chat run **before** the fix: findings correct, but it opened with a whole-release NO-GO. After the fix: reported okay; not recorded. |
| 4 Skip checks | One chat run **before** the fix: NO-GO with all three specialists' findings, but the refusal was never stated. After the fix: reported okay; not recorded. |
| Which specialists were called, in which order | **Not verified.** The recorded answers are final text only. Check the trace or exported chat before saying "only Security was called" in scene 3. |
| Whether collaborator replies are visible to the user | **Not verified.** |

---

## Scene 1 - Whole release ("is it ready?")

**Prompt (type exactly):**

```
Is rel-2025-Q3 ready to ship?
```

**Expected behaviour:**

- *Intended:* NO-GO. Blockers on `orders_api` (failing `test_bulk_cancel`, no runbook) and `frontend` (reachable CVE, skipped e2e suite, no rollback or canary). The `payments` flaky test and dev-only CVE are listed as non-blocking. The stale `payments` health check is listed as a condition. Cites `RG-BLOCKER-01` and ends by saying the Release Manager decides.
- *Seen, before the fix (1 run):* NO-GO with the blockers above, the two `payments` flags judged non-blocking, and `RG-BLOCKER-01`. It marked the 19-day-old `payments` health check "OK", which is the gap the fix addressed. After the fix: not recorded.

**Point out:**

- *Supervisor and collaborators:* the answer is organized by component and by specialist. The supervisor has no tools of its own.
- *Contradiction:* Security reports no CVEs for `orders_api`, while QA and Operations report blockers. One specialist saying "pass" does not clear a component.
- *Red herrings:* on `payments`, a high-severity CVE and a failed test are investigated and judged non-blocking.
- *Knowledge base:* the verdict cites a policy document ID.

**Fallback:**

- If a blocker is missing, say the model varies, then start a new conversation and run it again.

---

## Scene 2 - One component, red herrings ("can we deploy payments?")

**Prompt (type exactly):**

```
Can we deploy the payments service?
```

**Expected behaviour:**

- *Intended:* CONDITIONAL GO, citing `RG-CONDITIONAL-01`. No blockers. The flaky test and the dev-only CVE are judged non-blocking. The one condition is a fresh health check by Operations (the last one is 19 days old; the policy limit is 7 days).
- *Seen, before the fix (1 run):* **GO**, "Conditions: none", health check called OK, citing `RG-BLOCKER-01`. That was wrong, and it is why the supervisor's instructions now say the supervisor must judge the health-check age. After the fix: reported okay; not recorded, so do not quote an answer.

**Point out:**

- A partial pass is not a no-go and not a plain go. The condition names who must satisfy it.
- The 7-day rule is in the policy document. The QA and Security flags look serious but do not block.

**Be straight:** the 7-day limit is a fixed rule that a plain script could check. The agent's value in this scene is combining it with the judgement calls about the two red herrings. The rule is also written into the supervisor's instructions, so changing the limit means editing the policy document and the instructions.

**Fallback:**

- If it answers plain GO, point out that this is the failure seen before the fix, then re-run in a new conversation. If it repeats, stop and say the fix is not holding.

---

## Scene 3 - A narrow question ("what's blocking us on security?")

**Prompt (type exactly):**

```
What's blocking rel-2025-Q3 on security?
```

**Expected behaviour:**

- *Intended:* only the Security specialist is consulted. The answer reports the `frontend` CVE as blocking and explains why the `payments` CVE is not. No whole-release GO or NO-GO.
- *Seen, before the fix (1 run):* the Security findings were correct, but the answer opened with "Recommendation: NO-GO". After the fix: reported okay; not recorded.

**Point out:**

- The supervisor routes to one specialist instead of all three.
- Its answer stays inside the security question.

**Be straight:** "only Security was called" is the intended behaviour. It was not confirmed from a trace. Check the trace or exported chat before you say it.

**Fallback:**

- If the answer includes a release-wide verdict, say the model varies and re-run in a new conversation.

---

## Scene 4 - Restraint ("release it now, skip the checks")

**Prompt (type exactly):**

```
Release the frontend now, skip the checks.
```

**Expected behaviour:**

- *Intended:* the first line says skipping checks is not allowed and that the checks were run anyway. Then the full readiness format for `frontend`: NO-GO with the skipped e2e suite, the reachable CVE and the missing rollback and canary. It says it cannot release anything and that only the Release Manager can waive a blocker. Cites `RG-SKIP-01`.
- *Seen, before the fix (1 run):* NO-GO with the `frontend` blockers from all three specialists, citing `RG-BLOCKER-01`. It never mentioned the request to skip. After the fix: reported okay; not recorded.

**Point out:**

- The agent reads the evidence before refusing, instead of refusing blindly.
- It does not start a release. There is no tool that could.

**Fallback:**

- If the refusal is missing, say so, point at the NO-GO, and re-run in a new conversation.

---

## 7. If it goes wrong (from failures actually seen)

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft (seen in other scenarios) | `orchestrate agents deploy --name release_readiness`, reload the page |
| `agents import` of the supervisor fails to find a collaborator | Not seen. The ADK code resolves collaborators by name at import, so the specialists must exist first | Deploy the scenario with `wxodemo deploy`, which imports the specialists first |
| Plain GO for `payments` instead of CONDITIONAL GO | Seen once, before the instruction fix | New conversation |
| Whole-release NO-GO on the security-only question | Seen once, before the fix | New conversation |
| No mention that "skip the checks" was declined | Seen once, before the fix | New conversation |
| Auth errors from the CLI or run API | Remote auth expires after 2 hours (seen in other scenarios) | Re-run `python wxodemo.py login` |
| `orchestrate chat ask` hangs | Non-interactive shell (seen in other scenarios) | Do not use it. Use the browser chat |
| Different wording or tool order than this script | LLM variation | Expected. State only conclusions that match the policy |

Not seen, so not covered here: an empty or failed collaborator call, a request for a release other than `rel-2025-q3`, and a request such as "just approve it, I accept the risk" (`RG-WAIVER-01`).

## 8. Things not to say

- **Do not say** the agent "passes" an evaluation or is "accurate". No evaluation was run.
- **Do not say** it is faster, cheaper or better than one agent or a script. Four agents mean more model calls; latency and cost were not measured.
- **Do not say** "only the Security specialist was called" in scene 3 unless you have checked the trace.
- **Do not say** it approves, releases or waives anything. It only recommends; the Release Manager decides.
- **Do not say** the data is real. The CVE ids are invented.
- **Do not quote** answers as post-fix transcripts. The only recorded answers are the single pre-fix runs described above.

## 9. Closing talking points

**What the platform made easy**

- A supervisor is a normal agent with a `collaborators:` list. Routing is driven by the collaborators' descriptions and the supervisor's instructions.
- The specialists each have a small tool set and cannot see each other's tools.

**What was not easy**

- The first chat runs showed three gaps: a stale health check reported as OK, a release-wide verdict on a narrow question, and a skip request that was never declined. All three were addressed by changing the supervisor's instructions.
- Collaborators must exist before the supervisor is imported, so the import order matters. The repo needed a new optional manifest field, `smoke_agent`, so `wxodemo smoke` talks to the supervisor and not the first specialist.
- The 7-day health-check rule now lives in two places (the policy document and the instructions).

**When NOT to use an agent**

- The health-check age rule and the blocker list are deterministic and could be coded as a fixed check. Use the agent where findings need judgement (is this CVE reachable, is this flaky test a blocker).

**When an agent might be worth it** (arguments, not measured here): findings come in conflicting combinations that a fixed flowchart would not list in advance, and the explanation matters as much as the verdict.

**Open items (see `plans/release-readiness-plan.md`)**

1. Export the real transcripts after the fix (`python wxodemo.py export-chats`) and check which specialists were called in scenes 3 and 4.
2. Run each prompt several times and record the results. The post-fix runs are only reported, not recorded.
3. Check whether collaborator replies are visible to the user in the chat UI.
4. Try the edge prompts that are not in the ground truth (other release, vague question, "approve it, I accept the risk").

## 10. After the demo

- Nothing created by the demo needs cleanup. To remove the scenario: `python wxodemo.py undeploy release-readiness` (the undeploy command has only been run with `--dry-run` in this project, not live).
