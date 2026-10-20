# hello_world — ADK Setup Check Agent

## Purpose

`hello_world` is the smallest possible agent. It proves the watsonx Orchestrate ADK
setup works end to end: the environment is active, a Python tool imports, a native
agent imports, and the agent calls the tool.

**What this agent does:**
- Calls the `greeting` tool when the user types "Hello" or "Greeting" and replies
  `Hello World!`.
- For any other input, answers helpfully and says it can greet the user.

**What this agent does not do:**
- Anything beyond greeting. It is a setup check, not a demo.

## Files

- `agent.yaml` — agent definition
- `greetings.py` — the `greeting` Python tool (imported by `wxodemo` before the agent)
- `examples.md` — example prompts

## Dependencies

None beyond an active WXO environment. The agent uses the model
`groq/openai/gpt-oss-120b`, which must be available in the target instance
(`orchestrate models list`).

## Deploy

Run from the **repo root** with the virtual environment activated:

```bash
python wxodemo.py deploy hello_world

# Or manually:
orchestrate tools import -k python -f standalone/hello-world/greetings.py
orchestrate agents import --file standalone/hello-world/agent.yaml
orchestrate agents deploy --name hello_world
```

Re-running import is safe — it updates in place.

## Test

```powershell
orchestrate chat start
```

Type `Hello` or `Greeting` — the agent calls the tool and responds with `Hello World!`.

## Teardown

```bash
python wxodemo.py undeploy hello_world

# Or manually:
orchestrate agents remove --name hello_world --kind native
orchestrate tools remove --name greeting
```

## Known limits

| Limit | Detail |
|---|---|
| Prompt-based trigger | The "Hello" / "Greeting" trigger is enforced by the LLM following the instructions, not by code. |
| Draft agents | On Developer Edition `orchestrate agents deploy` may fail; the agent then stays a draft. |

## Examples

See [`examples.md`](examples.md).
