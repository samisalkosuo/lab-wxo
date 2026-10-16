#!/usr/bin/env bash
# deploy-all.sh
# Deploys scenarios to a WXO environment non-interactively.
# Reads credentials from env.cfg in the repository root; never reads secrets from other sources.
#
# What gets deployed comes from the scenario manifests (scenarios/<id>/scenario.yaml), read by
# scripts/scenario_manifest.py. Without --scenario, every manifest with `status: live` is deployed.
#
# Import order (dependency chain):
#   connections -> tools (flat .py, OpenAPI .yaml, package folders) -> knowledge bases -> flows -> agents
#
# Prerequisites:
#   - Copy env.cfg.example to env.cfg and fill in WXO_API_KEY, WXO_URL, WXO_ENV_NAME.
#   - The `orchestrate` CLI must be on PATH (activated venv, or system install).
#   - Python with PyYAML (the one that runs `orchestrate`; ibm-watsonx-orchestrate depends on PyYAML).
#
# Usage:
#   bash scripts/deploy-all.sh                             # every live scenario
#   bash scripts/deploy-all.sh --scenario incident-triage  # one scenario

set -euo pipefail

SCENARIO=""
while [ $# -gt 0 ]; do
    case "$1" in
        --scenario) [ $# -ge 2 ] || { echo "ERROR: --scenario needs a value" >&2; exit 1; }; SCENARIO="$2"; shift 2 ;;
        --scenario=*) SCENARIO="${1#--scenario=}"; shift ;;
        -h|--help) sed -n '2,19p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) echo "ERROR: unknown argument '$1'. Usage: deploy-all.sh [--scenario ID]" >&2; exit 1 ;;
    esac
done

# The orchestrate CLI prints Unicode symbols after knowledge-base import. On Windows (Git Bash) Python defaults
# to cp1252 for redirected output and crashes with UnicodeEncodeError. Force UTF-8 (harmless on Linux/macOS).
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

# ── Prerequisite: orchestrate on PATH ─────────────────────────────────────
if ! command -v orchestrate &>/dev/null; then
    echo "ERROR: 'orchestrate' not found on PATH. Activate your virtual environment first." >&2
    exit 1
fi

# ── Resolve the deploy plan from the scenario manifests ───────────────────
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
PLAN_ARGS=("$SCRIPT_DIR/scenario_manifest.py" deploy-plan)
[ -n "$SCENARIO" ] && PLAN_ARGS+=(--scenario "$SCENARIO")
if ! PLAN="$("$PY" "${PLAN_ARGS[@]}" | tr -d '\r')"; then
    echo "ERROR: could not build the deploy plan (see message above). Aborting." >&2
    exit 1
fi
# plan_lines KIND... -> the plan lines whose first field is one of the given kinds
plan_lines() {
    local kind
    for kind in "$@"; do printf '%s\n' "$PLAN" | awk -F'\t' -v k="$kind" '$1 == k'; done
}

# ── Read env.cfg ───────────────────────────────────────────────────────────
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
    # Strip CR (for Windows-edited files) and leading/trailing whitespace
    line="$(printf '%s' "$raw_line" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
    # Skip blank lines and comments
    [[ -z "$line" || "$line" == \#* ]] && continue
    # Split on the FIRST '=' only
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

echo "=== WXO Deploy All ==="
echo "Root: $ROOT"
if [ -n "$SCENARIO" ]; then echo "Scenario: $SCENARIO"; else echo "Scenarios: all with status 'live'"; fi

# ── Register and activate environment ────────────────────────────────────
echo ""
echo "[0/6] Registering and activating environment '$WXO_ENV_NAME' ..."
echo "    orchestrate env add -n $WXO_ENV_NAME -u <url> --type $WXO_ENV_TYPE"
# 'env add' asks "update the environment?" when the name already exists; answer Y so re-runs are non-interactive.
echo "Y" | orchestrate env add -n "$WXO_ENV_NAME" -u "$WXO_URL" --type "$WXO_ENV_TYPE"

echo "    orchestrate env activate $WXO_ENV_NAME --api-key ***"
orchestrate env activate "$WXO_ENV_NAME" --api-key "$WXO_API_KEY"

# ── Connections ────────────────────────────────────────────────────────────
echo ""
echo "[1/6] Importing connections..."
CONNECTIONS_DIR="$ROOT/connections"
if [ -d "$CONNECTIONS_DIR" ]; then
    while IFS= read -r -d '' file; do
        echo "    connections import -f $(basename "$file")"
        orchestrate connections import -f "$file"
    done < <(find "$CONNECTIONS_DIR" -name "*.yaml" -print0 | sort -z)
else
    echo "  (no connections/ directory, skipping)"
fi

# ── Tools ─────────────────────────────────────────────────────────────────
echo ""
echo "[2/6] Importing tools..."
n=0
while IFS=$'\t' read -r kind p1 p2 p3; do
    [ -n "$kind" ] || continue
    n=$((n + 1))
    case "$kind" in
        tool_py)
            echo "    tools import -k python -f $(basename "$p1")"
            orchestrate tools import -k python -f "$ROOT/$p1" ;;
        tool_openapi)
            echo "    tools import -k openapi -f $(basename "$p1")"
            orchestrate tools import -k openapi -f "$ROOT/$p1" ;;
        tool_pkg)
            echo "    tools import -k python -p $(basename "$p1") -f $(basename "$p2") -r requirements.txt"
            orchestrate tools import -k python -p "$ROOT/$p1" -f "$ROOT/$p2" -r "$ROOT/$p3" ;;
    esac
done < <(plan_lines tool_py tool_openapi tool_pkg)
[ "$n" -gt 0 ] || echo "  (no tools in the plan, skipping)"

# ── Knowledge bases ────────────────────────────────────────────────────────
echo ""
echo "[3/6] Importing knowledge bases..."
n=0
while IFS=$'\t' read -r kind p1; do
    [ -n "$kind" ] || continue
    n=$((n + 1))
    echo "    knowledge-bases import -f $(basename "$p1")"
    orchestrate knowledge-bases import -f "$ROOT/$p1"
done < <(plan_lines kb)
[ "$n" -gt 0 ] || echo "  (no knowledge bases in the plan, skipping)"

# ── Flows ─────────────────────────────────────────────────────────────────
echo ""
echo "[4/6] Importing flows..."
n=0
while IFS=$'\t' read -r kind p1; do
    [ -n "$kind" ] || continue
    n=$((n + 1))
    echo "    tools import -k flow -f $(basename "$p1")"
    orchestrate tools import -k flow -f "$ROOT/$p1"
done < <(plan_lines flow)
[ "$n" -gt 0 ] || echo "  (no flows in the plan, skipping)"

# ── Agents ─────────────────────────────────────────────────────────────────
echo ""
echo "[5/6] Importing agents..."
n=0
while IFS=$'\t' read -r kind p1 agent_name; do
    [ -n "$kind" ] || continue
    n=$((n + 1))
    echo "    agents import -f ${p1#agents/}"
    orchestrate agents import -f "$ROOT/$p1"

    # 'agents import' creates a DRAFT agent. The chat UI lists only LIVE agents,
    # so promote it. This fails on the Developer Edition (draft only); warn and continue.
    echo "    agents deploy --name $agent_name"
    if ! orchestrate agents deploy --name "$agent_name"; then
        echo "WARNING: agents deploy failed for '$agent_name'. The agent exists as a draft; it may not appear in the chat UI." >&2
    fi
done < <(plan_lines agent)
[ "$n" -gt 0 ] || echo "  (no agents in the plan, skipping)"

echo ""
echo "=== Deploy complete ==="
