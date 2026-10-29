# Traffic Generator — Plan

## Overview

A standalone containerised Python application (`traffic-gen/`) that periodically calls watsonx
Orchestrate agents via the REST API to generate usage data. It runs outside the `wxodemo` CLI
package and has **no import dependency on it**.

Each minute-window it fires exactly one call at a **random second within that window**, so
timing varies naturally from call to call:

1. At the start of each `CALL_INTERVAL_MINUTES`-wide window, draw a random offset in
   `[0, window_seconds - 1]`.
2. Sleep until `window_start + random_offset`.
3. Pick one callable agent and one prompt at random.
4. POST the prompt to the WXO run API.
5. For normal agents: poll for completion and log the outcome.
6. For flow-triggering agents: fire-and-forget (log "sent, not waiting").
7. Sleep until the next window boundary.
8. Any error is printed to stdout; the loop continues to the next window.

Example with `CALL_INTERVAL_MINUTES=1`:
```
00:00 window → fires at 00:25
01:00 window → fires at 01:01
02:00 window → fires at 02:54
03:00 window → fires at 03:38
```

### Auto-discovery on rebuild

The agent pool is derived entirely from the repo's existing YAML files — no hardcoded agent
names or flags anywhere in `app.py`. When a new scenario or standalone agent is added to the
repo, **rebuilding the container is sufficient** to include it:

| Source | What is read |
|---|---|
| `scenarios/*/scenario.yaml` | `smoke_agent` (or first agent) = callable entry point; agents not in `smoke_agent` = excluded sub-agents; `flows: [...]` non-empty = fire-and-forget |
| `standalone/*/agent.yaml` | `name:` field = callable standalone agent |
| `evaluation/*/ground_truth.json` | `smoke_prompts[].prompt` = prompts for scenario agents |
| `traffic-gen/prompts.yaml` | prompts for standalone agents |

### Scope

- **In scope:** Python app, Dockerfile, `prompts.yaml` for standalone agents, env-var config.
- **Out of scope:** deployment automation, metrics backends, dashboards.

### Configuration (all env vars)

| Variable | Default | Description |
|---|---|---|
| `WXO_API_KEY` | required | IBM Cloud or MCSP API key |
| `WXO_URL` | required | `https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>` |
| `WXO_ENV_TYPE` | `ibm_iam` | `ibm_iam` or `mcsp` |
| `CALL_INTERVAL_MINUTES` | `1` | Window size in minutes; one call fires at a random second within each window |
| `AGENT_FILTER` | _(all)_ | Comma-separated agent names to restrict the pool (optional) |

### REST API calls used

| Purpose | Endpoint |
|---|---|
| Get IAM token | `POST https://iam.cloud.ibm.com/identity/token` (or MCSP URL) |
| List agents | `GET {WXO_URL}/v1/orchestrate/agents` → `[{id, name}]` |
| Send prompt | `POST {WXO_URL}/v1/orchestrate/runs` with `{message: {role, content}, agent_id}` |
| Poll for result | `GET {WXO_URL}/v1/orchestrate/runs/{run_id}` |

---

## Sub-Tasks

---

### Sub-Task 1 — `prompts.yaml`: standalone agent prompts

**Status:** `[x] done`

**Intent**
Define a YAML file that maps each standalone agent name to a list of prompts. This is the only
prompt source for standalone agents, and it is the only file that must be updated manually when
a new standalone agent is added. Scenario agent prompts come from `ground_truth.json` and need
no manual entry.

**Expected Outcomes**
- `traffic-gen/prompts.yaml` exists with at least three prompts per standalone agent.
- Format: agent name as key, list of prompt strings as value.
- Adding a new standalone agent only requires adding an entry here and rebuilding.

**Todo List**
1. Create `traffic-gen/prompts.yaml`.
2. For each of the 7 standalone agents add 3–5 realistic prompts drawn from the agent
   descriptions and the existing demo slides in `docs/demo/standalone-agents.js`:
   - `hello_world` — greetings that trigger the greeting tool
   - `document_classifier` — short texts with explicit category lists
   - `information_redactor` — texts containing PII/credentials to redact
   - `metadata_extractor` — unstructured texts with extractable fields specified
   - `priority_assessor` — incidents/complaints to prioritise
   - `translator` — text + target language instructions
   - `travel_rules_qa` — Finnish travel regulation questions

**Relevant Context**
- `docs/demo/standalone-agents.js` contains ready-made example prompts for every agent.
- `standalone/<name>/agent.yaml` describes each agent's capabilities.

---

### Sub-Task 2 — Core Python module (`app.py`)

**Status:** `[x] done`

**Intent**
Write the single-file Python application. Self-contained, stdlib only. Discovers its agent
pool by reading the repo's YAML manifests at startup — no agent names, exclusions, or flags
hardcoded in the source.

**Expected Outcomes**
- `traffic-gen/app.py` exists and is runnable with `python app.py`.
- On startup: authenticates, discovers agents from manifests, looks up IDs from WXO API,
  builds the callable pool, then enters the scheduler loop.
- Every iteration logs to stdout: ISO timestamp, agent name, truncated prompt, outcome or error.
- Errors are caught and printed; the loop never stops.
- Adding a new scenario or standalone agent requires only a container rebuild — zero code changes.

**Todo List**
1. Create `traffic-gen/app.py`.

2. Implement `get_token(api_key, env_type)` — mirrors `src/wxodemo/chats.py:get_token()`.
   Re-fetch proactively every 50 minutes (IAM tokens expire in ~1 hour); also re-fetch on HTTP 401.

3. Implement a minimal `Api` class (GET + POST, Bearer token, retry on 429, raise on other errors).

4. Implement `discover_agents(repo_root)` — reads manifests, returns a list of `AgentSpec`:
   ```
   AgentSpec(name, flow_triggering, prompts)
   ```
   Algorithm:
   a. For each `scenarios/*/scenario.yaml`:
      - Callable agent = `smoke_agent` value if present, else first entry in `agents[]`.
      - All other agents in `agents[]` are sub-agents → excluded from pool.
      - `flow_triggering = len(flows) > 0` (non-empty `flows:` list means fire-and-forget).
      - Prompts: read `evaluation/<id>/ground_truth.json` → `smoke_prompts[].prompt`.
        If the file is missing or has no prompts, skip this agent with a warning.
   b. For each `standalone/*/agent.yaml`:
      - Name = `name:` field.
      - `flow_triggering = False`.
      - Prompts: look up name in `traffic-gen/prompts.yaml`.
        If no prompts found, skip with a warning.
   c. Apply `AGENT_FILTER` (comma-separated names): keep only matching agents if set.
   d. Return the final list.

5. Implement `load_catalog(api, base_url)` — `GET /v1/orchestrate/agents`, returns `{name: id}`.
   Try `/v1/orchestrate/agents` first (same pattern as `src/wxodemo/chats.py:load_catalog()`).

6. Implement `resolve_pool(specs, catalog)`:
   - Match each `AgentSpec` against the WXO catalog by name.
   - Log a warning for any agent in specs but not found in WXO (not deployed).
   - Return only agents present in WXO as `PoolEntry(name, id, flow_triggering, prompts)`.

7. Implement `send_prompt(api, base_url, entry)`:
   - Pick a random prompt from `entry.prompts`.
   - `POST /v1/orchestrate/runs` body: `{"message": {"role": "user", "content": prompt}, "agent_id": entry.id}`.
   - If `flow_triggering=False`: poll `GET /v1/orchestrate/runs/{run_id}` every 5 s, up to 180 s.
     Log terminal status.
   - If `flow_triggering=True`: do not poll. Log "sent (fire-and-forget)".

8. Implement the scheduler loop in `main()`:
   - Read env vars; validate `WXO_API_KEY` and `WXO_URL` are set (exit 1 if not).
   - Locate `repo_root` (probe `Path(__file__).parent / "scenarios"` first, then `parent.parent`).
   - Call `discover_agents(repo_root)`.
   - Authenticate → `get_token(...)`.
   - Call `load_catalog(api, base_url)` and `resolve_pool(specs, catalog)`.
   - Print the active pool at startup.
   - Scheduler loop (window-based jitter):
     ```
     window = CALL_INTERVAL_MINUTES * 60  # seconds
     while True:
         window_start = time.monotonic()
         offset = random.randint(0, window - 1)
         time.sleep(offset)                      # wait random offset within window
         pick entry, call send_prompt, catch/print errors
         elapsed = time.monotonic() - window_start
         time.sleep(max(0, window - elapsed))    # sleep remainder to next boundary
     ```
   - Token refresh check before each call (re-fetch if >50 min since last fetch or on 401).

**Relevant Context**
- Auth: `src/wxodemo/chats.py:48–79`.
- HTTP + retry: `src/wxodemo/chats.py:82–115`.
- Agent catalog: `src/wxodemo/chats.py:421–431`.
- Run creation + polling: `src/wxodemo/smoke.py:161–198`.
- Manifest parsing reference: `src/wxodemo/manifest.py` and `src/wxodemo/discovery.py`
  (do NOT import these — replicate only what is needed).
- `scenario.yaml` `smoke_agent` field: present when the callable agent is not the first listed
  (e.g. `release-readiness`, `hr-tacit-knowledge`). When absent, the first `agents[]` entry is callable.
- `hr-tacit-knowledge` has two independent callable agents (`hr_tk_curator`, `hr_tk_guide`)
  and a `smoke_agent` of `hr_tk_guide`. Only `hr_tk_guide` is the smoke/traffic target.

---

### Sub-Task 3 — Dockerfile

**Status:** `[x] done`

**Intent**
Package the application as a minimal container. The build copies the full set of manifest and
evaluation files so that a rebuild automatically picks up new agents — no code changes required.

**Expected Outcomes**
- `traffic-gen/Dockerfile` builds successfully with `docker build -t traffic-gen .` run from
  the repo root (build context = repo root, not `traffic-gen/`).
- Running the container with the required env vars starts the loop.
- No secrets baked into the image.
- Adding a new scenario = `docker build` only.

**Todo List**
1. Create `traffic-gen/Dockerfile`.
2. Base image: `python:3.11-slim`. No `requirements.txt` needed (stdlib only).
3. `COPY` everything the app reads at runtime:
   - `traffic-gen/app.py` → `/app/app.py`
   - `traffic-gen/prompts.yaml` → `/app/prompts.yaml`
   - `scenarios/` → `/app/scenarios/` (for `scenario.yaml` manifest files)
   - `standalone/` → `/app/standalone/` (for `agent.yaml` name fields)
   - `evaluation/` → `/app/evaluation/` (for `ground_truth.json` prompt files)
4. Set `WORKDIR /app`, `ENV PYTHONUNBUFFERED=1`, `CMD ["python", "app.py"]`.
5. Note in a comment that the build context must be the repo root:
   `docker build -f traffic-gen/Dockerfile -t traffic-gen .`

**Relevant Context**
- `app.py` computes `repo_root = Path(__file__).parent.parent`.
  - Locally: `traffic-gen/app.py` → parent = `traffic-gen/`, parent.parent = repo root. ✓
  - In container: `/app/app.py` → parent = `/app/`, parent.parent = `/`. ✗
  - Fix: inside the container, `scenarios/`, `standalone/`, and `evaluation/` are all placed
    under `/app/`, which is also `Path(__file__).parent`. So `app.py` must detect whether it
    is inside the container (e.g. check if `Path(__file__).parent / "scenarios"` exists and
    use that as `repo_root`, else fall back to `parent.parent`).
  - Simpler: pass the repo root as an env var `REPO_ROOT` (default empty = auto-detect).
    The Dockerfile does not set it; locally it is also not set. Auto-detection:
    try `parent` first, then `parent.parent`.

---

### Sub-Task 4 — README

**Status:** `[x] done`

**Intent**
Document how to build, configure and run the traffic generator.

**Expected Outcomes**
- `traffic-gen/README.md` covers: purpose, env vars, build command, run command, how
  auto-discovery works, how to add a new standalone agent's prompts, `AGENT_FILTER` usage.

**Todo List**
1. Create `traffic-gen/README.md`.
2. Include copy-pasteable `docker build` (from repo root) and `docker run` with all env vars
   as placeholders.
3. Explain the auto-discovery: scenario agents from `scenario.yaml`, standalone agents from
   `agent.yaml`, fire-and-forget detection from `flows:` section.
4. Explain that adding a new scenario agent requires only `docker build`.
5. Explain that adding a new standalone agent requires adding an entry to `prompts.yaml` and
   `docker build`.
6. Document `AGENT_FILTER` and `CALL_INTERVAL_MINUTES`, and explain the jitter behaviour.

---

## Implementation Notes

### Path resolution (local vs container)
`app.py` locates manifest directories by probing:
1. `Path(__file__).parent / "scenarios"` — true inside the container (all files under `/app/`).
2. `Path(__file__).parent.parent / "scenarios"` — true locally (app lives in `traffic-gen/`).

### Token refresh
IAM tokens expire in ~1 hour. Re-authenticate:
- Proactively every 50 minutes (track `token_fetched_at`).
- Reactively on HTTP 401 (one retry per request).

### Stdout log format
```
[2025-11-01T12:00:25Z] incident_triage  "Investigate incident INC-1001 on the..."  → sent (fire-and-forget)
[2025-11-01T12:01:01Z] translator       "Translate to French: Hello, how are yo..."  → completed (42s)
[2025-11-01T12:02:54Z] hello_world      "Hello"  → ERROR: HTTP 503 on /v1/orchestrate/runs
[2025-11-01T12:03:38Z] release_readiness  "Is the release ready to ship?"  → completed (18s)
```

Timestamps reflect the random-offset firing times, not the window boundaries.

### YAML parsing
The app reads YAML using only the stdlib. Scenario and agent YAML files in this repo use only
basic YAML features (mappings, lists, strings), so a minimal hand-rolled parser for the two
patterns needed (key: value and list items) is sufficient — **or** simply rely on the fact
that Python 3.11 ships without PyYAML by default and use `import tomllib` for config if
applicable. Better: detect and use `yaml` if available, else fall back to a minimal regex
parser for the two specific patterns needed (`name:`, `smoke_agent:`, `flows:`, `agents:`).
