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
├── docs/
│   └── demo/
│       └── incident-triage-demo.md   # Human-readable demo script
├── connections/                  # Connection templates (empty for this demo)
├── scripts/
│   ├── deploy-all.ps1            # Deploy everything (Windows PowerShell)
│   ├── deploy-all.sh             # Deploy everything (Linux/macOS bash)
│   ├── teardown.ps1              # Remove everything (Windows PowerShell)
│   ├── teardown.sh               # Remove everything (Linux/macOS bash)
│   └── package.py                # Build distributable zip
├── dist/                         # Packaged zip output (git-ignored)
├── env.cfg                       # Secrets -- DO NOT COMMIT
├── env.cfg.example               # Template -- safe to commit
├── activate-wxo.ps1              # Standalone environment activation
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

## Setup

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
.\scripts\deploy-all.ps1
```

### Linux / macOS (bash)

```bash
bash scripts/deploy-all.sh
```

The script reads `env.cfg`, registers the WXO environment non-interactively, then imports resources in dependency order:

```
connections -> tools (flat .py, multi-file packages) -> knowledge bases -> flows -> agents -> agents deploy
```

Each imported agent is promoted from draft to live with `orchestrate agents deploy --name <name>` at the end of the script. **This step is required** because the chat UI only shows live agents. If you skip it (or if the deploy call fails on Developer Edition), the agent will not appear in the agent picker.

Re-running is safe: existing resources are updated in place.

**Auth expiry:** the remote token expires after 2 hours. Re-run the deploy script before a demo or after a long gap.

## Teardown (dev cleanup)

```powershell
.\scripts\teardown.ps1 -DryRun   # preview -- prints commands, makes no changes
.\scripts\teardown.ps1            # real deletion (UNTESTED -- see warning in script)
```

```bash
bash scripts/teardown.sh --dry-run   # preview
bash scripts/teardown.sh             # real deletion (UNTESTED -- see warning in script)
```

Resources are removed in reverse dependency order (agents first, then flows, then tools, then knowledge bases). The teardown scripts use real WXO resource names, not file names.

**Important:** real deletion was never executed during development (demo resources on `techzone1` were preserved). Use `-DryRun` / `--dry-run` to review the commands first. The behaviour of the remove subcommands (confirmation prompts, errors when an agent still references a tool) is untested. Check `orchestrate agents remove --help`, `orchestrate tools remove --help`, and `orchestrate knowledge-bases remove --help` for any required flags before running for real.

## Packaging

Build a distributable zip for external users:

```bash
python scripts/package.py [--version 1.0.0]
```

This produces `dist/wxo-incident-triage-<version>.zip`. The zip contains only the incident-triage agent and its dependencies -- it excludes `env.cfg`, `local/`, dev tooling state, and instance-specific artefacts. A post-build security check deletes the zip and exits non-zero if any excluded pattern or secret-bearing string is found.

The zip includes `INSTALL.md` (generated by `package.py`) with full setup instructions for external users.

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
- **`orchestrate chat ask` hangs** in non-interactive shells. Use the ADK run API instead (see `scripts/smoke_test_triage.py`).

## Adding a New Agent

1. Create a directory under `agents/<your-agent-name>/`
2. Add `agent.yaml` -- see [`agents/hello-world/agent.yaml`](agents/hello-world/agent.yaml) as a template
3. Add tools to `tools/` (single `.py` file) or `tools/<package_name>/` (multi-file package with `requirements.txt`)
4. Run `scripts/deploy-all.ps1` -- the new agent is picked up automatically
