#!/bin/bash
# Kindle display update wrapper - cron-safe environment setup

set -e

# --- Cron-safe environment ---
# HOME must be set explicitly (cron may not set it)
export HOME="${HOME:-/home/tmagari}"
export USER="${USER:-tmagari}"
export LANG="${LANG:-ja_JP.UTF-8}"
export LC_ALL="${LC_ALL:-ja_JP.UTF-8}"
export TZ="${TZ:-Asia/Tokyo}"

# pyenv (cron does not source ~/.bashrc)
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/shims:$PYENV_ROOT/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/kindle_display_enhanced.py"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/logs/kindle_monitor.log}"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Source environment variables (API keys etc.)
if [ -f "$HOME/.env.kindle" ]; then
    set -a
    source "$HOME/.env.kindle"
    set +a
fi

# Warn if API key missing
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: ANTHROPIC_API_KEY not set" >> "$LOG_FILE"
fi

# Use pyenv's python directly (absolute path - most reliable)
PYTHON_BIN="$PYENV_ROOT/versions/3.8.13/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
    # Fallback to shim
    PYTHON_BIN="$(which python3)"
fi

cd "$SCRIPT_DIR"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Cron run started (python=$PYTHON_BIN) ===" >> "$LOG_FILE"
"$PYTHON_BIN" "$PYTHON_SCRIPT" >> "$LOG_FILE" 2>&1

exit 0
