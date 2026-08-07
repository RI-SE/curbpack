# Demo fixture notes

```bash
# Magic path (no product mutation)
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor && cyberready demo

# Or build from source
go build -o bin/cyberready ./cmd/cyberready
./bin/cyberready demo --keep
```

`testdata/demo-app/` (and the embedded copy under `internal/demo/data/`) is a minimal **house-policy** fixture. The `demo` command copies it into a temp git repo, runs `check` + `prepare-release`, and never writes into the caller’s product cwd.

Automated unit tests under `internal/*/ *_test.go` use a fake `.git` directory (no `git init`) so they run in restricted sandboxes — except `internal/demo` which needs real `git` for the sandbox test.

CI (`.github/workflows/ci.yml`) runs `go test ./...` plus doctor/demo and offline CRA / house-policy smokes.
