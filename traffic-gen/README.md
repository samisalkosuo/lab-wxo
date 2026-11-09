# WXO Traffic Generator

Standalone containerised Python application that periodically calls deployed watsonx Orchestrate
agents via the REST API to generate realistic usage data on a WXO instance.

**What it is for.** A freshly deployed instance has an empty Home dashboard and empty
Observability and Analytics pages. Run the generator for a while before a demo and those pages
show realistic traffic: messages, adoption, tool calls and run durations.

**What it does not do.** It does not deploy anything and it does not answer approval forms.
Agents that start an approval flow are sent a prompt and left waiting (see "How it works").

## Quick start

1. Deploy the agents you want traffic for (see the root [`README.md`](../README.md#deploy-to-your-instance)).
   Only deployed (`live`) agents receive traffic; others are skipped with a warning.
2. Ensure `env.cfg` is configured in the repository root.
3. Build and start using `wxodemo.py traffic`:

   ```bash
   python wxodemo.py traffic build     # builds wxo-traffic-gen image (auto-detects podman/docker)
   python wxodemo.py traffic start     # starts in background using env.cfg credentials
   python wxodemo.py traffic logs      # follow live log output (Ctrl+C to stop)
   python wxodemo.py traffic stop      # stop when done
   ```

You can also run container commands directly with `podman` or `docker` (see [Standalone Container Usage](#standalone-container-usage) below).

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

- Docker or Podman. The commands below use `docker`; with Podman, replace `docker` with
  `podman`. With Podman 6.1.4 the image builds, and the container starts and stops with the
  message `WXO_API_KEY is not set` when no key is given. A full container run against a real
  instance has not been verified.
- A WXO instance with agents deployed (see the quick start).
- A WXO API key and instance URL (IBM Cloud IAM or MCSP; see `WXO_ENV_TYPE` below).
- No Python install is needed on your machine. Python runs inside the container.

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
| `WXO_API_KEYS_FILE` | no | _(unset)_ | Path inside the container to a CSV of extra users (`user,api_key`). See "Multiple users" below |

### Why `live` is the default

Runs sent without an `environment_id` execute against the **draft** agent. Draft runs appear in
Observability / Analytics, but the WXO **Home** dashboard (Messages, Adoption, …) only counts
**live** usage. The generator therefore looks up each agent's `live` environment ID from
`GET /v1/orchestrate/agents` and sends it as `environment_id`. Agents without a live
environment are skipped with a warning. Set `WXO_ENVIRONMENT=draft` to omit `environment_id`
and exercise the draft agents instead.

---

## Multiple users

By default every call uses the single `WXO_API_KEY`, so usage data shows one user. To spread traffic
across several users, list extra API keys in a CSV. Each call then picks a **random user** from the pool.

Copy [`api-keys.csv.example`](../api-keys.csv.example) to `api-keys.csv` in the repository root
(the file is gitignored because it holds secrets) and edit it:

```csv
# Extra users for the traffic generator. Lines starting with # and blank lines are ignored.
user,api_key
alice,<alice-api-key>
bob,<bob-api-key>
```

- The header needs an `api_key` column; the `user` column is optional. A blank user becomes `user-N`
  (N = data row number). Rows with an empty key are skipped with a warning.
- The `WXO_API_KEY` from `env.cfg` is **always in the pool**, labelled `default`. A CSV row with the same
  key is dropped, and duplicate user labels get a `-2`, `-3` suffix.
- Keys that fail the token exchange at startup are dropped with a warning. If none are valid, the app exits with an error.
- Logs show the **user label**, never the key. Log lines are prefixed with `[user]` only when the CSV added users.
- If `WXO_API_KEYS_FILE` is unset, missing or unreadable, only `WXO_API_KEY` is used.
- The CSV is read once at startup. **Restart the container** (`traffic restart`) after editing it.

`python wxodemo.py traffic start` / `redeploy` mount `api-keys.csv` read-only at `/app/api-keys.csv` and set
`WXO_API_KEYS_FILE` automatically when the file exists. The CSV is never copied into the image.
With a manual `docker run`, mount it yourself (see [Run](#run)).

---

## CLI commands (via wxodemo)

`wxodemo traffic` manages the container lifecycle and credentials automatically:

```bash
# Build / rebuild image
python wxodemo.py traffic build [--no-cache] [--engine podman|docker]

# Start in background
python wxodemo.py traffic start [--interval MIN] [--agents A1,A2] [--env live|draft] [-f]

# Check container and image status
python wxodemo.py traffic status

# Follow logs (default) or tail last N lines (Ctrl+C to stop)
python wxodemo.py traffic logs
python wxodemo.py traffic logs -n 50

# Stop and remove container
python wxodemo.py traffic stop

# Rebuild and restart in one command
python wxodemo.py traffic redeploy

# Preview discovered agent pool and prompts
python wxodemo.py traffic pool [--agents A1,A2] [--json]
```

---

## Standalone Container Usage

If you prefer to invoke Podman or Docker directly without `wxodemo`, run the commands from the **repository root**:

### Build

```bash
# Using Docker
docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen .

# Or using Podman
podman build -f traffic-gen/Dockerfile -t wxo-traffic-gen .
```

### Run

```bash
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.eu-de.watson-orchestrate.cloud.ibm.com/instances/your-instance-id \
  -e WXO_ENV_TYPE=ibm_iam \
  -e CALL_INTERVAL_MINUTES=1 \
  wxo-traffic-gen
```

To send runs to draft agents instead of live:

```bash
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.eu-de.watson-orchestrate.cloud.ibm.com/instances/your-instance-id \
  -e WXO_ENVIRONMENT=draft \
  wxo-traffic-gen
```

To use several users, mount the CSV read-only and point `WXO_API_KEYS_FILE` at it:

```bash
docker run --rm \
  -e WXO_API_KEY=your-api-key-here \
  -e WXO_URL=https://api.eu-de.watson-orchestrate.cloud.ibm.com/instances/your-instance-id \
  -v "$(pwd)/api-keys.csv:/app/api-keys.csv:ro" \
  -e WXO_API_KEYS_FILE=/app/api-keys.csv \
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

Inside the container, the application uses Python 3.11 stdlib only (`urllib`, `json`, `random`, `time`,
`pathlib`, `dataclasses`). No `pip install` step is needed.
