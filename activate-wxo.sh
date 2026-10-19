#!/usr/bin/env bash
# activate-wxo.sh
# Reads env.cfg, registers the WXO environment (if needed), and activates it.
# If an API key is present in env.cfg or passed as $1, it activates non-interactively;
# otherwise, it activates interactively and prompts for the API key.
# For full non-interactive deploy, run scripts/deploy-all.sh instead.

set -euo pipefail

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

API_KEY_ARG="${1:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR"
ENV_FILE="$ROOT/env.cfg"

WXO_API_KEY=""
WXO_URL=""
WXO_ENV_NAME=""
WXO_ENV_TYPE=""

if [ -f "$ENV_FILE" ]; then
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
fi

if [ -n "$API_KEY_ARG" ]; then
    WXO_API_KEY="$API_KEY_ARG"
fi

if [ "$WXO_API_KEY" = "your-api-key-here" ]; then
    WXO_API_KEY=""
fi

WXO_ENV_TYPE="${WXO_ENV_TYPE:-ibm_iam}"

if [ -z "$WXO_URL" ] || [ -z "$WXO_ENV_NAME" ]; then
    echo "ERROR: env.cfg (or environment variables) must define WXO_URL and WXO_ENV_NAME." >&2
    exit 1
fi

echo "Registering WXO environment '$WXO_ENV_NAME' ..."
echo "Y" | orchestrate env add -n "$WXO_ENV_NAME" -u "$WXO_URL" --type "$WXO_ENV_TYPE"

if [ -n "$WXO_API_KEY" ]; then
    echo "Activating WXO environment '$WXO_ENV_NAME' with API key..."
    orchestrate env activate "$WXO_ENV_NAME" --api-key "$WXO_API_KEY"
else
    echo "Activating WXO environment '$WXO_ENV_NAME' (interactive)..."
    orchestrate env activate "$WXO_ENV_NAME"
fi

echo "Done. Active environment: $WXO_ENV_NAME"
