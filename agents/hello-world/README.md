# Hello World Agent

A simple Hello World agent that demonstrates the basic watsonx Orchestrate ADK setup.

## Files

- `agent.yaml` — agent definition
- `../tools/greetings.py` — Python tool used by this agent

## Deploy

```powershell
# From repo root:
orchestrate tools import -k python -f tools/greetings.py
orchestrate agents import -f agents/hello-world/agent.yaml
```

## Test

```powershell
orchestrate chat start
```

Type `Hello` or `Greeting` — the agent will call the tool and respond with `Hello World!`
