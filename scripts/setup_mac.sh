#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
POLICY_FILE_DEFAULT="$PROJECT_ROOT_DIR/opa/policy.rego"

echo "[macOS Setup] Starting setup for Redis, OPA, Node/pnpm, Python..."

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This script is intended for macOS only." >&2
  exit 1
fi

# Install Homebrew if missing
if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$('"$(/usr/libexec/path_helper -s)"')"' >/dev/null 2>&1 || true
fi

echo "[brew] Updating..."
brew update

echo "[brew] Installing packages: python@3.12, redis, opa, node@20, pnpm..."
brew install python@3.12 redis opa node@20 pnpm || true

echo "[redis] Starting Redis via brew services..."
brew services start redis || true

echo "[redis] Testing Redis connectivity (redis-cli ping)..."
if command -v redis-cli >/dev/null 2>&1; then
  redis-cli ping || { echo "Redis ping failed. Check that redis is running."; }
else
  echo "redis-cli not found in PATH. Ensure Homebrew bin is on PATH."
fi

echo "[opa] OPA installed. To run OPA with your project policy, use:"
POLICY_FILE="${1:-$POLICY_FILE_DEFAULT}"
if [[ ! -f "$POLICY_FILE" ]]; then
  echo "  (Policy file not found at $POLICY_FILE. Using default path hint: $POLICY_FILE_DEFAULT)"
fi
cat <<EOT

  # In a separate terminal (from project root):
  opa run --server opa/policy.rego

OPA will listen on http://localhost:8181. Test with:

  curl -sS -X POST http://localhost:8181/v1/data/authz/allow \
    -H 'Content-Type: application/json' \
    -d '{"input": {"user": "u", "role": "teacher", "action": "x", "resource": "y"}}'

EOT

echo "[node] Node and pnpm installed. To run frontend:"
cat <<EON

  cd "$PROJECT_ROOT_DIR/ascend-educate-nextjs"
  pnpm install
  # Ensure you set NEXT_PUBLIC_BACKEND_URL and Supabase envs in .env.local
  pnpm dev

EON

echo "[python] To run backend (from project root):"
cat <<EOPY

  cd "$PROJECT_ROOT_DIR"
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python -m uvicorn trunk:app --reload

EOPY

echo "[Done] macOS setup completed."


