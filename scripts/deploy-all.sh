#!/usr/bin/env bash
# deploy-all.sh
# Deploys all resource types to a WXO environment non-interactively.
# Reads credentials from env.cfg in the repository root; never reads secrets from other sources.
#
# Import order (dependency chain):
#   connections -> tools (flat .py, OpenAPI .yaml, package folders) -> knowledge bases -> flows -> agents
#
# Prerequisites:
#   - Copy env.cfg.example to env.cfg and fill in WXO_API_KEY, WXO_URL, WXO_ENV_NAME.
#   - The `orchestrate` CLI must be on PATH (activated venv, or system install).
#
# Usage:
#   bash scripts/deploy-all.sh

set -euo pipefail

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
TOOLS_DIR="$ROOT/tools"
if [ -d "$TOOLS_DIR" ]; then
    # Single-file Python tools: tools/*.py
    while IFS= read -r -d '' file; do
        echo "    tools import -k python -f $(basename "$file")"
        orchestrate tools import -k python -f "$file"
    done < <(find "$TOOLS_DIR" -maxdepth 1 -name "*.py" -print0 | sort -z)

    # OpenAPI tools: tools/*.yaml
    while IFS= read -r -d '' file; do
        echo "    tools import -k openapi -f $(basename "$file")"
        orchestrate tools import -k openapi -f "$file"
    done < <(find "$TOOLS_DIR" -maxdepth 1 -name "*.yaml" -print0 | sort -z)

    # Multi-file Python package tools: tools/<name>/ with requirements.txt
    while IFS= read -r -d '' pkg_dir; do
        req_file="$pkg_dir/requirements.txt"
        [ -f "$req_file" ] || continue
        # Find top-level .py entry files inside the package folder
        found_entry=0
        while IFS= read -r -d '' entry; do
            found_entry=1
            echo "    tools import -k python -p $(basename "$pkg_dir") -f $(basename "$entry") -r requirements.txt"
            orchestrate tools import -k python \
                -p "$pkg_dir" \
                -f "$entry" \
                -r "$req_file"
        done < <(find "$pkg_dir" -maxdepth 1 -name "*.py" ! -name "__init__.py" -print0 | sort -z)
        if [ "$found_entry" -eq 0 ]; then
            echo "  WARNING: package '$(basename "$pkg_dir")' has requirements.txt but no top-level .py entry file; skipping." >&2
        fi
    done < <(find "$TOOLS_DIR" -mindepth 1 -maxdepth 1 -type d -print0 | sort -z)
else
    echo "  (no tools/ directory, skipping)"
fi

# ── Knowledge bases ────────────────────────────────────────────────────────
echo ""
echo "[3/6] Importing knowledge bases..."
KNOWLEDGE_DIR="$ROOT/knowledge"
if [ -d "$KNOWLEDGE_DIR" ]; then
    while IFS= read -r -d '' file; do
        echo "    knowledge-bases import -f $(basename "$file")"
        orchestrate knowledge-bases import -f "$file"
    done < <(find "$KNOWLEDGE_DIR" -name "*.yaml" -print0 | sort -z)
else
    echo "  (no knowledge/ directory, skipping)"
fi

# ── Flows ─────────────────────────────────────────────────────────────────
echo ""
echo "[4/6] Importing flows..."
FLOWS_DIR="$ROOT/flows"
if [ -d "$FLOWS_DIR" ]; then
    while IFS= read -r -d '' file; do
        echo "    tools import -k flow -f $(basename "$file")"
        orchestrate tools import -k flow -f "$file"
    done < <(find "$FLOWS_DIR" -name "*.py" -print0 | sort -z)
else
    echo "  (no flows/ directory, skipping)"
fi

# ── Agents ─────────────────────────────────────────────────────────────────
echo ""
echo "[5/6] Importing agents..."
AGENTS_DIR="$ROOT/agents"
if [ -d "$AGENTS_DIR" ]; then
    while IFS= read -r -d '' agent_yaml; do
        agent_dir="$(basename "$(dirname "$agent_yaml")")"
        echo "    agents import -f $agent_dir/agent.yaml"
        orchestrate agents import -f "$agent_yaml"

        # 'agents import' creates a DRAFT agent. The chat UI lists only LIVE agents,
        # so promote it. This fails on the Developer Edition (draft only); warn and continue.
        agent_name="$(grep -m1 -E '^name:' "$agent_yaml" | sed -E 's/^name:[[:space:]]*//' | tr -d '\r' | awk '{print $1}')"
        if [ -n "$agent_name" ]; then
            echo "    agents deploy --name $agent_name"
            if ! orchestrate agents deploy --name "$agent_name"; then
                echo "WARNING: agents deploy failed for '$agent_name'. The agent exists as a draft; it may not appear in the chat UI." >&2
            fi
        fi
    done < <(find "$AGENTS_DIR" -mindepth 2 -maxdepth 2 -name "agent.yaml" -print0 | sort -z)
else
    echo "  (no agents/ directory, skipping)"
fi

echo ""
echo "=== Deploy complete ==="
