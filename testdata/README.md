# Demo fixture notes

```bash
go build -o bin/cyberready ./cmd/cyberready
cd /path/to/product   # git repo
./bin/cyberready init --packs cra-baseline
# or: ./bin/cyberready init --packs house-policy --hooks
./bin/cyberready check
./bin/cyberready prepare-release
open review-pack/buyer-onepager.html
```

Automated unit tests under `internal/*/ *_test.go` use a fake `.git` directory (no `git init`) so they run in restricted sandboxes.

CI (`.github/workflows/ci.yml`) runs `go test ./...` plus offline smoke for CRA and house-policy fixtures.
