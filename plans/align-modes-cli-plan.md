# Plan: Align Custom Modes with Current wxodemo CLI

## Top-Level Overview

The two custom modes in `.bob/custom_modes.yaml` — **Scenario Builder** and **Standalone Builder**
— reference `python wxodemo.py` commands in their `roleDefinition` finishing rituals.
Several CLI commands that are directly relevant to each mode's job are not mentioned at all,
and the finishing rituals are incomplete or missing steps that would give the AI a stronger
quality gate.

This plan updates both `roleDefinition` blocks so they accurately reflect every command the AI
should know about, extend the finishing ritual, and correctly sequence prerequisite steps
(login / doctor before real runs).

**Scope:** `.bob/custom_modes.yaml` only. No code changes. No changes to skills or plan files.

---

## Sub-Task 1 — Scenario Builder: add missing commands and extend finishing ritual

**Status:** [x] done

### Intent
The Scenario Builder mode currently tells the AI to run only `python wxodemo.py validate <id>` as
its final check. The CLI also offers `new-scenario` (which scaffolds the manifest and stubs the
agent and ground-truth the mode is responsible for), `smoke` (a live prompt pass), `eval` (ADK
evaluation), `deploy` / `undeploy` / `status` (lifecycle management), and `login` / `doctor`
(prerequisites). The mode's role definition should name these so the AI knows they exist and can
use them correctly during the scenario lifecycle — not just at the finish line.

### Expected Outcomes
- `roleDefinition` for `scenario-builder` lists every CLI command relevant to the scenario
  lifecycle and when to use each.
- The finishing ritual includes, in order:
  1. `python wxodemo.py validate <id>` (manifest + demo consistency — already present)
  2. `python wxodemo.py smoke <id> --dry-run` (preview smoke prompts without a live call)
  3. Notes that a real `smoke <id>` and `deploy <id>` require a live instance and `login` first.
- The `new-scenario` command is surfaced as the correct way to scaffold a new scenario (aligns
  with what `wxo-scenario-authoring` section 7 already says).
- The `--dry-run` pattern is explained for `deploy` and `smoke`.

### Todo List
1. Open `.bob/custom_modes.yaml` and locate the `scenario-builder` `roleDefinition` block.
2. After the existing build-order paragraph, insert a **CLI reference paragraph** that lists:
   - `new-scenario <id> --name ... --description ...` — scaffold manifest and stubs
   - `validate <id>` — check manifest + demo consistency (must print OK)
   - `deploy <id>` / `deploy <id> --dry-run` — deploy or preview
   - `undeploy <id>` — tear down
   - `status <id>` — compare repo with what is live
   - `smoke <id> --dry-run` / `smoke <id>` — preview or run smoke prompts
   - `eval <id> --dry-run` / `eval <id>` — preview or run ADK evaluation
   - `login` — required before any live operation
3. Replace the single-line finishing ritual (`python wxodemo.py validate <id>`) with a
   two-step finishing ritual:
   - Step 1: `python wxodemo.py validate <id>` — fix every PROBLEM before continuing.
   - Step 2: `python wxodemo.py smoke <id> --dry-run` — confirm smoke prompts are present.
   - Note: real smoke / deploy need a live instance; call `login` first.

### Relevant Context
- File: [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml)
- CLI source: [`src/wxodemo/cli.py`](src/wxodemo/cli.py) — `cmd_validate`, `cmd_smoke`, `cmd_eval`,
  `cmd_deploy`, `cmd_new_scenario`
- Skill reference: [`.bob/skills/wxo-scenario-authoring/SKILL.md`](.bob/skills/wxo-scenario-authoring/SKILL.md)
  section 7 build order (already tells AI to use `new-scenario`; mode should be consistent)

---

## Sub-Task 2 — Standalone Builder: add missing commands and tighten finishing ritual

**Status:** [x] done

### Intent
The Standalone Builder mode's finishing ritual calls `list --kind standalone` and
`deploy <name> --dry-run`. This is reasonable but incomplete: it doesn't mention `status`,
`undeploy`, `login` / `doctor`, or the fact that `validate` is a no-op for standalone agents
(so the AI should not try to run it). The mode also states conventions that should reference
`deploy` / `undeploy` by their actual flag syntax.

### Expected Outcomes
- `roleDefinition` for `standalone-builder` lists every CLI command relevant to standalone agents.
- The finishing ritual explicitly states that `validate` does nothing for standalone agents.
- The finishing ritual adds `python wxodemo.py doctor` as a preflight check when something fails.
- The conventions paragraph already references `list`, `deploy`, `undeploy` correctly; a note is
  added that `login` is required before any live `deploy` / `undeploy`.
- `status` is mentioned as the way to confirm a live deployment.

### Todo List
1. Open `.bob/custom_modes.yaml` and locate the `standalone-builder` `roleDefinition` block.
2. After the existing conventions paragraph, insert a **CLI reference paragraph** that lists:
   - `list --kind standalone` — show all standalone agents
   - `deploy <name>` / `deploy <name> --dry-run` — deploy or preview
   - `undeploy <name>` / `undeploy <name> --dry-run` — undeploy or preview
   - `status <name>` — compare repo with what is live
   - `login` — required before any live deploy / undeploy
   - `doctor` — check environment health if something fails
   - `validate` — note: standalone agents have no manifest; validate is a no-op for them
3. Replace the two-step finishing ritual with:
   - Step 1: Confirm `standalone/<name>/examples.md` exists and follows the format.
   - Step 2: `python wxodemo.py list --kind standalone` — verify the agent is discovered.
   - Step 3: `python wxodemo.py deploy <name> --dry-run` — preview the deploy commands.
   - Note: real deploy needs a live instance; call `login` first, `status <name>` after.

### Relevant Context
- File: [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml)
- CLI source: [`src/wxodemo/cli.py`](src/wxodemo/cli.py) — `cmd_list`, `cmd_deploy`,
  `cmd_undeploy`, `cmd_status`, `cmd_validate` (which explicitly returns 0 and prints
  "Standalone agents have no manifest to validate")
- Standalone reference: [`standalone/README.md`](standalone/README.md) (if it exists)
