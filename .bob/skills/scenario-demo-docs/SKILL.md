---
name: scenario-demo-docs
description: Use when the user wants to write or update the demo script markdown (docs/demo/<id>-demo.md) or the presentation slides (docs/demo/scenarios/<id>.js) for a watsonx Orchestrate demo scenario in this repo, or to check that a scenario's demo script, slides and manifest are consistent. Incident Triage is the template.
---

# Scenario Demo Docs (lab-wxo)

Every scenario ships two documents that follow Incident Triage:

| Document | Path | Template |
|---|---|---|
| Demo script (for the presenter) | `docs/demo/<id>-demo.md` | `templates/demo-script.template.md` (10 sections, scenes) |
| Slides (for the audience) | `docs/demo/scenarios/<id>.js` | `templates/scenario.template.js` (6 slides) |

Templates are in this skill's folder: `.bob/skills/scenario-demo-docs/templates/`. The consistency checks run as part of `python wxodemo.py validate <id>`.

Load `wxo-scenario-authoring` first for what the scenario itself must contain. This skill only covers the documents.

## Rules that matter most

1. **Write the demo script after you have run the scenario**, not before. "Expected behaviour (observed)", "what was and was not verified", "if it goes wrong" and "things not to say" can only contain what you saw. State how many runs, and what was not driven (for example an approval form that only a browser can answer).
2. **No invented numbers.** Do not put minutes saved, % reductions, latency figures or run counts on a slide or in the script unless a recorded run supports them. Illustrative figures must say "illustrative". (The existing Incident Triage benefits slide has an unmeasured MTTR claim; do not copy that pattern.)
3. **Be honest about the agent-vs-script question** in the benefits slide and the closing talking points. Do not claim the agent beats a script or passes an evaluation unless the repo holds the run that shows it.
4. **Same prompts everywhere.** Each "Prompt (type exactly)" block in the markdown must equal the matching `prompt-box` text on the Live Demo Prompts slide, character for character, in the same order.
5. **Real names only.** Tool chips, flow names and knowledge-base names must be the exact names in `scenarios/<id>/scenario.yaml`. Show only tools attached to the agent plus the flow; never list a write tool that only the flow calls as an agent tool.
6. **Describe the mock honestly.** Say what the knowledge-base documents really are (the built-in KB uses `.txt`; the Incident Triage mapping slide says "Local Markdown Runbooks", which is wrong). Only list real-world systems you can name accurately.
7. **Do not add CSS or JS to the shell** for a scenario. Use the classes listed in the template header. If a new component is truly needed, change `presentation.html` once and tell the user.

## Procedure

1. **Gather facts** (use `read_file` / `grep`, do not rely on memory): `scenarios/<id>/scenario.yaml`, `agents/<id>/agent.yaml`, `evaluation/<id>/ground_truth.json`, the scenario plan `plans/<id>-plan.md`, and the notes of real runs (SDK dry-runs, browser tests). If runs were not done, tell the user the script cannot be completed yet and stop at a draft that says "not verified" in every verification row.
2. **Demo script.** Copy `templates/demo-script.template.md` to `docs/demo/<id>-demo.md` with `execute_command` (`Copy-Item`) or `write_file`, then fill it in:
   - Keep section numbers 1-10 and the order. Delete the optional evaluation scene unless `evaluation.tier` is `full`.
   - Scenes: at least one vague or messy-input scene, one main-path scene, one trap scene (red herring or tempting wrong answer), one governed-action scene if there is an approval flow (copy the Approve / Reject structure of Scene 4 in `incident-triage-demo.md`), and one restraint scene if the scenario has a "do nothing" case.
   - Each scene: Prompt, Expected behaviour (observed), Point out, Fallback. Add "Be straight" for known easy cases or limits.
3. **Slides.** Copy `templates/scenario.template.js` over the placeholder `docs/demo/scenarios/<id>.js` and fill it in:
   - Keep the six slides in order: Overview, Why and How the Agent is Used, How and Why the Agent Works, Real-Life Backend Services Mapping, Business and Operational Benefits, Live Demo Prompts. Add or remove cards inside a slide as needed; do not change the slide order.
   - Slide 1 (Overview) must include the `.fit-card` directly below `.callout-banner` with Industry (explicitly "Cross-Industry" or specific vertical), Function, and Target Roles pills.
   - Set `status: "live"` only when the scenario is deployed and the demo script exists; otherwise keep `"soon"` and the short placeholder slide.
   - `tag` text "Scenario N • ..." uses N = the scenario's position in the `<script src>` order in `presentation.html`. The tags are static text; if you reorder scripts, update every tag.
   - Make sure `presentation.html` has `<script src="scenarios/<id>.js"></script>` (new scenarios need one line there; this is the only edit to the shell).
   - Escape `${`, backticks and `</script` inside the template literals; avoid them in text.
4. **Check.** Run:
   ```
   python wxodemo.py validate <id>
   ```
   It checks the manifest and prints the demo checks as `demo: ...` lines. The demo checks verify the script tag, slide-tag numbers, leftover `{{...}}` / `AUTHOR NOTE`, prompt equality between md and slides, copy-button ids, and tool chips against the manifest. Fix every PROBLEM. It does not check facts, tone or claims: re-read rule 1-3 yourself.
5. **Look at it.** Open `docs/demo/presentation.html` in a browser (it works from `file://`), go to the new scenario, click through all six slides and press **Copy Prompt** once. State to the user what you did and did not check; a headless check cannot test clicks.
6. **Update the plan and README** pointers for the scenario if they exist, and tell the user what is still unverified.

`python wxodemo.py new-scenario <id> --name "..." --description "..."` already copies the demo-script template to `docs/demo/<id>-demo.md` (with `{{ID}}`, `{{NAME}}`, `{{AGENT_NAME}}` filled in), so in step 2 you edit that file instead of copying the template. For slides it only creates a short "soon" placeholder `docs/demo/scenarios/<id>.js` and adds the `<script>` tag; step 3 still means copying `templates/scenario.template.js` over that placeholder. Use the step 2 copy command only for a scenario that was created without the scaffold.

## Pointers to the reference files

- Script structure and tone: `docs/demo/incident-triage-demo.md` (honest "what was not verified", "things not to say", "if it goes wrong").
- Slide markup: `docs/demo/scenarios/incident-triage.js`.
- Shell and available CSS classes: `docs/demo/presentation.html`.
- Manifest schema: header of `scenarios/incident-triage/scenario.yaml`.
