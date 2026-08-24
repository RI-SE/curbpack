# Demo & gauntlet fixtures

```bash
# Magic path (no product mutation) — pinned release
curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.sh | sh
curbpack doctor && curbpack demo

# Or build from source (contributor / development)
go build -o bin/curbpack ./cmd/curbpack
./bin/curbpack demo --keep
```

## Layout

| Path | Purpose |
|------|---------|
| `demo-app/` | Minimal house-policy fixture (also embedded under `internal/demo/data/`) |
| `realish/` | Synthetic products for gauntlet (`node-saas`, `cra-device`, `dirty-monorepo`) |
| `adversarial/packs/` | Fail-closed packs (unknown check, path traversal, bad regex) |
| `gauntlet-baseline.json` | Expected pass/fail ratchet for `scripts/gauntlet-ratchet.sh` |
| `receipt/` | Manual Receipt v0 pilot fixtures (request / responses / disposition) |

`demo` copies the embedded demo into a temp git repo, runs `check` + `prepare-release`, and never writes into the caller’s product cwd.

Automated unit tests under `internal/*/ *_test.go` use a fake `.git` directory (no `git init`) so they run in restricted sandboxes — except `internal/demo` which needs real `git` for the sandbox test.

CI (`.github/workflows/ci.yml`) runs `go test ./...`, doctor/demo smokes, **claim-safety**, **heal/baseline gauntlet**, and install-from-release. See [docs/launch-readiness.md](../docs/launch-readiness.md).
