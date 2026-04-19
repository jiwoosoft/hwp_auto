#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DIR="$PROJECT_ROOT/mcp-server"
VENV_PYTHON="$MCP_DIR/.venv/bin/python"

cd "$MCP_DIR"
if [ -x "$VENV_PYTHON" ]; then
  exec "$VENV_PYTHON" server.py
fi
exec python3 server.py
