# Scenario Tooling - Plan

## Top-Level Overview

**Goal.** Make adding a new WXO demo scenario a repeatable, low-effort task. Each scenario must ship working resources (agent, tools, knowledge base, optional flow), a detailed demo markdown modelled on [`docs/demo/incident-triage-demo.md`](../docs/demo/incident-triage-demo.md), and a section in [`docs/demo/presentation.html`](../docs/demo/presentation.html) modelled on the six Incident Triage slides.

**Scope.** Tooling and conventions only (skills, a mode, a manifest, script changes, a presentation refactor). Building the scenarios themselves (HR Onboarding, Cloud FinOps, and the plan's Phase B / Phase C) is out of scope here; each gets its own plan file once this tooling exists.

**Primary purpose of the repo (user-stated).** Showcase WXO with a presentation and scenarios. Evaluation machinery is secondary.

### Findings that drive the plan

| Finding | Evidence |
|---|---|
| `.bob/` has one skill (`wxo-adk`), no custom modes | `.bob/skills/wxo-adk/SKILL.md`, `.bob/mcp.json` |
| `deploy-all.sh` is generic (globs `tools/`, `knowledge/`, `flows/`, `agents/`) but cannot deploy one scenario only | [`scripts/deploy-all.sh`](../scripts/deploy-all.sh) lines 80-180 |
| `package.py` is hard-coded to incident triage (allow-list, zip name, `INSTALL_MD` text) | [`scripts/package.py`](../scripts/package.py) lines 116-169, 263+, 528 |
| `teardown.ps1` / `teardown.sh` hard-code resource names | plan Sub-Task 9 notes |
| `smoke_test_triage.py` hard-codes the agent UUID and prompts | plan Sub-Task 8 notes |
| `presentation.html` sidebar buttons are hand-written with `switchScenario(n)`; slide data lives in the `scenariosData` array; HR / FinOps are placeholders | [`docs/demo/presentation.html`](../docs/demo/presentation.html) lines 856-880, 1420-1462, 1500-1513 |
| Plan Phase B / C are "Customer Returns" and "Release Readiness", while the presentation sidebar promises "HR Onboarding" and "Cloud FinOps" | [`plans/incident-triage-plan.md`](incident-triage-plan.md) lines 496-510 vs presentation lines 865-879 |

### Confirmed decisions

1. **Evaluation is two tiers.** Core (always created): a small `ground_truth.json` per scenario (expected root cause / outcome, expected action, key tools); used as the demo-script checklist and smoke-test expectations. Optional (off by default): plain-code `baseline.py`, ADK `test_cases/` and `eval_config.yaml`, added only when the scenario needs a "why not a script?" answer or a quality check. Reason: the incident-triage evaluation had a 0/15 final-answer check, hand-installed dependencies, unshipped results, and a baseline that matched the agent; the "agent vs plain script" argument already has a card on the benefits slide.
2. **Presentation uses per-scenario JS files.** Each scenario is `docs/demo/scenarios/<id>.js` pushing one object onto a shared `window.SCENARIOS` array; the shell renders the sidebar from the array. Reason: works from `file://` (no `fetch`), slides are rich HTML components, no build step, smallest change. A generator from JSON can still be added later on top of the same files.
3. **Tooling set:** two skills, one Scenario Builder mode, a `scenario.yaml` manifest per scenario, and scenario-aware deploy / package / teardown / smoke-test scripts.

Accepted trade-off: demo prompts appear in both the demo markdown and the slides. The skill's checklist must verify both copies match.

### Open item to resolve before scenario work starts

The scenario list differs between the plan (Returns, Release Readiness) and the presentation (HR Onboarding, Cloud FinOps). The user said "all these will be implemented". Decide the order and numbering; sidebar numbering follows the order of `docs/demo/scenarios/*.js` registration.

### Target layout (additions)

```
.bob/skills/wxo-scenario-authoring/SKILL.md     what every scenario ships + Phase A lessons
.bob/skills/scenario-demo-docs/SKILL.md         demo markdown + presentation recipe
.bob/skills/scenario-demo-docs/templates/       demo-script.template.md, scenario.template.js
.bob/custom_modes.yaml                          Scenario Builder mode (path per create-mode skill)
scenarios/<name>/scenario.yaml                  manifest: names of every resource the scenario owns
docs/demo/scenarios/<id>.js                     slide data per scenario
docs/demo/scenarios/_helpers.js                 optional card / promptCard / mappingTable helpers
scripts/new-scenario.py                         scaffold the folder skeleton from the manifest
```

---

## Sub-Tasks

### Sub-Task 1: Scenario manifest and conventions

- **Intent:** One machine-readable description of what a scenario owns, so scripts stop hard-coding names.
- **Expected Outcomes:**
  - A documented `scenario.yaml` schema (scenario id, display name, agents, tool packages and tool names, knowledge base names, flow names, evaluation tier, demo markdown path, presentation file path).
  - `scenarios/incident-triage/scenario.yaml` written for the existing scenario as the reference example, matching actual resource names.
  - Naming conventions written down (folder `kebab-case`, YAML `snake_case`, ID prefixes such as `INC-`, `RB-`).
- **Todo List:**
  - [x] Define the schema from what `deploy-all`, `teardown` and `package.py` actually need today.
  - [x] Write the incident-triage manifest using real names (agent `incident_triage`, 8 tools, KB `incident_triage_runbooks`, flow `request_remediation`).
  - [ ] Record conventions in the authoring skill (Sub-Task 2) rather than a separate doc.
- **Relevant Context:** [`scripts/teardown.ps1`](../scripts/teardown.ps1), [`scripts/package.py`](../scripts/package.py) `build_allow_list()`, `agents/incident-triage/agent.yaml`, `knowledge/incident-triage/incident_triage_runbooks.yaml`.
- **Status:** `[x] done` (the convention-recording todo moves to Sub-Task 2)
- **Status notes:**
  - Created [`scenarios/incident-triage/scenario.yaml`](../scenarios/incident-triage/scenario.yaml). The schema is documented in the file's header comment (it is the reference example to copy).
  - Fields: `id`, `name`, `description`, `status`, `agents[]` (name, path, kind), `tools[]` (path, entry, names, attached), `knowledge_bases[]` (name, path), `flows[]` (name, path), `evaluation` (path, tier `core|full`, package_include), `demo.script`, `package.zip_prefix`.
  - `tools[].names` lists every `@tool`; `attached` lists the ones the agent may call. `execute_remediation` is in `names` but not `attached` (flow-only).
  - Verified by a throwaway script (deleted) against the repo: agent name, agent tools minus the flow equal `attached`, agent KB, the 8 `@tool` names in source order, KB name, flow `name=`, the 4 evaluation package items and the demo script path. All passed.
  - Not covered by the manifest yet: `hello_world` agent and `greeting` tool (not a demo scenario; the current teardown scripts still hard-code them, to be handled in Sub-Task 5). Presentation file path is implied by `id` (`docs/demo/scenarios/<id>.js`), not stored.
  - Context for later sub-tasks: `package.py` allow-list currently includes all of `docs/demo/` (line 172); Sub-Task 5 must decide whether a per-scenario zip ships only that scenario's demo files plus the shared presentation shell. The YAML parser is PyYAML (present in `.venv`); it is not in the `package.py` standard-library-only constraint, so Sub-Task 5 must either parse the manifest without PyYAML or relax that constraint.

### Sub-Task 2: Skill `wxo-scenario-authoring`

- **Intent:** Encode what every scenario must contain and the Phase A lessons, so no scenario rediscovers them.
- **Expected Outcomes:**
  - `SKILL.md` with a per-scenario checklist: mock data package (static, read-only, deterministic), fewer than 10 tools on the agent, bounded tool outputs, write actions behind a flow gate and not attached to the agent, knowledge base documents as `.txt` / `.html`, agent YAML, README, `ground_truth.json`, manifest, demo markdown, presentation file.
  - A "legitimacy" check (agent-washing test: next step depends on previous findings, vague input, clarifying questions) taken from the incident-triage plan.
  - The two evaluation tiers documented, optional tier off by default.
  - A "verify, do not assume" list carried from the plan (idempotent re-import, model availability, flow rendering in browser chat UI, auth expiry).
  - Links to the `wxo-adk` skill for CLI details instead of duplicating them.
- **Todo List:**
  - [x] Draft the skill from [`plans/incident-triage-plan.md`](incident-triage-plan.md) decisions and Sub-Task status notes.
  - [x] Follow the `create-skill` skill for frontmatter and location.
  - [x] Review against the actual incident-triage layout so every checklist item maps to a real file.
  - [x] Record naming conventions here (moved from Sub-Task 1).
- **Relevant Context:** `.bob/skills/wxo-adk/SKILL.md`, plan lines 15-25 and 59-85.
- **Status:** `[x] done`
- **Status notes:**
  - Created [`.bob/skills/wxo-scenario-authoring/SKILL.md`](../.bob/skills/wxo-scenario-authoring/SKILL.md) (about 100 lines). Name matches the directory and the name regex; frontmatter has `name` and `description` only. Every repo path named in the skill was checked to exist.
  - Sections: goal and non-goals; agent-washing test; what every scenario ships (a path table with naming rules); design rules from Phase A; approval-flow pattern; two evaluation tiers; build order; verify-do-not-assume list; secrets and hygiene; done checklist.
  - **Not available until the next task:** per the `create-skill` guidance a new skill is picked up in a new conversation, so it was not activated or tried here.
  - **Added beyond the original outline (flag if you disagree):**
    - Rule 4: tool, flow and KB names are instance-wide, so they must be unique across scenarios. This follows from name-based import ("Existing Tool found. Updating...") and name-based teardown, but a name clash was **not tested**; the skill says so. It matters because a second scenario with a tool called `open_ticket` or `get_metrics` would likely replace the triage tool. The manifest from Sub-Task 1 does not check this yet; Sub-Task 5's scaffold or deploy script could (compare names across all `scenarios/*/scenario.yaml`).
    - Rule 7: scenarios with an approval flow should validate service / incident consistency in code, because Incident Triage Open Item 7 is still unfixed.
  - The skill refers to `scenario-demo-docs` (Sub-Task 4) as a skill that does not exist yet, and to deploy/package behaviour that Sub-Task 5 will deliver (`scenario.yaml` read by scripts). Those sentences become true only after those sub-tasks.
  - Context for Sub-Task 4: the skill's presentation row says the slide `tag` ("Scenario N • ...") must match the sidebar position; the demo-docs template should either tell the author to set N from the script-tag order or compute it.

### Sub-Task 3: Presentation refactor to per-scenario JS files

- **Intent:** Remove hand-edited sidebar HTML and index numbers; make a scenario a single file.
- **Expected Outcomes:**
  - `docs/demo/scenarios/incident-triage.js` holds the existing six slides, moved with no content change.
  - Placeholder files with `status: "soon"` exist for all four upcoming scenarios in confirmed order: `customer-returns.js` and `release-readiness.js` (new) and `hr-onboarding.js` and `cloud-finops.js` (current placeholder slides moved). The sidebar then shows five entries.
  - `presentation.html` keeps the shell, CSS and navigation; the sidebar (name, badge Live / Coming Soon, description) and the "Scenario N Slides" title render from `window.SCENARIOS`.
  - URL hash navigation (`#scenario/slide`) and keyboard shortcuts still work; page opens correctly from `file://`.
  - Optional `_helpers.js` extracted only if it clearly shortens the existing slides (do not refactor slide markup beyond that).
- **Todo List:**
  - [x] Add the `status` and `description` fields to the scenario object shape.
  - [x] Move `scenariosData` entries to their own files unchanged; add `<script src>` tags before the shell script.
  - [x] Generate sidebar buttons from the array; delete the three hand-written buttons and `switchScenario(n)` literals.
  - [~] Open in a browser and check all six triage slides, copy buttons, TOC, dots, hash, light / dark toggle, and the two placeholders. (Partly done headless; see status notes for what was NOT checked.)
- **Relevant Context:** [`docs/demo/presentation.html`](../docs/demo/presentation.html) lines 856-880 (sidebar), 977-1462 (data), 1465-1600 (state and rendering functions).
- **Status:** `[x] done` (pending the manual browser checks listed below)
- **Status notes:**
  - **Scenario object shape (documented in the comment above `buildScenarioList()` in `presentation.html`):** `id`, `name` (top bar title), `label` (sidebar name, number is prefixed automatically), `description`, `status` (`"live"` | `"soon"`), `slides[]` (`title`, `tag`, `subtitle`, `render()`). Each file does `window.SCENARIOS = window.SCENARIOS || []; window.SCENARIOS.push({...});`.
  - **Files:** `docs/demo/scenarios/{incident-triage,customer-returns,release-readiness,hr-onboarding,cloud-finops}.js`. The shell loads them with five `<script src="scenarios/...">` tags placed before the inline script; tag order = sidebar order. Adding a scenario = new file + one `<script src>` line.
  - **Shell changes:** `scenariosData` is now `window.SCENARIOS`; new `buildScenarioList()` creates the sidebar buttons (with `textContent`, no innerHTML) and is called from `init()` before `updateScenarioItems()`. The three hand-written buttons are gone; `presentation.html` went from 1673 to about 1230 lines. No CSS or other function changed.
  - **Content unchanged:** a throwaway script compared the original incident-triage block (441 lines, original lines 978-1418) with the new file after removing the three added fields; they are identical. The two original placeholders moved as-is with new "Scenario 4 / 5" tags; the two new placeholders (customer-returns, release-readiness) copy their callout format.
  - **Verified headless (Edge `--dump-dom` from `file://`, so no server needed):** sidebar shows 5 entries in the confirmed order with 1 Live and 4 Coming Soon badges and the right descriptions; exactly one active item; the default view is Incident Triage with counter 1 / 6, 6 TOC items and 6 dots; hash `#0/5` opens the prompts slide with 5 prompt cards; hash `#1/0` and `#4/0` open Customer Returns and Cloud FinOps with "Scenario 2 / 5 Slides" titles and 1 slide each.
  - **NOT verified (needs a manual look in a browser):** clicking sidebar buttons and the Previous / Next buttons, keyboard shortcuts, actually copying a prompt to the clipboard (and toast), light / dark toggle, fullscreen, and how the page looks visually. I did not change those functions, but I did not exercise them either. A `--dump-dom` run executes the page script but no clicks.
  - **Pre-existing behaviour noticed, not changed:** `handleKeydown` compares `e.key === "Space"`, but the browser sends `" "` for the space bar, so space does not advance slides. The slide tags are hard-coded ("Scenario 1 • ..."), so they must match the sidebar position; the new-scenario scaffold (Sub-Task 5) and template (Sub-Task 4) should note this or compute it.
  - **Not done on purpose:** no `_helpers.js` (the plan made it optional "only if it clearly shortens the existing slides"; slide markup was not touched). Placeholder scenario files have no matching manifest yet (only incident-triage has `scenario.yaml`).
  - The throwaway scripts and the copy of the original page under `.bob/tmp/` were deleted.

### Sub-Task 4: Skill `scenario-demo-docs` with templates

- **Intent:** Make each scenario's demo markdown and slides follow the incident-triage structure.
- **Expected Outcomes:**
  - `templates/demo-script.template.md` derived from [`docs/demo/incident-triage-demo.md`](../docs/demo/incident-triage-demo.md): the 10 sections (audience and goal, prerequisites, opening the chat UI, reset checklist, how to read the script / what was verified, scenes, if it goes wrong, things not to say, closing talking points, after the demo). The evaluation scene becomes optional.
  - `templates/scenario.template.js` derived from the six triage slides: Overview, Why and How the Agent is Used, How and Why the Agent Works, Real-Life Backend Services Mapping, Business and Operational Benefits, Live Demo Prompts.
  - `SKILL.md` giving the recipe and a consistency checklist: prompts identical in markdown and slides, tool names match `agent.yaml`, ground truth matches the demo claims, "what was and was not verified" filled from real runs only (no invented results).
- **Todo List:**
  - [x] Extract the template from the triage markdown, replacing scenario content with placeholders and keeping the honesty sections.
  - [x] Extract the slide template from `incident-triage.js` (after Sub-Task 3).
  - [x] Write `SKILL.md` including the prompt-duplication consistency check.
- **Relevant Context:** heading structure of `incident-triage-demo.md` (10 sections, scenes 1-6); `docs/demo/scenarios/incident-triage.js`.
- **Status:** `[x] done`
- **Status notes:**
  - **Files (all under `.bob/skills/scenario-demo-docs/`):** `SKILL.md` (56 lines), `templates/demo-script.template.md`, `templates/scenario.template.js`, `check_demo_consistency.py` (standard library; PyYAML used only for the optional manifest check).
  - **Demo-script template:** keeps the 10 sections and the Prompt / Expected behaviour (observed) / Point out / Fallback scene shape, the "what was and was not verified" table, "if it goes wrong", "things not to say", closing points and open items. Scenes 1 and 2 are given as examples with a note on which kinds of scene to include (vague input, main path, trap, governed action, restraint). The evaluation scene is optional and marked for deletion unless `evaluation.tier` is `full`. The honesty rule (only what was observed, with run counts) is stated at the top.
  - **Slide template:** the six Incident Triage slides with placeholders, using only CSS classes that exist in `presentation.html` (checked). The `{{N}}` slide-tag number is explained in the header and checked by the script (this closes the Sub-Task 3 note about hard-coded tags). Syntax-checked with `node --check` (exit 0).
  - **Checker `check_demo_consistency.py`:** checks the `<script src>` tag, slide-tag number vs sidebar position, leftover `{{...}}` / `AUTHOR NOTE`, prompts equal between md and slides (in order), copy-button ids vs prompt-box ids, and tool chips vs the manifest names. Run on the real repo: Incident Triage passes (5 prompts compared, 10 chips); the four placeholder scenarios pass with "no demo script yet" notes. **Fault-injection test (files created and deleted):** unfilled templates and a copy of the triage files with a changed prompt, a wrong slide number, a bad copy id and a misspelled tool chip were all reported as PROBLEM, exit 1. Test files were removed; `git status` shows no stray files.
  - **Decisions I made that you may want to change:**
    - The `SKILL.md` tells the author not to copy two things I found in the existing Incident Triage slides: the benefits slide states "from 30-45 minutes ... to under 15 seconds", which is not backed by anything measured in the repo, and the mapping slide says "Local Markdown Runbooks" although the runbooks are `.txt` and the plan notes markdown is not supported by the built-in KB. I did **not** change the existing slide; fixing it is a separate, small edit if you want it.
    - The checker was placed inside the skill folder rather than in `scripts/`, so it stays with the templates. The `package.py` allow-list is explicit, so it will not ship in the zip.
  - **Not done / not verified:** the skill was not activated in this conversation (new skills load in the next task); the templates have been syntax-checked and exercised by the checker but never used to build a real scenario, so the first real use (Customer Returns) is the real test. The demo-script template is not machine-checked beyond leftovers, prompts and placeholders.

### Sub-Task 5: Scenario-aware scripts

- **Intent:** Deploy, package, remove and smoke-test any scenario by name, driven by its manifest.
- **Expected Outcomes:**
  - `deploy-all.ps1` / `deploy-all.sh` accept an optional scenario name (`-Scenario` / `--scenario`) and deploy only that scenario's resources; with no argument behaviour is unchanged.
  - `package.py --scenario <name>` builds `dist/wxo-<name>-<version>.zip` from the manifest, keeps the deny-list security check, and generates the `INSTALL.md` text from the manifest instead of hard-coded incident-triage text. Output for incident triage is equivalent to the current zip.
  - Teardown scripts read resource names from the manifest.
  - `smoke_test_triage.py` becomes a generic smoke test that finds the agent by name and reads prompts from `ground_truth.json`; once it has no hard-coded UUID it may join the package allow-list.
  - `scripts/new-scenario.py` scaffolds the empty folder skeleton, a manifest, a `ground_truth.json` stub, a demo markdown from the template, and a presentation stub.
- **Todo List:**
  - [x] Add scenario selection to the deploy scripts (both shells), keeping the import order connections, tools, knowledge bases, flows, agents.
  - [x] Parameterize `package.py` and `INSTALL_MD` by manifest.
  - [x] Parameterize both teardown scripts; re-run `-DryRun` / `--dry-run` only (no real deletion).
  - [x] Generalize the smoke test; dry-run only (live run against the dev instance NOT done, see notes).
  - [x] Write `new-scenario.py` and test by scaffolding a throwaway scenario, then deleting it.
  - [x] Syntax-check PowerShell (parser) and bash (`bash -n`); rebuild the incident-triage zip and compare its entry list to the baseline (now 40 entries, not 35 — see notes).
- **Relevant Context:** [`scripts/deploy-all.sh`](../scripts/deploy-all.sh), `scripts/deploy-all.ps1`, [`scripts/package.py`](../scripts/package.py), `scripts/teardown.*`, [`scripts/smoke_test.py`](../scripts/smoke_test.py) (replaces `smoke_test_triage.py`, deleted).
- **Status:** `[x] done` (live smoke test, live deploy and real deletion not verified; see notes)
- **Status notes:**
  - **What was built:** `scripts/scenario_manifest.py` (`list`, `deploy-plan`, `teardown-plan`, `validate`); scenario-aware `deploy-all.*` and `teardown.*` (`-Scenario` / `--scenario`); `package.py --scenario`; `smoke_test.py`; `new-scenario.py`; `scenarios/hello-world/scenario.yaml`; `scenarios/incident-triage/install-notes.md`. README, demo markdown, agent README and both skills updated to match.
  - **Verified (all against a fake `orchestrate` executable, never a real instance):**
    - New `deploy-all.ps1` / `.sh` issue the same command sequence as the old ps1 baseline; the only difference is an added `Scenarios:` / `Scenario:` line.
    - New `teardown.ps1` / `.sh` `-DryRun` output matches the baseline plus a scope line.
    - New incident-triage zip has 40 entries vs 41 in the baseline. Added: `scenarios/incident-triage/scenario.yaml`, `scripts/scenario_manifest.py`, `scripts/smoke_test.py`. Removed: the four placeholder scenarios' JS files. `presentation.html` in the zip is a trimmed copy with only the incident-triage script tag. Post-build security check passed (re-run at the end of this sub-task).
    - Inside an extracted zip, `scenario_manifest.py validate`, `deploy-plan`, `deploy-all.ps1` (fake orchestrate) and `smoke_test.py --dry-run` work.
    - Fault injection in a sandbox: 21/21 passed (manifest validation faults, deny-list, secret/long-token detection, `results/`, `..` in `package_include`, missing script tag).
    - `bash -n` on both shell scripts, PowerShell parser on both ps1 scripts, `py_compile` on the four Python scripts, `scenario_manifest.py validate` OK, `check_demo_consistency.py incident-triage` OK.
    - `new-scenario.py` in a sandbox: dry run writes nothing; refuses to overwrite; rejects bad ids and agent-name clashes; leaves existing placeholder JS and script tags untouched and computes the correct sidebar position; generated JS passes `node --check`; `package.py` works for a "soon" scenario; `deploy-plan` skips "soon" scenarios unless named.
  - **Decisions:** `smoke_prompts` key added to `ground_truth.json` (four prompts copied exactly from the old script); `install-notes.md` per scenario is appended to the generated INSTALL known-issues list; the zip carries a trimmed `presentation.html`; a manifest was added for hello-world so teardown/deploy cover it; the scripts now depend on PyYAML (they use the Python next to the `orchestrate` executable); `INSTALL.md` dropped the "connections" step and the hello-world lines because the zip has neither.
  - **NOT verified:** the live path of `smoke_test.py` (it uses `AgentClient.get_draft_by_name(...)[0]['id']`, matched to how the ADK itself reads it); any live deploy, teardown or package against a real instance; real deletion; Git Bash was used for `bash -n` only.
  - **Cleanup done:** deleted `scripts/smoke_test_triage.py`, `.bob/tmp/` and my two test zips in `dist/`. `dist/wxo-incident-triage-1.0.0.zip` was rebuilt by the final package run (it pre-existed; it is git-ignored). Remaining `smoke_test_triage` mentions are in the two plan files as history.

### Sub-Task 6: Custom mode "Scenario Builder"

- **Intent:** One entry point that loads the right skills and permissions for scenario work.
- **Expected Outcomes:**
  - A mode defined per the `create-mode` skill with a role definition that: loads `wxo-scenario-authoring`, `scenario-demo-docs` and `wxo-adk` first; uses the ADK docs MCP tools; edits only repo files (no reading of `env.cfg` or `local/`); finishes with the consistency checklist.
  - Tool groups limited to read / edit / command / MCP as needed.
- **Todo List:**
  - [ ] Follow the `create-mode` skill for schema and file location.
  - [ ] Test by starting a throwaway scenario with `new-scenario.py` in the mode and checking it follows the skills.
- **Relevant Context:** skills from Sub-Tasks 2 and 4; `.bob/mcp.json`.
- **Status:** `[ ] pending` (depends on Sub-Tasks 2 and 4)

### Sub-Task 7: Documentation and follow-on plans

- **Intent:** Keep the repo understandable and set up the real scenario work.
- **Expected Outcomes:**
  - [`README.md`](../README.md) has a short "Adding a new scenario" section pointing to the mode, skills and scaffold script, replacing the generic 4-step "Adding a New Agent" text.
  - The scenario order is decided (see open item) and one plan file exists per scenario to be built next (for example `plans/hr-onboarding-plan.md`), each using the Sub-Task template from this plan and the incident-triage plan.
  - The Phase B / C outlines in [`plans/incident-triage-plan.md`](incident-triage-plan.md) are either linked to those plans or reconciled with the HR / FinOps names.
- **Todo List:**
  - [x] Update README structure tree and "adding a scenario" section.
  - [x] Resolve the scenario list mismatch with the user.
  - [x] Create the follow-on plan files.
- **Relevant Context:** README lines 190-196 ("Adding a New Agent"), plan lines 496-510.
- **Status:** `[x] done`
- **Status notes:**
  - **README:** added "Recommended: open the Scenario Builder mode in Bob" sentence and a pointer to `plans/<id>-plan.md` for follow-on plans. The structure tree and the scaffold/validate/skills instructions were already up to date from Sub-Task 5; only the mode mention and plan-file pointer were missing.
  - **Scenario list mismatch resolved:** Sub-Task 3 already included all five scenarios in the confirmed sidebar order (1=Incident Triage, 2=Customer Returns, 3=Release Readiness, 4=HR Onboarding, 5=Cloud FinOps). The incident-triage-plan.md Phase B/C outlines now link to the new plan files; a new "Additional scenarios" section links HR Onboarding and Cloud FinOps and states the build order.
  - **Follow-on plan files created:** `plans/customer-returns-plan.md`, `plans/release-readiness-plan.md`, `plans/hr-onboarding-plan.md`, `plans/cloud-finops-plan.md`. Each follows the sub-task template (overview, agent-washing check, mock world table, sub-tasks 1-7 mirroring the incident-triage build order, open items, suggested build order, not-done list). Sidebar position, scenario id, and phase linkage are stated in the header of each file.
  - **Not done (by design):** no scenario is built by this plan. The plan files are outlines; the mock world table rows and tool names are proposals subject to revision when the scenario is actually started.

---

## Suggested order

1 (manifest) and 3 (presentation refactor) are independent and can go first. 2 follows 1; 4 follows 3; 5 follows 1; 6 follows 2 and 4; 7 last.

## Not done by this plan

- No new agent, tool or knowledge base is built.
- No change to the incident-triage agent, tools or evaluation; its open items (plan lines 75-85) stay as they are.
- No generator from markdown / JSON for slides (deferred; can be layered on the per-scenario JS files later).
