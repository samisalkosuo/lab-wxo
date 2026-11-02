# Public release documentation plan

## Overview

**Goal.** Make the repo useful to colleagues, customers and partners who find it on GitHub: they can (1) deploy the samples into their own watsonx Orchestrate (WXO) instance and (2) learn how to build their own agents, ideally with Bob.

**Scope.** Documentation only: `README.md`, the other READMEs, `docs/`, and the few Bob mode/skill lines that refer to README sections that will no longer exist. No agent, tool, flow or CLI behaviour changes.

**Decisions already made (from the user)**
- Root README order: intro, prerequisites, deploy commands, then everything else.
- Remove the "Repository Structure" tree. Keep a short "where things live" paragraph instead.
- No counts ("10 scenarios") in the title or intro. The README "What is included" tables are kept and must be updated whenever an agent is added.
- Python: say what was used (3.14) and the minimum (3.11). Bob: recommended for development, not required.
- WXO API key and URL: a placeholder "see the watsonx Orchestrate documentation"; the user will add details later.
- Docker or Podman: optional, only for the traffic generator.
- Keep `plans/` as is. It shows how development progresses and how Bob uses plans.
- Keep `techzone1` mentions in `plans/` and `.bob/`. Neutralise them in user-facing READMEs and demo scripts only.
- MIT license is already added. Do not add `CONTRIBUTING.md`.
- Add sample Bob prompts for creating a small scenario and a standalone agent.

**Facts the docs must state (verified in the repo)**
- All agents use `llm: groq/openai/gpt-oss-120b`; the instance must offer it (`orchestrate models list`).
- `knowledge/travel-request/*.yaml` use embedding model `ibm/granite-embedding-278m-multilingual`; only the travel-request scenario needs it.
- Dependencies: `requirements.txt` pins `ibm-watsonx-orchestrate==2.18.2`; the evaluation framework is optional and not installed by `setup`.
- `traffic-gen` uses only the Python standard library and runs in a container (Dockerfile at `traffic-gen/Dockerfile`, build context is the repo root).
- Scenario agents are in `agents/`, standalone in `standalone/`; `wxodemo deploy` only deploys what a scenario manifest lists or what is under `standalone/`.

---

## Proposed root README outline

1. **Title and intro**: what the repo is, who it is for, what you can do with it (deploy samples, learn patterns, build with Bob). Mock/synthetic data, as-is notice.
2. **Prerequisites**: table (Python 3.11+, tested on 3.14; WXO instance with API key and URL, "see the WXO documentation"; model `groq/openai/gpt-oss-120b`; embedding model only for travel-request; optional Docker or Podman; optional Bob).
3. **Deploy**: venv, `setup`, `env.cfg`, `doctor`, `login`, `deploy hello-world` (smoke check), `deploy --all`, `undeploy`.
4. **Try it**: first prompts to type in the WXO chat for a few agents, and where the demo scripts are.
5. **What is included**: the two agent tables (kept; one line each; no counts).
6. **Learn by example**: pattern to sample map (no tools, tool, knowledge base, approval flow, multi-agent).
7. **Build your own**: pointer to Bob modes and to `docs/building-with-bob.md`; manual route for non-Bob users.
8. **Development**: `wxodemo` command table, link to `docs/wxodemo.md`, evaluation and smoke tests, running the repo tests, "where things live" paragraph, `plans/` explained.
9. **Traffic generator and chat export**: what each does and how to start (short, link out).
10. **Known limitations and troubleshooting**: actionable items only, link to `docs/known-issues.md` and the troubleshooting table in `docs/wxodemo.md`.
11. **License and trademarks**.

---

## Sub-tasks

Process one at a time and let the user review each before the next.

### 1. Root README rewrite
- **Intent:** Replace the 355-line README with the outline above.
- **Expected outcomes:** A newcomer reaches a working `hello_world` deploy from the README alone; no directory tree; no internal test statistics; anchors that other files link to still resolve.
- **Todo:**
  1. Keep the content of the existing Quick start, but reorder (intro, prerequisites, deploy first).
  2. Add the prerequisites table, including the model and embedding-model requirements.
  3. Add a first-deploy check (`deploy hello-world`, then a chat prompt) before `deploy --all`.
  4. Keep the two "What is included" tables; drop the description repetition from the section "Standalone Agents".
  5. Add "Learn by example" and "Build your own" sections.
  6. Add short traffic-gen and export-chats sections.
  7. Replace "Status and Known Limitations" with a short actionable list and a link to `docs/known-issues.md` (sub-task 6).
  8. Remove "Repository Structure"; add the "where things live" paragraph and an explanation of `plans/`.
  9. Add license and trademark lines. Add a note that the repo is as-is and not an official product.
- **Relevant context:** current [`README.md`](../README.md); links from `docs/wxodemo.md` to `#quick-start` and `#running-the-evaluation-optional` (lines 5, 186, 313).
- **Status:** `[x] done` - README rewritten (296 lines, no directory tree). `docs/wxodemo.md` line 5 now links to `#deploy-to-your-instance`; the `#running-the-evaluation-optional` anchor still exists. Links to `docs/building-with-bob.md` (sub-task 2) and `docs/known-issues.md` (sub-task 6) are intentionally dangling until those files exist. Notes for later sub-tasks: the README license section says the travel PDF is CC BY-NC-ND 4.0 and links to `agents/travel-request/README.md#source-attribution`; that README still says the redistribution question is open (fix in sub-task 4). The API key/URL step has an HTML TODO comment for the user to fill in. Try-it prompts are not run live; the `cloud_finops`, `customer_returns` and `release_readiness` prompts are verbatim from `ground_truth.json`; the `incident_triage` prompt is adapted (the ground-truth prompt says not to call the approval flow) and the `translator` prompt is adapted from `examples.md`.

### 2. Building with Bob guide, with sample prompts
- **Intent:** Show how to use the Scenario Builder and Standalone Builder modes and give copy-and-paste starter prompts.
- **Expected outcomes:** New file `docs/building-with-bob.md`, linked from the README. It explains the two modes, the skills they load (`wxo-scenario-authoring`, `wxo-adk`, `scenario-demo-docs`), what Bob will ask or produce, and what to check afterwards (`validate`, `smoke --dry-run`, `eval --dry-run`; `list`, `test-upload --dry-run`, `deploy --dry-run`).
- **Todo:**
  1. Describe prerequisites (Bob installed, repo opened as workspace, `.bob/` present, WXO docs MCP configured by `.bob/mcp.json`).
  2. Add the sample prompts below.
  3. Add the manual route (no Bob) with links to `standalone/README.md` and the reference scenario `incident-triage`.
  4. Note that Bob's output must be reviewed and tested; do not claim results without a run.
- **Relevant context:** [`.bob/custom_modes.yaml`](../.bob/custom_modes.yaml), [`.bob/skills/`](../.bob/skills/), [`standalone/README.md`](../standalone/README.md).
- **Status:** `[x] done` - `docs/building-with-bob.md` written (179 lines) and linked from the README. Contents: what the repo ships for Bob, before you start, which mode, how a session goes, 3 standalone + 3 scenario sample prompts (changed from the draft below: `parcel-tracking` replaces `order-status`, prompts are written as code blocks, tool names are prefixed to avoid clashes), review/extend prompts, tips, what to check, reviewing Bob output, and the manual route. Verified: all relative links and anchors resolve; project modes in `.bob/custom_modes.yaml` and the Modes selector match the Bob docs. NOT verified: the sample prompts were not run in Bob; the guide says so. Removed an unverified Bob product URL. The guide tells readers to add new agents to the README "What is included" tables, which sub-task 3 makes Bob do automatically.

**Sample prompts (original draft; the final versions are in `docs/building-with-bob.md`)**

Scenario Builder (small: 2 to 3 tools, 1 knowledge base, at most one approval flow):

1. *Laptop refresh request.* "Create a new scenario `laptop-refresh` with the Scenario Builder. An IT service desk agent checks whether an employee is eligible for a laptop refresh. Two mock read tools (`lookup_employee_device`, `check_refresh_eligibility`), one small knowledge base with the refresh policy, and one approval flow before a mock `order_laptop` write tool. Industry: cross-industry. Function: IT. Target role: IT service desk analyst."
2. *Order status (no flow, smallest).* "Create a read-only scenario `order-status` with two mock tools (`get_order`, `get_shipping_status`) and a short shipping FAQ knowledge base. No write actions, so no flow."
3. *Meeting-room booking.* "Create a scenario `room-booking` with three mock tools (`list_rooms`, `check_availability`, `book_room`). `book_room` is a write tool, so put it behind a confirmation flow."

Standalone Builder:

1. *Meeting-notes summarizer (no tools).* "Create a standalone agent `meeting-notes-summarizer` that turns pasted meeting notes into decisions, action items with owners, and open questions. No tools, no knowledge base. Refuse requests that are not meeting notes."
2. *Unit converter (with a Python tool).* "Create a standalone agent `unit-converter` with a Python `@tool` that converts between common length, weight and temperature units. The tool does the arithmetic; the agent only parses the request."
3. *Sentiment classifier (strict JSON).* "Create a standalone agent `sentiment-classifier` that returns JSON with sentiment, confidence and a one-line reason for pasted text. Follow the style of `document-classifier`."

Also include "review/extend" prompts, e.g. "Review the `incident-triage` scenario against the `wxo-scenario-authoring` skill and list gaps."

### 3. Update Bob mode and skill references to README sections that go away
- **Intent:** The Standalone Builder mode and `standalone/README.md` tell Bob to update "the Standalone agents table and Repository Structure" in the README. After sub-task 1 there is no Repository Structure section.
- **Expected outcomes:** Bob keeps the "What is included" tables up to date for both scenario and standalone agents, and nothing refers to a removed section.
- **Todo:**
  1. Edit finishing step 7 in [`.bob/custom_modes.yaml`](../.bob/custom_modes.yaml) (Standalone Builder) to name the "What is included" table.
  2. Add the same step for the Scenario Builder finishing list (currently there is none) so new scenarios also appear in the README table.
  3. Edit step 5 in [`standalone/README.md`](../standalone/README.md) (also fix the duplicate step number 5).
  4. Search for other references: `grep "Repository Structure"`.
- **Relevant context:** `.bob/custom_modes.yaml` lines 142 to 160; `standalone/README.md` lines 38 to 61.
- **Status:** `[x] done` - Standalone Builder finishing step 7 now names the "Standalone agents" table under "What is included" (alphabetical, plus "Learn by example" when relevant). Scenario Builder got a new finishing step 4 for the "Scenario agents" table. `standalone/README.md` steps renumbered 1-7 (duplicate 5 fixed) and now link to `README.md#what-is-included`. Added a checklist line to the `wxo-scenario-authoring` skill (section 10). No other reference to "Repository Structure" remains outside `plans/`. Verified: `.bob/custom_modes.yaml` still parses (2 modes), `python wxodemo.py validate` all ok, `python -m pytest -q` 357 passed. Not verified: Bob following the new steps in a real session. Note for sub-task 6: the test count is 357, not "about 250" (`docs/wxodemo.md`).

### 4. Agent README cleanup
- **Intent:** Make every agent README read the same way and remove internal or stale content.
- **Expected outcomes:** Each README has: what it shows, how to deploy, example prompts, components, mock data note, limitations. No outdated status, no run statistics, no `techzone1`.
- **Todo:**
  1. Fix [`agents/hr-tacit-knowledge/README.md`](../agents/hr-tacit-knowledge/README.md): status says `soon` and "Sub-Task 8 required", but the manifest says `live`.
  2. Fix [`agents/incident-triage/README.md`](../agents/incident-triage/README.md): remove the "`incident-triage-plan.md` Sub-Task 4" pointer or make it a proper link, move the eval statistics and `techzone1` line to `docs/known-issues.md`.
  3. Review the other `agents/*/README.md` and `standalone/*/README.md` for `techzone1`, "not verified" wording and plan references; keep factual limitations, remove test logs.
  4. Keep links to `plans/` only where they help readers understand the development history.
  5. Review `docs/demo/*-demo.md` for `techzone1` and "earlier test" logs (user-facing text only; do not change measured claims that the consistency checks depend on).
  6. Remove "clean install untested" statements (the user verified a first install on a brand-new instance): `agents/incident-triage/README.md`, `agents/travel-request/README.md`, `docs/demo/incident-triage-demo.md`, `docs/demo/travel-request-demo.md`, `docs/demo/cloud-finops-demo.md`, `.bob/skills/wxo-scenario-authoring/SKILL.md`. Do not rewrite `plans/`.
- **Relevant context:** grep for `techzone1` and `status.*soon` across `*.md`; template described in sub-task 1 of `docs/building-with-bob.md`.
- **Status:** `[x] done` - Edited agent READMEs (hr-tacit-knowledge, incident-triage, travel-request, hr-onboarding, customer-returns, release-readiness, rr-ops/qa/security, yel-income-assessment, pension-disability-triage, cloud-finops), demo scripts (incident-triage, travel-request, cloud-finops, hr-onboarding, pension-disability-triage, yel-income-assessment, release-readiness, hr-tacit-knowledge), `standalone/information-redactor/README.md`, `scenarios/cloud-finops/scenario.yaml`, `docs/demo/scenarios/cloud-finops.js` and the `wxo-scenario-authoring` skill. Removed `techzone1`, plan/Sub-Task pointers, clean-install statements and the travel PDF redistribution-open wording; "Open items" footers no longer point to `plans/`. Reconciled "not tested" claims against the demo scripts and manifests: hr-onboarding (browser-verified scenes; Approve/Reject outcomes per form not recorded), customer-returns (verified), yel-income-assessment (ENT-801 and approval flow live; ENT-802..804 data layer only), cloud-finops (user confirmed both forms browser-verified; contradictory "not verified" lines removed). Left as written because the evidence says so: travel-request approval flow and release-readiness post-fix runs (unverified), pension-ove-advisor flow (unverified). Not touched: the `Plan:` link in `agents/hr-tacit-knowledge/README.md` line 5 (points to kept `plans/`). Incident-triage eval statistics remain in its README; moving them to `docs/known-issues.md` is part of sub-task 6. Verified: `validate` all ok, pytest 357 passed. Note: some edits were silently lost once (OneDrive sync?) and re-applied; a final grep over agent READMEs, demo scripts and scenario files finds no `techzone1`, Sub-Task or clean-install wording.

### 5. Standalone and traffic-gen READMEs
- **Intent:** Close the prerequisite and clarity gaps in the two secondary READMEs.
- **Expected outcomes:** `standalone/README.md` has correct numbering and no "future tools" wording; `traffic-gen/README.md` states prerequisites precisely, covers Docker or Podman, and explains what it does and how to start in a few lines at the top.
- **Todo:**
  1. `standalone/README.md`: fix numbering; reword the `examples.md` rationale so it does not mention "future tools"; remove the directory-layout tree if redundant with the numbered steps.
  2. `traffic-gen/README.md`: add "Quick start" at the top (build, run, what you will see); prerequisites: a WXO instance with agents already deployed (`python wxodemo.py deploy --all`), API key, container runtime Docker or Podman (give the Podman command equivalents only after they are tried, or say they are expected to work the same); no Python install needed.
  3. Keep the rest (env vars, agent pool, adding agents, log format).
- **Relevant context:** [`traffic-gen/README.md`](../traffic-gen/README.md), [`traffic-gen/Dockerfile`](../traffic-gen/Dockerfile).
- **Status:** `[x] done` - `traffic-gen/README.md`: added what-it-is-for / what-it-does-not-do, a 4-step Quick start (deploy agents, build from repo root, run, watch the log and stop), precise prerequisites (Docker or Podman, deployed agents, API key and URL, no Python install). `standalone/README.md`: numbering was already fixed in sub-task 3; "future tools" wording removed at both places; the directory-layout tree was kept because it documents the per-agent files. Verified: with Podman 6.1.4 the image builds and the container exits with `WXO_API_KEY is not set` when no key is given (then the test image was removed). NOT verified: a full container run against a real instance (Docker is not installed here); the README says so. pytest 357 passed.

### 6. Known issues document and `docs/wxodemo.md` cleanup
- **Intent:** Keep honest limitations, but out of the front page, and make the CLI reference useful to outsiders.
- **Expected outcomes:** New `docs/known-issues.md` with the current limitations (evaluation results, wrong-incident approval requests, `chat ask` hanging, promotion to live on Developer Edition, platform coverage). `docs/wxodemo.md` has no "Migrating from the old scripts" section and no stale numbers.
- **Todo:**
  1. Create `docs/known-issues.md` from the "Status and Known Limitations" section and agent README limitations, rewritten so each item says what happens and what to do.
  2. Remove "Migrating from the old scripts" from `docs/wxodemo.md`, and remove its entry from the Contents list.
  3. Make the test count wording consistent ("a few hundred tests" or the exact `pytest` count after running it).
  4. Update the README anchors used in `docs/wxodemo.md` (lines 5, 186, 313) to match the new README sections.
  5. Move the evaluation-framework install notes into the README Development section or `docs/wxodemo.md`.
- **Relevant context:** [`docs/wxodemo.md`](../docs/wxodemo.md) lines 7 to 20 (contents), 295 to 375.
- **Status:** `[x] done` - Created `docs/known-issues.md` (evaluation results, Incident Triage wrong-incident requests, per-scenario verification gaps, tooling and platform). It keeps only current issues and drops the clean-install bullet. Two statements of the old README list were re-worded to what the records show: scenario `undeploy` has been recorded as run with `--dry-run` only; `smoke` live-run bullet not carried over because the demo scripts record smoke runs against deployed agents. `agents/incident-triage/README.md` "Known limitations" now links to it (numbers moved; 0 of 15 *passes*). `docs/wxodemo.md`: removed "Migrating from the old scripts" and its Contents entry, "about 250 tests" -> "a few hundred tests", eval troubleshooting row links to the README section. Verified: markdown link and anchor check over all non-plans, non-.bob `*.md` found only 3 broken links, all in git-ignored `local/` scratch files; `validate` all ok; pytest 357 passed.

### 7. Clean-install verification
- **Intent:** Record that a first install on a brand-new instance works.
- **Expected outcomes:** The README no longer lists a clean install as a limitation, and no other user-facing file says it is untested.
- **Todo:**
  1. Done by the user: deployed to a brand-new WXO instance with a new API key and URL; it worked. (Which commands were run, and whether `deploy --all` was used, was not recorded.)
  2. Remove the "no clean install tested" wording from the places listed under sub-task 4.
- **Relevant context:** the "untested" statements are in `agents/incident-triage/README.md`, `agents/travel-request/README.md`, `docs/demo/incident-triage-demo.md`, `docs/demo/travel-request-demo.md`, `docs/demo/cloud-finops-demo.md` and `.bob/skills/wxo-scenario-authoring/SKILL.md` (line 85). The `plans/` files keep their historical wording.
- **Status:** `[x] done` - README "Known limitations" renamed "Good to know" and the first-install bullet removed. The remaining wording cleanup happens in sub-task 4.

### 8. Final checks
- **Intent:** Make sure the documentation set is consistent and nothing broken was shipped.
- **Expected outcomes:** No dead relative links in `*.md`; no leftover references to removed sections; tests and `validate` still pass; no secrets or personal paths introduced.
- **Todo:**
  1. Check relative links and anchors in all `*.md` files (script or grep).
  2. `python wxodemo.py validate` (all) and `python -m pytest -q`; `python -m ruff check src tests wxodemo.py` if any Python was touched.
  3. Search the tree for `SAMISALKOSUO`, `eyJ`, instance ids and `Repository Structure`.
  4. Re-read the README from the top as a first-time user.
- **Status:** `[x] done` - Verified: link and anchor check over all non-plans, non-.bob markdown (only 3 broken links, all in git-ignored `local/`); `validate` all ok; pytest 357 passed. Secret scan over all 454 tracked and untracked-not-ignored files: no match for the `env.cfg` API key, URL or instance id (values compared without printing), no JWT, no private key, no AWS or GitHub token, no IBM e-mail address; the only `C:/Users` or user-name hits are the clone URL, a plan sentence and a test dummy. Git history scan (`git log --all -S/-G`): the env.cfg values, JWTs and instance URLs appear in no commit; `env.cfg` was never tracked. The only `SAMISALKOSUO`/`C:/Users` hits in history are the local-only `refs/notes/bob` notes (never pushed; `git ls-remote origin` shows only `main`). Largest file is the 311 KB travel PDF; no key, cert, db or zip files. README tables list every agent (hr-tacit-knowledge-guide is covered by the `hr_tk_guide` entry in the hr-tacit-knowledge row). README read-through as a first-time user found no gaps beyond the open items below. NOT verified: the README steps were not re-run end to end in this session (the user tested a first install earlier); the sample Bob prompts were not run in Bob.

---

## Open items for the user (not blocking)
- WXO API key and URL instructions: placeholder now, details to be added by the user.
- Wording for the trademark notice and the "as-is, not an official product" disclaimer; check IBM's internal rules for publishing.
- Podman is expected to accept the same commands as Docker; this has not been tried here, so the README will say so until it is.
