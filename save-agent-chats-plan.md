# Plan: Save Agent Chats and Traces from WXO

## Top-Level Overview

This plan defines the implementation of a single-command export script (`scripts/export_agent_chats.py`) that backs up all watsonx Orchestrate (WXO) conversation histories and execution traces. 

The script operates with zero required CLI arguments by default, pulling configuration from the standard `env.cfg` file. It queries the WXO REST API for all message threads and their conversation turns, and invokes the ADK Observability Traces CLI/SDK to export trace logs. All data is structured into a timestamped directory (format `YYYYMMDDHHMMSS`, e.g., `export/20261019125234/`) with organized subdirectories for threads and traces, alongside a summary manifest.

---

## Sub-Tasks

### Sub-Task 1: Core Configuration and Authentication Handler
- **Intent**: Provide robust configuration loading from `env.cfg` and token acquisition (IBM IAM or MCSP) to authenticate against the WXO instance REST endpoints.
- **Expected Outcomes**:
  - Reusable helper functions that parse `env.cfg` adhering to repository standards.
  - Automatic IAM / MCSP token exchange returning a valid Bearer token for API requests.
  - Graceful error reporting if required configuration keys (`WXO_API_KEY`, `WXO_URL`, `WXO_ENV_NAME`) are missing.
- **Todo List**:
  1. Define configuration reader loading `env.cfg` from repo root or a user-specified path.
  2. Implement OAuth2 token retrieval for IBM Cloud IAM (`https://iam.cloud.ibm.com/identity/token`) and MCSP environments.
  3. Validate URL normalization for `WXO_URL` instance endpoints.
- **Relevant Context**:
  - `standalone/manage.py:94-114` (configuration parsing pattern)
  - `env.cfg.example`
- **Status**: [x] done

---

### Sub-Task 2: REST API Message Threads & Chat Exporter
- **Intent**: Query the WXO Message Threads API to extract all conversational threads, handle pagination, and retrieve full message histories for each thread.
- **Expected Outcomes**:
  - Extraction of all threads via `GET /v1/threads` (with pagination support and optional agent filtering).
  - Retrieval of all message turns for each thread via `GET /v1/threads/{thread_id}/messages`.
  - Individual thread JSON files written to `<export_dir>/threads/<thread_id>.json`.
  - Consolidated index and metadata file written to `<export_dir>/threads/summary.json`.
- **Todo List**:
  1. Implement paginated fetching of threads from `/v1/threads`.
  2. Implement per-thread message fetching from `/v1/threads/{thread_id}/messages`.
  3. Structure the output into `threads/<thread_id>.json` and `threads/summary.json`.
  4. Ensure robust error handling for rate limits, empty threads, and transient connection issues.
- **Relevant Context**:
  - OpenAPI endpoints: `/v1/threads`, `/v1/threads/{thread_id}/messages`
  - OpenAPI schemas: `Thread`, `Message`
- **Status**: [x] done

---

### Sub-Task 3: ADK Observability Traces Exporter
- **Intent**: Extract execution traces and span observations from WXO using the ADK CLI (`orchestrate observability traces`) or SDK.
- **Expected Outcomes**:
  - Execution of trace search across configurable time windows (e.g., `--last 30d` by default).
  - Export of individual trace observations via `orchestrate observability traces export` for each discovered trace ID.
  - Individual trace JSON files written to `<export_dir>/traces/<trace_id>.json`.
  - Consolidated index file written to `<export_dir>/traces/summary.json`.
  - Graceful fallback and reporting if ADK CLI is unauthenticated or no traces exist in the window.
- **Todo List**:
  1. Implement trace discovery using `orchestrate observability traces search`.
  2. Implement observation exporting using `orchestrate observability traces export`.
  3. Save exported trace files into `traces/<trace_id>.json` and index them in `traces/summary.json`.
  4. Ensure clean handling when observability traces are disabled or empty.
- **Relevant Context**:
  - Documentation: `/traces/traces_with_cli.mdx`
  - CLI commands: `orchestrate observability traces search`, `orchestrate observability traces export`
- **Status**: [x] done

---

### Sub-Task 4: Main Script Orchestration & Output Directory Layout
- **Intent**: Assemble the backup pipeline into a unified CLI script (`scripts/export_agent_chats.py`) with zero-argument defaults, timestamped output directories, and optional CLI flags.
- **Expected Outcomes**:
  - Single-command execution: `python scripts/export_agent_chats.py` running with no arguments.
  - Creation of output folder `export/YYYYMMDDHHMMSS/` with `threads/`, `traces/`, and top-level `manifest.json`.
  - Helpful optional flags: `--output-dir`, `--agent-id`, `--last`, `--threads-only`, `--traces-only`, `--env-file`.
  - Comprehensive execution summary printed to stdout (number of threads, messages, and traces backed up).
- **Todo List**:
  1. Define CLI argument parser with argparse.
  2. Generate timestamp directory string in `YYYYMMDDHHMMSS` format (e.g., `20261019125234`).
  3. Execute threads exporter and traces exporter workflows in sequence.
  4. Write top-level `manifest.json` containing export timestamp, instance URL, counts, and duration.
  5. Print formatted CLI status output.
- **Relevant Context**:
  - `scripts/` directory conventions
  - `scripts/smoke_test.py` and `standalone/manage.py`
- **Status**: [x] done

---

### Sub-Task 5: Verification and Documentation
- **Intent**: Verify script execution across various parameter configurations and document its usage.
- **Expected Outcomes**:
  - Successful dry-run / execution verification showing created files and directory structure.
  - Documentation added or updated (e.g., in `scripts/README.md` or top-level docs) explaining how to use the backup tool.
- **Todo List**:
  1. Test script with argument parsing and help banner (`--help`).
  2. Verify error handling when `env.cfg` is missing or when backend endpoints return errors.
  3. Verify output directory structure and JSON formatting.
  4. Add usage documentation for the backup script.
- **Status**: [x] done
