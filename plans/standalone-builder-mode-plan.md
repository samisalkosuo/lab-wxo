# Plan: `standalone-builder` Bob mode

## Overview

Add a custom Bob mode, `standalone-builder`, for creating ad-hoc watsonx Orchestrate agents
under `standalone/`. It goes in `.bob/custom_modes.yaml` next to `scenario-builder`.
Scenario Builder's workflow is built around manifests, `ground_truth.json`, demo docs and
the consistency checker, none of which apply to standalone agents. A separate mode gives
users a clear choice and loads the right rules.

Decision (confirmed with the user): conventions go directly in the mode's `roleDefinition`,
and the mode activates the existing `wxo-adk` skill. No new skill. `scenario-builder`'s
`whenToUse` gets a cross-reference to the new mode.

**Non-goals:**
- No new skill.
- No changes to `standalone/manage.py`, to the existing agent, or to scenario files.
- No changes to the `scenario-builder` `roleDefinition`. Only its `whenToUse` changes.

---

## Sub-Tasks

### Task 1 - Add the `standalone-builder` mode to `.bob/custom_modes.yaml`

**Intent:**
Give users a dedicated mode whose always-loaded instructions encode the standalone-agent
conventions, so they are not confused with the scenario rules.

**Expected Outcomes:**
- `.bob/custom_modes.yaml` contains a second entry with slug `standalone-builder`.
- The same `groups` as scenario-builder: read, edit, execute, mcp, skill, todo, subagent.
- The file still parses as valid YAML, and `scenario-builder` is unchanged apart from Task 2.

**Todo List:**
1. Append the new mode entry. Use the same style as `scenario-builder` (folded `>-` blocks).
2. `roleDefinition` content:
   - Role: create and maintain one-off agents under `standalone/<agent-name>/`. They are
     not owned by any scenario.
   - At the start of every task, activate `wxo-adk`. Use the ADK docs MCP tools to check
     CLI commands and YAML schemas before writing anything.
   - Read `standalone/README.md` first for conventions.
   - Layout: one subdirectory per agent, containing `agent.yaml` and `README.md`. No
     `scenario.yaml`, no manifest entry, no packaging, no evaluation or demo-doc
     requirements.
   - Deploy and teardown go through `python standalone/manage.py` (`list`, `deploy`,
     `undeploy`, `--agent`, `--dry-run`). `manage.py` discovers agents automatically.
   - Agents may reuse KBs and tools that scenarios already deploy. They must not duplicate
     them. The README must name every resource that has to be live already.
   - Hard limits:
     - Never read, print, or package `env.cfg` or `local/`.
     - Never edit files under `scenarios/`, `agents/`, `tools/`, `flows/` or `knowledge/`, and never add the agent to a scenario manifest.
     - Never attach a write tool directly to an agent.
     - Never have `manage.py` or the agent README remove a shared KB.
     - Never claim the agent was tested or retrieves correctly without a recorded run.
   - Finish every task by running `python standalone/manage.py list` and
     `python standalone/manage.py deploy --agent <name> --dry-run`. Fix any failure.
     Report what was not verified, especially anything that needs a live instance.
3. `whenToUse`: one-off or ad-hoc agents that are not part of a demo scenario. Also point
   users to Scenario Builder for scenario work.

**Relevant Context:**
- `.bob/custom_modes.yaml` (existing `scenario-builder` entry is the template)
- `standalone/README.md` and `standalone/manage.py` (conventions the prompt must match)
- `standalone/travel-rules-qa/` (reference example of a standalone agent)
- `.bob/skills/wxo-adk/SKILL.md` (the skill the mode activates)

**Status:** [x] done

---

### Task 2 - Cross-reference from Scenario Builder

**Intent:**
Stop users from picking Scenario Builder for standalone work.

**Expected Outcomes:**
- The `scenario-builder` `whenToUse` ends with a sentence such as: "For one-off agents not
  owned by a scenario, use Standalone Builder instead."

**Todo List:**
1. Edit `whenToUse` of `scenario-builder` in `.bob/custom_modes.yaml` (lines 38-41). Add the
   sentence. Change nothing else in that entry.

**Relevant Context:**
- `.bob/custom_modes.yaml:38-41`

**Status:** [x] done

---

### Task 3 - Mention the mode in the docs

**Intent:**
Make the mode discoverable where people read about standalone agents.

**Expected Outcomes:**
- `standalone/README.md` has a short note that the **Standalone Builder** mode is the
  recommended way to author new standalone agents with Bob.
- The "Standalone Agents" section of the root `README.md` has the same one-line pointer.

**Todo List:**
1. Check whether the root `README.md` or `standalone/README.md` already mentions the
   Scenario Builder mode. Match its wording and placement.
2. Add one line to each file. Do not restructure either file.

**Relevant Context:**
- `README.md` ("Standalone Agents" section)
- `standalone/README.md`

**Status:** [x] done

---

### Task 4 - Validate

**Intent:**
Make sure the config is valid and that the two modes don't overlap.

**Expected Outcomes:**
- `.bob/custom_modes.yaml` loads with PyYAML and has two modes with distinct slugs.
- The `whenToUse` texts of the two modes don't overlap.

**Todo List:**
1. Run `python -c "import yaml;print([m['slug'] for m in yaml.safe_load(open('.bob/custom_modes.yaml'))['customModes']])"`. Expected output: `['scenario-builder', 'standalone-builder']`.
2. Read both `whenToUse` entries side by side.
3. Report that the mode only appears in Bob's mode picker after a reload. This cannot be
   checked from the CLI.

**Relevant Context:**
- `.bob/custom_modes.yaml`

**Status:** [x] done
