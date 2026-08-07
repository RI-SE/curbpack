# Demo fixture notes

Use any git product repo:

```bash
go build -o cyberready ./cmd/cyberready
cd /path/to/product   # git repo
./cyberready init --medtech
# edit docs/annex-vii/*.md — remove placeholders
./cyberready validate
./cyberready prepare-release
open review-pack/buyer-onepager.html
```

Automated unit tests under `internal/*/ *_test.go` use a fake `.git` directory (no `git init`) so they run in restricted sandboxes.
