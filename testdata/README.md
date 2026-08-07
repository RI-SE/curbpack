# Demo & gauntlet fixtures

```bash
# Magic path (no product mutation)
curl -fsSL https://raw.githubusercontent.com/afelin/cyberready/main/scripts/install.sh | sh
cyberready doctor && cyberready demo

# Or build from source
go build -o bin/cyberready ./cmd/cyberready
./bin/cyberready demo --keep
```

## Layout

| Path | Purpose |
|------|---------|
| `demo-app/` | Minimal house-policy fixture (also embedded under `internal/demo/data/`) |
| `realish/` | Synthetic products for gauntlet (`node-saas`, `cra-device`, `dirty-monorepo`) |
| `adversarial/packs/` | Fail-closed packs (unknown check, path traversal, bad regex) |
| `gauntlet-baseline.json` | Expected pass/fail ratchet for `scripts/gauntlet-ratchet.sh` |

`demo` copies the embedded demo into a temp git repo, runs `check` + `prepare-release`, and never writes into the caller’s product cwd.

Automated unit tests under `internal/*/ *_test.go` use a fake `.git` directory (no `git init`) so they run in restricted sandboxes — except `internal/demo` which needs real `git` for the sandbox test.

CI (`.github/workflows/ci.yml`) runs `go test ./...`, doctor/demo smokes, **claim-safety**, **heal/baseline gauntlet**, and install-from-release. See [docs/launch-readiness.md](../docs/launch-readiness.md).
