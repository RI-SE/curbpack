## Summary
- 

## Why
- 

## Test plan
- [ ] `go test ./...`
- [ ] `go run ./cmd/curbpack check` (or equivalent fixture command)

## Ops checklist (required)
- [ ] Branch is up to date with `main` before merge
- [ ] Required CI checks are green
- [ ] No direct push to `main` (PR merge only)
- [ ] After merge: run `./scripts/curb-sync.sh`
- [ ] Confirm `origin/main` and `corp-origin/main` are the same SHA

## Risk / rollback
- [ ] Rollback path is clear (revert PR or restore previous tag/pin docs as needed)
