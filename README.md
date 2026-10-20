# watsonx Orchestrate Lab

A development environment for building and deploying IBM watsonx Orchestrate agents using the ADK (Agent Development Kit).

Agents, tools, knowledge bases, and flows in this repo are version-controlled and distributable. Run `python wxodemo.py deploy --all` to import everything into an existing WXO instance (see the [Quick start](#quick-start)). Re-running the deploy over existing resources is safe — re-import updates in place. A clean first install on a fresh instance has not been tested. All commands are documented in [`docs/wxodemo.md`](docs/wxodemo.md).

## Repository Structure

```
lab-wxo/
├── agents/
│   ├── incident-triage/
│   │   ├── agent.yaml
│   │   └── README.md
│   └── travel-request/
│       ├── agent.yaml
│       └── README.md
├── tools/
│   ├── incident_triage/          # Multi-file Python tool package
│   │   ├── incident_triage.py    # Entry file (8 @tool functions)
│   │   ├── requirements.txt
│   │   └── data/                 # Static mock-world data modules
│   └── travel_request/           # Multi-file Python tool package
│       ├── travel_request.py     # Entry file (employee, budget, rates, reimbursement tools)
│       ├── requirements.txt
│       └── data/                 # Static mock employees, policy and rate data
├── knowledge/
│   ├── incident-triage/
│   │   ├── incident_triage_runbooks.yaml
│   │   └── runbooks/             # Six .txt runbook files
│   └── travel-request/
│       ├── travel_state_rules.yaml    # Finnish state travel regulation (PDF)
│       ├── travel_agency_policy.yaml  # English fictional agency policy
│       ├── VM_2025_63.pdf
│       └── policy/               # Policy .txt files
├── flows/
│   ├── incident_triage/
│   │   └── request_remediation.py
│   └── travel_request/
│       └── travel_submit_request.py
├── evaluation/
│   ├── incident-triage/
│   │   ├── eval_config.yaml
│   │   ├── ground_truth.json
│   │   └── test_cases/           # 5 evaluation test cases (.json)
│   └── travel-request/
│       └── ground_truth.json
├── scenarios/
│   ├── incident-triage/scenario.yaml   # Manifest: every resource the scenario owns
│   └── travel-request/scenario.yaml
├── docs/
│   ├── wxodemo.md                # Full reference for the wxodemo CLI
│   └── demo/
│       ├── incident-triage-demo.md   # Human-readable demo script
│       ├── travel-request-demo.md
│       ├── presentation.html         # Slide shell; loads scenarios/*.js
│       └── scenarios/                # One slides file per scenario (4 are "coming soon" placeholders)
├── standalone/
│   ├── README.md                 # What standalone means, wxodemo usage
│   ├── hello-world/              # ADK setup check (agent + greeting tool)
│   ├── translator/               # Translation agent (fixed language list, optional tone)
│   └── travel-rules-qa/          # Finnish travel regulation PDF Q&A agent
├── connections/                  # Connection templates (empty for this demo)
├── src/wxodemo/                  # The wxodemo CLI package (deploy, undeploy, status, smoke, ...)
├── tests/                        # pytest suite for the CLI (no network or ADK login needed)
├── wxodemo.py                    # Launcher: python wxodemo.py <command>
├── pyproject.toml                # Package metadata; `pip install -e .` gives a `wxodemo` command
├── env.cfg                       # Secrets -- DO NOT COMMIT
├── env.cfg.example               # Template -- safe to commit
└── requirements.txt              # ibm-watsonx-orchestrate and pinned deps
```

## Agents

### Demo scenario agents

Deployed with `python wxodemo.py deploy` from the scenario manifests in `scenarios/`.

| Agent | Name in WXO | Scenario | Description |
|---|---|---|---|
| [incident-triage](agents/incident-triage/) | `incident_triage` | `incident-triage` | Diagnoses mock production incidents; routes remediation through a human-approval flow |
| [travel-request](agents/travel-request/) | `travel_request` | `travel-request` | Decides whether a business trip is approved, needs approval, or is denied under the Finnish state travel rules; estimates reimbursement with tools and issues a request id only through a human-approval flow |

### Standalone agents

Deployed with `python wxodemo.py deploy <name>` (see [Standalone Agents](#standalone-agents)); not part of any scenario.

| Agent | Name in WXO | Description |
|---|---|---|
| [hello-world](standalone/hello-world/) | `hello_world` | Simple greeting agent with a `greeting` tool -- verifies ADK setup |
| [translator](standalone/translator/) | `translator` | Translates user text into a named target language from a fixed supported list, with an optional tone or style; no tools, no knowledge base |
| [travel-rules-qa](standalone/travel-rules-qa/) | `travel_rules_qa` | Answers English questions about the Finnish state travel regulation (Valtion matkustussääntö 2026) from a PDF knowledge base, citing Finnish sections |

## Quick start

**Prerequisites:** Python 3.11 or later and a watsonx Orchestrate (WXO) instance with an API key. Everything else, including the ADK (`ibm-watsonx-orchestrate`), is installed by step 2. The project was developed and deployed on Python 3.14. On 3.14 the optional evaluation framework could not be installed normally (see [Running the evaluation](#running-the-evaluation-optional)); other versions were not tested.

**1. Create a virtual environment (optional, recommended).** `wxodemo` never creates or activates one; it uses the Python that starts it.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
```
```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
```

**2. Install the dependencies.**

```bash
python wxodemo.py setup          # pip install -r requirements.txt, then runs doctor
```

Optional: `pip install -e .` adds a `wxodemo` command, so you can type `wxodemo deploy --all` instead of `python wxodemo.py deploy --all`.

**3. Fill in `env.cfg`.** Copy the template and edit it. The file is mandatory; `wxodemo` never prompts for credentials.

```powershell
Copy-Item env.cfg.example env.cfg   # Windows
```
```bash
cp env.cfg.example env.cfg          # Linux / macOS
```

```ini
WXO_API_KEY=your-api-key-here
WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>
WXO_ENV_NAME=my-env
WXO_ENV_TYPE=ibm_iam      # optional: ibm_iam (default) or mcsp (AWS-hosted)
```

> **`env.cfg` contains secrets -- do not commit it.** It is git-ignored, and `wxodemo` never prints or logs the key.

**4. Check, log in, deploy.**

```bash
python wxodemo.py doctor                    # is everything ready?
python wxodemo.py login                     # register and activate the WXO environment
python wxodemo.py deploy --all --dry-run    # preview
python wxodemo.py deploy --all              # every live scenario + every standalone agent
python wxodemo.py smoke incident-triage     # send the smoke prompts to the deployed agent
```

Deploying is repeatable: existing resources are updated in place. The run stops at the first failing step, names it, and writes the details to `local/wxodemo.log`. The remote token lasts about 2 hours, so run `python wxodemo.py login` shortly before a demo.

**5. Clean up when you are done.**

```bash
python wxodemo.py undeploy --all --dry-run  # preview
python wxodemo.py undeploy --all            # shows the plan, asks [y/N]
```

Removing a knowledge base deletes its ingested documents.

### Commands

| Command | Purpose |
|---|---|
| `setup` | Install `requirements.txt` with the current Python, then run `doctor` |
| `doctor` | Check Python, ADK, `orchestrate`, `env.cfg` and the active WXO environment |
| `login` | Register and activate the WXO environment from `env.cfg` |
| `list` | Scenarios and standalone agents, with kind and status |
| `status` | What the repo defines versus what is deployed in WXO |
| `deploy [names] [--all] [--kind K]` | Deploy in dependency order (login included) |
| `undeploy [names] [--all] [--kind K]` | Remove in reverse order, with `[y/N]` unless `--yes` |
| `validate [names]` | Manifest and demo-consistency checks |
| `smoke <scenario>` | Send a scenario's smoke prompts to its deployed agent |
| `eval <scenario>` | Run the ADK evaluation for a scenario |
| `export-chats` | Export agent chats and traces |
| `new-scenario <id>` | Scaffold a new scenario |
| `logs` | Show the log file path and its last lines |

Names are scenario ids or standalone agent names (see `list`). `--kind scenario|standalone` narrows `--all`. Commands that change something take `--dry-run`. Exit codes: 0 ok, 1 command failed, 2 configuration or usage error.

**Full reference** (every option, `env.cfg` keys, log file, exit codes, troubleshooting, and a table from the old scripts to the new commands): [`docs/wxodemo.md`](docs/wxodemo.md).

## Running the evaluation (optional)

> **Dependency warning:** the evaluation framework `ibm-watsonx-orchestrate-evaluation-framework==1.5.2` and its transitive dependencies (`agentops`, `langchain`, `fuzzywuzzy`, `portkey-ai`, `openinference-*`, `jsonargparse`) are **not** installed automatically. On Python 3.14 the `pandas~=2.2.3` pin cannot be satisfied. On other Python versions you can try (untested here):
>
> ```bash
> pip install ibm-watsonx-orchestrate-evaluation-framework==1.5.2
> ```
>
> If pip fails on the pandas pin, use `--no-deps` and install pandas separately:
>
> ```bash
> pip install --no-deps ibm-watsonx-orchestrate-evaluation-framework==1.5.2
> pip install pandas
> ```
>
> A clean-instance install of the evaluation framework was not tested. The dependency issue was resolved manually on the development machine.

Once the dependencies are installed (Incident Triage):

```bash
python wxodemo.py eval incident-triage
```

The command exits with code 1 when its output is piped or redirected (a progress-rendering issue); the result files are still written to `evaluation/incident-triage/results/<timestamp>/`.

To send a scenario's diagnosis-only prompts to the deployed agent, use `python wxodemo.py smoke <id>` (`--dry-run` prints the prompts without calling the instance). It does not grade the answers.

## Demo

See [`docs/demo/incident-triage-demo.md`](docs/demo/incident-triage-demo.md) for the human-readable demo script: exact prompts, expected agent behaviour, fallback notes, and closing talking points.

## Status and Known Limitations

This is a demo / lab repo. The following items are open as of the current state:

- **No clean-instance install tested.** The only tested deploy was a re-install over an existing environment (`techzone1`). First-import on a fresh WXO instance was not verified.
- **Evaluation final-answer check: 0 of 15 runs pass.** Tool-selection metrics are good (recall 1.0 in 13 of 15 runs, `tool_match_success` true in 13 of 15), but `is_success` requires the text check to also pass. The text check fails because the agent writes IDs with non-breaking hyphens (U+2011, e.g. `RB-TLS-01`) which break exact keyword matches, and produces long answers compared with the one-sentence expected responses. The overall score is not a useful signal in its current form.
- **Wrong incident reference in approval requests (3 of 19 vague-opening runs).** On "Hey, checkout is slow...", the agent sometimes investigates the payments service while working INC-1001 and then calls `request_remediation` with `service=payments, incident_id=INC-1001` (mismatched). The instruction change in `agent.yaml` gave no measurable improvement. The human approval gate catches this before any execution; a proper fix is to validate service/incident consistency inside the flow.
- **Evaluation dependencies installed by hand.** `ibm-watsonx-orchestrate-evaluation-framework==1.5.2` and its transitive dependencies are not installed automatically. On Python 3.14 the `pandas~=2.2.3` pin cannot be satisfied. See [Running the evaluation](#running-the-evaluation-optional) for the workaround.
- **`wxodemo` has been run on Windows only.** The automated tests (about 250, with `orchestrate` replaced by a fake) do not need a platform-specific tool, but runs on native Linux and macOS were not done.
- **`orchestrate chat ask` hangs** in non-interactive shells. Use the ADK run API instead (see `src/wxodemo/smoke.py`).
- **Scenario `undeploy` (tools, flows, knowledge bases) has only been run with `--dry-run`** against the live instance. Standalone agent `undeploy` and `deploy` were run for real.
- **`wxodemo smoke` was not run live against an instance in this form.** Its logic is covered by tests with a faked ADK client; a live run of the command itself has not been recorded.
- **Promotion to live is required.** If `orchestrate agents deploy` is refused (for example on the Developer Edition), `wxodemo deploy` stops with exit code 1 and leaves the agent as a draft. This change has not been run against a Developer Edition instance.

## Adding a New Scenario

Every scenario is a folder of resources described by a manifest, plus a demo script and a section in the presentation.

**Recommended:** open the **Scenario Builder** mode in Bob. It loads the three relevant skills in the right order and enforces the design rules and final consistency checks automatically.

Scaffold the folder skeleton first:

```bash
python wxodemo.py new-scenario customer-returns --name "Customer Returns" --description "One line for the sidebar"
```

This creates `scenarios/<id>/scenario.yaml` (status `soon`), an agent stub, a `ground_truth.json` stub, the demo script from the template, and registers `docs/demo/scenarios/<id>.js` in `presentation.html`. Then build the tools, knowledge base and flow, list them in the manifest, and check:

```bash
python wxodemo.py validate <id>
```

The skills `wxo-scenario-authoring` (what a scenario must contain and how to build it) and `scenario-demo-docs` (demo script and slides, with templates; their consistency checks run in `wxodemo validate`) in `.bob/skills/` describe the full procedure. Incident Triage is the reference scenario; its manifest header documents every field. Follow-on plans for each upcoming scenario are in `plans/<id>-plan.md`.

## Adding a Plain Agent

1. Create a directory under `agents/<your-agent-name>/`
2. Add `agent.yaml` -- see [`agents/incident-triage/agent.yaml`](agents/incident-triage/agent.yaml) as a template
3. Add tools to `tools/` (single `.py` file) or `tools/<package_name>/` (multi-file package with `requirements.txt`)
4. Add `scenarios/<id>/scenario.yaml` listing the agent and its tools (see [`scenarios/travel-request/scenario.yaml`](scenarios/travel-request/scenario.yaml)). **`wxodemo deploy` only deploys what a manifest lists**, so an agent without a manifest is not picked up.
5. Run `python wxodemo.py deploy <id>`

## Standalone Agents

**Standalone agents** are ad-hoc agents that a developer builds and deploys directly,
without creating a scenario manifest, demo script, or evaluation ground truth. They live
in `standalone/<agent-name>/` and are deployed with `python wxodemo.py deploy <name>`
(or `--kind standalone`); they have no scenario manifest.

Use `standalone/` when an agent answers a focused question (a document, an API, a quick
tool test) rather than driving a structured demo. For a scenario-quality agent with
evaluation and demo requirements, use `scenarios/` + `agents/` instead.

**Recommended:** open the **Standalone Builder** mode in Bob to author a new standalone agent.

See [`standalone/README.md`](standalone/README.md) for conventions, the directory layout,
and full deploy/undeploy instructions.

**Quick reference:**

```bash
python wxodemo.py list --kind standalone                   # show all standalone agents
python wxodemo.py deploy --all --kind standalone           # deploy all
python wxodemo.py deploy travel_rules_qa                   # deploy one
python wxodemo.py deploy travel_rules_qa --dry-run         # preview
python wxodemo.py undeploy travel_rules_qa
```

## Backing Up Agent Chats

To back up and archive all agent conversation histories and interactive chats from your WXO instance:

```bash
# Zero-config default: reads env.cfg and exports all agent chats into export/YYYYMMDDHHMMSS/
python wxodemo.py export-chats

# Optional: filter by agent or time window
python wxodemo.py export-chats --agent translator
python wxodemo.py export-chats --last 30d
```
