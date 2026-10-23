# wxodemo CLI Consolidation Plan

## Top-Level Overview

**Goal.** Replace the ~14 scattered PowerShell/bash/Python helper scripts with one idempotent Python CLI, `wxodemo`, so a developer can get from clone to deployed agents in a few commands.

**Scope (confirmed with user).**
- Absorb everything: activation/login, deploy/undeploy for scenarios and standalone agents, chat export, smoke test, new-scenario scaffold, manifest validation, demo-consistency check.
- Delete all old `.ps1`/`.sh` scripts, `standalone/manage.py`, and the old `scripts/*.py` after migration.
- Package lives in `src/wxodemo/`, is pip-installable (`pip install -e .` gives a `wxodemo` command), and a thin root `wxodemo.py` keeps `python wxodemo.py ...` working.
- Python venv is **optional but recommended**. The tool never creates, detects or activates a venv. It uses whichever interpreter launched it. The README's first step is the manual venv creation.
- WXO login is done by the tool (`orchestrate env add` + `env activate --api-key`). Config persists in `~/.config/orchestrate`, so it survives the script exiting.
- `env.cfg` is mandatory. The tool never prompts. Missing file or missing/empty values give a clear error (exit code 2) listing what is needed.
- Console output is short and friendly. Detailed output (full commands with secrets masked, stdout/stderr, timings) goes to a log file. The log file is git-ignored.
- README becomes a quick start. Detailed reference goes in `docs/wxodemo.md`.

**Non-goals.**
- No auto venv handling, no interactive prompts for credentials.
- No new deploy semantics. The dependency order stays connections, tools, knowledge bases, flows, agents, then agent promotion.
- No change to agent, tool or flow content.

**Command surface (all idempotent; mutating commands support `--dry-run`).**

| Command | Purpose | Replaces |
|---|---|---|
| `setup` | `pip install -r requirements.txt` with the current interpreter, warn (but continue) if not in a venv, then run `doctor` | pip part of `activate-lab-wxo.*` |
| `doctor` | Check Python version, ADK and PyYAML importable, `orchestrate` found, `env.cfg` keys, active WXO env | new |
| `login` (alias `activate`) | `env add` + `env activate` from `env.cfg` | `activate-wxo.*` |
| `list` | Scenarios and standalone agents, with kind and status | `scenario_manifest.py list`, `manage.py list` |
| `status` | What the repo defines vs. what is deployed in WXO | new |
| `deploy [names...] / --all [--kind]` | Deploy in dependency order; auto-login first | `deploy-all.*`, `manage.py deploy` |
| `undeploy [names...] / --all [--kind]` | Reverse order, confirmation `[y/N]` unless `--yes`; non-TTY without `--yes` fails | `teardown.*`, `manage.py undeploy` |
| `validate [name]` | Manifest validation and demo-consistency checks | `scenario_manifest.py validate`, `check_demo_consistency.py` |
| `smoke <scenario>` | Send smoke prompts to the deployed agent | `smoke_test.py` |
| `export-chats` | Export chats and traces | `export_agent_chats.py` |
| `new-scenario <id>` | Scaffold a scenario | `new-scenario.py` |
| `eval <scenario>` | Run the ADK evaluation for a scenario | README command `orchestrate evaluations evaluate` |
| `logs [--tail N]` | Show log path / last lines | new |

**Target addressing.** Unified names: a name resolves to a scenario or a standalone agent. `--kind scenario|standalone` filters `--all` and disambiguates a name that matches both kinds.

**Undeploy safety.** Explicit targets or `--all` are required. The tool prints what will be removed, then asks `[y/N]` unless `--yes` is given. `--dry-run` only previews. A non-TTY run without `--yes` fails.

**Key design rules.**
- stdlib-only for CLI parsing (argparse), config, logging, `setup`, `doctor`, so these work before anything is installed. PyYAML and ADK imports are lazy and only for commands that need them.
- ADK discovery: look for `orchestrate` next to `sys.executable`, then fall back to `PATH`. Subprocesses get `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` (Windows encoding issue handled today by the `.ps1` scripts).
- Exit codes: 0 ok, 1 command failure, 2 configuration/usage error.
- Log file `local/wxodemo.log` (rotating). `local/` is already ignored. Add an explicit entry plus `*.log` is already ignored.
- The API key is never printed to the console or log (masked).

**Target layout.**
```
wxodemo.py                 # root launcher: adds src/ to sys.path, calls wxodemo.cli.main()
pyproject.toml             # metadata, console script, ruff + pytest config
src/wxodemo/               # __init__, __main__, cli, config, logging_setup, adk, manifest,
                           # discovery, deploy, status, chats, smoke, scaffold, validate, doctor
tests/                     # pytest; orchestrate subprocess mocked
docs/wxodemo.md            # detailed reference
README.md                  # short quick start
```

---

## Sub-Tasks

### 1. Package skeleton, config, logging, ADK runner, `doctor`, `setup`, `login`, `logs`

**Intent.** Build the foundation every other command relies on, and deliver the "get started" path (`setup`, `doctor`, `login`) first.

**Expected Outcomes.**
- `python wxodemo.py --help` and `wxodemo --help` (after `pip install -e .`) work.
- Missing/incomplete `env.cfg` fails with exit code 2 and an actionable message. No prompts.
- Console output is concise; `local/wxodemo.log` has full detail with secrets masked.
- `setup`, `doctor`, `login`, `logs` work on Windows and Linux/macOS.

**Todo List.**
1. Create `pyproject.toml` (Python >=3.11, console script `wxodemo`, ruff/pytest config). Decide dependency declaration so `requirements.txt` stays the source for `setup`.
2. Create `src/wxodemo/` package with `__main__.py` and `cli.py` (argparse subcommands, shared flags `--verbose`, `--dry-run` where relevant).
3. `config.py`: parse `env.cfg`, validate required keys, produce the error message with a pointer to `env.cfg.example`.
4. `logging_setup.py`: console formatter (short, ✓/✗ steps) plus rotating file handler in `local/wxodemo.log`; secret masking filter.
5. `adk.py`: locate `orchestrate`, run subprocesses with the UTF-8 env, capture output to log, surface the CLI's error on failure.
6. Implement `doctor`, `setup` (warn if not in a venv, continue), `login`, `logs`.
7. Add root `wxodemo.py` launcher.
8. Update `.gitignore` (explicit log entry; confirm no stray conflicts).

**Relevant Context.** `activate-wxo.ps1`/`.sh` (env add with piped "Y", env activate `--api-key`), `activate-lab-wxo.*`, `env.cfg.example`, `requirements.txt`, `.gitignore`.

**Status.** `[x] done`

**Notes for next sub-task.**
- Modules in `src/wxodemo/`: `config.py` (`repo_root()`, `env_cfg_path()`, `log_path()`, `load_config()` returning a frozen `Config`, `ConfigError` mapped to exit code 2), `logging_setup.py` (`setup_logging`, helpers `plain/info/ok/warn/fail`, `register_secret`, `mask`, `get_logger`), `adk.py` (`find_orchestrate()`, `run_orchestrate(args, input_text=, check=, cwd=)`, `AdkError`, `AdkNotFoundError`), `doctor.py` (`run_doctor()`, `in_virtualenv()`), `cli.py` (`build_parser()`, `main()`; each command is a `cmd_*` function registered with `set_defaults(func=...)`).
- New commands add a subparser in `build_parser()`, call `register_secret(cfg.api_key)` after `load_config()`, print through the logging helpers (not `print`, except raw data output), and raise `ConfigError`/`AdkError` instead of returning ad-hoc codes. `main()` converts these to exit codes 2 and 1.
- `run_orchestrate` has no `dry_run` parameter. Commands check `args.dry_run` themselves and print `[dry-run] would ...` lines.
- Console marks fall back to ASCII (`[ok]`, `[x]`, `[!]`) when stdout cannot encode the check marks (Windows cp1252).
- `.gitignore` was not edited (the editing tools are blocked for it). `local/` and `*.log` already cover `local/wxodemo.log`, so no change is needed.
- Pre-existing `ruff check .` reports about 250 findings in `tools/` and other existing code. Validate new code with `ruff check src tests wxodemo.py`. Tests run with `python -m pytest`.
- `pyproject.toml` reads dependencies from `requirements.txt`, so `pip install -e .` works and installs the `wxodemo` console command.
- Validated: `--help`, `doctor`, real `login` (idempotent), `login --dry-run`, `setup --dry-run`, missing `env.cfg` gives exit 2, API key absent from the log, `pip install -e .` gives a working `wxodemo` command, 8 tests pass, ruff clean on new code.

---

### 2. Discovery and manifest layer: `list`, `validate` (manifest part)

**Intent.** One place that knows what exists in the repo (scenarios and standalone agents) and what each needs deployed.

**Expected Outcomes.**
- `wxodemo list` shows scenarios and standalone agents with kind and status (live/soon).
- Name resolution with `--kind` filter and ambiguity errors.
- `validate` reproduces all existing manifest checks.

**Todo List.**
1. Port `scripts/scenario_manifest.py` (list, deploy-plan, teardown-plan, validate) into `manifest.py` returning Python objects instead of TSV.
2. Port standalone discovery from `standalone/manage.py` into `discovery.py` (`@tool` regex scan, `agent.yaml`).
3. Unified target resolver: names, `--all`, `--kind`.
4. Implement `list` and `validate`.

**Relevant Context.** `scripts/scenario_manifest.py`, `standalone/manage.py`, `scenarios/*/scenario.yaml`, `standalone/*/agent.yaml`.

**Status.** `[x] done`

**Notes for next sub-task.**
- `manifest.py`: `load_scenarios(root)` returns `{id: Scenario}` (`Scenario.id`, `.data`, `.root`, `.get()`). Plans are typed: `deploy_plan(all_scenarios, chosen)` returns `list[DeployStep]` (`kind` is `tool_py | tool_openapi | tool_pkg | kb | flow | agent`, plus `path`, `entry`, `requirements`, `name`). `teardown_plan(chosen)` returns `list[RemoveStep]` (`kind`, `name`, `agent_kind`) already in removal order (agents reversed, flows, tools, KBs). `validate_scenario`, `name_clashes`, `owned_names`, `TOOL_RE`, and `ManifestError` (exit code 1) are also there. Paths are absolute `Path` objects; use `rel(root, path)` for display.
- `deploy_plan` raises `ManifestError` on cross-scenario name clashes, as the old script did. Pass all scenarios as the first argument so the clash check sees every scenario.
- `discovery.py`: `all_targets(root)` returns `(targets, problems)`. `Target` has `kind` (`scenario | standalone`), `name`, `status`, `summary`, plus `.scenario` or `.agent` (`StandaloneAgent` with `dir`, `yaml_path`, `tools: list[ToolFile(path, names)]`). `resolve_targets(targets, names, select_all=, kind=, live_only=)` implements the agreed rules: names or `--all` (not both, not neither), `--kind` filter, an ambiguity error when a name matches both kinds, and `live_only=True` drops `soon` scenarios for `deploy --all`. Standalone agents also resolve by directory name (`hello-world` for `hello_world`).
- `config.py` gained `UsageError` (exit code 2); `ConfigError` is now a subclass. Raise `UsageError` for bad arguments. `main()` maps `UsageError` to 2, `ManifestError` and `AdkError` to 1.
- Standalone agents have no manifest, so `validate <standalone name>` prints a note and exits 0.
- `logging_setup.setup_logging` now sets `stdout` to `errors="replace"` so odd characters in descriptions cannot crash the console.
- Standalone deploy: the old `manage.py` only imports `*.py` files containing `@tool` functions, and treats a failed `agents deploy` as non-fatal (Developer Edition limitation). Under the "stop at first error" decision, sub-task 3 should decide whether the promotion step stays non-fatal for standalone agents or is treated as a hard failure; the old scenario scripts treated it as required.
- Tests: `tests/test_discovery.py` builds a throwaway repo layout (`make_scenario`, `make_standalone` helpers) that sub-task 3 can reuse for plan-order tests.
- Validated: `list`, `list --kind standalone`, `validate` (matches the old `scenario_manifest.py validate`: both OK on the two real scenarios), unknown name gives exit 2, 23 tests pass, ruff clean on new code.

---

### 3. `deploy`, `undeploy`, `status`

**Intent.** The core value: one idempotent way to deploy/undeploy any mix of agents.

**Expected Outcomes.**
- `deploy` runs login, then connections, tools (flat, package, openapi), knowledge bases, flows, agents, and `agents deploy` promotion, with a clear per-step summary.
- `undeploy` shows a plan, asks `[y/N]` (or `--yes`), fails on non-TTY without `--yes`, runs in reverse order.
- `--dry-run` previews both.
- `status` compares repo definitions against WXO.

**Todo List.**
1. Implement deploy plan execution for scenarios (from `manifest.py`) and standalone agents (from `discovery.py`).
2. Implement undeploy with confirmation logic and reverse order. Verify the actual `remove` behaviour against a real instance (old scripts were only tested with dry-run).
3. Implement `status` using `orchestrate ... list` output (check ADK docs for the output format option).
4. Stop at the first failing step with exit code 1. Report the failing resource and point to the log file.

**Relevant Context.** `scripts/deploy-all.ps1`/`.sh`, `scripts/teardown.ps1`/`.sh`, `standalone/manage.py`; import order and CLI flags from the inventory (`tools import -k python -p -f -r`, `knowledge-bases import`, `agents remove --kind`).

**Status.** `[x] done`

**Notes for next sub-task.**
- New module `deploy.py`: `run_deploy(targets, cfg, root, dry_run)`, `run_undeploy(targets, cfg, root, dry_run, assume_yes)`, `run_status(targets, cfg)`. Work is first built as `Action(label, args, optional, warning, resource)` objects (`scenario_deploy_actions`, `standalone_deploy_actions`, `scenario_remove_actions`, `standalone_remove_actions`), then run by `_execute`. A dry run prints the actions and runs nothing, and needs no `env.cfg`.
- `adk.py` gained `login(cfg)` (used by `login`, `deploy`, `undeploy`, `status`; `deploy` and `undeploy` log in automatically). `run_orchestrate` now passes `stdin=DEVNULL` unless `input_text` is given, so a CLI that unexpectedly prompts fails instead of hanging.
- CLI: `deploy|undeploy|status [names...] [--all] [--kind scenario|standalone]`, plus `--dry-run` (deploy, undeploy) and `-y/--yes` (undeploy). `_select()` and `_config_for()` in `cli.py` are the shared helpers. `deploy --all` skips scenarios with status `soon`.
- Decisions made: stop at the first failure (exit 1, names the failing step); promotion (`agents deploy`) failing is only a warning for scenarios and standalone agents alike (Developer Edition limitation, as in the old scripts). The question I asked about making it fatal for scenarios is still open; the current behaviour matches the old scripts.
- Order: deploy puts scenarios before standalone agents; undeploy reverses that, because standalone agents (for example `travel_rules_qa`) use knowledge bases owned by scenarios.
- Undeploy: first runs `login`, then lists what exists (`agents|tools|knowledge-bases list --verbose`), skips what is already absent, prints the plan and asks `[y/N]`. Non-TTY without `--yes` fails with exit 2 before any call. Answering anything but y/yes exits 1 and removes nothing.
- Verified against the real CLI: `agents|tools|knowledge-bases remove` take no confirmation prompt and have no `--yes` flag (checked via `--help`). Real `undeploy` of `hello_world` and `translator` followed by `deploy` worked, and a second `undeploy` was a clean no-op. Scenario undeploy (tools, flows, KBs) has NOT been run for real, to keep the demo resources on `techzone1`; only `--dry-run` was checked. KB removal deletes ingested documents.
- `knowledge-bases list --verbose` prints JSON with raw newlines inside strings (invalid strict JSON), so `_json_from` parses with `strict=False`. Keep that for any other `list --verbose` parsing (`smoke`, `export-chats`).
- Standalone `deploy` warns if the agent's `knowledge_base` entries are missing from WXO; it never imports KBs (as before).
- Connections: `connections/*.yaml` are imported before scenarios when any scenario is deployed (the directory is currently empty).
- `logging_setup` console handler now resolves `sys.stdout` at write time (`_StdoutHandler`), which fixed a closed-stream error under pytest.
- Tests: `tests/helpers.py` (repo builders, `pythonpath` includes `tests/`), `tests/test_deploy.py` (mocked `run_orchestrate`; covers order, stop-on-failure, promotion warning, prompt answers, TTY rule, skip-absent, status states). 46 tests pass; `ruff check src tests wxodemo.py` clean.

---

### 4. Port remaining commands: `smoke`, `export-chats`, `new-scenario`, demo-consistency check

**Intent.** Complete the absorption so the old scripts can be deleted.

**Expected Outcomes.**
- Each command has the same behaviour and flags as its predecessor, with output moved to the new console/log style.
- `validate` also runs the demo-consistency checks.

**Todo List.**
1. Port `smoke_test.py` into `smoke.py`.
2. Port `export_agent_chats.py` into `chats.py`. Credentials now come from the shared config module.
3. Port `new-scenario.py` into `scaffold.py`. Templates stay in `.bob/skills/scenario-demo-docs/templates/` and are read from there.
4. Port `.bob/skills/scenario-demo-docs/check_demo_consistency.py` into `validate.py`.
5. Add `eval <scenario>`: wrapper around `orchestrate evaluations evaluate --config evaluation/<id>/eval_config.yaml`. Check the ADK docs for the exact flags, and note that the evaluation extras may need a Python version below 3.14 (pandas wheel issue in README).

**Relevant Context.** `scripts/smoke_test.py`, `scripts/export_agent_chats.py`, `scripts/new-scenario.py`, `.bob/skills/scenario-demo-docs/`.

**Status.** `[x] done`

**Notes for next sub-task.**
- New modules, all wired into `cli.py` (`build_parser`, one `cmd_*` each): `smoke.py` (`smoke <scenario> [--only ID]... [--dry-run]`), `chats.py` (`export-chats [--agent] [--last 7d] [--raw-traces] [--workers N] [--output-dir] [--dry-run]`), `scaffold.py` (`new-scenario <id> --name --description [--agent-name] [--dry-run]`), `validate.py`, `evaluate.py` (`eval <scenario> [--dry-run]`). `validate` now also runs the six demo-consistency checks (reported as `demo: ...` lines per scenario) and still checks cross-scenario name clashes.
- `smoke`: same behaviour as `smoke_test.py` (agent looked up by name, prompts from `smoke_prompts`, exit 1 if any run is not `completed`). New: it calls `login(cfg)` first, so the 2-hour token is refreshed; `--dry-run` needs no `env.cfg`. Tool extraction and the run loop are in testable functions (`extract_results`, `_run_case`).
- `export-chats`: same output layout as before (`export/<timestamp>/<agent>/*.md|json`, `summary.json`, `manifest.json`, `README.md`), now using `Config` from `env.cfg`. The API-key-to-token exchange is registered as a secret. The old `--env-file` flag is dropped (one `env.cfg`). Emoji were removed from the Markdown transcripts. Fix found while testing on the real instance: a chunked response cut off mid-body raised `http.client.IncompleteRead`, which was not retried; `Api.request` now retries `HTTPException`. Verified for real: last 24h on `techzone1` exported 345 conversations (320 threads + 457 traces, duplicates skipped).
- `new-scenario`: same files and rules as before, with the same dry-run. Fix: the script tag is inserted with the file's own line endings (the old code produced a mixed CRLF/LF result on CRLF files; covered by a test). The "next steps" text now names `wxodemo` commands. Verified in the real repo, then reverted with git.
- `eval`: runs `orchestrate evaluations evaluate --config evaluation/<id>/eval_config.yaml` with the terminal attached (the framework's progress rendering exits 1 when output is piped, as the README says), after `login`. `travel-request` has no `eval_config.yaml`, so `eval travel-request` exits 2 with an explanation. The evaluation framework itself is NOT in `requirements.txt`; documented as optional (sub-task 7). It was started for real and loaded the 5 test cases, but the run was stopped by my tool timeout; the partial results folder was deleted.
- Not ported on purpose: the old `scenario_manifest.py` CLI (`validate`/`list` subcommands) is covered by `validate` and `list`. The agent-name guessing heuristic in `chats.detect_agent` still hard-codes demo agent names (incident_triage, hello_world, translator, travel_*); it only applies to threads with no agent id.
- Open item for sub-task 6: `.bob/skills/scenario-demo-docs/templates/demo-script.template.md` mentions `check_demo_consistency.py` in its AUTHOR NOTES; change it to `python wxodemo.py validate <id>`. `scaffold.TEMPLATE` points at that file.
- Tests added: `tests/test_scaffold_validate.py`, `tests/test_smoke_eval.py`, `tests/test_chats.py` (fake API; no network). 125 tests pass; `ruff check` and `ruff format --check` clean on `src tests wxodemo.py`.

---

### 5. Tests

**Intent.** Make the CLI safely refactorable and avoid regressions in the deploy/undeploy order.

**Expected Outcomes.** `pytest` passes without network access or an ADK login. Ruff is clean.

**Todo List.**
1. Unit tests: config validation messages, secret masking, target resolution, deploy/undeploy plan ordering, `--dry-run`, undeploy confirmation rules (TTY, non-TTY, `--yes`).
2. Mock the `orchestrate` subprocess boundary.
3. Run on the two existing scenarios and standalone agents as fixtures.

**Relevant Context.** The `scenarios/` and `standalone/` directories as realistic fixtures.

**Status.** `[x] done`

**Notes for next sub-task.**
- Test files in `tests/`: `helpers.py` (repo builders + shared `FakeOrchestrate`), `test_config.py`, `test_logging.py`, `test_discovery.py`, `test_deploy.py`, `test_scaffold_validate.py`, `test_smoke_eval.py`, `test_chats.py`, `test_cli.py`, `test_doctor_adk.py`, `test_manifest.py`, `test_edge_cases.py`. 254 tests pass in about 5 s; no network, no ADK login and no real `env.cfg` needed.
- Coverage (coverage.py): 96% total; `deploy.py`, `adk.py`, `doctor.py` 100%; lowest is `chats.py` 92%. `__main__.py` shows 0% only because it is exercised through a subprocess.
- Validation clean: `python -m ruff format --check src tests wxodemo.py`, `python -m ruff check src tests wxodemo.py`, `python -m pytest -q`.
- Windows caveat: `Path("a/b")` renders as `a\b` in command args; build expected values with `str(Path(...))`.
- `cli.main()` last-resort handler now logs the traceback with `logger.debug(..., exc_info=True)`, so it goes to the log file only and not the console.
- `tests/test_cli.py` has real-repo subprocess tests (`validate`, `deploy --all --dry-run`, `undeploy --all --dry-run`, `list`). They read `scenarios/` and `standalone/` and do not depend on the old scripts, so sub-task 6 must keep them green.
- Open question still unanswered: should a failed `agents deploy` (promotion to LIVE) be fatal for scenarios? Currently a warning for all targets, as in the old scripts.

---

### 6. Remove old scripts and update everything that references them

**Intent.** Leave one way of doing things and no dangling references.

**Expected Outcomes.** No references remain to deleted scripts, except historical `plans/` (decision below). Docs, skills and modes point at `wxodemo` commands.

**Todo List.**
1. Delete `activate-lab-wxo.ps1/.sh`, `activate-wxo.ps1/.sh`, `scripts/deploy-all.*`, `scripts/teardown.*`, `scripts/*.py`, `standalone/manage.py`, and the old `check_demo_consistency.py`.
2. Update `.bob/custom_modes.yaml` (the "finish with" validation commands), and the three skills `wxo-adk`, `wxo-scenario-authoring`, `scenario-demo-docs` plus its templates.
3. Update `agents/*/README.md`, `standalone/README.md` and each `standalone/*/README.md`, `docs/demo/*-demo.md`, and `evaluation/incident-triage/eval_config.yaml` comments.
4. Run a final grep for old script names.

**Relevant Context.** The grep inventory of 41 files referencing the old scripts.

**Status.** `[x] done`

**Notes for next sub-task.**
- Decision made (answer to the open question): a failed `agents deploy` (promotion to LIVE) is now **fatal for every target** (scenarios and standalone agents). The `optional`/`warning` fields and `PROMOTE_WARNING` were removed from `deploy.Action`; `_execute` raises `AdkError("<label> failed...")` for any failing action. Test `test_promotion_failure_is_fatal` replaced the old "only a warning" test. The Developer Edition note in `standalone/README.md` and the `wxo-scenario-authoring` skill now say the deploy stops with exit 1 there.
- Deleted: `activate-lab-wxo.ps1/.sh`, `activate-wxo.ps1/.sh`, all of `scripts/` (including the `__pycache__`), `standalone/manage.py`, `.bob/skills/scenario-demo-docs/check_demo_consistency.py` (via `git rm`, so they are staged as deletions).
- Updated to `wxodemo` commands: `.bob/custom_modes.yaml` (both "finish with" blocks), skills `wxo-adk`, `wxo-scenario-authoring`, `scenario-demo-docs`, both templates (including the reset checklist and troubleshooting rows in `demo-script.template.md`, which now say `python wxodemo.py login`), `agents/*/README.md`, `standalone/README.md` and the three standalone READMEs, `docs/demo/incident-triage-demo.md`, `docs/demo/travel-request-demo.md`, and `evaluation/incident-triage/eval_config.yaml` comments.
- `README.md` was edited only enough to remove dangling references: the structure tree, setup, Deploy, Teardown, evaluation, new-scenario, standalone and export-chats sections now name `wxodemo` commands, and the "Known limitations" bullets about the old scripts were replaced. Sub-task 7 still owns the quick-start rewrite and `docs/wxodemo.md`.
- Final grep (`activate-lab-wxo|activate-wxo|deploy-all|teardown.ps1/.sh|scenario_manifest|smoke_test|export_agent_chats|new-scenario.py|check_demo_consistency|manage.py|scripts/`) matches only `plans/*.md` (historical, left unchanged by decision 4) and this plan file. Three lines in the two demo scripts that describe historical runs ("`scripts/smoke_test.py` style", "Sub-Task 9 ... teardown scripts") were reworded or left as history; `docs/demo/incident-triage-demo.md` line 315 is a historical progress note and was left alone.
- Validated: `ruff format --check` and `ruff check` clean on `src tests wxodemo.py`, 254 tests pass, `wxodemo validate` OK for both scenarios, `deploy --all --dry-run` and `undeploy --all --dry-run` work.
- Not run: a real `deploy` after making promotion fatal (it needs a live Enterprise instance; on the Developer Edition `techzone1` this change means the deploy would now exit 1 if `agents deploy` is unsupported there, which earlier real runs did not hit).

---

### 7. Documentation

**Intent.** README is quick to consume. Details live in a separate doc.

**Expected Outcomes.**
- `README.md` quick start: prerequisites, create venv (optional, recommended), `pip install -e .` or `python wxodemo.py setup`, fill `env.cfg`, `doctor`, `login`, `deploy`, `smoke`, `undeploy`, with a short command table.
- `docs/wxodemo.md` has the full command reference, `env.cfg` keys, log file location and debugging, exit codes, target addressing, troubleshooting, and a migration table from old scripts to new commands.

**Todo List.**
1. Rewrite the relevant README sections (Quickstart, Deploy, Teardown, Standalone, Backing up chats, Adding a new scenario).
2. Write `docs/wxodemo.md`.
3. Update the "Known limitations" section (the bash-untested note disappears).

**Relevant Context.** `README.md`, `standalone/README.md`.

**Status.** `[x] done`

**Notes.**
- New [`docs/wxodemo.md`](docs/wxodemo.md): running it, `env.cfg` keys, every command with options and examples, target addressing, deploy and undeploy order and semantics, log file and debugging, exit codes, troubleshooting table, migration table from the old scripts (with the behaviour changes listed), and a development section (layout, how to add a command). Facts were checked against `cli.py`, `config.py`, `doctor.py`, `deploy.py`, `adk.py`, `manifest.py` and by running the error paths (usage errors, bad `--last`, bad id, `eval travel-request`, `smoke --dry-run --only`) and `doctor` for real.
- `README.md`: the Prerequisites, Quickstart/Setup, Deploy and Teardown sections were replaced by one short **Quick start** (venv, `setup`, `env.cfg`, `doctor`/`login`/`deploy`/`smoke`, cleanup), a command table and a link to the reference. The structure tree lists `docs/wxodemo.md`. "Known limitations" lost the bash-untested note and the old-script notes, and now states: Windows only, scenario `undeploy` only dry-run, `wxodemo smoke` not run live in this form, promotion to live is required and unverified on a Developer Edition instance.
- Line endings: `README.md` was CRLF in git, so it was normalised back to CRLF after editing; `docs/wxodemo.md` was written CRLF to match.
- Not done on purpose: `plans/*.md` stay historical. `Running the evaluation` and the other lower README sections were only touched in sub-task 6.
- Validated: relative links in both documents resolve, ruff format and check clean on `src tests wxodemo.py`, 254 tests pass, `wxodemo validate` OK, grep for old script names matches only `plans/`, the plan and the migration table.

## Final state

All 7 sub-tasks are done. Open items for a human: run a real scenario `undeploy` on a disposable instance; run `deploy` on a Developer Edition instance to see the fatal promotion behaviour; run `smoke` live; try Linux or macOS.

---

## Decisions (resolved)

1. `env.cfg`: `WXO_API_KEY`, `WXO_URL`, `WXO_ENV_NAME` are required. `WXO_ENV_TYPE` stays optional (default `ibm_iam`), as today.
2. `deploy` and `undeploy` stop at the first error (exit code 1) and say which step failed. No `--keep-going`.
3. Scaffold templates stay under `.bob/skills/scenario-demo-docs/templates/`. `scaffold.py` reads them from there.
4. Historical `plans/*.md` are left unchanged.
5. Add an `eval` command wrapping `orchestrate evaluations evaluate` (see sub-task 4).
