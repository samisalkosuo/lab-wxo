# Plan: Traffic Generator — Target the Live Environment

## Top-Level Overview
The WXO Home dashboard (Messages, Feedback, Adoption, etc.) does not change while `traffic-gen`
is running, although Observability / Analytics shows the calls (51 conversations in the last
hour). Working hypothesis: `traffic-gen/app.py` posts runs with only `agent_id`, so runs are
executed against the **draft** agent. Observability shows draft traces, while Home appears to
report production (live) usage only.

The fix is to resolve each agent's `live` environment ID and include `environment_id` in the
`POST /v1/orchestrate/runs` body, with a `WXO_ENVIRONMENT` env var (default `live`) to choose
the target environment.

Non-goals: changes to `wxodemo` CLI, scheduling logic, prompts, or agent discovery.

Hypothesis status: not yet confirmed. Sub-task 1 verifies it before any code is changed.

---

## Sub-Tasks

### Sub-Task 1: Verify the hypothesis against the live WXO instance
- **Intent**: Confirm that (a) agents expose a `live` environment with an ID, and (b) runs sent
  with that `environment_id` increment the Home dashboard. Avoid coding against an unverified assumption.
- **Expected Outcomes**:
  - Known shape of `GET /v1/orchestrate/agents` / `GET /v1/orchestrate/agents/{id}` responses
    (is `environments[]` present in the list response, or only in the by-id response?).
  - Known environment name string for live (e.g. `live`) and how it is represented.
  - Confirmation that a run with `environment_id` of the live env raises the Home message count.
- **Todo List**:
  - [x] Call `GET {WXO_URL}/v1/orchestrate/agents` and inspect one item for `environments[]` (`id`, `name`, `current_version`).
  - [x] If not in the list response, call `GET /v1/orchestrate/agents/{id}` for one agent. (Not needed: list response includes `environments[]`.)
  - [x] Send one manual run with `environment_id` = live env ID; check Home "Messages" and the Analytics page. (Confirmed by user: Home Messages rose by one.)
  - [x] Record the findings in the Notes section of this plan. If the hypothesis is wrong, stop and re-plan.
- **Relevant Context**:
  - `traffic-gen/app.py` — `load_catalog`, `send_prompt`
  - ADK docs: `/apis/agents/get-a-registered-agent-by-id` (`environments[]`), `RunOrchestrate` schema (`environment_id`, `version`)
- **Status**: `[x] done`

---

### Sub-Task 2: Resolve environment IDs and send `environment_id` in runs
- **Intent**: Make the generator target the configured environment (default `live`).
- **Expected Outcomes**:
  - `load_catalog` returns, per agent, the ID plus the environment ID matching `WXO_ENVIRONMENT`.
  - `send_prompt` includes `environment_id` in the run body when one was resolved.
  - Agents with no matching environment are skipped with a warning (not sent to draft silently).
  - Startup pool listing shows the environment name used.
- **Todo List**:
  - [x] Add `WXO_ENVIRONMENT` env var (default `live`; `draft` allowed, meaning omit `environment_id`) in `main()` and the module docstring.
  - [x] Extend `PoolEntry` with `environment_id: str | None` (new `CatalogEntry` holds the agent ID and environments by name).
  - [x] Update `load_catalog` / `resolve_pool` to read `environments[]` (list response includes it; no by-id lookup).
  - [x] Add `environment_id` to the body in `send_prompt` when set.
  - [x] Log a warning and skip agents lacking the requested environment; exit 1 if the pool ends up empty (existing behaviour).
  - [x] Log the target environment at startup (`Target environment: <name>`).
- **Verification**: pool resolution against the real catalog: `live` 17/17 with env IDs, `draft` 17/17 with none, unknown name 0/17 with warnings. `py_compile` OK. Probe scripts removed.
- **Relevant Context**:
  - `traffic-gen/app.py` lines ~384–417 (`load_catalog`, `resolve_pool`), ~424–433 (`send_prompt`), ~488 (`main`)
  - Stdlib-only constraint stays: no new dependencies.
- **Status**: `[x] done`

---

### Sub-Task 3: Documentation and verification
- **Intent**: Keep docs aligned and confirm the Home dashboard now reflects traffic.
- **Expected Outcomes**:
  - `traffic-gen/README.md` documents `WXO_ENVIRONMENT` in the env var table and run examples.
  - `plans/traffic-gen-plan.md` REST calls table and config table mention `environment_id`.
  - After running the generator for a few minutes, Home "Messages" increases (allowing for dashboard refresh delay).
- **Todo List**:
  - [x] Update `traffic-gen/README.md` (env var table, a short note on why live matters for the Home dashboard).
  - [x] Update `plans/traffic-gen-plan.md` (config table, REST calls table).
  - [x] Run the generator against the instance with default settings. (Ran `app.py` locally filtered to `hello_world`: "Target environment: live", run completed in 5s. Home comparison is left to the user.)
  - [ ] Run once with `WXO_ENVIRONMENT=draft` to confirm the override still works. (Not run live; covered by the `resolve_pool` check in Sub-Task 2: draft gives 17/17 with no `environment_id`.)
  - [ ] Rebuild the Docker image (`docker build -f traffic-gen/Dockerfile -t wxo-traffic-gen .`) and smoke-run. (Blocked: `docker` is not installed on this machine. Run it where Docker is available.)
- **Relevant Context**:
  - `traffic-gen/README.md`, `plans/traffic-gen-plan.md`, `traffic-gen/Dockerfile`
- **Status**: `[-] mostly done` (docs updated, live run verified; Docker rebuild and the draft live run remain)

---

## Notes
- Windows console issue (pre-existing, not changed): the `→` in log lines raises a `charmap` error when
  stdout is redirected on Windows, so the result line is lost. Set `PYTHONUTF8=1` locally. The Docker
  image is unaffected (Linux, `PYTHONUNBUFFERED=1`; UTF-8 default).
- Sub-Task 1 findings (probed against the live instance):
  - `GET /v1/orchestrate/agents` already returns `environments[]` per agent, so no per-agent
    by-id lookup is needed. Shape: `{id, name, current_version, voice, semantic_version}`.
  - Environment names are `draft` (`current_version: null`) and `live` (`current_version: 1`).
  - `POST /v1/orchestrate/runs` accepts `environment_id` (live) and completes normally; the run
    GET response carries no environment field, so the effect on Home can only be checked in the UI.
  - Probe scripts: `local/probe_env.py`, `local/probe_run.py` (delete when done).
- Fire-and-forget (flow-triggering) agents still need no polling; `environment_id` applies equally.
- If Home still does not move after the live fix, the cause is likely aggregation delay or a
  different Home data source; investigate before further code changes.
