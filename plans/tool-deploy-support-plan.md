# Plan: Add Tool Deployment Support to `wxodemo.py`

## Top-Level Overview

This plan adds first-class support for `tool` as a deployable and manageable target kind in `wxodemo.py`, alongside `scenario` and `standalone`.

This enables users to discover, list, check status, deploy, and undeploy shared or standalone tool packages (such as `tools/report_generator`) directly via `wxodemo.py` commands (`deploy`, `undeploy`, `status`, `list`, and `validate`) without having to manually construct complex `orchestrate tools import/remove` commands.

---

## Sub-Tasks

### Sub-Task 1: Tool Target Discovery & Kind Registration
- **Intent:** Define the `ToolPackage` / `ToolTarget` data structure and implement discovery for tool packages and single-file tools under `tools/`. Add `"tool"` to supported `KINDS` in `src/wxodemo/discovery.py` and update CLI kind choices in `src/wxodemo/cli.py`.
- **Expected Outcomes:**
  - `KINDS = ("scenario", "standalone", "tool")` in `src/wxodemo/discovery.py`.
  - `ToolTarget` dataclass holding path, entry point, requirements file, and discovered `@tool` function names.
  - `discover_tools(root: Path)` scans `tools/` for multi-file tool packages (directories with `.py` containing `@tool`) and standalone tool files (`tools/*.py`).
  - `all_targets()` includes discovered tool targets.
  - `Target.matches()` allows matching tool targets by folder name / file stem, with kebab-case and snake_case alias support.
  - `src/wxodemo/cli.py` `--kind` arguments in parser updated to include `"tool"`.
- **Todo List:**
  1. Define `ToolTarget` dataclass in `src/wxodemo/discovery.py`.
  2. Implement `discover_tools()` in `src/wxodemo/discovery.py`.
  3. Integrate `discover_tools` into `all_targets()`.
  4. Update `Target` dataclass with `tool: ToolTarget | None = None` and match logic.
  5. Update `KINDS` tuple and `cli.py` parser `--kind` choices.
- **Relevant Context:**
  - Discovery logic: [`src/wxodemo/discovery.py`](src/wxodemo/discovery.py)
  - CLI argument definitions: [`src/wxodemo/cli.py`](src/wxodemo/cli.py)
- **Status:** `[ ] pending`

---

### Sub-Task 2: Tool Deploy, Undeploy, and Status Actions
- **Intent:** Implement deploy action generation, teardown action generation, and expected resource mapping for tool targets in `src/wxodemo/deploy.py`.
- **Expected Outcomes:**
  - `tool_deploy_actions(tool: ToolTarget) -> list[Action]`: Generates `tools import -k python -p <dir> -f <entry> -r <reqs>` for packages, or `tools import -k python -f <file>` for single files.
  - `tool_remove_actions(tool: ToolTarget) -> list[Action]`: Generates `tools remove --name <name>` for each discovered `@tool` function.
  - `expected_resources()` updated to return tool names for `tool` targets.
  - `_scenarios_first()` ordering updated so that when deploying `--all`, tools are deployed before scenarios and standalone agents; on undeploy, tools are removed after agents and scenarios.
  - `wxodemo list`, `wxodemo status`, `wxodemo deploy <tool>`, and `wxodemo undeploy <tool>` work seamlessly.
- **Todo List:**
  1. Implement `tool_deploy_actions` in `src/wxodemo/deploy.py`.
  2. Implement `tool_remove_actions` in `src/wxodemo/deploy.py`.
  3. Update `expected_resources` for tool targets.
  4. Update deployment order (`tools` first -> `scenarios` -> `standalone`).
  5. Update teardown order (`standalone` -> `scenarios` -> `tools`).
- **Relevant Context:**
  - Deployment execution: [`src/wxodemo/deploy.py`](src/wxodemo/deploy.py)
- **Status:** `[ ] pending`

---

### Sub-Task 3: Unit Testing & CLI Verification
- **Intent:** Update existing tests and add comprehensive unit tests in `tests/test_discovery.py`, `tests/test_deploy.py`, and `tests/test_cli.py` to verify tool discovery, resolution, kind filtering, deploy order, undeploy order, and CLI output.
- **Expected Outcomes:**
  - Tests verify `wxodemo list --kind tool` shows tool targets (e.g. `report_generator`).
  - Tests verify `wxodemo deploy report_generator --dry-run` produces the correct `orchestrate tools import` command.
  - Tests verify `wxodemo undeploy report_generator --dry-run` produces the correct `orchestrate tools remove` commands.
  - Tests verify `--all` deployment and undeployment ordering with tools included.
  - All existing and new tests pass.
- **Todo List:**
  1. Add `make_tool_pkg` helper in `tests/helpers.py`.
  2. Add unit tests for tool discovery and resolution in `tests/test_discovery.py`.
  3. Add unit tests for tool deploy and undeploy actions in `tests/test_deploy.py`.
  4. Add CLI end-to-end tests for `list`, `deploy`, `undeploy`, `status` with `--kind tool` in `tests/test_cli.py`.
  5. Run full test suite (`pytest`) to ensure no regressions.
- **Relevant Context:**
  - Test suite: [`tests/test_discovery.py`](tests/test_discovery.py), [`tests/test_deploy.py`](tests/test_deploy.py), [`tests/test_cli.py`](tests/test_cli.py)
- **Status:** `[ ] pending`
