# Standalone agents: move examples to `examples.md`

## Overview

Each standalone agent README currently embeds its example prompts. Move them into a dedicated
`standalone/<agent>/examples.md` so future tools can consume them from one predictable file,
and link to it from the README. Update the **Standalone Builder** mode (and `standalone/README.md`)
so every new agent must ship an `examples.md`. Making this mandatory is the point of the change.

Scope: two existing agents (`translator`, `travel-rules-qa`), `standalone/README.md`, and
`.bob/custom_modes.yaml` (standalone-builder). No changes to `agent.yaml` or `manage.py`.

Decisions (confirmed with user): file name `examples.md`, markdown, numbered list as today.

## Examples file format (shared by all agents)

So that tools can parse the files reliably, every `examples.md` uses the same shape:

- `# <agent_name> — Examples` heading
- One short intro sentence
- A numbered list. Each item is `N. *"prompt"* — expected behaviour` (prompt in italics and quotes,
  em dash, expected behaviour or source section on the same item).
- No other content that is not an example.

`travel-rules-qa` currently splits the expected source onto a second line. Keep the second line
as an indented continuation of the same list item (existing text is preserved verbatim, not rewritten).

---

## Sub-task 1: Create `examples.md` for both agents and link from READMEs

**Intent:** Separate the example prompts from the READMEs without changing their content.

**Expected Outcomes:**
- `standalone/translator/examples.md` and `standalone/travel-rules-qa/examples.md` exist with the current examples verbatim.
- Each README no longer contains the examples; its examples section is a one-line pointer to `examples.md`.

**Todo List:**
1. Create `standalone/translator/examples.md` with the 5 prompts from README lines 59-65.
2. Create `standalone/travel-rules-qa/examples.md` with the 5 questions (and section references) from README lines 83-100, plus the "well covered by the document" intro.
3. In `translator/README.md` replace `## Example prompts` section with a short section linking to `examples.md`.
4. In `travel-rules-qa/README.md` replace `## Example questions` section likewise (keep `## Document attribution` intact).

**Relevant Context:**
- [`standalone/translator/README.md`](standalone/translator/README.md:59)
- [`standalone/travel-rules-qa/README.md`](standalone/travel-rules-qa/README.md:83)

**Status:** [ ] pending

---

## Sub-task 2: Make `examples.md` mandatory in the Standalone Builder mode

**Intent:** Ensure future agents created by the mode always include an examples file.

**Expected Outcomes:**
- The mode's Conventions list `standalone/<agent-name>/examples.md` as required, with the format above.
- The mode says the agent README must link to `examples.md` and must not embed the examples.
- The finish checklist verifies `examples.md` exists for the agent and is linked from the README.

**Todo List:**
1. In `.bob/custom_modes.yaml` (standalone-builder, line 67-69) add `examples.md` to the per-agent file list and mark it mandatory, since future tools read it.
2. Add a convention bullet describing the format and that README links to it rather than duplicating.
3. Add to the "Finish every task" section a check that `examples.md` exists and is linked in README (alongside the existing `manage.py` commands).
4. Keep the YAML `>-` block valid (indentation only, no stray colons breaking it).

**Relevant Context:**
- [`.bob/custom_modes.yaml`](.bob/custom_modes.yaml:51)

**Status:** [ ] pending

---

## Sub-task 3: Update `standalone/README.md` conventions

**Intent:** Keep the human-facing docs consistent with the mode.

**Expected Outcomes:**
- Directory layout shows `examples.md`.
- "Adding a new agent" lists creating `examples.md` as a required step, with the format.

**Todo List:**
1. Add `examples.md` to the layout tree (lines 19-26).
2. Add a numbered step in "Adding a new agent" (lines 36-41) for `examples.md` and note README must link to it.

**Relevant Context:**
- [`standalone/README.md`](standalone/README.md:17)

**Status:** [ ] pending

---

## Validation

- `python standalone/manage.py list` and `python standalone/manage.py deploy --agent translator --dry-run` / `--agent travel_rules_qa --dry-run` still succeed (the files are not touched by manage.py; this is a regression check).
- grep READMEs to confirm no example prompts remain and links resolve.
- Re-read `.bob/custom_modes.yaml` to confirm valid YAML.
