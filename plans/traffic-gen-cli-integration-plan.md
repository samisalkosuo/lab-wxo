# Plan: Traffic Generator CLI Integration into wxodemo

## Top-Level Overview
Integrate the traffic generator (`traffic-gen/`) into the main `wxodemo` CLI via a new `traffic` command group (with `traffic-gen` as an alias). This provides a first-class developer experience with subcommands `build`, `start`, `stop`, `status`, `redeploy`, `logs`, and `pool`. Credentials and configuration are read automatically from `env.cfg` (with CLI override options), container engines (`podman` or `docker`) are auto-detected, secrets are masked in logging, and all documentation is updated to recommend the `wxodemo` CLI while retaining direct container engine commands in `traffic-gen/README.md`.

---

## Sub-Tasks

### Sub-Task 1: Traffic Generator Module and CLI Wiring
- **Intent**: Create the container management and pool preview logic in `src/wxodemo/traffic.py` and register the `traffic` command group in `src/wxodemo/cli.py`.
- **Expected Outcomes**:
  - Auto-detection of container runtime (`podman` or `docker`) with optional `--engine` flag.
  - Subcommands implemented:
    - `build`: Build the `wxo-traffic-gen` container image from repository root.
    - `start`: Start the container in background (or foreground/follow mode) with credentials from `env.cfg` and optional overrides (`--interval`, `--agents`, `--env`, `--container-name`).
    - `stop`: Stop and clean up the running container.
    - `status`: Show container state (running/stopped/absent), image details, and active target configuration.
    - `redeploy`: Atomic convenience execution of stop + build + start.
    - `logs`: View and follow container log output (`-f/--follow`, `-n/--tail`).
    - `pool`: Discover and display local agent pool, flow-triggering flags, and prompt counts without running containers.
  - Full `--dry-run` support across all subcommands.
  - Secrets from `env.cfg` masked in command line logs.
- **Todo List**:
  - [x] Implement `src/wxodemo/traffic.py` with engine detection, container lifecycle helpers, and pool inspector.
  - [x] Register `traffic` (and alias `traffic-gen`) in `src/wxodemo/cli.py` with all subcommands, arguments, and dry-run handling.
  - [x] Ensure credentials from `env.cfg` are registered with `register_secret()` before execution.
- **Relevant Context**:
  - `src/wxodemo/cli.py` — parser structure and error handling patterns
  - `src/wxodemo/config.py` — `load_config()`, `repo_root()`
  - `src/wxodemo/logging_setup.py` — `register_secret()`, `ok()`, `warn()`, `fail()`, `plain()`
  - `traffic-gen/app.py` & `traffic-gen/Dockerfile` — container build context and runtime environment variables
- **Status**: `[x] done`

---

### Sub-Task 2: Automated Tests for Traffic Generator Commands
- **Intent**: Provide unit tests covering CLI argument parsing, execution paths, dry runs, error cases, and pool inspection.
- **Expected Outcomes**:
  - Unit tests in `tests/test_traffic.py` and updates in `tests/test_cli.py`.
  - Mocked subprocess executions for `podman`/`docker` verifying correct arguments, image names, and environment variables.
  - Tests verifying behavior when container engines are absent or commands fail.
  - Tests validating the `pool` command output against sample fixtures.
- **Todo List**:
  - [x] Create `tests/test_traffic.py` with unit tests for engine detection, `build`, `start`, `stop`, `status`, `redeploy`, `logs`, and `pool`.
  - [x] Update `tests/test_cli.py` to ensure `traffic` and `traffic-gen` are in documented/registered commands.
  - [x] Verify test suite passes cleanly.
- **Relevant Context**:
  - `tests/test_cli.py` & `tests/helpers.py` — test fixtures and mock patterns
- **Status**: `[x] done`

---

### Sub-Task 3: Documentation Updates
- **Intent**: Update documentation to guide users toward `wxodemo traffic ...` while keeping standalone container commands documented.
- **Expected Outcomes**:
  - Root `README.md` updated with `wxodemo traffic` commands in quick start and traffic generator sections.
  - `traffic-gen/README.md` updated to lead with `wxodemo traffic` while keeping direct `podman`/`docker` commands as standalone alternatives.
  - `docs/wxodemo.md` updated with full reference for `traffic` and its subcommands.
- **Todo List**:
  - [x] Update `README.md` traffic generator section.
  - [x] Update `traffic-gen/README.md` quick start, build, and run sections.
  - [x] Update `docs/wxodemo.md` command table and detailed command section.
- **Relevant Context**:
  - `README.md`
  - `traffic-gen/README.md`
  - `docs/wxodemo.md`
- **Status**: `[x] done`

---

### Sub-Task 4: Optional Doctor Integration & Validation
- **Intent**: Add container runtime visibility into `wxodemo doctor` and validate all components.
- **Expected Outcomes**:
  - `wxodemo doctor` reports detected container runtime (e.g. `Podman 5.x` or `Docker 27.x`) as informational (optional check).
  - Validation across repo passes without errors.
- **Todo List**:
  - [x] Add optional container engine check to `src/wxodemo/doctor.py`.
  - [x] Run full test suite (`pytest`) to ensure no regressions.
- **Relevant Context**:
  - `src/wxodemo/doctor.py`
- **Status**: `[x] done`
