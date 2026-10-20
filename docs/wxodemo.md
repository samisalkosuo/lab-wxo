# wxodemo reference

`wxodemo` is the one command-line tool for this repo. It sets up the Python environment, logs in to watsonx Orchestrate (WXO), deploys and removes scenarios and standalone agents, runs smoke tests and evaluations, exports chats and scaffolds new scenarios.

For a short walk-through see the [Quick start in the README](../README.md#quick-start). This page is the full reference.

## Contents

- [Running it](#running-it)
- [Configuration: env.cfg](#configuration-envcfg)
- [Commands](#commands)
- [Target names](#target-names)
- [Deploy and undeploy in detail](#deploy-and-undeploy-in-detail)
- [Output, log file and debugging](#output-log-file-and-debugging)
- [Exit codes](#exit-codes)
- [Troubleshooting](#troubleshooting)
- [Migrating from the old scripts](#migrating-from-the-old-scripts)
- [Development](#development)

## Running it

Two equivalent ways:

```bash
python wxodemo.py <command> [options]     # from the repo root, nothing to install
wxodemo <command> [options]               # after: pip install -e .
```

Global options go **before** the command:

| Option | Meaning |
|---|---|
| `-v`, `--verbose` | Also print debug output on screen (it is always written to the log file). Example: `python wxodemo.py -v deploy --all` |
| `--version` | Print the version |
| `-h`, `--help` | Help. Works for every command too: `python wxodemo.py deploy --help` |

Python 3.11 or later is required. A virtual environment is optional but recommended. `wxodemo` never creates, detects or activates one. It uses the Python that started it and looks for the `orchestrate` command next to that interpreter first, then on `PATH`.

All commands are safe to repeat. Commands that change something accept `--dry-run`, which prints what would happen and changes nothing.

## Configuration: env.cfg

`env.cfg` lives in the repo root and is **required** for every command that talks to WXO. `wxodemo` never prompts for credentials. Create it from the template:

```powershell
Copy-Item env.cfg.example env.cfg    # Windows
```
```bash
cp env.cfg.example env.cfg           # Linux / macOS
```

| Key | Required | Meaning |
|---|---|---|
| `WXO_API_KEY` | yes | API key of your WXO instance (WXO web UI: Settings, API details) |
| `WXO_URL` | yes | Service instance URL: `https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<instance-id>` |
| `WXO_ENV_NAME` | yes | A local name for the environment in the ADK, for example `my-env` |
| `WXO_ENV_TYPE` | no | `ibm_iam` (default) or `mcsp` (AWS-hosted instances) |

Format: one `KEY=VALUE` per line. Blank lines and lines starting with `#` are ignored. Values may be wrapped in single or double quotes.

A missing file, a missing or empty required key, or a value that is still the template placeholder (`your-api-key-here`, or a URL containing `<` or `>`) stops the command with exit code 2 and a message that names the keys to fix.

`env.cfg` holds a secret and is git-ignored. Do not commit it.

The API key is never printed on screen and never written to the log. It is masked as `****` in every command line and output that is logged.

Commands that need no credentials: `list`, `validate`, `new-scenario`, `logs`, `doctor` (it reports a bad `env.cfg` instead of stopping), and every `--dry-run`.

## Commands

| Command | What it does |
|---|---|
| `setup` | `pip install -r requirements.txt` with the current Python, then `doctor`. Warns, but continues, outside a virtual environment. |
| `doctor` | Checks Python version, ADK and PyYAML installed, `orchestrate` found, `env.cfg` complete, active WXO environment. |
| `login` (alias `activate`) | Registers the environment from `env.cfg` and activates it. Config persists in `~/.config/orchestrate`, so it survives the command ending. |
| `list [--kind K]` | Lists scenarios and standalone agents with kind and status. |
| `status [names...] [--all] [--kind K]` | Compares what the repo defines with what exists in WXO. |
| `deploy [names...] [--all] [--kind K] [--dry-run]` | Deploys in dependency order. Logs in first. |
| `undeploy [names...] [--all] [--kind K] [--dry-run] [-y]` | Removes in reverse order. Asks `[y/N]` unless `--yes`. |
| `validate [names...] [--kind K]` | Manifest checks plus demo-consistency checks. Default: all scenarios. |
| `smoke <scenario> [--only ID]... [--dry-run]` | Sends the scenario's smoke prompts to its deployed agent. |
| `eval <scenario> [--dry-run]` | Runs the ADK evaluation for a scenario. |
| `export-chats [options]` | Exports agent chats and traces. |
| `new-scenario <id> --name N --description D [--agent-name A] [--dry-run]` | Scaffolds a new scenario. |
| `logs [-n N]` | Prints the log file path and its last N lines (default 20). |

### setup

```bash
python wxodemo.py setup
python wxodemo.py setup --dry-run     # show the pip command only
```

Uses `sys.executable -m pip`, so packages go into whichever Python runs the tool. If `pip` fails, the last lines of its error are shown and the full output is in the log.

### doctor

```bash
python wxodemo.py doctor
```

Exit code 0 when everything is ready, 1 when Python, the ADK or the `orchestrate` command has a problem, 2 when `env.cfg` is the only problem. PyYAML missing is a warning (scenarios need it).

### login

```bash
python wxodemo.py login
python wxodemo.py login --dry-run
```

Runs `orchestrate env add` (answering the "update the environment?" question with `Y`, so repeats work) and `orchestrate env activate --api-key`. `deploy`, `undeploy`, `status`, `smoke`, `eval` and `export-chats` log in by themselves, which also refreshes the token. The token expires after about 2 hours, so run `login` (or any of those) shortly before a demo.

### list

```bash
python wxodemo.py list
python wxodemo.py list --kind standalone
```

Columns: `NAME`, `KIND` (`scenario` or `standalone`), `STATUS` (`live` or `soon` for scenarios, `-` for standalone), `DESCRIPTION`.

### status

```bash
python wxodemo.py status --all
python wxodemo.py status incident-triage
```

Reads the agents, tools (including flows) and knowledge bases in the active environment and prints one row per target:

| State | Meaning |
|---|---|
| `deployed` | Every agent, tool and knowledge base the target owns exists |
| `partial` | Some exist; the missing ones are listed |
| `not deployed` | None exist |

### deploy

```bash
python wxodemo.py deploy --all                       # all live scenarios + all standalone agents
python wxodemo.py deploy --all --kind scenario
python wxodemo.py deploy incident-triage travel_rules_qa
python wxodemo.py deploy --all --dry-run             # needs no env.cfg
```

See [Deploy and undeploy in detail](#deploy-and-undeploy-in-detail).

### undeploy

```bash
python wxodemo.py undeploy incident-triage --dry-run
python wxodemo.py undeploy incident-triage            # shows the plan, asks [y/N]
python wxodemo.py undeploy --all --yes                # no question
```

Explicit names or `--all` are required. Without `--yes` in a non-interactive shell the command fails (exit 2) before it removes anything. Answering anything but `y` or `yes` cancels with exit 1 and removes nothing.

### validate

```bash
python wxodemo.py validate                  # all scenarios
python wxodemo.py validate incident-triage
```

Checks each `scenarios/<id>/scenario.yaml` (required fields, files that exist, names unique across scenarios, a `smoke_prompts` list for live scenarios) and then the demo documents (output lines start with `demo:`): the slide script tag in `presentation.html`, slide tag numbers, leftover `{{...}}` or `AUTHOR NOTE` text, prompt equality between `docs/demo/<id>-demo.md` and `docs/demo/scenarios/<id>.js`, copy-button ids, and tool chips against the manifest. It does not judge facts, tone or claims. Standalone agents have no manifest, so naming one prints a note and exits 0. Exit code 1 if any check reports a problem.

### smoke

```bash
python wxodemo.py smoke incident-triage
python wxodemo.py smoke incident-triage --only INC-1001     # one prompt id, repeatable
python wxodemo.py smoke incident-triage --dry-run           # print the prompts, send nothing
```

Finds the deployed agent by name, sends each prompt from `smoke_prompts` in `evaluation/<id>/ground_truth.json` through the ADK run API, and prints the tools called and the start of each answer. It does not grade answers. Exit code 1 if any run does not finish with status `completed`. The prompts are diagnosis only, because the approval form cannot be answered through the run API.

### eval

```bash
python wxodemo.py eval incident-triage
python wxodemo.py eval incident-triage --dry-run
```

Logs in, then runs `orchestrate evaluations evaluate --config evaluation/<id>/eval_config.yaml` with the terminal attached. A scenario without an `eval_config.yaml` (currently `travel-request`) exits 2 with an explanation. The evaluation framework is **not** in `requirements.txt`; see [Running the evaluation](../README.md#running-the-evaluation-optional). Results go to `evaluation/<id>/results/<timestamp>/`. The evaluation command itself exits 1 when its output is piped or redirected (a progress-rendering issue), although the result files are still written.

### export-chats

```bash
python wxodemo.py export-chats                      # last 7 days, all agents
python wxodemo.py export-chats --agent translator
python wxodemo.py export-chats --last 30d
```

| Option | Default | Meaning |
|---|---|---|
| `--agent` | all | Only this agent (name or id) |
| `--last` | `7d` | Window for Web UI chats: a number plus `m`, `h` or `d` (`90m`, `24h`, `7d`) |
| `--raw-traces` | off | Also save the raw trace JSON |
| `--workers` | `10` | Parallel downloads |
| `--output-dir` | `export/` | Base folder |
| `--dry-run` | | Show what would be exported |

Output: `export/<timestamp>/<agent>/*.md|json`, plus `summary.json`, `manifest.json` and a `README.md`. The `export/` folder is git-ignored.

### new-scenario

```bash
python wxodemo.py new-scenario customer-returns --name "Customer Returns" \
    --description "One line for the sidebar"
```

`<id>` is kebab-case. The agent name defaults to the id with underscores; override it with `--agent-name` (snake_case). Creates `scenarios/<id>/scenario.yaml` (status `soon`), an agent stub, an `evaluation/<id>/ground_truth.json` stub, `docs/demo/<id>-demo.md` from the template, and a placeholder `docs/demo/scenarios/<id>.js` registered in `presentation.html`. It refuses to run when `scenarios/<id>/` already exists, and changes nothing in that case. The templates live in `.bob/skills/scenario-demo-docs/templates/`. Finish with `python wxodemo.py validate <id>`.

### logs

```bash
python wxodemo.py logs
python wxodemo.py logs -n 100
```

## Target names

A target is a **scenario** (a folder under `scenarios/` with a manifest) or a **standalone agent** (a folder under `standalone/` with an `agent.yaml`). Commands that take targets accept:

- one or more **names**: a scenario id such as `incident-triage`, or a standalone agent's WXO name such as `travel_rules_qa`. A standalone agent also resolves by its folder name (`hello-world` for `hello_world`).
- `--all`, to select everything. Do not combine names with `--all`, and do not give neither (exit 2).
- `--kind scenario|standalone`, which narrows `--all`, and settles a name that matches both kinds (otherwise that is an error asking you to add `--kind`).

`deploy --all` skips scenarios whose status is `soon`. Naming a `soon` scenario deploys it anyway. `undeploy --all` and `status --all` include every scenario.

## Deploy and undeploy in detail

### Deploy order

Everything a target owns is imported in dependency order:

```
connections -> tools -> knowledge bases -> flows -> agents -> promote agents to live
```

- **Connections** (`connections/*.yaml`) are imported once, before any scenario. The folder is currently empty.
- **Tools** are flat `.py` files, multi-file packages (`-p` with an entry file and `requirements.txt`) and OpenAPI files, as listed in the manifest.
- **Promotion**: `orchestrate agents import` creates a draft. The chat UI lists only live agents, so each agent is followed by `orchestrate agents deploy --name <agent>`. A failure here fails the deploy, like any other step.
- **Scenarios go before standalone agents**, because standalone agents (for example `travel_rules_qa`) can use knowledge bases that scenarios own. A standalone `deploy` only warns if an agent's knowledge base is missing; it never imports knowledge bases itself.
- Standalone agents import only the `*.py` files that contain `@tool` functions, before the agent.
- Tool, flow, knowledge-base and agent names are shared by the whole WXO instance. `deploy` refuses to run when two scenarios use the same name.

The run **stops at the first failing step**, exit code 1, naming the step (for example `Knowledge base incident_triage_runbooks failed.`) and the last lines of the ADK error. The full output is in the log file. There is no keep-going mode. Fix the cause and run the command again: re-import updates existing resources in place.

### Undeploy order

The reverse: standalone agents first, then for each scenario its agents, flows, tools and knowledge bases. Names come from the manifests and are the real WXO resource names.

`undeploy` logs in, reads what exists, **skips what is already absent**, prints the plan and asks `[y/N]`. The `orchestrate ... remove` commands themselves never ask and have no `--yes` flag, which is why the confirmation lives in `wxodemo`.

Removing a knowledge base deletes its ingested documents. A knowledge base shared with another scenario or a standalone agent is removed too, so re-import it afterwards if you still need it.

## Output, log file and debugging

The screen shows short, friendly steps: `[ok]`/check mark for success, `[!]` for warnings, `[x]` for failures. When the terminal cannot show the check marks (Windows cp1252), plain ASCII is used instead.

The **log file** is `local/wxodemo.log`. It is rotating (1 MB, three older files kept), and git-ignored (`local/` and `*.log`). It contains every command line, the command output (stdout and stderr), timings, and the Python traceback of an unexpected error, all with secrets masked.

```bash
python wxodemo.py logs            # path + last 20 lines
python wxodemo.py -v deploy ...   # debug lines on screen as well
```

To investigate a failure: read the red message first (it names the step), then `python wxodemo.py logs -n 80`, or open the file.

Every `orchestrate` call runs with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` (this avoids Windows `charmap` errors), and with stdin closed, so a command that unexpectedly asks a question fails instead of hanging.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success (for `doctor`: ready) |
| 1 | A command failed: an `orchestrate` step, a manifest or validation problem, a failed smoke run, an undeploy that was cancelled, or an unexpected error |
| 2 | Configuration or usage error: bad or missing `env.cfg`, unknown or ambiguous target, `undeploy` without `--yes` in a non-interactive shell, invalid option value |
| 127 | The `orchestrate` command was not found for this Python |
| 130 | Interrupted with Ctrl-C |

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `env.cfg not found` or `missing values for: ...` (exit 2) | Create or complete `env.cfg` from `env.cfg.example`. Placeholder values count as missing. |
| `The 'orchestrate' CLI was not found` (exit 127) | The ADK is not installed for the Python you used. Run `python wxodemo.py setup` with the same Python (and activate your venv first, if you use one). |
| `doctor` says the ADK is missing but you installed it | It was installed in a different Python. `doctor` prints the interpreter path it checked. |
| Auth errors, `401`, or "token expired" | The token lasts about 2 hours. Run `python wxodemo.py login`. |
| `Unknown target 'x'` (exit 2) | Names must match `python wxodemo.py list`. |
| `'x' matches both a scenario and a standalone agent` | Add `--kind scenario` or `--kind standalone`. |
| `undeploy needs confirmation, but this is not an interactive terminal` | Add `--yes` (or `--dry-run` to preview). |
| Deploy stops at `Agent <name> live failed` | Promotion to live was refused. The agent exists as a draft. This happens on the Developer Edition, which supports drafts only. The agent can still be used through the ADK run API; the chat UI will not list it. |
| Deploy stops at a knowledge-base step, or the knowledge base shows "document(s) failed in ingestion" | Updating a knowledge base in place has failed ingestion in testing. Remove it and import it again: `orchestrate knowledge-bases remove --name <kb>`, then `python wxodemo.py deploy <scenario>`. |
| A standalone agent answers without document facts | Its knowledge base is not deployed. The deploy printed `Knowledge base(s) not found`. Deploy the scenario that owns it first. |
| Only `AskOrchestrate` in the chat picker | The agent is still a draft or you reloaded too early. Run `python wxodemo.py status`, then reload the chat page. |
| `UnicodeEncodeError ... charmap` from a command you ran yourself | Windows console encoding. Run it through `wxodemo`, or set `$env:PYTHONUTF8 = "1"`. |
| `orchestrate chat ask` hangs | It hangs in non-interactive shells. Use `wxodemo smoke`, or the browser chat. |
| `eval` exits 1 but the result folder exists | The evaluation framework exits 1 when its output is piped. Run it in a normal terminal. |
| `eval` cannot import the evaluation package | It is optional and not in `requirements.txt`. See the README. |
| A message ends with `Details: .../local/wxodemo.log` | Open that file or run `python wxodemo.py logs -n 80`. |

## Migrating from the old scripts

| Old | New |
|---|---|
| `.\activate-lab-wxo.ps1`, `source activate-lab-wxo.sh` | Create the venv yourself (optional), then `python wxodemo.py setup` and `python wxodemo.py login` |
| `.\activate-wxo.ps1`, `activate-wxo.sh` | `python wxodemo.py login` |
| `scripts/deploy-all.ps1`, `deploy-all.sh` | `python wxodemo.py deploy --all` |
| `deploy-all ... -Scenario X` / `--scenario X` | `python wxodemo.py deploy X` |
| `scripts/teardown.ps1`, `teardown.sh` | `python wxodemo.py undeploy --all` (asks for confirmation) |
| `teardown ... -DryRun` / `--dry-run` | `python wxodemo.py undeploy ... --dry-run` |
| `scripts/scenario_manifest.py list` | `python wxodemo.py list` |
| `scripts/scenario_manifest.py validate --scenario X` | `python wxodemo.py validate X` |
| `.bob/skills/scenario-demo-docs/check_demo_consistency.py X` | `python wxodemo.py validate X` (runs both checks) |
| `scripts/smoke_test.py --scenario X` | `python wxodemo.py smoke X` |
| `scripts/export_agent_chats.py` | `python wxodemo.py export-chats` (same options; `--env-file` is gone, there is one `env.cfg`) |
| `scripts/new-scenario.py X ...` | `python wxodemo.py new-scenario X ...` |
| `standalone/manage.py list` | `python wxodemo.py list --kind standalone` |
| `standalone/manage.py deploy [--agent A]` | `python wxodemo.py deploy A` or `deploy --all --kind standalone` |
| `standalone/manage.py undeploy [--agent A]` | `python wxodemo.py undeploy A` or `undeploy --all --kind standalone` |
| `orchestrate evaluations evaluate --config evaluation/X/eval_config.yaml` | `python wxodemo.py eval X` |

What changed in behaviour:

- `env.cfg` is mandatory and nothing prompts for credentials.
- `deploy` and `undeploy` stop at the first error (the old scripts could carry on).
- A failed promotion to live is an error for every target (the old scripts only warned).
- `undeploy` asks for confirmation and skips resources that do not exist.
- The tool never creates or activates a virtual environment.

## Development

```bash
pip install -e .                 # adds the `wxodemo` command
python -m pytest -q              # about 250 tests, a few seconds, no network, no ADK login, no env.cfg
python -m ruff check src tests wxodemo.py
python -m ruff format --check src tests wxodemo.py
```

Layout:

```
wxodemo.py                 # launcher: adds src/ to sys.path, calls wxodemo.cli.main()
pyproject.toml             # metadata, console script, ruff + pytest config; dependencies come from requirements.txt
src/wxodemo/
    cli.py                 # argparse commands, exit-code mapping
    config.py              # env.cfg parsing and the error messages
    logging_setup.py       # console + rotating file log, secret masking
    adk.py                 # find and run `orchestrate`, login
    manifest.py            # scenario.yaml loading, deploy and teardown plans, validation
    discovery.py           # scenarios + standalone agents, target resolution
    deploy.py              # deploy, undeploy, status
    validate.py            # manifest + demo-consistency checks
    smoke.py  evaluate.py  chats.py  scaffold.py  doctor.py
tests/                     # pytest; the `orchestrate` call boundary is replaced by a shared fake
```

Rules for new commands: add a subparser in `build_parser()` in `cli.py`, call `register_secret(cfg.api_key)` after `load_config()`, print through the helpers in `logging_setup.py` (`plain`, `info`, `ok`, `warn`, `fail`), raise `UsageError` (exit 2) or `AdkError` / `ManifestError` (exit 1) instead of returning ad-hoc codes, and check `args.dry_run` before running anything that changes state. The CLI parsing, config, logging, `setup` and `doctor` use only the standard library so they work before anything is installed; PyYAML and ADK imports stay lazy.

Pre-existing `ruff check .` findings in `tools/` and other older code are not part of this tool; check only `src tests wxodemo.py`.
