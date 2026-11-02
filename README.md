# watsonx Orchestrate Lab

Sample agents, tools, knowledge bases and approval flows for **IBM watsonx Orchestrate (WXO)**, plus the tooling to deploy them into your own WXO instance with one command.

The repo is built for two purposes:

1. **Use the samples.** Deploy ready-made agents (business scenarios and small single-purpose agents) into your WXO instance and try them in the chat.
2. **Learn by example.** Read how each agent is put together and build your own. The repo is designed to be developed with [Bob](#build-your-own-agents), which has custom modes and skills for creating scenarios and standalone agents, but you can also work by hand with the ADK.

All business data in this repo is mock or synthetic. Nothing connects to an external system.

> Provided as-is for demonstration and learning, with no support.

## Prerequisites

| Requirement | Details |
|---|---|
| Python | 3.11 or later. Developed and used on Python 3.14. |
| watsonx Orchestrate instance | A SaaS instance you can import agents into, plus its **API key** and **instance URL**. Consult the watsonx Orchestrate documentation to create the key and find the URL. <!-- TODO: add step-by-step instructions for finding the API key and URL --> |
| LLM `groq/openai/gpt-oss-120b` | Every agent uses this model, so your instance must offer it. Check with `orchestrate models list` once the ADK is installed (step 2 below). |
| Embedding model `ibm/granite-embedding-278m-multilingual` | Only the `travel-request` scenario needs it, for its two knowledge bases. |
| Git | To clone the repo. |
| Docker or Podman | Optional. Only for the [traffic generator](#traffic-generator). |
| Bob | Optional, but recommended if you want to create your own agents (see [Build your own agents](#build-your-own-agents)). |

The ADK (`ibm-watsonx-orchestrate`) is installed by the `setup` command below; you do not install it separately.

## Deploy to your instance

Run everything from the repo root.

**1. Clone and create a virtual environment** (optional but recommended; `wxodemo` never creates or activates one for you).

```bash
git clone https://github.com/samisalkosuo/lab-wxo.git
cd lab-wxo
```
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
python wxodemo.py setup          # installs requirements.txt (the ADK), then runs the checks
```

**3. Create `env.cfg`** from the template and fill in your values. The file is required; `wxodemo` never prompts for credentials.

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

> **`env.cfg` contains a secret. Never commit it.** It is git-ignored, and `wxodemo` never prints or logs the key.

**4. Check your setup and log in.**

```bash
python wxodemo.py doctor         # Python, ADK, orchestrate CLI and env.cfg all OK?
python wxodemo.py login          # registers and activates your WXO environment
```

The login token lasts about 2 hours; run `login` again if you get authentication errors.

**5. Deploy a first agent and test it.**

```bash
python wxodemo.py deploy hello-world
```

Open the chat in your WXO instance, select **hello_world** and type `Hello`. The agent calls its Python tool and replies `Hello World!`. If that works, your setup is ready.

**6. Deploy the rest.**

```bash
python wxodemo.py deploy --all --dry-run     # preview what would be imported
python wxodemo.py deploy --all               # every live scenario and every standalone agent
```

Deploying is repeatable: existing resources are updated in place. A run stops at the first failing step, names it, and writes details to `local/wxodemo.log`. If `deploy --all` stops, for example because a model or embedding model is not available on your instance, deploy the scenarios and agents you need by name instead: `python wxodemo.py deploy incident-triage translator`.

**7. Remove everything again** when you are done.

```bash
python wxodemo.py undeploy --all --dry-run   # preview
python wxodemo.py undeploy --all             # shows the plan and asks [y/N]
```

Removing a knowledge base deletes its ingested documents.

## Try it

Open the chat in your WXO instance, select an agent and paste a prompt. Each agent also has a full demo script in [`docs/demo/`](docs/demo/) with exact prompts, expected behaviour and talking points; open [`docs/demo/presentation.html`](docs/demo/presentation.html) in a browser for the slide decks.

| Agent | First prompt to try | What to look for |
|---|---|---|
| `incident_triage` | `Investigate incident INC-1001 on the checkout service. Use your tools to find the root cause and propose a fix.` | The agent checks health, logs, metrics and deployments, cites a runbook, then asks for human approval before any remediation. |
| `cloud_finops` | `Our cloud bill jumped 30% this month. Can you investigate why?` | Spend analysis from tools, with approval forms before resources are reclaimed or resized. |
| `customer_returns` | `I bought a ProBlend 500 blender last month and it broke after a few uses. My order number is ORD-1001.` | Warranty and return policy checks, then a governed refund. |
| `release_readiness` | `Is rel-2025-Q3 ready to ship?` | A supervisor agent calls three specialist agents and combines their findings. |
| `field_maintenance` | `The cooling pump on line 2 is vibrating and running hot. Check it and tell me what to do.` | Asset lookup, history, readings and spares from a mock Maximo, a cited procedure, then a work log approval form (Submit / Reject) before anything is written. |
| `translator` | `Translate 'Our quarterly results are in' to German, but make it sound enthusiastic.` | A tool-free agent with a clarification and refusal path. |

> The approval cards (Approve / Reject) only render in the WXO **browser** chat, not through the API or `wxodemo smoke`.

## What is included

Keep these tables up to date when you add an agent.

### Scenario agents

Business scenarios with mock data, tools, knowledge bases, approval flows, evaluation test cases and a demo script. Deploy by scenario name, for example `python wxodemo.py deploy incident-triage`.

| Agent | Name in WXO | Scenario | Description |
|---|---|---|---|
| [cloud-finops](agents/cloud-finops/) | `cloud_finops` | `cloud-finops` | Investigates spend anomalies, recommends rightsizing, and governs cloud resource reclamation through human approval flows |
| [customer-returns](agents/customer-returns/) | `customer_returns` | `customer-returns` | Conversational returns agent evaluating warranty and return policies; issues governed refunds via approval flow |
| [field-maintenance](agents/field-maintenance/) | `field_maintenance` | `field-maintenance` | Maintenance field assistant: resolves an asset from a vague fault report in a mock Maximo, checks history, open work orders, PM, spares and readings, cites procedures and safety steps, and writes a work log only through an approval flow |
| [hr-onboarding](agents/hr-onboarding/) | `hr_onboarding` | `hr-onboarding` | Conversational HR onboarding assistant that analyzes role-based access policies and initiates governed IT provisioning flows |
| [hr-tacit-knowledge](agents/hr-tacit-knowledge/) | `hr_tk_curator`, `hr_tk_guide` | `hr-tacit-knowledge` | Curates tacit HR knowledge from harvested work artefacts via expert review flow (`hr_tk_curator`) and answers employee questions with citations (`hr_tk_guide`) |
| [incident-triage](agents/incident-triage/) | `incident_triage` | `incident-triage` | Diagnoses production incidents with runbook knowledge; routes automated remediation through human approval |
| [pension-disability-triage](agents/pension-disability-triage/) | `pension_disability_triage` | `pension-disability-triage` | Triages Finnish statutory disability pension claims (TyEL/YEL), enforces rehabilitation-first priority, handles occupational accident waivers, and governs medical board referrals through a human approval flow |
| [pension-ove-advisor](agents/pension-ove-advisor/) | `pension_ove_advisor` | `pension-ove-advisor` | Advises Finnish pension members on partial early old-age pension (OVE), calculates actuarial reductions, simulates combined income, and files applications |
| [release-readiness](agents/release-readiness/) | `release_readiness` | `release-readiness` | Multi-agent supervisor coordinating specialist agents (`rr_qa`, `rr_security`, `rr_ops`) to evaluate release readiness against gating criteria |
| [travel-request](agents/travel-request/) | `travel_request` | `travel-request` | Evaluates business travel authorization against Finnish state regulations and agency policy, estimates per-diem reimbursements, and submits approval requests |
| [yel-income-assessment](agents/yel-income-assessment/) | `yel_income_assessment` | `yel-income-assessment` | Assesses Finnish statutory YEL entrepreneurial income against industry sector benchmarks and submits formal underwriter decisions |

### Standalone agents

Small single-purpose agents with no scenario around them. Deploy by name, for example `python wxodemo.py deploy translator`.

| Agent | Name in WXO | Description |
|---|---|---|
| [document-classifier](standalone/document-classifier/) | `document_classifier` | Classifies text or documents into user-specified categories with confidence and single-sentence reasoning in strict JSON |
| [entity-extractor](standalone/entity-extractor/) | `entity_extractor` | Extracts people, organizations, locations, products, dates, amounts, emails, phones, identifiers and user-defined custom entities into JSON; format-based entities come from a regex Python tool |
| [hello-world](standalone/hello-world/) | `hello_world` | Simple greeting agent with a `greeting` tool -- verifies ADK setup |
| [information-redactor](standalone/information-redactor/) | `information_redactor` | Detects and masks sensitive information and personal identifiers in pasted text before sharing; typed placeholders, no tools, no knowledge base |
| [language-detector](standalone/language-detector/) | `language_detector` | Detects language or mixed languages in any text; returns structured JSON with full name, ISO 639-1, ISO 639-2, BCP 47 tag, script, confidence, and proportion per language |
| [metadata-extractor](standalone/metadata-extractor/) | `metadata_extractor` | Extracts user-specified arbitrary metadata fields from provided text into strict JSON schemas |
| [priority-assessor](standalone/priority-assessor/) | `priority_assessor` | Assigns structured priority levels (Critical, High, Medium, Low) to incoming items using configured rules or common-sense defaults |
| [report-generator](standalone/report-generator/) | `report_generator` | Generates realistic synthetic reports for five predefined types: Doctor Visit Summary, Traffic Incident, Building Inspection, Quarterly Project Update, and Social Services Visit; refuses requests outside those five types |
| [translator](standalone/translator/) | `translator` | Translates user text into a named target language from a fixed supported list, with an optional tone or style; no tools, no knowledge base |
| [travel-rules-qa](standalone/travel-rules-qa/) | `travel_rules_qa` | Answers English questions about the Finnish state travel regulation (Valtion matkustussääntö 2026) from a PDF knowledge base, citing Finnish sections |

## Learn by example

Each pattern below has a sample you can read, deploy and copy.

| To learn how to build... | Read this sample |
|---|---|
| An agent with instructions only (no tools, no knowledge base) | [`standalone/translator`](standalone/translator/) |
| An agent with strict JSON output | [`standalone/document-classifier`](standalone/document-classifier/) |
| An agent that calls a Python tool | [`standalone/hello-world`](standalone/hello-world/), [`standalone/entity-extractor`](standalone/entity-extractor/) |
| An agent that answers from a knowledge base (PDF) | [`standalone/travel-rules-qa`](standalone/travel-rules-qa/) |
| Tools + knowledge base + human-approval flow | [`agents/incident-triage`](agents/incident-triage/) (the reference scenario) |
| A supervisor agent with collaborator agents | [`agents/release-readiness`](agents/release-readiness/) |
| Governed write actions (flow-only tools) | [`agents/customer-returns`](agents/customer-returns/), [`agents/hr-tacit-knowledge`](agents/hr-tacit-knowledge/), [`agents/field-maintenance`](agents/field-maintenance/) |
| Read-only tools that mimic an enterprise system (mock Maximo) | [`agents/field-maintenance`](agents/field-maintenance/) |
| Evaluation test cases and ground truth | [`evaluation/incident-triage`](evaluation/incident-triage/) |

## Build your own agents

**With Bob (recommended).** This repo ships custom Bob modes and skills (in [`.bob/`](.bob/)) that know the repo's conventions, the ADK CLI and the ADK documentation. Open the repo as a Bob workspace and pick a mode:

- **Scenario Builder** creates a complete demo scenario: mock-data tools, knowledge base, approval flow, agent, manifest, evaluation cases, demo script and slides.
- **Standalone Builder** creates a small one-off agent under `standalone/`.

Sample prompts and what to check afterwards: [`docs/building-with-bob.md`](docs/building-with-bob.md).

**By hand.** Copy the closest sample from [Learn by example](#learn-by-example), then:

- Standalone agent: follow [`standalone/README.md`](standalone/README.md). `wxodemo` discovers any folder under `standalone/` that contains an `agent.yaml`.
- Scenario: scaffold it with `python wxodemo.py new-scenario <id> --name "..." --description "..."`, build the tools, knowledge base, flow and agent, list them in `scenarios/<id>/scenario.yaml`, and check with `python wxodemo.py validate <id>`. `scenarios/incident-triage/scenario.yaml` documents every field.
- `wxodemo deploy` only deploys what a scenario manifest lists or what lives under `standalone/`. An agent in `agents/` that no manifest lists is not picked up.

## Development

### `wxodemo` commands

`wxodemo` is the one CLI for this repo. Run it as `python wxodemo.py <command>`, or as `wxodemo <command>` after `pip install -e .`.

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
| `eval <target>` | Run the ADK evaluation for a scenario or standalone agent |
| `test-upload <target>` | Upload test cases to the WXO Tests tab (and optionally evaluate) |
| `export-chats` | Export agent chats and traces |
| `new-scenario <id>` | Scaffold a new scenario |
| `logs` | Show the log file path and its last lines |

Names are scenario ids or standalone agent names (see `list`). `--kind scenario|standalone` narrows `--all`. Commands that change something take `--dry-run`. Exit codes: 0 ok, 1 command failed, 2 configuration or usage error. Every option, the `env.cfg` keys, the log file and troubleshooting are in [`docs/wxodemo.md`](docs/wxodemo.md).

### Where things live

Scenario agents are defined in `agents/`, their Python tools in `tools/`, knowledge-base sources in `knowledge/`, approval flows in `flows/`, and the manifest that ties them together in `scenarios/<id>/scenario.yaml`. Evaluation test cases are in `evaluation/`, standalone agents in `standalone/`, and demo scripts and slides in `docs/demo/`. The CLI is in `src/wxodemo/` with its tests in `tests/`. The `plans/` folder holds the plan Bob and the author wrote before building each scenario or feature, with the decisions and test notes recorded as work progressed. Read them to see how a plan-first workflow with Bob unfolds; they are working notes, not user documentation.

### Smoke tests

```bash
python wxodemo.py smoke incident-triage --dry-run   # print the prompts, send nothing
python wxodemo.py smoke incident-triage             # send them to the deployed agent
```

`smoke` sends diagnosis-only prompts through the ADK run API and prints the tools called and the start of each answer. It does not grade the answers.

### Running the evaluation (optional)

The ADK evaluation framework is not installed by `setup`. Install it first:

```bash
pip install ibm-watsonx-orchestrate-evaluation-framework==1.5.2
```

On Python 3.14 pip cannot satisfy its `pandas~=2.2.3` pin. Work around it with:

```bash
pip install --no-deps ibm-watsonx-orchestrate-evaluation-framework==1.5.2
pip install pandas
```

Its other dependencies (`agentops`, `langchain`, `fuzzywuzzy`, `portkey-ai`, `openinference-*`, `jsonargparse`) may need installing by hand too. Then:

```bash
python wxodemo.py eval incident-triage
python wxodemo.py eval entity-extractor      # a standalone agent with an eval_config.yaml
```

The command exits 1 when its output is piped or redirected (a progress-rendering issue); the result files are still written to `evaluation/<scenario>/results/<timestamp>/` or `standalone/<agent>/results/<timestamp>/`. Both locations are git-ignored.

### Repo tests

```bash
pip install pytest ruff
python -m pytest -q                              # no network, no ADK login, no env.cfg needed
python -m ruff check src tests wxodemo.py
```

## Traffic generator

[`traffic-gen/`](traffic-gen/) is a small containerised Python app that periodically sends prompts to your deployed agents through the WXO REST API. Use it to fill the WXO Home, Observability and Analytics dashboards with realistic usage when preparing a demo. It needs deployed agents, your API key and URL, and Docker or Podman. It reads the agent list and prompts from the scenarios and standalone agents in this repo, so there is nothing to configure.

```bash
docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen .     # build from the repo root
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id> \
  wxo-traffic-gen
```

Options, the agent pool and the log format are in [`traffic-gen/README.md`](traffic-gen/README.md).

## Back up agent chats

```bash
python wxodemo.py export-chats                        # last 7 days, all agents, into export/<timestamp>/
python wxodemo.py export-chats --agent translator --last 30d
```

## Good to know

- **Mock data, probabilistic agents.** The data is fictional, and model output varies from run to run. Use the demo scripts as a guide, not as exact expected text.
- **`wxodemo` has been run on Windows only.** The Linux and macOS commands are provided but were not run on those systems. The test suite replaces `orchestrate` with a fake and needs no platform-specific tool.
- **Developer Edition.** After import, `wxodemo deploy` promotes each agent to live. If your edition refuses promotion, the deploy stops with exit code 1 and the agent stays a draft.
- **Approval forms need the browser chat.** The Approve / Reject cards cannot be answered through the API.
- **Evaluation scores are not a quality signal yet.** See [`docs/known-issues.md`](docs/known-issues.md) for what the current results do and do not show.

Something else failing? Check the troubleshooting table in [`docs/wxodemo.md`](docs/wxodemo.md#troubleshooting) and `python wxodemo.py logs`.

## License and third-party content

The code and sample data in this repo are released under the [MIT License](LICENSE).

[`knowledge/travel-request/VM_2025_63.pdf`](knowledge/travel-request/VM_2025_63.pdf) (*Valtion matkustussääntö 2026*, Ministry of Finance, Finland) is third-party content distributed unmodified under **CC BY-NC-ND 4.0**, not under the MIT License. Source and attribution: [`agents/travel-request/README.md`](agents/travel-request/README.md#source-attribution).

IBM, watsonx and watsonx Orchestrate are trademarks of International Business Machines Corporation, registered in many jurisdictions worldwide. Other names may be trademarks of their respective owners.
