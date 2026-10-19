---
name: wxo-scenario-authoring
description: Use when the user wants to create, add, scaffold, or review a new watsonx Orchestrate demo scenario in this repo (for example customer returns, release readiness, HR onboarding, cloud FinOps), or asks what a scenario must contain, how scenarios are laid out, or how to keep a new scenario consistent with Incident Triage.
---

# WXO Scenario Authoring (lab-wxo)

A **scenario** is one self-contained demo: a mock world, an agent, its tools, a knowledge base, an optional approval flow, a manifest, a demo script, and a presentation section. Incident Triage is the reference implementation. This skill says what a scenario ships and which Phase A lessons to keep. It does not repeat ADK CLI details: load the `wxo-adk` skill and the ADK docs MCP tools for those.

Load these first, in order: this skill, `wxo-adk`, then `scenario-demo-docs` for the demo markdown and slides (templates and `check_demo_consistency.py` live in that skill's folder).

## 1. Goal and non-goals

- Showcase WXO with a presentation and a runnable demo. Everything runs on **mock data**; no external services, no secrets.
- A user outside the repo must be able to deploy it with one script into their own WXO instance.
- Do not build an evaluation framework per scenario (see section 6). Do not touch another scenario's files.

## 2. Is it really an agent? (agent-washing test)

Before building, write down in the scenario plan why a fixed flowchart is not enough. Pass only if most hold:

- The next step depends on what the previous step found.
- The user's input can be vague or messy, and a clarifying question may be needed.
- The full decision tree cannot be drawn in advance.

If the scenario is a fixed sequence with well-formed inputs, model that part as a **flow** (Decisions node, deterministic rules) and keep the agent for the open-ended part. Customer Returns is meant to show exactly this split. Source: ADK docs, agent design, "agent-washing" decision matrix.

## 3. What every scenario ships

Names: folders and files that humans browse are `kebab-case`; Python package folders and WXO resource names are `snake_case` (ADK allows only alphanumeric + underscore in tool package paths). `<id>` is the kebab-case scenario id, `<pkg>` the snake_case form.

| Item | Path | Notes |
|---|---|---|
| Manifest | `scenarios/<id>/scenario.yaml` | Created by `python scripts/new-scenario.py <id> --name ... --description ...`; `scenarios/incident-triage/scenario.yaml` documents every field. Real resource names, not file names. `deploy-all`, `teardown` and `smoke_test.py` read it; check it with `python scripts/scenario_manifest.py validate --scenario <id>`. |
| Agent | `agents/<id>/agent.yaml`, `README.md` | `spec_version: v1`, `kind: native`, `style: react_core`, `llm: groq/openai/gpt-oss-120b` (the repo default). README: tools table, KB, mock data table, limitations. |
| Tools | `tools/<pkg>/<pkg>.py`, `tools/<pkg>/data/*.py`, `tools/<pkg>/requirements.txt`, `__init__.py` | One top-level entry file with `@tool` functions. Mock world in `data/`. `requirements.txt` pins `ibm-watsonx-orchestrate==2.18.2`. Copy the import fallback from `tools/incident_triage/incident_triage.py` (`try: from .data import ... except ImportError: from data import ...`). |
| Knowledge base | `knowledge/<id>/<name>.yaml` + `runbooks/*.txt` (or policy docs) | Built-in KB takes xlsx, docx, pdf, pptx, csv, html, txt; **markdown is not supported**, use `.txt`. Give every document a stable ID (like `RB-DEPLOY-01`) that the agent can cite. |
| Flow (if a write/approval gate is needed) | `flows/<pkg>/<flow_name>.py` | See section 5. |
| Ground truth | `evaluation/<id>/ground_truth.json` | Always (section 6). |
| Demo script | `docs/demo/<id>-demo.md` | From the `scenario-demo-docs` template. |
| Presentation | `docs/demo/scenarios/<id>.js` + one `<script src>` line in `presentation.html` | Slide `tag` text ("Scenario N • ...") must match the sidebar position, which is the order of the script tags. |

`agents/hello-world` and `tools/greetings.py` are setup checks, not a scenario.

## 4. Design rules carried over from Phase A

1. **Static, read-only mock world.** Python tools run in isolated containers, so state cannot live in memory between calls. Tools take keys (id, service, time window) and return deterministic results. Plant a clear root cause for every case and one red herring for at least one case.
2. **Fewer than 10 tools on the agent** (target 8). The ADK docs warn about "tool soup" at 10+.
3. **Business-capability tools, bounded output.** No raw API wrappers, no data firehose: filter, cap, and summarize results. Return clear error objects with a hint (see `list_open_incidents`).
4. **Tool and KB names are resources of the whole WXO instance, not of the scenario.** Import and teardown work by name (the Phase A deploy log shows "Existing Tool found. Updating..." on re-import; teardown uses `tools remove --name`). So two scenarios that define a tool with the same name would most likely update each other's tool on import and lose it on teardown (inferred from that behaviour, not tested). Make every tool, flow and KB name unique across scenarios (for example `returns_lookup_order`) and check the other manifests and `orchestrate tools list` before choosing names.
5. **Write actions never go on the agent.** Anything that changes state is a mock Python tool that only a **flow** calls after human approval. The agent gets the flow, not the tool. List the tool in the manifest under `names` but not under `attached`. Governance belongs in flows/tools, not in prompt instructions.
6. **Agent instructions** follow the structure of `agents/incident-triage/agent.yaml`: method, evidence standard, one-item-at-a-time rules, how to propose an action, clarifying-question rule, "what you must not do". Require the agent to cite a document ID and to report flow results verbatim.
7. **Validate in code what a prompt cannot guarantee.** Incident Triage still has an unfixed case where the agent files an approval request for the wrong incident (plan Open Item 7). For any scenario with an approval flow, add a deterministic check (for example, the flow or tool verifies that service and incident match) instead of relying on instructions.
8. **KB documents describe symptoms, then procedure.** The agent matches on symptoms and is told to cite only the single best-matching document.

## 5. Approval-flow pattern (when needed)

Use `flows/incident_triage/request_remediation.py` as the reference: input schema (Pydantic), user activity form with an Approve button and a separate Reject button, a conditions branch on the recorded decision, a tool node calling the internal write tool, and result scripts. Items that are unverified or were fragile and must be re-tested in the **browser chat UI** (not just the CLI) for every new flow: the form renders, Approve runs the write tool, Reject does not, and the agent resumes and reports the `message` verbatim. The evaluator cannot drive the approval form.

## 6. Evaluation: two tiers

- **Core, always created:** `evaluation/<id>/ground_truth.json`, a small file with one entry per demo case: id, the user-visible symptom, expected root cause or outcome, expected action (or `no_action`), whether human approval is required, red herrings, and the expected key tools. It is the checklist for the demo script and the expectations for the smoke test. Keep the shape of `evaluation/incident-triage/ground_truth.json`; the top-level key may be named after the case type (`cases` in the scaffold, `incidents` in Incident Triage). **One key is fixed: `smoke_prompts`**, a list of `{"id": ..., "prompt": ...}` that `scripts/smoke_test.py` sends to the agent and the validator requires for a live scenario. Write them diagnosis-only; an approval form cannot be answered through the run API.
- **Optional, off by default:** `baseline.py` (plain code, no agent, no LLM), ADK `test_cases/` and `eval_config.yaml`. Add them only if the scenario needs to answer "why not a script?" with data, or the user asks for a quality run. Incident Triage's optional tier produced a 0 of 15 final-answer check, hand-installed dependencies, and a baseline that matched the agent; the benefits slide already carries the agent-vs-script argument. Set `evaluation.tier: core` or `full` in the manifest accordingly.

## 7. Build order

1. Scenario plan file in `plans/<id>-plan.md` (sub-task format of `plans/incident-triage-plan.md`): purpose, agent-washing check, mock world table (case, symptom, planted cause, what it teaches), tool list, KB documents, flow, open items.
2. Mock data and read-only tools; test them directly with Python.
3. Knowledge base documents.
4. Write tool and flow (if any).
5. Agent YAML and README.
6. Manifest and `ground_truth.json` (run `scripts/new-scenario.py` first: it creates both as stubs, plus the demo script and slide placeholders). `validate` must print `OK`.
7. Deploy (`scripts/deploy-all.ps1 -Scenario <id>` / `deploy-all.sh --scenario <id>`; a scenario stays `status: soon` until it is ready, and `soon` scenarios are skipped by a deploy without a scenario name), then run each demo prompt several times (a single pass proves little; `python scripts/smoke_test.py --scenario <id>` does one pass of the `smoke_prompts`) and record what actually happened.
8. Demo markdown and presentation slides from the `scenario-demo-docs` templates. Fill "what was and was not verified" only from real runs.

## 8. Verify, do not assume

Treat these as open until you have checked them for the new scenario (they were open or only partly verified in Phase A):

- Re-importing tools, KBs, flows, agents over existing resources is safe; clean first install on a fresh instance is **untested**.
- The agent LLM and the KB embedding model (default `ibm/slate-125m-english-rtrvr-v2`) exist in the target instance.
- Imported agents are drafts; `orchestrate agents deploy --name <name>` is needed for the chat UI (fails on the Developer Edition; warn and continue).
- `orchestrate env activate` auth expires after about two hours.
- `orchestrate chat ask` hangs in non-interactive shells; use the ADK run API (see `scripts/smoke_test.py`, whose live path has not been run against an instance yet).
- The reworked deploy / teardown / package scripts were checked against a fake `orchestrate`, not a live instance.
- KB indexing takes time after import; wait before the first demo query.

## 9. Secrets and hygiene

- Never read, print, or package `env.cfg` or `local/` (both can hold secrets). Use `env.cfg.example` only.
- No instance-specific values (agent UUIDs, URLs, API keys) in committed files or in the manifest.
- Do not claim a result that was not observed. Do not say an agent "beats" a script, "passes" an evaluation, or "was tested" unless the repo contains the run that shows it.

## 10. Done checklist

- [ ] Agent-washing reasoning written down.
- [ ] Manifest names match `agent.yaml`, `@tool` functions, KB yaml `name:`, and flow `name=`.
- [ ] Tool and KB names are unique across all scenarios.
- [ ] No write tool attached to the agent; flow tested in the browser (Approve and Reject).
- [ ] `ground_truth.json` exists and matches the demo claims.
- [ ] Demo markdown and the slide prompts contain the **same** prompts word for word.
- [ ] Presentation file registered; slide tags match sidebar position; page opens from `file://`.
- [ ] README / plan updated with an honest "not tested" list.
