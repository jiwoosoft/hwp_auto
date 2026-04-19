#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: $0 <path-to-hwp-or-hwpx>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BRIDGE="$PROJECT_ROOT/mcp-server/bridges/rhwp_extract.mjs"

exec node "$BRIDGE" "$1" --include-tables=true --max-chars=50000
