#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
LOG_DIR="$ROOT_DIR/scripts/logs"
POLICY_FILE="$ROOT_DIR/opa/policy.rego"

mkdir -p "$LOG_DIR"

echo "[macOS Run] Starting Redis, OPA, Backend, and Frontend in separate Terminal tabs..."

# Redis via Homebrew services
if command -v brew >/dev/null 2>&1; then
  echo "[Redis] Ensuring Redis is running (brew services)..."
  brew services start redis >/dev/null 2>&1 || true
else
  echo "[Redis] Homebrew not found. Please ensure Redis is running (redis-server)." >&2
fi

# Verify Redis responds (optional)
if command -v redis-cli >/dev/null 2>&1; then
  (redis-cli ping || true) >/dev/null 2>&1
fi

# Launch OPA, Backend, Frontend in Terminal tabs
if ! command -v opa >/dev/null 2>&1; then
  echo "[OPA] 'opa' not found in PATH. Install OPA first." >&2
fi

OSA_SCRIPT=$(cat <<'EOS'
on run argv
  set projRoot to item 1 of argv
  set policyFile to item 2 of argv

  tell application "Terminal"
    activate

    do script "cd " & quoted form of projRoot & "; clear; echo '[OPA] Starting...'; opa run --server " & quoted form of policyFile

    delay 0.2
    do script "cd " & quoted form of projRoot & "; clear; echo '[Backend] Starting...'; python3 -m uvicorn trunk:app --reload" in window 1

    delay 0.2
    do script "cd " & quoted form of (projRoot & "/ascend-educate-nextjs") & "; clear; echo '[Frontend] Starting...'; npm run dev" in window 1
  end tell
end run
EOS
)

osascript -e "$OSA_SCRIPT" "$ROOT_DIR" "$POLICY_FILE"

echo "[macOS Run] Terminals launched."


