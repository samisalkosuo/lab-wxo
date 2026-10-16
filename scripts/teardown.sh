#!/usr/bin/env bash
# teardown.sh
# Removes the resources created by deploy-all.sh from the active WXO environment.
# Resources are removed in reverse dependency order: agents first, then flows, then tools,
# then knowledge bases, because agents reference tools and knowledge bases.
#
# WHAT is removed comes from the scenario manifests (scenarios/<id>/scenario.yaml), read by
# scripts/scenario_manifest.py. Manifests list the REAL resource names (not file names): the tool
# package tools/incident_triage/incident_triage.py exports several @tool functions, each of which
# becomes an individual named tool in WXO. Without --scenario, EVERY scenario is removed (also
# 'soon' ones: a resource that was never deployed only gives a non-fatal warning).
#
# SAFETY: Use --dry-run to print every command without executing it.
#   bash scripts/teardown.sh --dry-run
#   bash scripts/teardown.sh --scenario incident-triage --dry-run
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
SCENARIO=""
while [ $# -gt 0 ]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --scenario) [ $# -ge 2 ] || { echo "ERROR: --scenario needs a value" >&2; exit 1; }; SCENARIO="$2"; shift 2 ;;
        --scenario=*) SCENARIO="${1#--scenario=}"; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
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
if [ -n "$SCENARIO" ]; then echo "Scenario: $SCENARIO"; else echo "Scenarios: ALL"; fi

# ── Prerequisite: orchestrate on PATH ─────────────────────────────────────────
if ! command -v orchestrate &>/dev/null; then
    echo "ERROR: 'orchestrate' not found on PATH. Activate your virtual environment first." >&2
    exit 1
fi

# ── Resolve the teardown plan from the scenario manifests ─────────────────────
# Prefer the python that sits next to the orchestrate CLI (same environment, has PyYAML).
PY=""
ORCH_DIR="$(dirname "$(command -v orchestrate)")"
for cand in "$ORCH_DIR/python" "$ORCH_DIR/python.exe" "$ORCH_DIR/python3"; do
    if [ -x "$cand" ]; then PY="$cand"; break; fi
done
if [ -z "$PY" ]; then
    PY="$(command -v python3 || command -v python || true)"
fi
if [ -z "$PY" ]; then
    echo "ERROR: Python not found. Activate the virtual environment that has ibm-watsonx-orchestrate installed." >&2
    exit 1
fi
PLAN_ARGS=("$SCRIPT_DIR/scenario_manifest.py" teardown-plan)
[ -n "$SCENARIO" ] && PLAN_ARGS+=(--scenario "$SCENARIO")
if ! PLAN="$("$PY" "${PLAN_ARGS[@]}" | tr -d '\r')"; then
    echo "ERROR: could not build the teardown plan (see message above). Aborting." >&2
    exit 1
fi
# plan_lines KIND -> the plan lines whose first field is KIND
plan_lines() { printf '%s\n' "$PLAN" | awk -F'\t' -v k="$1" '$1 == k'; }

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
# The plan lists agents in reverse manifest order, each with its kind (native|external).
#
# CLI: orchestrate agents remove --name <name> --kind <kind>
# NOTE: --kind is required per 'orchestrate agents remove --help'.
echo ""
echo "[1/5] Removing agents..."

while IFS=$'\t' read -r _ name kind; do
    invoke_remove "agents remove --name $name --kind $kind" \
        agents remove --name "$name" --kind "$kind"
done < <(plan_lines agent)

# ── Step 2: Remove flow tool ──────────────────────────────────────────────────
# Flows are imported as tools (kind=flow), e.g. the remediation approval flow.
# They must be removed before the Python tools they call (e.g. execute_remediation).
# CLI: orchestrate tools remove --name <name>
echo ""
echo "[2/5] Removing flow tool..."

while IFS=$'\t' read -r _ name; do
    invoke_remove "tools remove --name $name" \
        tools remove --name "$name"
done < <(plan_lines flow)

# ── Step 3: Remove Python tools ───────────────────────────────────────────────
# These are the @tool-decorated functions listed in each manifest's tools[].names.
# WXO registers each function as a separate named tool, named exactly as the function.
# CLI: orchestrate tools remove --name <name>
echo ""
echo "[3/5] Removing Python tools..."

while IFS=$'\t' read -r _ name; do
    invoke_remove "tools remove --name $name" \
        tools remove --name "$name"
done < <(plan_lines tool)

# ── Step 4: Remove knowledge bases ────────────────────────────────────────────
# Knowledge bases can be removed after tools because nothing references them at
# the CLI level (the reference is inside agent.yaml only, and the agent is gone).
# CLI: orchestrate knowledge-bases remove --name <name>
# NOTE: removing a built-in Milvus KB deletes the ingested document data too.
echo ""
echo "[4/5] Removing knowledge bases..."

while IFS=$'\t' read -r _ name; do
    invoke_remove "knowledge-bases remove --name $name" \
        knowledge-bases remove --name "$name"
done < <(plan_lines kb)

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
