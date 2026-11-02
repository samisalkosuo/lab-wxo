# Building your own agents with Bob

This repo was built with IBM Bob, and it ships what Bob needs to build more agents the same way: two custom modes, three skills and a connection to the watsonx Orchestrate (WXO) ADK documentation. You do not need Bob to use the samples or to build agents by hand (see [Without Bob](#without-bob)), but it speeds up development a lot and keeps new agents consistent with the existing ones.

## What you get

| Piece | Where | What it does |
|---|---|---|
| **Scenario Builder** mode | [`.bob/custom_modes.yaml`](../.bob/custom_modes.yaml) | Creates a complete demo scenario: mock-data tools, knowledge base, approval flow, agent, manifest, evaluation cases, demo script and slides. |
| **Standalone Builder** mode | [`.bob/custom_modes.yaml`](../.bob/custom_modes.yaml) | Creates a small one-off agent under `standalone/`, with `examples.md`, test cases and an evaluation config. |
| Skill `wxo-scenario-authoring` | [`.bob/skills/`](../.bob/skills/) | What every scenario must contain, the design rules, and the build order. |
| Skill `wxo-adk` | [`.bob/skills/`](../.bob/skills/) | ADK CLI commands, agent YAML and the agent development lifecycle. |
| Skill `scenario-demo-docs` | [`.bob/skills/`](../.bob/skills/) | Templates and consistency checks for the demo script and slides. |
| ADK documentation connection | [`.bob/mcp.json`](../.bob/mcp.json) | Lets Bob look up ADK commands and YAML schemas in the published watsonx Orchestrate ADK documentation before it writes anything. |

The modes load the skills automatically. You only pick a mode and describe what you want.

## Before you start

1. Install Bob and open **this repo as the workspace folder**, so Bob finds the `.bob/` folder.
2. Complete the [deploy steps in the README](../README.md#deploy-to-your-instance) at least as far as `python wxodemo.py doctor`, so Python, the ADK and `env.cfg` are ready. To deploy what Bob builds, run `python wxodemo.py login` too.
3. Select **Scenario Builder** or **Standalone Builder** in Bob's mode selector.

Bob is told never to read or print `env.cfg`, but it can run `wxodemo` commands that use it. Keep `env.cfg` out of anything you paste into a prompt.

## Which mode?

| You want... | Use | Typical size |
|---|---|---|
| A focused agent that does one job (classify, extract, translate, answer from a document) | **Standalone Builder** | One folder, minutes of review |
| A business demo with several tools, a knowledge base, an approval gate, evaluation cases and a presentation | **Scenario Builder** | Many files across `agents/`, `tools/`, `knowledge/`, `flows/`, `scenarios/`, `evaluation/` and `docs/demo/` |

Start with a standalone agent if this is your first time. It is the quickest way to see the whole loop: describe, build, validate, deploy, try.

## How a session goes

1. **Describe** what you want in a prompt (see the samples below). Name the agent or scenario id, say what it must do, what it must refuse, and which tools or knowledge it needs.
2. **Plan.** The Scenario Builder writes a plan file in `plans/<id>-plan.md` first (purpose, target fit, whether it really needs an agent, mock data, tools, knowledge, flow). Read it and correct it before the build. This is the same plan-first workflow you can see in the existing [`plans/`](../plans/) folder.
3. **Build.** Bob creates the files in the order set by the skills: mock data and tools, knowledge base, flow, agent YAML, manifest and evaluation files, demo documents.
4. **Check.** Bob runs the checks listed below and reports what it verified and what it could not (anything that needs a live instance or a browser click).
5. **Deploy and try.** You review the result, deploy it, and chat with it in your WXO instance.

Bob may stop and ask a question, for example if a name clashes with an existing scenario. Answer it rather than letting it guess.

## Sample prompts

These are starting points. They have not been run as written, so expect to adjust them. Copy one into Bob in the matching mode.

### Standalone Builder

**1. Agent with instructions only (no tools)**

```text
Create a standalone agent `meeting-notes-summarizer` that turns pasted meeting notes
into three sections: decisions, action items with an owner and a due date if given,
and open questions. No tools and no knowledge base. If the input is not meeting notes,
politely say so and do not summarize it. Follow the style of the `translator` agent.
```

**2. Agent with a Python tool (deterministic logic)**

```text
Create a standalone agent `unit-converter`. It needs a Python @tool that converts between
common units of length, weight and temperature, because the arithmetic must not be done by
the model. The agent only parses the request, calls the tool and reports the result.
It must refuse units it does not know. Follow the style of `entity-extractor`.
```

**3. Agent with strict JSON output**

```text
Create a standalone agent `sentiment-classifier`. For any pasted text it returns only JSON
with `sentiment` (positive, neutral or negative), `confidence` (0 to 1) and a one-sentence
`reason`. If no text is given, it asks for it. Follow the style of `document-classifier`.
```

### Scenario Builder

Keep the first scenario small: two or three tools, at most one knowledge base and at most one approval flow.

**1. Read-only scenario (smallest, no flow)**

```text
Create a read-only scenario `parcel-tracking`. A customer-service agent answers "where is
my parcel?" questions. Two mock tools: `parcel_get_shipment` (status and location by
tracking number) and `parcel_get_delivery_estimate`. One short knowledge base with a
delivery FAQ (delays, lost parcels, address changes). No write actions, so no flow.
Industry: logistics. Function: customer service. Target role: customer service agent.
```

**2. Scenario with an approval gate**

```text
Create a scenario `laptop-refresh`. An IT service desk agent checks whether an employee is
eligible for a laptop refresh. Two mock read tools (`lr_get_device`, `lr_check_eligibility`),
one small knowledge base with the refresh policy, and one approval flow that a manager
completes before a mock write tool `lr_order_laptop` runs. The agent must not have the write
tool directly. Industry: cross-industry. Function: IT. Target role: IT service desk analyst.
```

**3. Scenario where part of the work is a flow, not an agent**

```text
Create a scenario `room-booking`. Mock tools: `rb_list_rooms`, `rb_check_availability`,
`rb_book_room`. Booking changes state, so put `rb_book_room` behind a confirmation flow.
In the plan, explain which part needs an agent and which part is a fixed sequence that
belongs in the flow. Industry: cross-industry. Function: facilities. Target role: office
administrator.
```

### Review and extend

```text
Review the `incident-triage` scenario against the wxo-scenario-authoring skill and list any gaps.
```

```text
Add an example prompt that tests the refusal path to the `translator` agent: update examples.md and add a test case.
```

```text
Explain how the `release-readiness` supervisor agent calls its collaborator agents, and what I would change to add a fourth specialist.
```

## Tips for good prompts

- **Name things.** Give the id (`kebab-case`) and, for tools, the names you want. Prefix tool and knowledge-base names with the scenario (for example `lr_`). They are shared across the whole WXO instance, so clashes overwrite each other.
- **Say what it must refuse.** Out-of-scope requests and prompt injection are the cases that go wrong first.
- **Put calculations in tools.** If a number must be exact, ask for a Python tool. The repo's samples do this on purpose.
- **Never give an agent a write tool directly.** Ask for the write action to sit behind a flow with a human approval step. Both modes are instructed to do this.
- **Point at an example.** "Follow the style of `translator`" is more precise than a long description.

## What to check afterwards

Bob runs these itself. Run them again before you deploy, and read any problem they report.

**Standalone agent**

```bash
python wxodemo.py list --kind standalone          # is the agent discovered?
python wxodemo.py test-upload <name> --dry-run    # are the test cases found?
python wxodemo.py deploy <name> --dry-run         # do the deploy commands look right?
```

**Scenario**

```bash
python wxodemo.py validate <id>                   # manifest, evaluation files and demo consistency; must print OK
python wxodemo.py smoke <id> --dry-run            # are the smoke prompts present and well formed?
python wxodemo.py eval <id> --dry-run             # is the evaluation config valid?
```

Then deploy and try it:

```bash
python wxodemo.py login
python wxodemo.py deploy <name or id>
python wxodemo.py status <name or id>             # confirm what is live
```

A new scenario starts with `status: soon` in its manifest, and `deploy --all` skips `soon` scenarios. Name the scenario to deploy it (`python wxodemo.py deploy <id>`), and change the status to `live` once you are happy with it. Full command reference: [`wxodemo.md`](wxodemo.md).

## Review what Bob produces

Bob can be wrong, and a generated agent is only a draft until you have tried it.

- Read the agent instructions and the tool code. Check that the agent does only what you asked.
- Chat with the deployed agent. Try the normal path, a refusal and a vague request.
- For flows, test **Approve** and **Reject** in the WXO browser chat. The evaluation cannot press those buttons.
- Do not put results in READMEs or demo scripts unless you saw them in a real run. The modes are instructed not to claim that something "passes" or "works" without a recorded run, so hold the generated text to that rule.
- Add the new agent to the tables under [What is included](../README.md#what-is-included) in the README.

## Without Bob

Everything the modes do can be done by hand with the same commands.

- **Standalone agent:** copy the closest sample from [Learn by example](../README.md#learn-by-example) and follow [`standalone/README.md`](../standalone/README.md). `wxodemo` discovers any folder under `standalone/` that has an `agent.yaml`.
- **Scenario:** scaffold with `python wxodemo.py new-scenario <id> --name "..." --description "..."`, build the pieces, list them in `scenarios/<id>/scenario.yaml`, and run `python wxodemo.py validate <id>`. [`scenarios/incident-triage/scenario.yaml`](../scenarios/incident-triage/scenario.yaml) documents every field, and the skill files in [`.bob/skills/`](../.bob/skills/) are plain Markdown you can read as a checklist.
- ADK documentation: <https://developer.watson-orchestrate.ibm.com>
