#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
go run ./scripts/art14-countdown/main.go site/index.html site/art14/index.html
