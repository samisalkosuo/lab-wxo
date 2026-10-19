# Plan: travel_rules_qa — Standalone PDF Q&A Agent

## Overview

The `travel_request` scenario agent uses the Finnish state travel regulation PDF
(`VM_2025_63.pdf`, `travel_state_rules` KB) in only 1 of 24 final answers, because its
instructions direct it toward tools for amounts and toward the agency-policy KB for
approval levels. The PDF is therefore largely wasted as a knowledge base on that agent.

The remedy is a **dedicated, single-purpose Q&A agent** whose only job is to answer
questions from the PDF in plain English, with Finnish citations. It has no tools, no
approval flow, and no scenario membership.

This agent also establishes a **new top-level directory `standalone/`** for ad-hoc agents
that are developed and deployed independently — not owned by any scenario, not driven by
demo requirements, and not subject to the scenario-authoring rules.

**Non-goals:**
- This agent does not replace the `travel_request` scenario agent.
- It is not wired into the scenario deploy scripts.
- It does not have evaluation, packaging, or demo-doc requirements.
- The `travel_state_rules` KB is already deployed as part of the travel-request scenario;
  this agent shares that resource — it does not create a duplicate.

---

## Repository structure after this plan

```
standalone/
└── travel-rules-qa/
    ├── README.md           # purpose, deploy command, known limits
    └── agent.yaml          # native agent definition
README.md                   # updated: new "Standalone Agents" section
```

The `standalone/` directory is intentionally flat: each subdirectory is one self-contained
agent. No manifest, no scenario.yaml, no packaging. A developer deploys directly with the
ADK CLI.

---

## Sub-Tasks

---

### Task 1 — Create the `standalone/` top-level directory with a root README

**Intent:**
Establish the `standalone/` directory as the canonical home for ad-hoc agents that are
not part of any scenario. Make the distinction explicit so future developers know where to
put one-off agents and what rules (or lack thereof) apply.

**Expected Outcomes:**
- `standalone/README.md` exists and explains the directory's purpose, conventions, and
  deploy/teardown workflow.
- The directory is clearly separated from `scenarios/`, `agents/`, and `tools/`.

**Todo List:**
1. Create `standalone/README.md` with:
   - One-paragraph description: what "standalone" means (ad-hoc, not scenario-owned,
     developer-deployed, no demo or evaluation requirements).
   - Convention: one subdirectory per agent, each with `agent.yaml` + `README.md`.
   - Deploy pattern:
     ```
     orchestrate knowledge-bases import --file <kb-yaml>   # if KB not already live
     orchestrate agents import --file agent.yaml
     orchestrate agents deploy --name <agent-name>
     ```
   - Teardown pattern (remove agent; leave shared KBs alone unless nothing else uses them).
   - Note: standalone agents may reference KBs or tools from scenario deployments;
     document which resources must already be deployed.

**Relevant Context:**
- README pattern: `README.md` (repo root) for tone and style.
- No `scenario.yaml`, no manifest tooling, no deploy scripts involved.

**Status:** [x] done

---

### Task 2 — Author `standalone/travel-rules-qa/agent.yaml`

**Intent:**
Create the agent definition for `travel_rules_qa`. The agent has exactly one knowledge
base (`travel_state_rules`, already deployed by the travel-request scenario), no tools,
and a focused system prompt that makes it a reliable Q&A interface for the Finnish state
travel regulation PDF.

The prompt must fix the root cause of low KB utilisation on the main agent: there is no
competition from tools or a second KB, and the agent is instructed to always search before
answering.

**Expected Outcomes:**
- `standalone/travel-rules-qa/agent.yaml` is a valid ADK native-agent YAML.
- The agent answers any question about the Finnish state travel regulation in English.
- Every answer cites the relevant section in Finnish format
  ("Valtion matkustussääntö 2026, 13 §").
- The agent never invents amounts — it reads them from retrieved passages only.
- The agent is honest when a question is outside the document's scope.

**Todo List:**
1. Create `standalone/travel-rules-qa/agent.yaml` with:
   - `spec_version: v1`, `kind: native`, `name: travel_rules_qa`
   - `llm: groq/openai/gpt-oss-120b`, `style: react_core`
   - `knowledge_base: [travel_state_rules]`
   - `tools: []` (empty — no tools)
   - System prompt covering:
     - Role: answer questions from *Valtion matkustussääntö 2026* only.
     - Language: user writes in English; answer in English; citations in Finnish.
     - Search rule: always search `travel_state_rules` in Finnish before answering
       (e.g. "päiväraha", "ateriat", "majoitus", "loma", "matkalippu", "korvaus").
     - Citation rule: cite section as "Valtion matkustussääntö 2026, N §"; never invent
       a section number not present in a retrieved passage.
     - Amount rule: state amounts only if they appear word-for-word in a retrieved
       passage; do not compute or combine figures.
     - Scope rule: if a question is not covered by the document, say so and do not guess.
     - Out-of-scope rule: approval decisions, budget checks, employee data, and booking
       are outside scope — direct the user to the `travel_request` agent for those.

**Relevant Context:**
- Existing KB YAML: `knowledge/travel-request/travel_state_rules.yaml`
- Existing agent pattern: `agents/travel-request/agent.yaml` (language + citation rules
  in `## Language` section are reusable verbatim)
- Known retrieval finding: section 13 (free meals) retrieved reliably in 3/3 dedicated
  runs; cross-language retrieval requires Finnish search terms.
- Embedding model on the KB: `ibm/granite-embedding-278m-multilingual`

**Status:** [x] done

---

### Task 3 — Author `standalone/travel-rules-qa/README.md`

**Intent:**
Give the developer who maintains or deploys this agent everything they need in one place:
what it does, its dependencies, deploy and teardown commands, and known limits.

**Expected Outcomes:**
- `standalone/travel-rules-qa/README.md` documents the agent clearly.
- A developer can deploy the agent from scratch by following the README alone.

**Todo List:**
1. Create `standalone/travel-rules-qa/README.md` with:
   - **Purpose** — one paragraph: what the agent does and why it exists separately.
   - **Dependencies** — the `travel_state_rules` KB must already be deployed (it is
     imported as part of the travel-request scenario; list the command to import it
     standalone if needed).
   - **Deploy** — exact ADK CLI commands in order:
     ```
     # Only if travel_state_rules is not already live:
     orchestrate knowledge-bases import --file knowledge/travel-request/travel_state_rules.yaml
     orchestrate agents import --file standalone/travel-rules-qa/agent.yaml
     orchestrate agents deploy --name travel_rules_qa
     ```
   - **Teardown** — remove agent only; leave KB if shared with travel_request scenario.
   - **Known limits** — cross-language retrieval accuracy (~55%), amounts only from
     retrieved passages, no tool access for employee/budget data.
   - **Example questions** — 3–4 questions the agent handles well (per-diem rules, free
     meals, own-car mileage, travel claim deadline).

**Relevant Context:**
- `plans/travel-request-plan.md` (retrieval accuracy notes, PDF section coverage)
- KB import gotcha: updating in place failed ingestion; must remove then import fresh.

**Status:** [x] done

---

### Task 4 — Create `standalone/manage.py` deploy/undeploy script

**Intent:**
Give developers a single Python script that can deploy or undeploy one, several, or all
agents inside `standalone/`. Because standalone agents have no scenario manifests, the
script must discover agents by walking the `standalone/` directory tree itself — every
subdirectory that contains `agent.yaml` is a standalone agent.

The script must mirror the quality and patterns of `scripts/deploy-all.ps1` and
`scripts/teardown.ps1`: reads credentials from `env.cfg`, registers and activates the
WXO environment, then runs the ADK CLI commands. Being pure Python makes it
cross-platform (no separate `.ps1` + `.sh` pair needed).

Each standalone agent has only `agent.yaml` — no tools, flows, or KB YAMLs of its own.
The deploy step is therefore just:
  1. `orchestrate agents import --file <path>/agent.yaml`
  2. `orchestrate agents deploy --name <name>`

The undeploy step is:
  1. `orchestrate agents remove --name <name> --kind native`

Knowledge bases are **not** touched by this script: they are shared with scenario
deployments and must be managed independently. The script must say so clearly in its
`--help` output.

**Expected Outcomes:**
- `standalone/manage.py` exists and is executable as `python standalone/manage.py`.
- `python standalone/manage.py list` prints each discovered agent name and its directory.
- `python standalone/manage.py deploy` deploys all agents found under `standalone/`.
- `python standalone/manage.py deploy --agent travel_rules_qa` deploys one named agent.
- `python standalone/manage.py undeploy` undeploys all agents.
- `python standalone/manage.py undeploy --agent travel_rules_qa` undeploys one agent.
- `--dry-run` flag prints every CLI command that would be run without executing anything.
- The script exits non-zero on any `orchestrate` CLI failure (deploy) or prints a warning
  and continues (undeploy — same non-fatal convention as `teardown.ps1`).
- Discovery is automatic: adding a new subdirectory with `agent.yaml` is picked up
  without touching `manage.py`.

**Todo List:**
1. Create `standalone/manage.py` with:
   - **Discovery** — walk `standalone/` for subdirectories containing `agent.yaml`;
     read the `name` field from each YAML to get the WXO agent name.
   - **env.cfg loading** — same parser as `deploy-all.ps1`: split on first `=`, skip
     blank lines and `#` comments. Read from repo root (`../env.cfg` relative to
     `standalone/`). Raise a clear error if `WXO_API_KEY`, `WXO_URL`, or `WXO_ENV_NAME`
     are missing.
   - **Environment setup** — `orchestrate env add` (pipe `Y` for non-interactive
     re-registration) then `orchestrate env activate --api-key`.
   - **`list` subcommand** — print one line per discovered agent: name, path.
   - **`deploy` subcommand** — for each selected agent:
       - `orchestrate agents import --file <agent.yaml>`
       - `orchestrate agents deploy --name <name>` (warn and continue if this step fails,
         same as deploy-all.ps1 — Developer Edition only supports draft agents)
   - **`undeploy` subcommand** — for each selected agent:
       - `orchestrate agents remove --name <name> --kind native` (warn and continue on
         failure, same non-fatal convention as teardown.ps1)
   - **`--agent NAME`** flag — filter to one named agent; error if not found.
   - **`--dry-run`** flag — print each `orchestrate` call prefixed with `[DRY-RUN]`
     and skip env activation.
   - **Unicode / encoding** — set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` at
     startup, same as the existing scripts.
   - **`--help` note** — state clearly that KBs are not managed here.
   - Use only stdlib + PyYAML (already a transitive dep of `ibm-watsonx-orchestrate`).

**Relevant Context:**
- `scripts/deploy-all.ps1` — env setup, `orchestrate agents import/deploy` pattern,
  Unicode env vars, non-fatal deploy warning.
- `scripts/teardown.ps1` — `orchestrate agents remove --name --kind`, non-fatal warning
  on remove failure, dry-run pattern.
- `scripts/scenario_manifest.py` — PyYAML loading, `rel()` helper, clean argparse style.
- Agent `kind` for all standalone agents is `native` (the only kind used in this repo).
- `orchestrate env add` prompts "update the environment?" when the name already exists;
  pipe `Y` to make it non-interactive (same trick as deploy-all.ps1 line 111).

**Status:** [x] done

---

### Task 5 — Update repo `README.md`

**Intent:**
Make the `standalone/` directory discoverable and explain the two-tier structure
(scenarios vs. standalone) to developers reading the repo for the first time.

**Expected Outcomes:**
- `README.md` has a new **Standalone Agents** section explaining the directory,
  the difference from scenarios, and a pointer to `standalone/README.md`.
- The repository structure tree in `README.md` includes the new `standalone/` directory.

**Todo List:**
1. Add `standalone/` to the directory tree in the "Repository Structure" section.
2. Add a new "Standalone Agents" section after "Adding a Plain Agent" with:
   - One paragraph: what standalone means vs. scenario-owned.
   - Pointer to `standalone/README.md` for conventions and deploy commands.
   - Note that the deploy scripts do not touch standalone agents.

**Relevant Context:**
- `README.md` lines 9–63 (directory tree), lines 246–253 ("Adding a Plain Agent" section)

**Status:** [x] done

---

## Design decisions recorded

| Decision | Rationale |
|---|---|
| New top-level `standalone/` directory (not under `agents/`) | `agents/` is for scenario-owned agents listed in a manifest. `standalone/` signals "no manifest, no scenario rules" to any developer reading the tree. |
| Agent reuses existing `travel_state_rules` KB | KB is already deployed by the scenario; duplicating it would waste storage and risk divergence. If the scenario is torn down, the KB import command is in the README. |
| No tools on the new agent | The PDF is the only source of truth for this agent. Adding tools would recreate the "competition" problem from the main agent. |
| No `scenario.yaml` or manifest entry | The deploy scripts must not touch this agent. Developer-only deployment by ADK CLI is the intended path. |
| Standalone agents may reference shared KBs | Shared resources are an acceptable dependency; the README documents which ones must be live. |
