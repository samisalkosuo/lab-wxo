# watsonx Orchestrate Lab

A development environment for building and deploying IBM watsonx Orchestrate agents using the ADK (Agent Development Kit).

Agents, tools, knowledge bases, and flows in this repo are version-controlled and distributable. Run `scripts/deploy-all.ps1` (or `deploy-all.sh`) to import everything into an existing WXO instance. Re-running the deploy scripts over existing resources is safe — re-import updates in place. A clean first install on a fresh instance has not been tested.

## Repository Structure

```
lab-wxo/
├── agents/
│   ├── hello-world/
│   │   ├── agent.yaml            # Agent definition
│   │   └── README.md
│   └── incident-triage/
│       ├── agent.yaml
│       └── README.md
├── tools/
│   ├── greetings.py              # Single-file Python tool
│   └── incident_triage/          # Multi-file Python tool package
│       ├── incident_triage.py    # Entry file (8 @tool functions)
│       ├── requirements.txt
│       └── data/                 # Static mock-world data modules
├── knowledge/
│   └── incident-triage/
│       ├── incident_triage_runbooks.yaml
│       └── runbooks/             # Six .txt runbook files
├── flows/
│   └── incident_triage/
│       └── request_remediation.py
├── evaluation/
│   └── incident-triage/
│       ├── baseline.py           # Plain-code baseline (no WXO needed)
│       ├── eval_config.yaml
│       ├── ground_truth.json
│       └── test_cases/           # 5 evaluation test cases (.json)
├── scenarios/
│   ├── incident-triage/scenario.yaml   # Manifest: every resource the scenario owns
│   └── hello-world/scenario.yaml
├── docs/
│   └── demo/
│       ├── incident-triage-demo.md   # Human-readable demo script
│       ├── presentation.html         # Slide shell; loads scenarios/*.js
│       └── scenarios/                # One slides file per scenario (4 are "coming soon" placeholders)
├── standalone/
│   ├── README.md                 # What standalone means, manage.py usage
│   ├── manage.py                 # Deploy / undeploy standalone agents
│   └── travel-rules-qa/          # Finnish travel regulation PDF Q&A agent
├── connections/                  # Connection templates (empty for this demo)
├── scripts/
│   ├── deploy-all.ps1            # Deploy live scenarios, or one with -Scenario (PowerShell)
│   ├── deploy-all.sh             # Same, --scenario (bash)
│   ├── teardown.ps1              # Remove scenarios, or one with -Scenario (PowerShell)
│   ├── teardown.sh               # Same, --scenario (bash)
│   ├── scenario_manifest.py      # Reads/validates manifests; builds deploy and teardown plans
│   ├── new-scenario.py           # Scaffold a new scenario
│   ├── smoke_test.py             # Send a scenario's prompts to its deployed agent
│   └── package.py                # Build distributable zip for one scenario
├── dist/                         # Packaged zip output (git-ignored)
├── env.cfg                       # Secrets -- DO NOT COMMIT
├── env.cfg.example               # Template -- safe to commit
├── activate-lab-wxo.ps1          # Convenience setup: creates/activates venv, installs deps & activates WXO (PowerShell)
├── activate-lab-wxo.sh           # Convenience setup (Bash)
├── activate-wxo.ps1              # Standalone environment activation (PowerShell)
├── activate-wxo.sh               # Standalone environment activation (Bash)
└── requirements.txt              # ibm-watsonx-orchestrate and pinned deps
```

## Agents

| Agent | Name in WXO | Description |
|---|---|---|
| [hello-world](agents/hello-world/) | `hello_world` | Simple greeting agent -- verifies ADK setup |
| [incident-triage](agents/incident-triage/) | `incident_triage` | Diagnoses mock production incidents; routes remediation through a human-approval flow |

## Prerequisites

- Python 3.11 or later (3.11--3.13 recommended; see [INSTALL.md in the zip](#packaging) for details)
- IBM watsonx Orchestrate ADK -- see the [installation guide](https://developer.watson-orchestrate.ibm.com/getting_started/installing)

```bash
pip install ibm-watsonx-orchestrate==2.18.2
```

## Quickstart / Setup

### Quick Setup (One Step)

Run the convenience script, which automatically sets up `.venv`, installs `requirements.txt`, reads or prompts for credentials (`env.cfg` / API key), and activates the watsonx Orchestrate environment:

```powershell
.\activate-lab-wxo.ps1    # Windows PowerShell (or: . .\activate-lab-wxo.ps1 to keep .venv active)
```

```bash
source ./activate-lab-wxo.sh   # Linux / macOS / Git Bash
```

---

### Manual Setup (Step-by-Step)

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Windows PowerShell
```

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure credentials

Copy the example config and fill in your values:

```powershell
Copy-Item env.cfg.example env.cfg   # Windows
```
```bash
cp env.cfg.example env.cfg          # Linux / macOS
```

Edit `env.cfg`:

```ini
WXO_API_KEY=your-api-key-here
WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>
WXO_ENV_NAME=my-env
# Optional: authentication type. Default is ibm_iam (IBM Cloud IAM).
# Use mcsp for AWS-hosted WXO instances.
WXO_ENV_TYPE=ibm_iam
```

- `WXO_API_KEY` -- IBM Cloud API key with Manager access to your WXO instance.
- `WXO_URL` -- the API base URL (from the WXO web UI under Settings, not the browser URL).
- `WXO_ENV_NAME` -- any short name used locally by the ADK CLI.
- `WXO_ENV_TYPE` -- `ibm_iam` (default) or `mcsp` (AWS-hosted instances).

> **`env.cfg` contains secrets -- do not commit it.**

## Deploy

### Windows (PowerShell)

```powershell
$env:PYTHONUTF8 = "1"   # avoids cp1252 encoding errors on Windows
.\scripts\deploy-all.ps1                            # every scenario with status: live
.\scripts\deploy-all.ps1 -Scenario incident-triage  # one scenario
```

### Linux / macOS (bash)

```bash
bash scripts/deploy-all.sh                             # every scenario with status: live
bash scripts/deploy-all.sh --scenario incident-triage  # one scenario
```

The script reads `env.cfg`, registers the WXO environment non-interactively, then imports what the scenario manifests (`scenarios/<id>/scenario.yaml`) list, in dependency order:

```
connections -> tools (flat .py, multi-file packages) -> knowledge bases -> flows -> agents -> agents deploy
```

The deploy and teardown scripts run `scripts/scenario_manifest.py` to read the manifests, so they need the Python environment that has PyYAML (the one with `orchestrate`; the ADK depends on PyYAML). A scenario with `status: soon` is skipped unless you name it with `-Scenario` / `--scenario`. Tool, flow, knowledge-base and agent names are shared by the whole WXO instance, so two scenarios must not reuse a name; the manifest tooling refuses a deploy when it finds a clash.

Each imported agent is promoted from draft to live with `orchestrate agents deploy --name <name>` at the end of the script. **This step is required** because the chat UI only shows live agents. If you skip it (or if the deploy call fails on Developer Edition), the agent will not appear in the agent picker.

Re-running is safe: existing resources are updated in place.

**Auth expiry:** the remote token expires after 2 hours. Re-run the deploy script before a demo or after a long gap.

## Teardown (dev cleanup)

```powershell
.\scripts\teardown.ps1 -DryRun                          # preview -- prints commands, makes no changes
.\scripts\teardown.ps1 -Scenario incident-triage -DryRun
.\scripts\teardown.ps1                                  # ALL scenarios, real deletion (UNTESTED -- see warning in script)
```

```bash
bash scripts/teardown.sh --dry-run                           # preview
bash scripts/teardown.sh --scenario incident-triage --dry-run
bash scripts/teardown.sh                                     # ALL scenarios, real deletion (UNTESTED -- see warning in script)
```

Resources are removed in reverse dependency order (agents first, then flows, then tools, then knowledge bases). The names come from the manifests and are the real WXO resource names, not file names. Without `-Scenario` / `--scenario` every scenario is removed, including ones marked `soon` (a resource that was never deployed only gives a non-fatal warning).

**Important:** real deletion was never executed during development (demo resources on `techzone1` were preserved). Use `-DryRun` / `--dry-run` to review the commands first. The behaviour of the remove subcommands (confirmation prompts, errors when an agent still references a tool) is untested. Check `orchestrate agents remove --help`, `orchestrate tools remove --help`, and `orchestrate knowledge-bases remove --help` for any required flags before running for real.

## Packaging

Build a distributable zip for external users:

```bash
python scripts/package.py --scenario incident-triage [--version 1.0.0]
```

This produces `dist/wxo-<zip_prefix>-<version>.zip` (the prefix is in the manifest). The zip contains only that scenario's resources, its demo script, a copy of `presentation.html` that loads only that scenario's slides, the deploy / teardown / smoke-test scripts and the manifest. It excludes `env.cfg`, `local/`, dev tooling state, instance-specific artefacts and every other scenario. A post-build security check deletes the zip and exits non-zero if any excluded pattern or secret-bearing string is found.

The zip includes `INSTALL.md`, generated by `package.py` from the manifest (known issues of the scenario go in `scenarios/<id>/install-notes.md`).

## Demo

See [`docs/demo/incident-triage-demo.md`](docs/demo/incident-triage-demo.md) for the human-readable demo script: exact prompts, expected agent behaviour, fallback notes, and closing talking points.

## Status and Known Limitations

This is a demo / lab repo. The following items are open as of the current state:

- **No clean-instance install tested.** The only tested deploy was a re-install over an existing environment (`techzone1`). First-import on a fresh WXO instance was not verified.
- **Agent not shown to beat the plain-code baseline.** The baseline script (`evaluation/incident-triage/baseline.py`) scores 5/5 on all four mock incidents, the same as the agent. The reported agent advantages (handling new incident types, recovering from changed log wording) are arguments, not measurements -- neither was run against a variant scenario.
- **Evaluation final-answer check: 0 of 15 runs pass.** Tool-selection metrics are good (recall 1.0 in 13 of 15 runs, `tool_match_success` true in 13 of 15), but `is_success` requires the text check to also pass. The text check fails because the agent writes IDs with non-breaking hyphens (U+2011, e.g. `RB-TLS-01`) which break exact keyword matches, and produces long answers compared with the one-sentence expected responses. The overall score is not a useful signal in its current form.
- **Wrong incident reference in approval requests (3 of 19 vague-opening runs).** On "Hey, checkout is slow...", the agent sometimes investigates the payments service while working INC-1001 and then calls `request_remediation` with `service=payments, incident_id=INC-1001` (mismatched). The instruction change in `agent.yaml` gave no measurable improvement. The human approval gate catches this before any execution; a proper fix is to validate service/incident consistency inside the flow.
- **Evaluation dependencies installed by hand.** `ibm-watsonx-orchestrate-evaluation-framework==1.5.2` and its transitive dependencies are not installed automatically. On Python 3.14 the `pandas~=2.2.3` pin cannot be satisfied. See `INSTALL.md` in the zip for the workaround.
- **Bash deploy script tested only via Git Bash on Windows** -- not on native Linux or macOS.
- **`orchestrate chat ask` hangs** in non-interactive shells. Use the ADK run API instead (see `scripts/smoke_test.py`).
- **`scripts/smoke_test.py` has only been run with `--dry-run`.** The live path (agent lookup by name, run, poll) was not run against an instance after it replaced `smoke_test_triage.py`.
- **The reworked deploy / teardown / package scripts were tested against a fake `orchestrate`** (their output matched the old scripts' command sequence) and the new package against the old zip's contents. They have not been run against a live instance.

## Adding a New Scenario

Every scenario is a folder of resources described by a manifest, plus a demo script and a section in the presentation.

**Recommended:** open the **Scenario Builder** mode in Bob. It loads the three relevant skills in the right order and enforces the design rules and final consistency checks automatically.

Scaffold the folder skeleton first:

```bash
python scripts/new-scenario.py customer-returns --name "Customer Returns" --description "One line for the sidebar"
```

This creates `scenarios/<id>/scenario.yaml` (status `soon`), an agent stub, a `ground_truth.json` stub, the demo script from the template, and registers `docs/demo/scenarios/<id>.js` in `presentation.html`. Then build the tools, knowledge base and flow, list them in the manifest, and check:

```bash
python scripts/scenario_manifest.py validate --scenario <id>
python .bob/skills/scenario-demo-docs/check_demo_consistency.py <id>
```

The skills `wxo-scenario-authoring` (what a scenario must contain and how to build it) and `scenario-demo-docs` (demo script and slides, with templates and a consistency checker) in `.bob/skills/` describe the full procedure. Incident Triage is the reference scenario; its manifest header documents every field. Follow-on plans for each upcoming scenario are in `plans/<id>-plan.md`.

## Adding a Plain Agent

1. Create a directory under `agents/<your-agent-name>/`
2. Add `agent.yaml` -- see [`agents/hello-world/agent.yaml`](agents/hello-world/agent.yaml) as a template
3. Add tools to `tools/` (single `.py` file) or `tools/<package_name>/` (multi-file package with `requirements.txt`)
4. Add `scenarios/<id>/scenario.yaml` listing the agent and its tools (see [`scenarios/hello-world/scenario.yaml`](scenarios/hello-world/scenario.yaml)). **The deploy scripts only deploy what a manifest lists**, so an agent without a manifest is not picked up.
5. Run `scripts/deploy-all.ps1 -Scenario <id>`

## Standalone Agents

**Standalone agents** are ad-hoc agents that a developer builds and deploys directly,
without creating a scenario manifest, demo script, or evaluation ground truth. They live
in `standalone/<agent-name>/` and are managed with `standalone/manage.py` — the scenario
deploy scripts in `scripts/` do not touch them.

Use `standalone/` when an agent answers a focused question (a document, an API, a quick
tool test) rather than driving a structured demo. For a scenario-quality agent with
evaluation, packaging, and demo requirements, use `scenarios/` + `agents/` instead.

**Recommended:** open the **Standalone Builder** mode in Bob to author a new standalone agent.

See [`standalone/README.md`](standalone/README.md) for conventions, the directory layout,
and full deploy/undeploy instructions.

**Quick reference:**

```bash
python standalone/manage.py list                           # show all standalone agents
python standalone/manage.py deploy                         # deploy all
python standalone/manage.py deploy --agent travel_rules_qa # deploy one
python standalone/manage.py deploy --dry-run               # preview
python standalone/manage.py undeploy --agent travel_rules_qa
```
