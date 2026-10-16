"""Build dist/wxo-incident-triage-<version>.zip for external users.

Usage:
    python scripts/package.py [--version 1.0.0]

The zip contains everything an external user needs to deploy the incident-triage
demo into their own watsonx Orchestrate instance.  It uses an ALLOW-LIST (only
listed paths are added) and then a DENY-LIST post-build check (fails with a non-
zero exit code and deletes the zip if any denied path or secret-bearing pattern
is found).

What ships:
    agents/incident-triage/       (agent.yaml + README.md)
    tools/incident_triage/        (multi-file package; no __pycache__)
    knowledge/incident-triage/    (KB yaml + runbooks)
    flows/incident_triage/        (request_remediation.py; no __pycache__)
    evaluation/incident-triage/   (test_cases/, eval_config.yaml, baseline.py,
                                   ground_truth.json -- NOT results/ or eval_run.log)
    docs/demo/                    (incident-triage-demo.md)
    scripts/deploy-all.ps1
    scripts/deploy-all.sh
    scripts/teardown.ps1          (safe: reads env.cfg, no secrets, -DryRun supported)
    scripts/teardown.sh           (safe: reads env.cfg, no secrets, --dry-run supported)
    env.cfg.example
    requirements.txt
    INSTALL.md                    (written by this script at the zip root)

What does NOT ship (by design):
    agents/hello-world/           — unrelated to the triage demo
    tools/greetings.py            — unrelated to the triage demo
    scripts/smoke_test_triage.py  — hard-codes an instance-specific agent UUID
    env.cfg                       — secrets
    local/                        — secrets (local/notes.md contains API keys)
    .venv/ .bob/ .orchestrate/    — local tooling state
    .git/                         — version-control history
    dist/                         — build output
    __pycache__/ *.pyc / *.pyo    — compiled bytecode
    evaluation/incident-triage/results/   — large, instance-specific result data
    evaluation/incident-triage/eval_run.log — instance-specific log

The post-build security check scans every entry name against the deny-list and
scans every TEXT entry for the literal string WXO_API_KEY= followed by a non-
empty value, and for long token-like strings (>= 40 chars of base64/hex chars
without whitespace).  If any check fails the zip is deleted and the script exits
non-zero.

NEVER reads, prints, or modifies env.cfg or local/notes.md.
"""

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VERSION_DEFAULT = "1.0.0"

# Patterns of zip-entry names (after normalisation to forward slashes) that must
# NEVER appear in the zip.  Checked after the build.
DENY_PATTERNS: list[str] = [
    r"(^|/)env\.cfg$",           # real secrets file (not .example)
    r"(^|/)local/",              # local/ directory and its contents
    r"(^|/)\.venv/",             # Python virtual environment
    r"(^|/)\.git(/|$)",          # git repository
    r"(^|/)dist/",               # build output
    r"(^|/)__pycache__/",        # compiled Python cache
    r"\.pyc$",                   # compiled Python bytecode
    r"\.pyo$",                   # optimised bytecode
    r"(^|/)\.bob/",              # Bob AI assistant state
    r"(^|/)\.orchestrate/",      # orchestrate CLI state
    r"(^|/)results/",            # evaluation result dumps (large, instance-specific)
    r"eval_run\.log$",           # evaluation log (instance-specific)
    r"smoke_test_triage\.py$",   # hard-coded instance UUID — excluded by design
    r"(^|/)agents/hello-world/", # unrelated agent
    r"(^|/)tools/greetings\.py$", # unrelated tool
]

# Secret-value patterns to scan inside text entries.
# Pattern 1: WXO_API_KEY= followed by a value that is not:
#   - empty / end-of-line
#   - a placeholder string (your-api-key-here, <...>, $..., "$...", "")
#   - a shell variable reference ($VALUE, "$VALUE", '""', etc.)
SECRET_VALUE_PATTERN = re.compile(
    r'WXO_API_KEY='           # key name
    r'(?!'                    # negative lookahead — safe values:
        r'your-api-key-here'  # our standard placeholder
        r'|<[^>]+>'           # angle-bracket placeholders like <your IBM Cloud API key>
        r'|\$[A-Za-z_]'       # shell variable $value
        r'|"\$[A-Za-z_]'     # quoted shell variable "$value"
        r'|""'                # empty string assignment
        r'|\s*$'              # end of line / whitespace only
    r')'
    r'(.+)',
    re.IGNORECASE
)
# Pattern 2: long token-like strings.
# Real API keys / tokens are random base64 or hex — they do NOT contain
# underscores (Python identifiers) or forward slashes used as path separators.
# We use a character class that does include the base64 slash (+/=) but then
# filter out any token that also contains an underscore or a slash, which
# distinguishes file paths and identifiers from actual secret tokens.
LONG_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9+/=]{40,}")

# File extensions we decode and scan for secrets (text files only)
TEXT_EXTENSIONS = {
    ".py", ".sh", ".ps1", ".yaml", ".yml", ".json", ".txt", ".md",
    ".cfg", ".env", ".example", ".ini", ".toml", ".conf",
}

# ---------------------------------------------------------------------------
# Allow-list: explicit source paths (relative to repo root) to include.
# For directories the entire tree is added except __pycache__ and .pyc files.
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


def build_allow_list() -> list[tuple[Path, str]]:
    """Return a list of (absolute_src_path, zip_entry_name) pairs.

    zip_entry_name uses forward slashes (POSIX) regardless of OS.
    """
    pairs: list[tuple[Path, str]] = []

    def add_tree(src_dir: Path, zip_prefix: str) -> None:
        """Walk src_dir and add every eligible file under zip_prefix/."""
        for abs_path in sorted(src_dir.rglob("*")):
            if not abs_path.is_file():
                continue
            rel = abs_path.relative_to(src_dir)
            parts = rel.parts
            # Skip __pycache__ directories and compiled bytecode
            if any(p == "__pycache__" for p in parts):
                continue
            if abs_path.suffix in (".pyc", ".pyo"):
                continue
            entry = zip_prefix + "/" + "/".join(parts)
            pairs.append((abs_path, entry))

    def add_file(src_file: Path, entry_name: str) -> None:
        if src_file.is_file():
            pairs.append((src_file, entry_name))
        else:
            print(f"  WARNING: expected file not found: {src_file}", file=sys.stderr)

    # Agents (triage only — hello-world excluded by design)
    add_tree(REPO_ROOT / "agents" / "incident-triage", "agents/incident-triage")

    # Tools package (triage only — greetings.py excluded by design)
    add_tree(REPO_ROOT / "tools" / "incident_triage", "tools/incident_triage")

    # Knowledge base
    add_tree(REPO_ROOT / "knowledge" / "incident-triage", "knowledge/incident-triage")

    # Flows
    add_tree(REPO_ROOT / "flows" / "incident_triage", "flows/incident_triage")

    # Evaluation — test_cases, eval_config, baseline, ground_truth
    # results/ and eval_run.log deliberately excluded
    eval_base = REPO_ROOT / "evaluation" / "incident-triage"
    add_tree(eval_base / "test_cases", "evaluation/incident-triage/test_cases")
    add_file(eval_base / "eval_config.yaml", "evaluation/incident-triage/eval_config.yaml")
    add_file(eval_base / "baseline.py", "evaluation/incident-triage/baseline.py")
    add_file(eval_base / "ground_truth.json", "evaluation/incident-triage/ground_truth.json")

    # Demo script
    add_tree(REPO_ROOT / "docs" / "demo", "docs/demo")

    # Deploy scripts
    add_file(REPO_ROOT / "scripts" / "deploy-all.ps1", "scripts/deploy-all.ps1")
    add_file(REPO_ROOT / "scripts" / "deploy-all.sh", "scripts/deploy-all.sh")

    # Teardown scripts (safe for external users: read env.cfg, no hardcoded secrets,
    # -DryRun / --dry-run modes print commands without executing)
    add_file(REPO_ROOT / "scripts" / "teardown.ps1", "scripts/teardown.ps1")
    add_file(REPO_ROOT / "scripts" / "teardown.sh", "scripts/teardown.sh")

    # Top-level files
    add_file(REPO_ROOT / "env.cfg.example", "env.cfg.example")
    add_file(REPO_ROOT / "requirements.txt", "requirements.txt")

    # INSTALL.md is generated and injected inline — see build_zip()

    return pairs


# ---------------------------------------------------------------------------
# Post-build security check
# ---------------------------------------------------------------------------

def check_zip(zip_path: Path) -> list[str]:
    """Return a list of violation strings.  Empty list = clean."""
    violations: list[str] = []
    deny_compiled = [re.compile(p) for p in DENY_PATTERNS]

    with zipfile.ZipFile(zip_path, "r") as zf:
        entries = sorted(zf.namelist())
        print("\n--- Zip entry list ---")
        for name in entries:
            print(" ", name)
        print(f"--- Total: {len(entries)} entries ---\n")

        for name in entries:
            # 1. Deny-list check on entry name
            for pattern in deny_compiled:
                if pattern.search(name):
                    violations.append(f"DENY-LIST MATCH: '{name}' matches /{pattern.pattern}/")

            # 2. Scan text entries for secret patterns
            lower_name = name.lower()
            ext = Path(name).suffix.lower()
            if ext in TEXT_EXTENSIONS:
                try:
                    raw = zf.read(name)
                    text = raw.decode("utf-8", errors="replace")
                    lines = text.splitlines()
                    for lineno, line in enumerate(lines, 1):
                        m = SECRET_VALUE_PATTERN.search(line)
                        if m:
                            violations.append(
                                f"SECRET PATTERN in {name}:{lineno}: "
                                f"WXO_API_KEY= with non-placeholder value"
                            )
                        # Long-token check: look for tokens >= 40 chars that look
                        # like random secrets.  LONG_TOKEN_PATTERN already excludes
                        # dots and hyphens so file paths and package names don't
                        # match.  Skip additional safe contexts below.
                        if "http" not in line and "github.com" not in line:
                            tokens = LONG_TOKEN_PATTERN.findall(line)
                            for tok in tokens:
                                # Paths and Python identifiers contain _ or /
                                if "_" in tok or "/" in tok:
                                    continue
                                # All-uppercase = env var name or constant
                                if re.match(r"^[A-Z]+$", tok):
                                    continue
                                # All-lowercase = word or identifier
                                if re.match(r"^[a-z]+$", tok):
                                    continue
                                # Skip known placeholder text
                                if "your-api-key-here" in tok or "instance-id" in tok:
                                    continue
                                violations.append(
                                    f"LONG TOKEN in {name}:{lineno}: "
                                    f"'{tok[:20]}...' ({len(tok)} chars) — review manually"
                                )
                except Exception as exc:
                    violations.append(f"SCAN ERROR reading {name}: {exc}")

    return violations


# ---------------------------------------------------------------------------
# INSTALL.md content
# ---------------------------------------------------------------------------

INSTALL_MD = r"""\
# Incident Triage Agent — Installation Guide

## What this package contains

A fully self-contained watsonx Orchestrate (WXO) demo agent that triages
production incidents over a fixed mock dataset. No external services are
called. Everything in this zip is an exact export from the development repo.

Included:
- `agents/incident-triage/`        — agent YAML and README
- `tools/incident_triage/`         — multi-file Python tool package (8 tools)
- `knowledge/incident-triage/`     — knowledge base YAML + 6 runbook `.txt` files
- `flows/incident_triage/`         — remediation approval flow
- `evaluation/incident-triage/`    — test cases, eval config, baseline script,
                                     ground truth (results not included — see below)
- `docs/demo/`                     — human-readable demo script
- `scripts/deploy-all.ps1`         — Windows deployment script
- `scripts/deploy-all.sh`          — Linux/macOS deployment script
- `env.cfg.example`                — configuration template
- `requirements.txt`               — `ibm-watsonx-orchestrate==2.18.2`

**Not included (by design):**
- `agents/hello-world/` and `tools/greetings.py` — unrelated to this demo
- `scripts/smoke_test_triage.py` — hard-codes a UUID specific to one instance
- `evaluation/incident-triage/results/` — large, instance-specific result data
- `env.cfg` and `local/` — secrets

---

## Prerequisites

### 1. Python

**Python 3.11 or later**, per the ADK docs (no upper bound is stated there).
This project was developed and deployed on Python 3.14 and deployment worked.
On 3.14 the evaluation framework's `pandas~=2.2.3` pin could not be satisfied
(no pre-built wheel), so the evaluation dependencies were installed by hand.
Whether the evaluation framework installs cleanly on Python 3.11-3.13 was NOT
tested here.  See the ADK docs:
https://developer.watson-orchestrate.ibm.com/getting_started/installing

### 2. IBM watsonx Orchestrate ADK CLI

Install into your active Python environment:

```bash
pip install ibm-watsonx-orchestrate==2.18.2
```

Verify:

```bash
orchestrate --version
```

### 3. Required model and embedding model

The agent uses `groq/openai/gpt-oss-120b`. The knowledge base uses the default
embedding model `ibm/slate-125m-english-rtrvr-v2`. Both must be available in your
WXO instance. If the LLM is unavailable, edit `agents/incident-triage/agent.yaml`
and replace the `llm:` value with a model your instance offers.

---

## Configuration

1. Copy the example config file and fill in your credentials:

   ```bash
   cp env.cfg.example env.cfg
   ```

2. Edit `env.cfg`:

   ```ini
   WXO_API_KEY=<your IBM Cloud API key>
   WXO_URL=https://api.<region>.watson-orchestrate.cloud.ibm.com/instances/<id>
   WXO_ENV_NAME=<a short name for your environment, e.g. my-env>
   # Optional: authentication type.  Default is ibm_iam (IBM Cloud IAM).
   # Use mcsp for AWS-hosted WXO instances.
   WXO_ENV_TYPE=ibm_iam
   ```

   - `WXO_API_KEY` — IBM Cloud API key with access to your WXO instance.
   - `WXO_URL` — the API base URL for your instance (from the WXO web UI, under
     Settings, not the browser URL).
   - `WXO_ENV_NAME` — any short alphanumeric name; used locally by the CLI.
   - `WXO_ENV_TYPE` — `ibm_iam` (default, IBM Cloud) or `mcsp` (AWS).

   **Keep `env.cfg` private.** Never commit it to version control.

---

## Deployment

### Windows (PowerShell)

```powershell
$env:PYTHONUTF8 = "1"   # avoids cp1252 encoding errors on Windows
.\\scripts\\deploy-all.ps1
```

### Linux / macOS (bash)

```bash
bash scripts/deploy-all.sh
```

The script reads `env.cfg`, registers the WXO environment non-interactively,
then imports resources in dependency order:
connections → tools (Python package) → knowledge base → flow → agent → deploy.

Re-running is safe: existing resources are updated in place.

**Auth expiry:** the remote authentication token expires after **2 hours**.
If you are deploying in multiple sessions or running the demo after a gap,
re-run the deploy script (or just the activate step) before starting.

---

## Opening the agent in the chat UI

1. Log in to your WXO instance in the browser.
2. Go to the chat, and in the agent picker select **Incident Triage**.
3. If the agent is not listed: `orchestrate agents deploy --name incident_triage`
   and reload the page.  Imported agents start as drafts; the deploy step
   promotes them to live.  The deploy scripts do this automatically.

---

## Knowledge base indexing

The knowledge base is embedded and indexed server-side after import. Check it
with `orchestrate knowledge-bases status` and wait until it reads `ready` before
using the agent. (Indexing time was not measured here.)

---

## Running the evaluation (optional)

> **Dependency warning (Open Item 5):** the evaluation framework
> `ibm-watsonx-orchestrate-evaluation-framework==1.5.2` and its transitive
> dependencies (`agentops`, `langchain`, `fuzzywuzzy`, `portkey-ai`,
> `openinference-*`, `jsonargparse`) are NOT installed automatically.  On
> Python 3.14 the `pandas~=2.2.3` pin cannot be satisfied.  On other Python
> versions you can try (untested here):
>
> ```bash
> pip install ibm-watsonx-orchestrate-evaluation-framework==1.5.2
> ```
>
> If pip fails on the pandas pin, use `--no-deps` and install pandas separately:
>
> ```bash
> pip install --no-deps ibm-watsonx-orchestrate-evaluation-framework==1.5.2
> pip install pandas
> ```
>
> A clean-instance install of the evaluation framework was not tested in this
> project.  The dependency issue was resolved manually on the development machine.
> Do not assume it installs cleanly.

Once dependencies are installed:

```bash
orchestrate evaluations evaluate --config evaluation/incident-triage/eval_config.yaml
```

Note: the command exits with code 1 when its output is piped or redirected (a
progress-rendering issue).  The result files are still written to
`evaluation/incident-triage/results/<timestamp>/`.

The plain-code baseline needs no WXO connection:

```bash
python evaluation/incident-triage/baseline.py
```

The evaluation results folder (`results/`) was not included in this zip because
it is large and specific to one instance.  Scene 6 of the demo script refers to
a file from that folder (`summary_metrics.csv`); run the evaluation yourself to
produce it, or skip that step during the demo.

---

## Removing everything

Use the included teardown scripts to remove all resources in the correct order
(agents first, then flows, then tools, then knowledge bases):

### Windows (PowerShell)

```powershell
$env:PYTHONUTF8 = "1"
.\scripts\teardown.ps1 -DryRun   # preview -- prints commands, makes no changes
.\scripts\teardown.ps1            # real deletion (see warning below)
```

### Linux / macOS (bash)

```bash
bash scripts/teardown.sh --dry-run   # preview
bash scripts/teardown.sh             # real deletion (see warning below)
```

**IMPORTANT -- real deletion was never tested during development.** The `-DryRun`
/ `--dry-run` output shows the exact CLI commands that would run:

```
orchestrate agents remove --name incident_triage --kind native
orchestrate agents remove --name hello_world --kind native
orchestrate tools remove --name request_remediation
orchestrate tools remove --name list_open_incidents
orchestrate tools remove --name get_incident
orchestrate tools remove --name get_service_health
orchestrate tools remove --name query_logs
orchestrate tools remove --name get_metrics
orchestrate tools remove --name list_recent_deployments
orchestrate tools remove --name open_ticket
orchestrate tools remove --name execute_remediation
orchestrate tools remove --name greeting
orchestrate knowledge-bases remove --name incident_triage_runbooks
```

The scripts read `env.cfg` and never print secrets. Run `--dry-run` first, then
check `orchestrate agents remove --help`, `orchestrate tools remove --help`, and
`orchestrate knowledge-bases remove --help` for any confirmation-prompt flags
before executing for real (none were found in `--help` output, but interactive
prompts at runtime were not tested).

---

## Known issues and honest notes

- **A clean-instance install was not tested.** The only tested deploy was a
  re-install over an existing environment (`techzone1`) that already had all
  resources.  Re-import is idempotent (existing resources are updated), but
  first-import on a fresh instance was not verified.
- **The bash deploy script was run only via Git Bash on Windows** and has not
  been tested on native Linux or macOS.
- **Evaluation final-answer check:** passes 0 of 15 runs on the development
  machine.  The tool-selection metrics are good (recall 1.0 in 13/15 runs), but
  `is_success` requires both tool and text checks to pass.  The text check fails
  because the agent writes IDs with non-breaking hyphens (U+2011) and produces
  long answers compared with one-line expectations.  Do not expect a green score.
- **Scene 6 of the demo script** references
  `evaluation/incident-triage/results/2026-10-16_11-37-26/summary_metrics.csv`
  which is from the development instance and is not in this zip.  Run the
  evaluation to produce your own results, or skip that part.
- **smoke_test_triage.py** is excluded from this package because it hard-codes
  the agent UUID from the development instance.  To run smoke tests, look up your
  agent's UUID with `orchestrate agents list -v` and pass it via an environment
  variable, or copy the script and edit `AGENT_UUID` to match your instance.
- **Auth expiry:** the WXO remote token lasts 2 hours.  Re-run the deploy script
  or `orchestrate env activate $envName --api-key $apiKey` before the demo.
"""


# ---------------------------------------------------------------------------
# Main build function
# ---------------------------------------------------------------------------

def build_zip(version: str) -> Path:
    dist_dir = REPO_ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    zip_name = f"wxo-incident-triage-{version}.zip"
    zip_path = dist_dir / zip_name

    print(f"Building {zip_path} ...")

    pairs = build_allow_list()

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add INSTALL.md at the zip root first
        zf.writestr("INSTALL.md", INSTALL_MD)
        print("  + INSTALL.md  (generated)")

        for abs_path, entry_name in pairs:
            # Safety: reject any pair whose entry name would be denied
            for pattern in DENY_PATTERNS:
                if re.search(pattern, entry_name):
                    raise RuntimeError(
                        f"Allow-list/deny-list conflict: "
                        f"'{entry_name}' matches deny pattern /{pattern}/. "
                        f"Fix build_allow_list()."
                    )
            zf.write(abs_path, entry_name)
            print(f"  + {entry_name}")

    print(f"\nZip written: {zip_path} ({zip_path.stat().st_size:,} bytes)")
    return zip_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the incident-triage external zip.")
    parser.add_argument("--version", default=VERSION_DEFAULT, help="Version string")
    args = parser.parse_args()

    zip_path = build_zip(args.version)

    print("\nRunning post-build security check ...")
    violations = check_zip(zip_path)

    if violations:
        print("\n*** SECURITY CHECK FAILED ***", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        print(f"\nDeleting {zip_path}", file=sys.stderr)
        zip_path.unlink(missing_ok=True)
        sys.exit(1)
    else:
        print("Security check passed. No denied paths or secret patterns found.")
        print(f"\nPackage ready: {zip_path}")


if __name__ == "__main__":
    main()
