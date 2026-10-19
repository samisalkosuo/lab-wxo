# Standalone Agents

This directory contains **ad-hoc agents** that are deployed directly to a WXO instance
by a developer. They are not owned by any scenario, not subject to the scenario-authoring
rules, and not touched by the scenario deploy or teardown scripts in `scripts/`.

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
├── manage.py               # deploy / undeploy script (see below)
└── <agent-name>/
    ├── agent.yaml          # ADK native-agent definition
    ├── README.md           # purpose, dependencies, deploy commands, known limits
    ├── examples.md         # example prompts (mandatory; consumed by future tools)
    └── <tool>.py           # optional: Python tool(s) the agent needs
```

One subdirectory per agent. Every subdirectory that contains `agent.yaml` is
automatically discovered by `manage.py`. Any `*.py` file in the subdirectory that
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
4. Deploy with `manage.py` (see below).

No manifest, no scenario.yaml, no scripts change required.

## Deploying and undeploying with `manage.py`

`manage.py` is a single cross-platform Python script. It reads credentials from
`env.cfg` in the repo root, activates the WXO environment, then runs the ADK CLI.

**Prerequisites:** virtual environment activated (`orchestrate` on PATH, PyYAML
available), `env.cfg` filled in with `WXO_API_KEY`, `WXO_URL`, `WXO_ENV_NAME`.

```bash
# List all discovered standalone agents
python standalone/manage.py list

# Deploy all standalone agents
python standalone/manage.py deploy

# Deploy one agent
python standalone/manage.py deploy --agent travel_rules_qa

# Preview without making any changes
python standalone/manage.py deploy --dry-run

# Undeploy one agent
python standalone/manage.py undeploy --agent travel_rules_qa

# Undeploy all standalone agents
python standalone/manage.py undeploy

# Preview undeploy
python standalone/manage.py undeploy --dry-run
```

> **Knowledge bases are not managed by `manage.py`.**
> KBs used by standalone agents are typically shared with scenario deployments.
> Import them with the scenario deploy scripts or manually with
> `orchestrate knowledge-bases import --file <kb.yaml>`.
> See each agent's `README.md` for the exact dependency commands.

## Notes

- **Re-running deploy is safe.** `orchestrate agents import` updates in place.
- **The `orchestrate env add` prompt** ("update the environment?") is answered
  automatically with `Y` so re-runs are non-interactive.
- **Developer Edition** only supports draft agents; `orchestrate agents deploy` may
  fail with a warning. The agent still exists as a draft and can be used via the ADK
  run API.
- **Teardown of shared KBs:** if a standalone agent shares a KB with a scenario and
  you run `scripts/teardown.ps1`, the KB will be removed. Re-import it with the
  command in the agent's `README.md`.
