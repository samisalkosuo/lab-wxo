#!/usr/bin/env bash
# teardown.sh
# Removes all resources created by deploy-all.sh from the active WXO environment.
# Resources are removed in reverse dependency order: agents first, then flows, then tools,
# then knowledge bases, because agents reference tools and knowledge bases.
#
# REAL RESOURCE NAMES (not file names) are used here.  The tool package
# tools/incident_triage/incident_triage.py exports several @tool functions, each of which
# becomes an individual named tool in WXO; file-name discovery does not work for packages.
#
# SAFETY: Use --dry-run to print every command without executing it.
#   bash scripts/teardown.sh --dry-run
#
# IMPORTANT — UNTESTED FOR REAL DELETION:
#   Real deletion was NEVER executed against a live instance during development.
#   The demo resources on instance 'techzone1' were preserved intentionally.
#   The --dry-run output shows the exact commands that would run, but their actual
#   behaviour (including any confirmation prompts, errors when an agent still
#   references a tool, or partial-delete side effects) is unknown.
#
#   If `orchestrate agents remove` / `orchestrate tools remove` /
#   `orchestrate knowledge-bases remove` require a --yes / --force flag to be
#   non-interactive, the commands below will hang waiting for input.  Check each
#   subcommand's --help output and add the flag if needed before running for real.
#
# Prerequisites:
#   - Copy env.cfg.example to env.cfg and fill in WXO_API_KEY, WXO_URL, WXO_ENV_NAME.
#   - The `orchestrate` CLI must be on PATH (activated venv, or system install).
#
# Usage:
#   bash scripts/teardown.sh           # real deletion (UNTESTED — see warning above)
#   bash scripts/teardown.sh --dry-run # print commands without running them

set -uo pipefail   # -e intentionally omitted: failures are non-fatal (warn and continue)

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

# ── Parse arguments ───────────────────────────────────────────────────────────
DRY_RUN=false
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

# ── Dry-run helper ────────────────────────────────────────────────────────────
invoke_remove() {
    # Usage: invoke_remove "description" arg1 arg2 ...
    local description="$1"; shift
    if $DRY_RUN; then
        echo "  [DRY-RUN] orchestrate $*"
    else
        echo "  -> $description"
        orchestrate "$@" || echo "  WARNING: orchestrate $* exited with code $? (continuing)"
    fi
}

# ── Banner ────────────────────────────────────────────────────────────────────
if $DRY_RUN; then
    echo "=== WXO Teardown (DRY-RUN — no changes will be made) ==="
else
    echo "=== WXO Teardown ==="
    echo "WARNING: Real deletion mode.  This will remove resources from the active WXO environment." >&2
    echo "NOTE: real deletion has never been tested.  Check --help for each subcommand if prompts appear." >&2
fi
echo "Root: $ROOT"

# ── Prerequisite: orchestrate on PATH ─────────────────────────────────────────
if ! command -v orchestrate &>/dev/null; then
    echo "ERROR: 'orchestrate' not found on PATH. Activate your virtual environment first." >&2
    exit 1
fi

# ── Read env.cfg and activate environment ────────────────────────────────────
# Same parsing logic as deploy-all.sh: split on the first '=' only, strip CR.
ENV_FILE="$ROOT/env.cfg"
if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: env.cfg not found at '$ENV_FILE'. Copy env.cfg.example and fill in your credentials." >&2
    exit 1
fi

WXO_API_KEY=""
WXO_URL=""
WXO_ENV_NAME=""
WXO_ENV_TYPE=""

while IFS= read -r raw_line; do
    line="$(printf '%s' "$raw_line" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    [[ -z "$line" || "$line" == \#* ]] && continue
    key="${line%%=*}"
    value="${line#*=}"
    case "$key" in
        WXO_API_KEY)  WXO_API_KEY="$value"  ;;
        WXO_URL)      WXO_URL="$value"      ;;
        WXO_ENV_NAME) WXO_ENV_NAME="$value" ;;
        WXO_ENV_TYPE) WXO_ENV_TYPE="$value" ;;
    esac
done < "$ENV_FILE"

if [ -z "$WXO_API_KEY" ] || [ -z "$WXO_URL" ] || [ -z "$WXO_ENV_NAME" ]; then
    echo "ERROR: env.cfg must define WXO_API_KEY, WXO_URL, and WXO_ENV_NAME." >&2
    exit 1
fi

WXO_ENV_TYPE="${WXO_ENV_TYPE:-ibm_iam}"

# Activate the environment so subsequent commands target the right instance.
echo ""
echo "[0/5] Registering and activating environment '$WXO_ENV_NAME' ..."
if $DRY_RUN; then
    echo "  [DRY-RUN] orchestrate env add -n $WXO_ENV_NAME -u <url> --type $WXO_ENV_TYPE"
    echo "  [DRY-RUN] orchestrate env activate $WXO_ENV_NAME --api-key ***"
else
    echo "Y" | orchestrate env add -n "$WXO_ENV_NAME" -u "$WXO_URL" --type "$WXO_ENV_TYPE" \
        || echo "WARNING: env add exited $? (may be expected if env already exists)"
    orchestrate env activate "$WXO_ENV_NAME" --api-key "$WXO_API_KEY"
fi

# ── Step 1: Remove agents ─────────────────────────────────────────────────────
# Agents must be removed first because they reference tools and knowledge bases.
# Both agents are kind=native (from agent.yaml).
#
# CLI: orchestrate agents remove --name <name> --kind native
# NOTE: --kind is required per 'orchestrate agents remove --help'.
echo ""
echo "[1/5] Removing agents..."

for agent_name in incident_triage hello_world; do
    invoke_remove "agents remove --name $agent_name --kind native" \
        agents remove --name "$agent_name" --kind native
done

# ── Step 2: Remove flow tool ──────────────────────────────────────────────────
# The remediation approval flow is imported as a tool (kind=flow).
# It must be removed before the Python tools it calls (execute_remediation).
# CLI: orchestrate tools remove --name <name>
echo ""
echo "[2/5] Removing flow tool..."

invoke_remove "tools remove --name request_remediation" \
    tools remove --name request_remediation

# ── Step 3: Remove Python tools ───────────────────────────────────────────────
# These are the @tool-decorated functions from tools/incident_triage/incident_triage.py
# and tools/greetings.py.  WXO registers each function as a separate named tool.
# The names are the function names exactly as written in the source.
# CLI: orchestrate tools remove --name <name>
echo ""
echo "[3/5] Removing Python tools..."

# tools/incident_triage/incident_triage.py — 8 @tool functions
for tool_name in \
    list_open_incidents \
    get_incident \
    get_service_health \
    query_logs \
    get_metrics \
    list_recent_deployments \
    open_ticket \
    execute_remediation
do
    invoke_remove "tools remove --name $tool_name" \
        tools remove --name "$tool_name"
done

# tools/greetings.py — single @tool function
invoke_remove "tools remove --name greeting" \
    tools remove --name greeting

# ── Step 4: Remove knowledge bases ────────────────────────────────────────────
# Knowledge bases can be removed after tools because nothing references them at
# the CLI level (the reference is inside agent.yaml only, and the agent is gone).
# CLI: orchestrate knowledge-bases remove --name <name>
# NOTE: removing a built-in Milvus KB deletes the ingested document data too.
echo ""
echo "[4/5] Removing knowledge bases..."

invoke_remove "knowledge-bases remove --name incident_triage_runbooks" \
    knowledge-bases remove --name incident_triage_runbooks

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "[5/5] Done."
if $DRY_RUN; then
    echo ""
    echo "=== Dry run complete — no changes were made ==="
    echo "Review the commands above, then run without --dry-run to perform real deletion."
    echo "REMINDER: real deletion has never been tested.  Check each subcommand's --help"
    echo "          output for confirmation-prompt flags before executing for real."
else
    echo ""
    echo "=== Teardown complete ==="
fi
