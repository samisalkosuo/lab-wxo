<!--
AUTHOR NOTES (delete every "AUTHOR NOTE" comment before you finish; `python wxodemo.py validate {{ID}}` fails on leftovers):
- Copy this file to docs/demo/{{ID}}-demo.md and replace every {{PLACEHOLDER}}.
- It mirrors docs/demo/incident-triage-demo.md (10 sections). Keep the section numbers and order.
- Honesty rule: "Expected behaviour (observed)" may only contain what you saw in real runs. State how many runs.
  If you did not run something, write "not verified". Never write a number, quote or tool order you did not observe.
- Prompts in "Prompt (type exactly)" blocks must be identical, word for word, to the prompt-box text in
  docs/demo/scenarios/{{ID}}.js (`wxodemo validate` compares them).
- Scenes: keep at least one messy/vague-input scene, one main-path scene, one trap scene (red herring or tempting
  wrong answer), one governed-action scene if the scenario has an approval flow, and one restraint scene if the
  scenario has a "do nothing" case. Delete scenes that do not apply; renumber.
- The evaluation scene (Scene {{EVAL}}) is optional: keep it only if the scenario has the optional evaluation tier.
-->

# {{NAME}} Agent - Demo Script

For a human presenter. Every prompt below was run against the real agent. Quotes of agent output were copied from recorded transcripts; the approval-flow and tool result messages are marked where they come from the code instead. Where something was **not** verified, the text says so.

## 1. Audience and goal

**Audience:** {{AUDIENCE}}

**Goal:** {{GOAL}}

**What this demo does NOT claim:**

- All data is a fixed, mock world. Nothing is connected to a real system.
- {{NOT_CLAIMED_1}}
- {{NOT_CLAIMED_2}}

## 2. Prerequisites

- The repo has been deployed to your WXO instance with `python wxodemo.py deploy {{ID}}`. This imports the tools, the knowledge base, {{FLOW_NOTE}} and the agent.
- **Imported agents are draft until deployed.** `wxodemo deploy` already runs `orchestrate agents deploy --name {{AGENT_NAME}}`. If you imported by hand, run that command, then reload the chat page. Until then the chat UI shows only `AskOrchestrate`.
- **Remote auth expires after 2 hours.** Re-activate before the demo (see the reset checklist).
- The agent uses `{{LLM}}`. The instance must offer that model.
- {{BROWSER_NOTE}}
- Do **not** use `orchestrate chat ask` for the demo or for rehearsal in a script shell. It hangs when run non-interactively.

## 3. Opening the right chat UI

1. Open your WXO instance in the browser (the web UI you log in to, not the API URL in `env.cfg`) and go to the chat.
2. In the agent picker choose **{{AGENT_DISPLAY}}** (YAML name `{{AGENT_NAME}}`). If it is missing, the agent is still draft: run `orchestrate agents deploy --name {{AGENT_NAME}}` and reload the page.
3. **Do not use AskOrchestrate.** A wrong agent selection produces a confusing generic answer that looks like an agent defect.
4. Start a **new conversation** for each scene. {{THREAD_NOTE}}

## 4. Reset checklist (run through this before every demo)

- [ ] Re-activate the environment so auth is fresh (valid for 2 hours). `wxodemo` reads the key from your own `env.cfg` and never prints it:
  ```
  python wxodemo.py login
  ```
- [ ] Confirm the agent exists: `orchestrate agents list` should list `{{AGENT_NAME}}`. If not, deploy it (section 3).
- [ ] Reload the browser chat page and confirm **{{AGENT_DISPLAY}}** is selectable.
- [ ] {{RESET_DATA_NOTE}}
- [ ] Do not force-kill `orchestrate` or `python` processes if something hangs. Wait, or re-run the activate step.

## 5. How to read this script

Each scene has: **Prompt**, **Expected behaviour**, **Point out**, **Fallback**.

- Tool names are the real ones: {{TOOL_NAMES}}. The knowledge base appears in transcripts as a tool call named `{{KB_NAME}}`. {{FLOW_DISPLAY_NOTE}}
- **The model varies.** Tool order and wording differ between runs. Quotes below are from specific runs; do not promise exact text.

### What was and was not verified

<!-- AUTHOR NOTE: one row per scene. Say how it was verified (browser, SDK run, N runs) and what was NOT driven. -->

| Scene | Verified how |
|---|---|
| 1 {{SCENE_1_SHORT}} | {{VERIFIED_1}} |
| 2 {{SCENE_2_SHORT}} | {{VERIFIED_2}} |

---

## Scene 1 - {{SCENE_1_TITLE}}

**Prompt (type exactly):**

```
{{PROMPT_1}}
```

**Expected behaviour (observed):**

- {{OBSERVED_1}} (based on {{N_RUNS_1}} runs)

**Point out:**

- *Tools:* {{POINT_TOOLS_1}}
- *Knowledge base:* {{POINT_KB_1}}

**Fallback:**

- {{FALLBACK_1}}

---

## Scene 2 - {{SCENE_2_TITLE}}

**Prompt (type exactly):**

```
{{PROMPT_2}}
```

**Expected behaviour (observed):**

- {{OBSERVED_2}} (based on {{N_RUNS_2}} runs)

**Point out:**

- {{POINT_2}}

**Be straight:** {{LIMIT_2}}

**Fallback:**

- {{FALLBACK_2}}

---

<!-- AUTHOR NOTE: copy a scene block for each additional scene. For a governed-action scene, copy the
     "Approval flow" structure of Scene 4 in incident-triage-demo.md (fresh conversation per path, what the
     form shows, Approve path, Reject path, what is code-sourced versus recorded, fallback for a stuck thread). -->

## Scene {{EVAL}} - Evaluation (optional)

<!-- AUTHOR NOTE: delete this whole scene unless the scenario has the optional evaluation tier
     (evaluation.tier: full in scenario.yaml). If kept, report only measured numbers and say plainly what did not pass. -->

{{EVAL_CONTENT}}

---

## 7. If it goes wrong (from failures actually seen)

<!-- AUTHOR NOTE: only list symptoms you actually saw. Keep the generic rows; add your own. -->

| Symptom | Cause seen in testing | What to do |
|---|---|---|
| Only `AskOrchestrate` in the agent picker | Agent is still draft | `orchestrate agents deploy --name {{AGENT_NAME}}`, reload the page |
| Confusing, generic answer; no tool calls | Wrong agent selected (AskOrchestrate) | Select **{{AGENT_DISPLAY}}**, new conversation |
| CLI or run API calls fail with auth errors | Remote auth expires after 2 hours, or a Python process was killed | Re-run `python wxodemo.py login` |
| `UnicodeEncodeError ... charmap` from the CLI | cp1252 console encoding on Windows | Run orchestrate through `wxodemo` (it sets UTF-8), or `$env:PYTHONUTF8 = "1"` |
| `orchestrate chat ask` prints nothing and hangs | Non-interactive shell | Do not use it. Use the browser chat |
| Different tool order or wording than this script | LLM variation | Expected. State the conclusions that matched in recorded runs |
| {{SYMPTOM}} | {{CAUSE}} | {{ACTION}} |

Not seen, so not covered here: {{NOT_SEEN}}.

## 8. Things not to say

<!-- AUTHOR NOTE: list the claims that the recorded runs do NOT support. -->

- **Do not say** {{DO_NOT_SAY_1}}.
- **Do not say** {{DO_NOT_SAY_2}}.

## 9. Closing talking points

**What the platform made easy**

- {{EASY_1}}

**What was not easy**

- {{NOT_EASY_1}}

**When NOT to use an agent**

- {{WHEN_NOT_1}}

**When an agent might be worth it** (arguments, not yet measured here): {{WHEN_WORTH}}

**Open items (still open at the time of writing; see `plans/{{ID}}-plan.md`)**

1. {{OPEN_1}}

## 10. After the demo

- {{AFTER_1}}
