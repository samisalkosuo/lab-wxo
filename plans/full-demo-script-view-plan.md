# Full Demo Script View - Plan

## Overview

The "Live Demo Prompts" slide (slide 6 of every scenario in `docs/demo/presentation.html`) only shows prompts. Presenters also need the expected answer for each prompt. This plan adds a "Show full script" view that:

- is opened by a small grey button at the lower right of each scene card (on the tip row) on slide 6;
- replaces the content of slide 6 (same slide slot, counter stays `6 / 6`) with the full script of that scenario: for each scene, the prompt(s) with a Copy button and the expected behaviour;
- is not a slide of its own, so it never appears in the left navigation, dots, or slide counter;
- opens scrolled to the scene whose button was pressed, and has a "Back to prompts" button.

Content source (decided with the user): the existing `docs/demo/<id>-demo.md` files, via a generated JS bundle (same pattern as `build-sample-docs-bundle.py` -> `sample-docs-bundle.js`, which works from `file://`). Per scene only the Prompt and Expected behaviour are shown. Point out, Fallback and Be straight blocks are dropped.

Applies to all 9 scenarios: incident-triage, customer-returns, release-readiness, hr-onboarding, cloud-finops, travel-request, pension-ove-advisor, yel-income-assessment, pension-disability-triage.

### Key findings from research

- Slide 6 of each scenario is built in `docs/demo/scenarios/<id>.js` (`prompt-card` > `prompt-card-top` + `prompt-box id="prompt-N"` + `prompt-tip`). Cards map one-to-one, in order, to the `**Prompt (type exactly...` blocks of the md (enforced by `src/wxodemo/validate.py`, which regex-matches `<div class="prompt-box" id="prompt-N">` - do not change that markup).
- Shell: `renderCurrentSlide()` in `presentation.html` (about line 1631) renders `slide.render()`; TOC and dots come from `deck.slides`; `copyPrompt(elementId, btn)` (about line 1735) reads text from an element id.
- The md files are NOT uniform:
  - Scene heading is `## Scene N - ...` (some use an em dash).
  - Prompt label varies: `**Prompt (type exactly):**`, `**Prompt (type exactly; same as scene 2):**`, and in yel scene 5 `**What to type (same thread as Scene 1):**` (no card on slide 6 for that scene).
  - Expected label varies: `**Expected behaviour (observed):**`, `(not verified ...)`, `(from 1 SDK smoke run)`, and `**What the form shows ...**` in customer-returns scene 5.
  - Some scenes have two prompts (travel scene 2), sub-sections `### 5a/5b` or `### 8a/8b` (approve/reject paths), an intro paragraph or blockquote before the first prompt (thread-continuity notes), tables, nested bullets and fenced code blocks in expected text.
  - Slide card scene pills do not always match md scene numbers (customer-returns "Scene 5 & 6", travel "Scene 2" twice), so mapping must be by prompt index, not by scene number.

## Design decisions

- Bundle: new script `docs/demo/build-demo-scripts-bundle.py` writes `docs/demo/demo-scripts-bundle.js` (`window.DEMO_SCRIPTS = { "<id>": { scenes: [...] } }`). Auto-generated header like the sample-docs bundle. The shell loads it with one `<script>` tag.
- Parsing rule (generic, not per-scenario): split each md on `## Scene` headings. Inside a scene, split into blocks at bold-label lines. Drop blocks labelled Point out, Fallback, Be straight. Keep everything else (intro text, prompt blocks, expected blocks, 5a/5b sub-sections) as markdown. Fenced code blocks that directly follow a Prompt/What to type label are flagged as prompts and get a Copy button; other code blocks stay plain. Each prompt is numbered in document order, so the Nth prompt matches `prompt-N` on slide 6.
- Rendering: a small markdown-to-HTML helper in the shell (paragraphs, bold, inline code, bullets incl. nested, numbered lists, fenced code, blockquote, tables, `###` headings). HTML-escape first. No external library, so it keeps working from `file://`.
- Navigation state: a `scriptView` flag/anchor in the shell. When set and the active slide is the Live Demo Prompts slide, `renderCurrentSlide()` renders the script view instead of `slide.render()`. Leaving the slide, pressing Back, or clicking the TOC entry for slide 6 clears it. The URL hash gets a suffix so a refresh keeps the view (for example `scenario/3/5/script/2`). TOC, dots, counter and progress bar are untouched.
- Slide 6 identification: the shell needs to know which slide is "the prompts slide". Use the last slide whose title is "Live Demo Prompts" (all 9 scenarios use this title); do not add a new field to scenario data.
- Button markup in each scenario `.js`: inside `prompt-tip`, push right with `margin-left:auto`; class `script-btn` (new grey, low-emphasis style defined once in the shell CSS). It calls a shell function, for example `showFullScript(promptIndex)`. No scenario-specific CSS or JS.
- Scope limits: standalone agents are not changed. The md files are not changed. Keeping the md and slide prompts equal stays enforced by the existing validator.

## Sub-tasks

### 1. Build the demo-scripts bundle generator

- **Intent**: Turn each `docs/demo/<id>-demo.md` into structured data the shell can render, with no hand copying.
- **Expected Outcomes**: `python docs/demo/build-demo-scripts-bundle.py` creates `docs/demo/demo-scripts-bundle.js` with all 9 scenarios; for every scenario the number of extracted prompts equals the number of `prompt-box` cards on slide 6 (except yel scene 5, whose "What to type" prompt has no card; handle by order, see below); Point out / Fallback / Be straight text does not appear in the output.
- **Todo List**:
  1. Write the parser per the parsing rule above (scenes, blocks, prompt flagging, sub-sections).
  2. Decide and implement how prompts without a slide card (yel scene 5) are numbered: numbering follows card ids only for prompts under a `**Prompt (` label; `**What to type` prompts get their own copy id and no card mapping.
  3. Emit the bundle with the auto-generated header comment (same style as `build-sample-docs-bundle.py`).
  4. Add a pytest in `tests/` (style of `tests/test_scaffold_validate.py`) covering: label variants, dropped blocks, two prompts in one scene, sub-sections, and that real repo md files parse to the same prompt list as `md_prompts()` in `src/wxodemo/validate.py`.
  5. Run it and commit-check the generated bundle by eye for the awkward scenes: travel 2 and 8, customer-returns 5, yel 5, cloud-finops 3.
- **Relevant Context**: `docs/demo/build-sample-docs-bundle.py`, `src/wxodemo/validate.py` (`md_prompts`), all `docs/demo/*-demo.md`, `tests/test_scaffold_validate.py`.
- **Status**: [x] done

### 2. Add the full-script view to the shell (`presentation.html`)

- **Intent**: Render the script view in place of slide 6, hidden from navigation.
- **Expected Outcomes**: Calling the show function replaces the slide 6 body with scenes (heading, intro, prompt with Copy, expected behaviour); counter still reads `6 / 6`; TOC and dots unchanged; Back returns to the prompt cards; the view opens at the chosen scene; copy works and shows the existing toast; works in dark and light themes.
- **Todo List**:
  1. Add the `<script src="demo-scripts-bundle.js">` tag next to `sample-docs-bundle.js`.
  2. Add CSS: `.script-btn` (grey, small, low emphasis, hover slightly lighter), script-view layout (scene header reusing `scene-pill` / `prompt-title`, prompt block reusing `prompt-box` look but with new ids so the validator regex is not affected, expected block, back button). Use existing CSS variables for both themes.
  3. Add the small markdown renderer and `showFullScript(promptIndex)` / `closeFullScript()`; hook into `renderCurrentSlide()` and `goToSlide` / `nextSlide` / `prevSlide` so the view is cleared on leaving slide 6; extend the hash handling in `init`/hash parsing so a refresh restores the view.
  4. Reuse `copyPrompt(elementId, btn)` for the copy buttons (give prompt blocks unique ids such as `script-prompt-N`).
  5. Handle a missing bundle entry gracefully (button shows nothing / view says no script available) for scenarios whose status is not live.
- **Relevant Context**: `docs/demo/presentation.html` (`renderCurrentSlide`, `goToSlide`, `copyPrompt`, hash handling in `init`, CSS near `.prompt-tip` at about line 863), `docs/demo/standalone-agents.js` loading pattern for `SAMPLE_DOCS`.
- **Status**: [x] done

### 3. Add the "Show full script" button to all 9 scenario slide 6s and the template

- **Intent**: Give every scene card the grey button at the lower right of the tip row.
- **Expected Outcomes**: Every `prompt-card` in the 9 scenario files has a `script-btn` inside the `prompt-tip` row, opening the full script scrolled to that card's scene; `templates/scenario.template.js` in the skill folder includes it so new scenarios get it.
- **Todo List**:
  1. Edit each `docs/demo/scenarios/<id>.js` (49 cards in total) to add the button to the tip row; pass the card's prompt number.
  2. Update `.bob/skills/scenario-demo-docs/templates/scenario.template.js` and the class list in its header.
  3. Update `.bob/skills/scenario-demo-docs/SKILL.md` (and `wxo-scenario-authoring` if it lists slide 6 markup): mention the button, and that the bundle must be rebuilt after changing a demo md.
- **Relevant Context**: `docs/demo/scenarios/*.js` (slide 6 sections at about lines 303-440+), `.bob/skills/scenario-demo-docs/templates/`.
- **Status**: [x] done

### 4. Validation and consistency

- **Intent**: Keep the bundle, md and slides from drifting apart.
- **Expected Outcomes**: `python wxodemo.py validate` still passes for all scenarios; a stale bundle (md changed, bundle not rebuilt) is reported.
- **Todo List**:
  1. Extend `src/wxodemo/validate.py` demo checks: bundle exists, has an entry for the scenario, its prompts equal the md prompts; each `showFullScript(n)` index exists. Keep the existing regexes working.
  2. Add test cases in `tests/test_scaffold_validate.py`.
  3. Run `python wxodemo.py validate` and the test suite.
  4. Open `presentation.html` in a browser (from `file://`) and, for at least two scenarios (one simple like hr-onboarding, one complex like travel-request), check: button looks grey and unobtrusive, opens at the right scene, copy works, Back works, left nav shows no extra entry, refresh restores the view, light theme readable. State to the user what a headless check could not test.
- **Relevant Context**: `src/wxodemo/validate.py`, `tests/test_scaffold_validate.py`, `wxodemo.py`.
- **Status**: [x] done

## Open points to confirm

- Include the short intro text that sits before a scene's first prompt (for example "Use one conversation for both prompts", or yel scene 5 "same thread as Scene 1")? The plan assumes yes, because without it some scenes are misleading, even though the user asked for only prompt + expected answer.
- Expected-behaviour headings carry honesty labels such as "(not verified against live instance)". The plan keeps these labels verbatim.

