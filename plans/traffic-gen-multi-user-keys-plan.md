# Traffic Generator: Multi-User API Keys Plan

## Overview

Today the traffic generator ([`traffic-gen/app.py`](../traffic-gen/app.py)) authenticates with a single
`WXO_API_KEY` (from `env.cfg`, passed by `python wxodemo.py traffic start` as a container env var). Usage data
therefore shows one user only.

Goal: let the generator pick a **random user (API key) per call** from a CSV list, so WXO usage/analytics show
traffic from several users. If no CSV is available, behaviour stays exactly as it is now (single key from `env.cfg`).

Approach (decisions confirmed with user):
- CSV file `api-keys.csv` in repo root, header `user,api_key`, gitignored (it holds secrets). Ship an `api-keys.csv.example`.
- The CSV is **mounted read-only at runtime** into the container; it is never copied into the image.
  The host CLI sets env var `WXO_API_KEYS_FILE` to the in-container path.
- Random key chosen **per call** (not per window / not per process).
- The `env.cfg` key (`WXO_API_KEY`) is **always part of the random pool**, labelled `default`; CSV users are added to it.
- Fallback: CSV absent (or no usable rows) -> pool is just the `env.cfg` key, as now.

Working assumptions (flag if wrong):
- The env.cfg key is always included in the pool together with the CSV users (user label `default`); if a CSV
  row has the same key as env.cfg, it is de-duplicated.
- Startup catalog lookup (`GET /v1/orchestrate/agents`) uses the env.cfg key's user (`default`) if valid, otherwise
  the first valid user. All users are assumed to
  have access to the same agents in the instance; a user lacking access to an agent will just log an ERROR on
  that call (existing error path in `send_prompt`).
- Keys that fail the token exchange at startup are dropped with a warning (user label only, never the key);
  if none remain, the generator exits with an error. Keys are validated once at startup; runtime 401s are
  handled by the existing per-key token refresh.
- Logs show the **user label**, never the key. Keys are registered with `register_secret` on the host side.

## Sub-Tasks

### 1. Container app: multi-key support
**Intent** Make `app.py` load a list of (user, key) pairs and use a random one per call, with one `TokenManager` per key.

**Expected Outcomes**
- With `WXO_API_KEYS_FILE` set and readable, each scheduled call uses a randomly chosen user; log line includes the user label.
- Without it, behaviour and log output are as before (single key, `WXO_API_KEY` required).
- Bad rows / failing keys are skipped with warnings; zero valid keys -> clear error and exit 1.

**Todo List**
1. Add a stdlib CSV loader (`csv` module) returning `[(user, api_key)]`; tolerate BOM, blank lines, `#` comment lines; skip rows with empty key; default user label to `user-N` if blank.
2. Keep `WXO_API_KEY` required (it is always in the pool); add the `default` user for it, de-duplicate against CSV keys; update the module docstring env-var list.
3. Build a `{user: TokenManager}` map; validate each at startup via `tokens.get()`; drop failures with a warning.
4. Make `Api` accept the `TokenManager` per request (or create one `Api` per user) so `send_prompt` can be called with a randomly chosen user; use the first valid user for `load_catalog`.
5. In the scheduler loop pick `random.choice(users)` per call and include the user label in `send_prompt` log lines.
6. Log at startup: number of users loaded and their labels (not keys).

**Relevant Context**
- [`traffic-gen/app.py`](../traffic-gen/app.py): `TokenManager`, `Api`, `send_prompt`, `main` (scheduler loop ~L595-609), `_fetch_token`.
- Stdlib-only constraint documented in the module docstring; `csv` is stdlib.

**Status** `[x] done`

**Implementation notes (for later sub-tasks)**
- New in [`traffic-gen/app.py`](../traffic-gen/app.py): `DEFAULT_USER = "default"`, `load_api_keys_csv(path: Path) -> list[(user, key)]`
  (header must contain an `api_key` column, `user` column optional; BOM/blank/`#` lines tolerated; empty-key rows skipped with a warning;
  blank user -> `user-N`, N = 1-based data row), `build_user_keys(default_key, csv_keys)` (env key first as `default`; CSV rows with a
  duplicate key are dropped; duplicate labels get a `-2`, `-3` suffix). `send_prompt(api, base_url, entry, user=None)` gained an optional
  `user` arg that prefixes log lines with `[user] `.
- `main()` reads env var `WXO_API_KEYS_FILE`; a missing/unreadable file -> warning and `WXO_API_KEY` only (does not exit). One `Api`/`TokenManager`
  per user in `apis: dict[str, Api]`; failing keys are dropped with a warning (label only); none valid -> exit 1. Catalog uses `default` else the first valid user.
  Startup logs `Token obtained. Users in pool (N): a, b, ...`. `random.choice(users)` per call.
- Log lines are prefixed with `[user]` only when the CSV yielded rows (`csv_keys` non-empty); with no CSV, log output is unchanged.
- **Expected in-container CSV path: `/app/api-keys.csv`** (Dockerfile `WORKDIR /app`; Sub-task 2 must mount it read-only and set
  `WXO_API_KEYS_FILE=/app/api-keys.csv`; no COPY of the CSV).
- Existing tests (`python -m pytest tests`): 409 passed. No existing test imports `app.py` (use `importlib`/`sys.path` insert of `traffic-gen/` in Sub-task 4);
  the loader and `build_user_keys` are plain functions with no network, so they are directly testable.

### 2. Host CLI: mount CSV on `traffic start`
**Intent** Have `wxodemo traffic start` / `redeploy` pass the CSV to the container when it exists.

**Expected Outcomes**
- If `<repo>/api-keys.csv` exists, the container command includes a read-only volume mount and `-e WXO_API_KEYS_FILE=/app/api-keys.csv`.
- If it does not exist, the command is unchanged from today.
- `--dry-run` output shows the mount but not key values; the CLI prints an info line such as "Using N users from api-keys.csv" (count only).
- Optional override of the CSV path via a `--keys-file` flag on `start`/`redeploy` (only if cheap; otherwise default path only).

**Todo List**
1. In `run_traffic_start` ([`src/wxodemo/traffic.py`](../src/wxodemo/traffic.py) ~L285-362) detect `root / "api-keys.csv"`; add `-v <abs path>:/app/api-keys.csv:ro` and the env var to `cmd`.
2. Count rows (header-aware) for the info message; register each key with `register_secret` so logs/dry-run mask them.
3. Verify Windows path handling for the `-v` argument with podman and docker (absolute host path, drive letter colon). Add `:Z` only if needed for SELinux/podman; confirm during testing.
4. If adding `--keys-file`, wire it in `cmd_traffic` and the `start`/`redeploy` parsers in [`src/wxodemo/cli.py`](../src/wxodemo/cli.py) (~L242-285, L416-477).
5. Make `config` optional behaviour unchanged (`config is None` dry-run path still works).

**Relevant Context**
- `run_traffic_start`, `run_traffic_redeploy`, `register_secret` import in `traffic.py`.
- [`src/wxodemo/cli.py`](../src/wxodemo/cli.py) `cmd_traffic`, `start`/`redeploy` subparsers.

**Status** `[x] done`

**Implementation notes**
- [`src/wxodemo/traffic.py`](../src/wxodemo/traffic.py): new `API_KEYS_FILENAME`, `API_KEYS_CONTAINER_PATH` (`/app/api-keys.csv`) and
  `read_api_keys_csv(path) -> list[str]` (header-aware; BOM/blank/`#` lines and empty keys skipped; no `api_key` header -> `[]`).
- `run_traffic_start` checks `root / "api-keys.csv"`; if present it registers every key with `register_secret`, prints
  `Using N users from api-keys.csv` (count only; N = CSV rows, the `default` env.cfg user is not counted) and appends
  `-v <resolved abs host path>:/app/api-keys.csv:ro -e WXO_API_KEYS_FILE=/app/api-keys.csv` before the image name.
  Unreadable CSV -> warning and command unchanged. Absent CSV -> command unchanged. Works in `--dry-run` (verified manually: no key values printed).
  `redeploy` gets this for free since it calls `run_traffic_start`.
- Windows path: the native resolved path (`C:\...\api-keys.csv`) is passed as a single list argument (no shell), so docker/podman split on the
  container-side colon correctly. Not verified against a real engine; no `:Z` added (add only if SELinux/podman on Linux needs it).
- `--keys-file` flag skipped (not requested). `config is None` dry-run path unchanged.
- `python -m pytest tests`: 409 passed. Sub-task 4 should cover CSV present/absent (use `tmp_path` as `root`, patch `find_container_engine`,
  call `setup_logging` or capture output) and assert key values never appear in captured output/command.

### 3. Repo hygiene and example file
**Intent** Keep secrets out of git and document the format.

**Expected Outcomes**
- `api-keys.csv` ignored by git; `api-keys.csv.example` committed with placeholder rows.

**Todo List**
1. Add `api-keys.csv` to [`.gitignore`](../.gitignore) and un-ignore `!api-keys.csv.example`.
2. Create `api-keys.csv.example` (`user,api_key` header + 2 placeholder rows).

**Relevant Context** `.gitignore` "Environment & Secrets" section; [`env.cfg.example`](../env.cfg.example) as the pattern.

**Status** `[x] done`

**Implementation notes**
- [`.gitignore`](../.gitignore) "Environment & Secrets": added `api-keys.csv` and `!api-keys.csv.example` after `!.env.example`.
- [`api-keys.csv.example`](../api-keys.csv.example): `#` comment line (the app loader and `read_api_keys_csv` both skip `#` lines), header `user,api_key`, two placeholder rows (`alice`, `bob`).
- Verified with `git check-ignore -v api-keys.csv api-keys.csv.example`: the real file matches the ignore rule, the example matches the `!` negation (not ignored; shows as untracked in `git status`).

### 4. Tests
**Intent** Cover the new logic without hitting the network.

**Expected Outcomes**
- Tests for CSV mount present/absent in `run_traffic_start` (dry-run command assertions) and that key values never appear in output.
- Tests for the `app.py` CSV loader (BOM, comments, blank/missing key, missing file fallback) and per-call user selection.

**Todo List**
1. Extend [`tests/test_traffic.py`](../tests/test_traffic.py) (existing `run_traffic_start` tests ~L130, L171) with CSV-present / CSV-absent cases.
2. Add loader tests; import `traffic-gen/app.py` via `importlib` if existing tests don't already do so (check the file first).
3. Run the project test suite and lint.

**Status** `[x] done`

**Implementation notes**
- [`tests/test_traffic.py`](../tests/test_traffic.py): `read_api_keys_csv` tests (BOM/comments/blank/empty key, no header, empty file) and `run_traffic_start`
  dry-run tests via helper `_dry_run_start`: CSV absent (no `-v`, no `WXO_API_KEYS_FILE`), present (`-v <abs>:/app/api-keys.csv:ro`, env var,
  `Using 2 users from api-keys.csv`, image last, no key values in output), unreadable (non-UTF-8) and no-header CSV.
- [`tests/test_traffic_app.py`](../tests/test_traffic_app.py) (new): loads `traffic-gen/app.py` via `importlib` from its file path. Covers `load_api_keys_csv`,
  `build_user_keys`, `send_prompt` user label (fake `Api`), and `main()` offline (fakes `TokenManager`, `discover_agents`, `load_catalog`, `resolve_pool`,
  `send_prompt`; a `BaseException` stops the loop): random user per call, unlabelled single-user fallback, missing CSV fallback, failing keys dropped,
  catalog user fallback, all-failing -> exit 1; no key values in output.
- `python -m pytest tests`: 434 passed. `ruff check` clean on the two traffic test files (pre-existing ruff errors remain in other test files; untouched).

### 5. Documentation
**Intent** Document the feature for users.

**Todo List**
1. [`traffic-gen/README.md`](../traffic-gen/README.md): env var table (~L70) add `WXO_API_KEYS_FILE`; CSV format, mount example for manual `docker run`, fallback behaviour.
2. [`docs/wxodemo.md`](../docs/wxodemo.md) traffic section: mention `api-keys.csv`.
3. Update the Dockerfile header run example comment only if it helps ([`traffic-gen/Dockerfile`](../traffic-gen/Dockerfile)); no COPY changes (keys are mounted, not baked).

**Status** `[x] done`

**Implementation notes**
- [`traffic-gen/README.md`](../traffic-gen/README.md): `WXO_API_KEYS_FILE` row in the env var table, new "Multiple users" section (CSV format, `default` env.cfg user,
  dedupe/labels, fallback, restart after editing, auto-mount by `traffic start`/`redeploy`), and a manual `docker run` example with `-v ...:/app/api-keys.csv:ro`.
- [`docs/wxodemo.md`](../docs/wxodemo.md) traffic section: "Multiple users" paragraph (gitignored `api-keys.csv`, `api-keys.csv.example`, auto-mount, count-only message).
- [`traffic-gen/Dockerfile`](../traffic-gen/Dockerfile): header comment only with the mount example; no COPY changes.

## Out of scope
- Per-user agent permission checks or catalog per user.
- Weighted/sticky user selection, key rotation while running (restart the container after editing the CSV).
- Changing how other `wxodemo` commands authenticate.
