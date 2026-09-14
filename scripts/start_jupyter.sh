#!/usr/bin/env bash
# Start JupyterLab for EDA, reading JUPYTER_TOKEN/JUPYTER_PORT from .env.
# The jupyter MCP server (see ~/.claude.json) connects to this lab over JUPYTER_URL.
set -euo pipefail

# Run from the repo root regardless of where the script is called.
cd "$(dirname "$0")/.."

# Load .env, then export only variables prefixed with JUPYTER_.
[ -f .env ] && . ./.env
while IFS= read -r var; do
  export "$var"
done < <(compgen -v | grep '^JUPYTER_')

PORT="${JUPYTER_PORT:-8889}"

if [ -z "${JUPYTER_TOKEN:-}" ]; then
  echo "error: JUPYTER_TOKEN is not set (expected in .env)" >&2
  exit 1
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "error: port $PORT is already in use; a server may be running." >&2
  exit 1
fi

# JupyterLab reads the token from the JUPYTER_TOKEN env var; no flag needed.
exec uv run jupyter lab \
  --port "$PORT" \
  --ip 127.0.0.1 \
  --no-browser \
  --ServerApp.root_dir="$PWD"
