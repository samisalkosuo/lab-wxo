# watsonx.orchestrate

A development environment for building and deploying IBM watsonx Orchestrate agents using the ADK (Agent Development Kit).

All agents, tools, knowledge bases, and flows in this repo are version-controlled and fully distributable — run `scripts/deploy-all.ps1` against any fresh WXO instance to reproduce the complete setup.

## Repository Structure

```
watsonx.orchestrate/
├── agents/                    # One subdirectory per agent
│   └── hello-world/
│       ├── agent.yaml         # Agent definition
│       └── README.md
├── tools/                     # Shared Python and OpenAPI tools
│   └── greetings.py
├── knowledge/                 # Knowledge base definitions and documents
├── flows/                     # Agentic workflow definitions
├── connections/               # Connection templates (no secrets)
├── scripts/
│   ├── deploy-all.ps1         # Deploy everything to a WXO instance
│   └── teardown.ps1           # Remove everything (dev cleanup)
├── env.cfg                    # Secrets — DO NOT COMMIT
├── env.cfg.example            # Template — safe to commit
├── activate-wxo.ps1           # Environment activation script
└── requirements.txt           # Python dependencies
```

## Prerequisites

- Python 3.10+
- IBM watsonx Orchestrate ADK — see the [installation guide](https://developer.watson-orchestrate.ibm.com/getting_started/installing)

## Setup

### 1. Create the virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure credentials

Copy the example config and fill in your values:

```powershell
Copy-Item env.cfg.example env.cfg
```

Edit `env.cfg`:

```ini
WXO_API_KEY=your-api-key-here
WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>
WXO_ENV_NAME=my-env
```

> **Note:** `env.cfg` contains secrets — do not commit it to source control.

## Usage

### Activate the WXO environment

```powershell
.\activate-wxo.ps1
```

### Deploy everything to WXO (fresh or existing instance)

```powershell
.\scripts\deploy-all.ps1
```

This script discovers and imports all tools and agents automatically. It is idempotent — safe to re-run against an existing instance.

### Remove everything from WXO (dev cleanup)

```powershell
.\scripts\teardown.ps1
```

### Deploy a single agent manually

```powershell
# Import a tool
orchestrate tools import -k python -f tools/greetings.py

# Import an agent
orchestrate agents import -f agents/hello-world/agent.yaml

# Test in terminal
orchestrate chat start

# Promote draft → live
orchestrate agents deploy --name hello_world
```

## Adding a New Agent

1. Create a directory under `agents/<your-agent-name>/`
2. Add `agent.yaml` — see [`agents/hello-world/agent.yaml`](agents/hello-world/agent.yaml) as a template
3. Add any Python tools to `tools/`
4. Run `scripts/deploy-all.ps1` — the new agent is picked up automatically

## Agents

| Agent | Description |
|---|---|
| [hello-world](agents/hello-world/) | Simple Hello World agent — verifies ADK setup |
