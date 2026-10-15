---
name: wxo-adk
description: Use when the user wants to create, author, import, deploy, or manage watsonx Orchestrate agents, skills, or tools using the ADK CLI. Also use when the user asks about orchestrate CLI commands, writing Python skills, defining agents in YAML, connecting tools, or the full agent development lifecycle.
---

# watsonx Orchestrate ADK — Agent Development Guide

This skill covers the full lifecycle: environment setup → skill authoring → agent authoring → deploying via CLI.

The installed ADK version in this project is **ibm-watsonx-orchestrate v2.18.2**.

---

## 0. Official Documentation (Always Consult First)

An MCP tool is connected that provides the full official watsonx Orchestrate developer documentation. **Always search this before answering any ADK question** — it is the authoritative source and takes precedence over any cached knowledge in this skill.

### How to use the docs MCP tools

Two tools are available:

**`mcp__watsonx-orchestrat_3b9d__search_ibm_watsonx_orchestrate_adk`** — semantic search across all docs:
```
query: "how to create a Python tool"
```

**`mcp__watsonx-orch_3b9d__query_docs_filesystem_ibm_watsonx_orches`** — filesystem commands against the docs:
```
# Explore structure
tree / -L 2

# Full-text search
rg -il "tool decorator" /

# Read a specific page
head -100 /tools/create_tool.mdx
cat /getting_started/installing.mdx

# Search with context
rg -C 5 "@tool" /tools/
```

### Key doc paths by topic

| Topic | Path |
|---|---|
| Installation / getting started | `/getting_started/installing.mdx`, `/getting_started/cli.mdx` |
| Concepts | `/getting_started/concepts.mdx` |
| Building agents | `/agents/build_agent.mdx`, `/agents/overview.mdx` |
| Agent styles | `/agents/agent_styles.mdx` |
| Importing agents | `/agents/import_agent.mdx` |
| Python tools / skills | `/tools/create_tool.mdx`, `/tools/tool_schemas.mdx` |
| OpenAPI tools | `/tools/create_openapi_tool.mdx` |
| Tool dependency management | `/tools/python_dependency_management.mdx` |
| Connections | `/connections/build_connections.mdx`, `/connections/overview.mdx` |
| Knowledge bases | `/knowledge_base/build_kb.mdx` |
| Local dev server | `/developer_edition/wxOde_setup.mdx`, `/developer_edition/manage_local_server.mdx` |
| SDK | `/sdk/sdk_intro.mdx` |
| Tutorials | `/tutorials/tutorial_1_hello_world.mdx` |
| Evaluate agents | `/evaluate/overview.mdx` |
| Traces / observability | `/traces/overview.mdx` |
| CLI reference | `/getting_started/cli.mdx` |
| REST API reference | `/apis/` |

### Workflow for any ADK question

1. Run `mcp__watsonx-orchestrat_3b9d__search_ibm_watsonx_orchestrate_adk` with a focused query.
2. If the result points to a specific page, read it with `mcp__watsonx-orch_3b9d__query_docs_filesystem_ibm_watsonx_orches` using `head` or `cat`.
3. Base the answer on what the docs say. Note the doc path as a reference.
4. Only fall back to the cached content in sections 1–8 below if the docs MCP returns nothing relevant.

---

## 1. Environment Setup

Always ensure an environment is active before running any other commands.

```powershell
# Register and activate (reads env.cfg via the project script)
.\activate-wxo.ps1

# Or manually:
orchestrate env add -n <name> -u <url> --type ibm_iam --activate
orchestrate env activate <name>

# List all configured environments
orchestrate env list

# Remove an environment
orchestrate env remove -n <name>
```

Credentials live in `env.cfg` (see `env.cfg.example` for the template):
```ini
WXO_API_KEY=...
WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>
WXO_ENV_NAME=...
```

---

## 2. Skills

Skills are callable functions exposed to agents. They are defined as Python functions or OpenAPI specs and imported into the platform.

### 2a. Python skill structure

A Python skill is a `.py` file with decorated functions:

```python
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission

@tool(
    name="get_weather",
    description="Returns current weather for a given city.",
    permission=ToolPermission.READ_ONLY,
)
def get_weather(city: str) -> str:
    """Returns weather info for the given city."""
    return f"Sunny, 22°C in {city}"
```

Key rules:
- Use type annotations on all parameters and the return type.
- The `description` in `@tool` is what the agent uses to decide when to call the skill.
- Keep functions focused — one responsibility per skill function.
- Return plain Python types (str, dict, list) or Pydantic models.

### 2b. Skill YAML definition (metadata file)

To import a Python skill, pair it with a YAML metadata file:

```yaml
# my_skill.yaml
name: my-skill
description: "Brief description shown in the UI"
tools:
  - name: get_weather
    file: get_weather.py
```

### 2c. Importing skills

```powershell
# Import a single skill file
orchestrate skills import --file path/to/skill.yaml

# Import all skills in a directory
orchestrate skills import --dir path/to/skills/ --recursive

# Upsert (update if already exists)
orchestrate skills import --file path/to/skill.yaml --upsert

# Upload a Python script to an existing skill
orchestrate skills upload-script --file get_weather.py --skill-name get_weather
```

### 2d. Managing skills

```powershell
orchestrate skills list
orchestrate skills list --verbose
orchestrate skills get --skill-name <name>
orchestrate skills export --skill-name <name> -o ./exported/
orchestrate skills update --skill-name <name> --file updated.yaml
orchestrate skills remove --skill-name <name>
```

---

## 3. Agents

Agents are the orchestration layer. They use LLMs to decide which skills/tools to call.

### 3a. Agent kinds

| Kind | Description |
|---|---|
| `NATIVE` | Built with watsonx Orchestrate — recommended for most use cases |
| `EXTERNAL` | Wraps an external API endpoint as an agent |
| `ASSISTANT` | Watson Assistant-style agent |
| `CUSTOM` | Custom Python agent packaged as a ZIP |

### 3b. Agent YAML definition

```yaml
# my_agent.yaml
name: my-agent
kind: NATIVE
title: "My Agent"
description: "Helps users with weather queries."
instructions: |
  You are a helpful assistant. When the user asks about weather,
  use the get_weather tool. Always respond in a friendly tone.
tools:
  - name: get_weather
```

Advanced fields:
```yaml
# Optional fields
style: DEFAULT          # or REACT, PLAN_EXECUTE
provider: watsonx       # LLM provider
model: meta-llama/llama-3-1-70b-instruct   # specific model
knowledge_bases:
  - name: my-kb
collaborators:
  - name: other-agent   # sub-agents this agent can delegate to
```

### 3c. Importing agents

```powershell
# Import from a YAML file
orchestrate agents import --file my_agent.yaml

# Import from a directory (package-root, auto-zipped)
orchestrate agents import --package-root ./my_agent_package/

# Import with a separate config file
orchestrate agents import --file agent.yaml --config-file config.yaml

# Safe import (won't overwrite existing)
orchestrate agents import --file my_agent.yaml --safe
```

### 3d. Creating agents directly via CLI

```powershell
orchestrate agents create \
  --name my-agent \
  --kind NATIVE \
  --instructions "You are a helpful assistant."
```

### 3e. Managing agents

```powershell
orchestrate agents list
orchestrate agents list --verbose
orchestrate agents export --agent-name <name> -o ./exported/
orchestrate agents publish --agent-name <name>
orchestrate agents remove --agent-name <name>
```

---

## 4. Tools

Tools are connections between agents and external systems (APIs, databases, etc.).

```powershell
# Import a tool (e.g. OpenAPI spec)
orchestrate tools import --kind openapi --file api-spec.yaml

# Import a tool linked to a connection (app)
orchestrate tools import --kind openapi --file api-spec.yaml --app-id <connection-id>

# List tools
orchestrate tools list
orchestrate tools list --verbose

# Export / remove
orchestrate tools export --tool-id <id> -o ./exported/
orchestrate tools remove --tool-id <id>
```

---

## 5. Connections (App IDs)

Connections store authentication credentials for external systems and are referenced by tools/agents via `--app-id`.

```powershell
orchestrate connections list
```

Auth types: `NONE`, `BASIC`, `BEARER`, `OAUTH`, `API_KEY`

---

## 6. Other Useful Commands

```powershell
# Knowledge bases (vector search)
orchestrate knowledge-bases list
orchestrate knowledge-bases import --file kb.yaml

# Models available to agents
orchestrate models list

# Toolkits (grouped tool collections)
orchestrate toolkits list

# Workspaces (IBM Cloud / CP4D)
orchestrate workspaces list

# Observability / tracing
orchestrate observability list

# Agent evaluation
orchestrate evaluations list

# Local dev server (requires entitlement)
orchestrate server start
orchestrate server stop

# Chat with an agent in terminal
orchestrate chat --agent-name <name>

# Settings
orchestrate settings list
```

---

## 7. Typical Development Workflow

Follow this sequence for a new agent from scratch:

1. **Activate environment**
   ```powershell
   .\activate-wxo.ps1
   ```

2. **Write the skill** — create a Python `.py` file with `@tool`-decorated functions.

3. **Import the skill**
   ```powershell
   orchestrate skills import --file my_skill.yaml --upsert
   ```

4. **Verify the skill imported**
   ```powershell
   orchestrate skills list
   ```

5. **Write the agent YAML** — reference the skill in the `tools:` list.

6. **Import the agent**
   ```powershell
   orchestrate agents import --file my_agent.yaml
   ```

7. **Verify the agent**
   ```powershell
   orchestrate agents list
   ```

8. **Test in terminal**
   ```powershell
   orchestrate chat --agent-name my-agent
   ```

9. **Publish to production**
   ```powershell
   orchestrate agents publish --agent-name my-agent
   ```

---

## 8. Project Conventions (this repo)

- Credentials: `env.cfg` (never commit; copy from `env.cfg.example`)
- Environment activation: `.\activate-wxo.ps1`
- Python virtual env: `.venv` — activate with `.\.venv\Scripts\Activate.ps1`
- ADK version: `ibm-watsonx-orchestrate==2.18.2`
- Instance region: `eu-de`
- Environment name: `techzone1`
