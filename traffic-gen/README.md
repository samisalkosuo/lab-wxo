# WXO Traffic Generator

Standalone containerised Python application that periodically calls deployed watsonx Orchestrate
agents via the REST API to generate realistic usage data on a WXO instance.

---

## How it works

One agent call fires per interval window, at a **random second within that window**:

```
window 00:00 → fires at 00:25
window 01:00 → fires at 01:01
window 02:00 → fires at 02:54
window 03:00 → fires at 03:38
```

Each iteration picks an agent and a prompt at random from the active pool, POSTs to the WXO
run API (targeting the agent's `live` environment by default), and logs the result to stdout.
Errors are printed but never stop the loop.

**Flow-triggering agents** (those whose scenario defines approval flows) are sent via
fire-and-forget: the request is sent but the app does not wait for the run to complete,
because those runs block on a human approval form.

All other agents are polled until the run reaches a terminal status or a 3-minute timeout.

---

## Prerequisites

- Docker (or compatible container runtime)
- A WXO instance with agents deployed
- An IBM Cloud API key (IAM) or MCSP API key

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `WXO_API_KEY` | yes | — | IBM Cloud or MCSP API key |
| `WXO_URL` | yes | — | `https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>` |
| `WXO_ENV_TYPE` | no | `ibm_iam` | `ibm_iam` (IBM Cloud) or `mcsp` (AWS-hosted) |
| `CALL_INTERVAL_MINUTES` | no | `1` | Window size in minutes; one call fires per window at a random second |
| `AGENT_FILTER` | no | _(all)_ | Comma-separated agent names to restrict the pool, e.g. `incident_triage,hello_world` |
| `WXO_ENVIRONMENT` | no | `live` | Agent environment that runs are sent to: `live` or `draft`. See below |

### Why `live` is the default

Runs sent without an `environment_id` execute against the **draft** agent. Draft runs appear in
Observability / Analytics, but the WXO **Home** dashboard (Messages, Adoption, …) only counts
**live** usage. The generator therefore looks up each agent's `live` environment ID from
`GET /v1/orchestrate/agents` and sends it as `environment_id`. Agents without a live
environment are skipped with a warning. Set `WXO_ENVIRONMENT=draft` to omit `environment_id`
and exercise the draft agents instead.

---

## Build

The build context **must be the repository root**, not the `traffic-gen/` directory.
The Dockerfile copies `scenarios/`, `standalone/`, and `evaluation/` from the repo root
so that the container picks up manifests and prompts automatically.

```bash
docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen .
```

---

## Run

```bash
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.eu-de.watson-orchestrate.cloud.ibm.com/instances/your-instance-id \
  -e WXO_ENV_TYPE=ibm_iam \
  -e CALL_INTERVAL_MINUTES=1 \
  wxo-traffic-gen
```

To send runs to the draft agents instead of live:

```bash
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.eu-de.watson-orchestrate.cloud.ibm.com/instances/your-instance-id \
  -e WXO_ENVIRONMENT=draft \
  wxo-traffic-gen
```

To restrict the pool to specific agents:

```bash
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.eu-de.watson-orchestrate.cloud.ibm.com/instances/your-instance-id \
  -e AGENT_FILTER=incident_triage,hello_world,translator \
  wxo-traffic-gen
```

`CALL_INTERVAL_MINUTES` can be changed without rebuilding — pass it at `docker run` time.

---

## Agent pool

The pool is built automatically at container startup from three sources:

| Source | What is read |
|---|---|
| `scenarios/*/scenario.yaml` | `smoke_agent` (or first agent listed) = callable entry point |
| `standalone/*/agent.yaml` | `name:` field = callable standalone agent |
| `evaluation/*/ground_truth.json` | `smoke_prompts[].prompt` = prompts for scenario agents |
| `traffic-gen/prompts.yaml` | prompts for standalone agents |

**Sub-agents are excluded automatically.** Any agent listed in a `scenario.yaml` that is
not the `smoke_agent` (e.g. `rr_qa`, `rr_security`, `rr_ops` for the Release Readiness
scenario) is treated as a collaborator and excluded from the pool.

**Flow-triggering agents are detected automatically.** If a `scenario.yaml` has a non-empty
`flows:` list, its callable agent is marked fire-and-forget.

On startup the app prints the active pool with agent IDs and prompt counts so you can
verify which agents were found and matched to live WXO deployments.

---

## Adding a new scenario agent

1. Add the scenario to the repo following the normal process (scenario manifest, agent YAML,
   `evaluation/<id>/ground_truth.json` with `smoke_prompts`).
2. Rebuild the container: `docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen .`

No code changes needed.

---

## Adding a new standalone agent

1. Add the agent to `standalone/<name>/agent.yaml` as usual.
2. Add an entry to `traffic-gen/prompts.yaml`:
   ```yaml
   your_agent_name:
     - "First example prompt for this agent."
     - "Second example prompt."
     - "Third example prompt."
   ```
3. Rebuild the container.

---

## Stdout log format

```
[2025-11-01T12:00:25Z] incident_triage                  "Investigate incident INC-1001 on the..."  → sent (fire-and-forget)
[2025-11-01T12:01:01Z] translator                        "Translate 'Our quarterly results are i..."  → completed (38s)
[2025-11-01T12:02:54Z] hello_world                       "Hello"  → completed (4s)
[2025-11-01T12:03:38Z] release_readiness                 "Is the release ready to ship?"  → completed (22s)
[2025-11-01T12:04:15Z] document_classifier               "Classify this customer ticket into [Bi..."  → error (timeout)
```

Timestamps reflect the actual fire time (random within the window), not the window boundary.
Warnings about skipped agents (not deployed, missing prompts) are also printed to stdout.

---

## No external dependencies

The application uses Python 3.11 stdlib only (`urllib`, `json`, `random`, `time`,
`pathlib`, `dataclasses`). No `pip install` step is needed.
