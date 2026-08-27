#!/usr/bin/env bash
set -euo pipefail
mkdir -p bin
go build -o bin/curbpack ./cmd/curbpack
go build -o bin/curbpack-mcp ./cmd/curbpack-mcp
