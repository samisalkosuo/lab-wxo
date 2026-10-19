#!/usr/bin/env bash
# activate-lab-wxo.sh
# Convenience bootstrap script for lab-wxo.
#
# What it does:
#   1. Creates Python virtual environment (.venv) if missing.
#   2. Activates the virtual environment.
#   3. Installs dependencies from requirements.txt.
#   4. Checks for env.cfg; prompts for credentials or API key if not configured.
#   5. Runs activate-wxo.sh to register and activate the WXO environment.
#
# Usage:
#   source ./activate-lab-wxo.sh   # Keep .venv active in current shell
#   bash ./activate-lab-wxo.sh     # Run in subshell

set -euo pipefail

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

API_KEY_ARG="${1:-}"

if [ -n "${BASH_SOURCE[0]:-}" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SCRIPT_DIR="$(pwd)"
fi

ROOT="$SCRIPT_DIR"
VENV_DIR="$ROOT/.venv"
REQ_FILE="$ROOT/requirements.txt"
ENV_FILE="$ROOT/env.cfg"
ACTIVATE_WXO="$ROOT/activate-wxo.sh"

echo ""
echo "=== lab-wxo Environment Activation ==="

# ── 1. Python & Virtual Environment ──────────────────────────────────────────
PY_CMD=""
for cand in python3 python py; do
    if command -v "$cand" &>/dev/null; then
        PY_CMD="$cand"
        break
    fi
done

if [ -z "$PY_CMD" ]; then
    echo "ERROR: Python is not found on PATH. Please install Python 3.11+ and try again." >&2
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[1/4] Creating virtual environment (.venv)..."
    "$PY_CMD" -m venv "$VENV_DIR"
else
    echo "[1/4] Virtual environment (.venv) found."
fi

# Activate virtual environment
if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/bin/activate"
elif [ -f "$VENV_DIR/Scripts/activate" ]; then
    # shellcheck disable=SC1091
    source "$VENV_DIR/Scripts/activate"
else
    echo "WARNING: Could not find activate script in $VENV_DIR. PATH may not be updated." >&2
fi

# ── 2. Install Requirements ──────────────────────────────────────────────────
echo "[2/4] Checking / installing dependencies from requirements.txt..."
if [ -f "$REQ_FILE" ]; then
    pip install --quiet --upgrade pip || true
    pip install --quiet -r "$REQ_FILE" || pip install -r "$REQ_FILE"
else
    echo "  (requirements.txt not found, skipping pip install)"
fi

# ── 3. Configuration & API Key ──────────────────────────────────────────────
echo "[3/4] Checking environment configuration (env.cfg)..."

RESOLVED_API_KEY="$API_KEY_ARG"

if [ ! -f "$ENV_FILE" ]; then
    echo "  env.cfg not found."
    read -r -p "  Would you like to create env.cfg now? (Y/n) " create_cfg || create_cfg="Y"
    if [[ -z "$create_cfg" || "$create_cfg" =~ ^[Yy] ]]; then
        read -r -p "  Enter WXO instance URL: " input_url
        read -r -p "  Enter WXO environment name [my-env]: " input_env_name
        input_env_name="${input_env_name:-my-env}"
        read -r -p "  Enter WXO API key (press Enter to skip/prompt later): " input_api_key
        read -r -p "  Enter WXO environment type (ibm_iam/mcsp) [ibm_iam]: " input_type
        input_type="${input_type:-ibm_iam}"

        cat <<EOF > "$ENV_FILE"
WXO_API_KEY=$input_api_key
WXO_URL=$input_url
WXO_ENV_NAME=$input_env_name
WXO_ENV_TYPE=$input_type
EOF
        echo "  Created env.cfg."
        if [ -n "$input_api_key" ]; then
            RESOLVED_API_KEY="$input_api_key"
        fi
    fi
else
    # Parse existing env.cfg
    EXISTING_KEY=""
    while IFS= read -r raw_line; do
        line="$(printf '%s' "$raw_line" | tr -d '\r' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ -z "$line" || "$line" == \#* ]] && continue
        key="${line%%=*}"
        value="${line#*=}"
        if [ "$key" = "WXO_API_KEY" ]; then
            EXISTING_KEY="$value"
        fi
    done < "$ENV_FILE"

    if [ -z "$RESOLVED_API_KEY" ]; then
        if [ -n "$EXISTING_KEY" ] && [ "$EXISTING_KEY" != "your-api-key-here" ]; then
            RESOLVED_API_KEY="$EXISTING_KEY"
        else
            echo "  WXO_API_KEY is not set in env.cfg."
            read -r -p "  Enter WXO API key (press Enter to activate interactively): " input_key
            if [ -n "$input_key" ]; then
                RESOLVED_API_KEY="$input_key"
                read -r -p "  Save this API key to env.cfg? (y/N) " save_key || save_key="N"
                if [[ "$save_key" =~ ^[Yy] ]]; then
                    if grep -q "^WXO_API_KEY=" "$ENV_FILE"; then
                        sed -i "s|^WXO_API_KEY=.*|WXO_API_KEY=$input_key|" "$ENV_FILE"
                    else
                        echo "WXO_API_KEY=$input_key" >> "$ENV_FILE"
                    fi
                    echo "  Updated env.cfg with API key."
                fi
            fi
        fi
    fi
fi

# ── 4. Execute activate-wxo.sh ──────────────────────────────────────────────
echo "[4/4] Activating WXO environment..."
if [ -f "$ACTIVATE_WXO" ]; then
    bash "$ACTIVATE_WXO" "$RESOLVED_API_KEY"
else
    echo "ERROR: $ACTIVATE_WXO not found." >&2
    exit 1
fi

echo ""
echo "=== lab-wxo activation complete! ==="
echo "To deploy scenarios, run:"
echo "  bash scripts/deploy-all.sh"
echo ""
echo "Tip: Run 'source ./activate-lab-wxo.sh' to keep .venv active in your shell."
echo ""
