#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STUDIO_DIR="$PROJECT_ROOT/vendor/rhwp-main/rhwp-studio"

cd "$STUDIO_DIR"
exec npm run dev -- --host 127.0.0.1 --port 7700
