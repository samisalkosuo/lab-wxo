# Standalone Agents

This directory contains **ad-hoc agents** that are deployed directly to a WXO instance
by a developer. They are not owned by any scenario, not subject to the scenario-authoring
rules. `python wxodemo.py deploy --all` deploys them together with the live scenarios;
use `--kind standalone` to pick only these.

## When to put an agent here

Use `standalone/` when an agent:
- answers a focused question (e.g. "explain this document") rather than driving a demo
- does not need evaluation ground truth, demo slides
- is built opportunistically during development, not as part of a structured scenario

Scenario-owned agents belong in `agents/<name>/` and must be listed in a
`scenarios/<id>/scenario.yaml` manifest.

## Directory layout

```
standalone/
├── README.md               # this file
└── <agent-name>/
    ├── agent.yaml          # ADK native-agent definition
    ├── README.md           # purpose, dependencies, deploy commands, known limits
    ├── examples.md         # example prompts (mandatory; consumed by future tools)
    └── <tool>.py           # optional: Python tool(s) the agent needs
```

One subdirectory per agent. Every subdirectory that contains `agent.yaml` is
automatically discovered by `wxodemo`. Any `*.py` file in the subdirectory that
contains `@tool` functions is imported as a Python tool before the agent on deploy,
and its tools are removed after the agent on undeploy (see
[`hello-world/`](hello-world/) for an example).

## Adding a new agent

**Recommended:** open the **Standalone Builder** mode in Bob. It loads the `wxo-adk` skill
and enforces the conventions below.

1. Create `standalone/<your-agent-name>/agent.yaml` — use an existing agent as a
   template (e.g. [`standalone/travel-rules-qa/agent.yaml`](travel-rules-qa/agent.yaml)).
2. Create `standalone/<your-agent-name>/README.md` — document the purpose,
   dependencies (KBs or tools that must already be deployed), deploy commands, and
   known limits.
3. Create `standalone/<your-agent-name>/examples.md` — **mandatory**. Future tools read
   it. Format: a `# <agent_name> — Examples` heading, one intro sentence, then a numbered
   list of `N. *"prompt"* — expected behaviour` items (see
   [`translator/examples.md`](translator/examples.md)). Include at least 3 examples,
   covering the normal path and any refusal or clarification path. The agent `README.md`
   links to this file and does not repeat the examples.
4. Add the agent and its interactive examples to `docs/demo/standalone-agents.js`
   so it appears in `docs/demo/presentation.html`.
5. Deploy with `wxodemo` (see below).

No manifest, no scenario.yaml and no CLI change required.

## Deploying and undeploying with `wxodemo`

`python wxodemo.py` reads credentials from `env.cfg` in the repo root, logs in to the
WXO environment, then runs the ADK CLI. Standalone agents are addressed by name, the same
way as scenarios.

**Prerequisites:** `python wxodemo.py doctor` passes (`orchestrate` found, PyYAML
available, `env.cfg` filled in with `WXO_API_KEY`, `WXO_URL`, `WXO_ENV_NAME`).

```bash
# List all discovered standalone agents
python wxodemo.py list --kind standalone

# Deploy one agent
python wxodemo.py deploy travel_rules_qa

# Deploy all standalone agents
python wxodemo.py deploy --all --kind standalone

# Preview without making any changes
python wxodemo.py deploy --all --kind standalone --dry-run

# Undeploy one agent (asks [y/N]; add --yes to skip the question)
python wxodemo.py undeploy travel_rules_qa

# Undeploy all standalone agents
python wxodemo.py undeploy --all --kind standalone

# Preview undeploy
python wxodemo.py undeploy --all --kind standalone --dry-run
```

> **Knowledge bases are not managed for standalone agents.**
> KBs used by standalone agents are typically shared with scenario deployments.
> Import them with the scenario deploy (`python wxodemo.py deploy <scenario>`) or manually with
> `orchestrate knowledge-bases import --file <kb.yaml>`.
> See each agent's `README.md` for the exact dependency commands.

## Notes

- **Re-running deploy is safe.** `orchestrate agents import` updates in place.
- **The `orchestrate env add` prompt** ("update the environment?") is answered
  automatically with `Y` so re-runs are non-interactive.
- **Promotion to live.** `wxodemo deploy` runs `orchestrate agents deploy` after the
  import and stops with exit code 1 if it fails. On the Developer Edition, which only
  supports draft agents, the agent still exists as a draft after the failure and can be
  used via the ADK run API.
- **Teardown of shared KBs:** if a standalone agent shares a KB with a scenario and
  you undeploy that scenario, the KB will be removed. Re-import it with the
  command in the agent's `README.md`.
