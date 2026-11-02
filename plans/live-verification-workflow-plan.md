# Live verification workflow for the Bob builder modes - Plan

## Overview

**Problem.** The Scenario Builder mode (`.bob/custom_modes.yaml`) ends its "finish" sequence with `validate`, `smoke --dry-run`, `eval --dry-run` and a README row. Real deployment and testing in WXO is only mentioned as a note ("requires a live instance"). In practice the author deploys, then tests the demo scenes in the WXO browser chat, and that testing leads to many changes (agent instructions, tools, prompts, demo script). The mode does not expect this loop, adds the README row before anything is verified, and does not say when a scenario becomes `live`.

**Goal.** Make live verification part of the workflow of both builder modes, and describe it in `docs/building-with-bob.md`:

1. Bob builds and runs only dry-run checks (status stays `soon`).
2. Bob deploys. Then the user tests **one scene at a time** in the real WXO chat and reports the result. Bob fixes, redeploys, and the user retests that scene. Repeat per scene.
3. Only when the **user confirms** that all scenes work as defined does Bob set the scenario live (manifest `status: live`, slide `status: "live"`), finalise the demo script "observed" text, rebuild the bundle, validate, and add the README row.

**Standalone Builder** gets a lighter version of the same loop: deploy, user tries the `examples.md` prompts in WXO, user confirms, then slides and README row.

**Non-goals.** No change to the `wxodemo` CLI (`status: soon/live` already exists in `src/wxodemo/manifest.py`; `deploy --all` already skips `soon`). No change to other scenarios' files. No automatic browser testing. `src/wxodemo/scaffold.py` "Next steps" text already says to set `live` after observing; leave it.

**Design decisions**
- Only the user can confirm a scene. Bob must never mark a scene verified itself, and must not claim "works/passes" without the user's report (consistent with the existing hard limits).
- The record of confirmed scenes lives in `plans/<id>-plan.md` under a "Live verification log" (scene, prompt used, result reported by user, changes made). The demo script's "What was and was not verified" table is filled from that log at the end.
- Bob presents the scene prompt exactly as it will appear in the demo script, so the same prompts get tested that will be shown.
- The README row moves from "finish every task" to after user confirmation.

## Sub-tasks

### 1. Update the Scenario Builder mode

- **Intent:** Encode the build -> deploy -> scene-by-scene live test -> confirm -> go live sequence in the mode's `roleDefinition`.
- **Expected Outcomes:** The mode stops after dry-run checks and asks the user to test live; it drives scene-by-scene testing; the README row and `live` status only happen after explicit user confirmation.
- **Todo List:**
  1. Edit the build order line in `roleDefinition` ("deploy and smoke/eval test -> demo markdown and slides") into: build -> dry-run checks -> deploy -> live scene testing with the user (iterate) -> user confirmation -> demo docs finalised, `status: live`, README.
  2. Replace "Finish every scenario task in this order" with two parts:
     - **Part A (build done):** validate, smoke dry-run, eval dry-run, then `login` + `deploy <id>`; draft the demo script with every verification row "not verified"; ask the user to test scene 1. Do NOT touch README and keep `status: soon`.
     - **Part B (live verification loop):** give the user the exact scene prompt and what to look for; wait for the user's result; on a problem fix files, `deploy <id>` again, and ask the user to retest the same scene; append to the Live verification log in `plans/<id>-plan.md`; move to the next scene only when the user says the current one works. Browser-only items (approval form Approve and Reject) are always tested by the user.
     - **Part C (after the user confirms all scenes work as defined):** finalise demo script from the log, set `status: live` in `scenarios/<id>/scenario.yaml` and in `docs/demo/scenarios/<id>.js`, run `python docs/demo/build-demo-scripts-bundle.py`, `validate <id>`, then add the README "Scenario agents" row (alphabetical, no other README section).
  3. Add hard limits: never set `live` or add the README row before user confirmation; never mark a scene verified without the user's report; one scene at a time.
  4. Keep the existing "report what was and was not verified" sentence, adjusted to the log.
- **Relevant Context:** `.bob/custom_modes.yaml` lines 18-21 (build order) and 50-63 (finish sequence), hard limits lines 40-48.
- **Status:** [ ] pending

### 2. Align the skills the Scenario Builder loads

- **Intent:** Skills and mode must not contradict each other.
- **Expected Outcomes:** Build order, done checklist and demo-docs procedure all say: live testing with the user precedes `live` status and the README row.
- **Todo List:**
  1. `.bob/skills/wxo-scenario-authoring/SKILL.md`: in section 7, split step 7 into deploy and the scene-by-scene live loop with user confirmation; make step 8 (demo docs final) and `status: live` come after confirmation. In section 10, add a checkbox "User confirmed every scene in WXO; Live verification log in the plan" and make the README row item depend on it.
  2. `.bob/skills/scenario-demo-docs/SKILL.md`: in Procedure, state that `status: "live"` in the `.js` file and the manifest is set only after user confirmation; the "What was and was not verified" table is filled from the plan's Live verification log; note that a draft with "not verified" rows is expected while testing is in progress and prompts changed during testing must be updated in both md and slides.
  3. Add a short "Live verification log" structure (columns: scene, prompt, user result, changes made) to section 7 step 1 of the authoring skill (plan file contents).
- **Relevant Context:** `.bob/skills/wxo-scenario-authoring/SKILL.md` sections 7, 8, 10; `.bob/skills/scenario-demo-docs/SKILL.md` rules 1 and procedure steps 2-6.
- **Status:** [ ] pending

### 3. Update the Standalone Builder mode

- **Intent:** Same principle, lighter: an agent is only "done" when the user has tried it in WXO.
- **Expected Outcomes:** The mode deploys after dry-runs, asks the user to try the `examples.md` prompts (normal path and refusal path) one at a time, iterates, and only after confirmation updates `docs/demo/standalone-agents.js` and the README row.
- **Todo List:**
  1. In "Finish every task in this order" keep steps 1-5 (examples.md, test cases, list, test-upload dry-run, deploy dry-run).
  2. Insert a live step: `login`, `deploy <name>`, `status <name>`, then ask the user to run each `examples.md` prompt in WXO; fix and redeploy on problems; keep `examples.md` and `test_cases/` in sync with any behaviour change.
  3. Move current steps 6 (standalone-agents.js slides) and 7 (README rows) to after the user confirms the examples behave as defined.
  4. Add a hard limit: no slides or README row before user confirmation (extends the existing "never claim the agent works without a recorded run").
- **Relevant Context:** `.bob/custom_modes.yaml` lines 137-165 (hard limits and finish sequence); `standalone/README.md` for conventions.
- **Status:** [ ] pending

### 4. Update `docs/building-with-bob.md`

- **Intent:** Document the development approach for human readers.
- **Expected Outcomes:** The guide describes the build -> deploy -> test each scene in WXO -> confirm -> go live loop and makes clear that the user is the tester.
- **Todo List:**
  1. "How a session goes": rewrite steps 4-5 so that Check = dry-run checks only; add "Deploy and test scene by scene" (Bob gives one prompt, you run it in the WXO chat, report back, Bob fixes and redeploys, repeat) and "Confirm and go live" (you confirm, Bob sets `live`, finalises the demo script, adds the README row). Add a Mermaid-free short numbered list (the repo docs use plain lists). Mention the Standalone version in one sentence.
  2. "What to check afterwards": keep the dry-run commands; change the trailing paragraph about `status: soon` so that `live` is set by Bob after your confirmation, not "once you are happy".
  3. "Review what Bob produces": reference the Live verification log in `plans/<id>-plan.md` as the record of what you confirmed; expect several fix-and-retest rounds.
  4. Tip: add one bullet "Test one scene at a time and say what is wrong in your own words" under "Tips for good prompts".
- **Relevant Context:** `docs/building-with-bob.md` sections "How a session goes" (lines 35-43), "What to check afterwards" (133-161), "Review what Bob produces" (163-171).
- **Status:** [ ] pending

### 5. Consistency check

- **Intent:** Make sure no remaining text says README/live happens at build time.
- **Expected Outcomes:** No contradictions across mode, skills and docs.
- **Todo List:**
  1. `grep` for "README", "status: live", "soon" in `.bob/`, `docs/building-with-bob.md`, `docs/wxodemo.md`, `standalone/README.md` and fix wording that conflicts.
  2. Re-read the edited `custom_modes.yaml` for valid YAML (folded `>-` blocks, indentation).
  3. Run `python wxodemo.py validate incident-triage` (any scenario) to confirm nothing in the repo tooling broke; no CLI code is changed.
- **Relevant Context:** files listed above.
- **Status:** [ ] pending
