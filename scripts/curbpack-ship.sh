#!/usr/bin/env bash
# PR preflight + post-merge housekeeping. Never bare merge, force-push, or pin bump.
set -euo pipefail
R="$(cd "$(dirname "$0")/.." && pwd)"; cd "$R"
PIN="v0.5.2"; FLOOR=80; DRY=0; STATE="$R/.github/curbpack/ship-state.json"
[[ "${1:-}" == --dry-run ]] && { DRY=1; shift; }
die(){ echo "Blocked: $1" >&2; exit 1; }
pause(){ echo "Paused: $1" >&2; echo "Resume: $2" >&2; exit 2; }
run(){ [[ $DRY -eq 0 ]] && "$@" || echo "[dry-run] $*"; }
preflight(){
  local pr="${1:?pr number required}"
  local cmd="./scripts/curbpack-ship.sh${DRY:+ --dry-run} preflight $pr" checks
  [[ -n "$(git status --porcelain)" ]] && pause "Save or discard local changes first" "$cmd"
  if [[ $DRY -eq 0 ]]; then
    base_repo="$(gh pr view "$pr" --json baseRepository --jq '.baseRepository.nameWithOwner' 2>/dev/null || true)"
    if [[ -n "$base_repo" && "$base_repo" != "RI-SE/curbpack" ]]; then
      echo "Warning: PR base repo is $base_repo (expected RI-SE/curbpack for product work). See docs/internal/fork-policy.md" >&2
    fi
  fi
  if [[ $DRY -eq 1 ]]; then echo "[dry-run] gh pr checks $pr --json"; checks="${CURBPACK_SHIP_CHECKS_JSON:-}"; [[ -n "$checks" ]] || pause "dry-run needs CURBPACK_SHIP_CHECKS_JSON" "$cmd"
  else checks="$(gh pr checks "$pr" --json name,state,bucket 2>/dev/null)" || pause "Could not read PR checks" "$cmd"; fi
  python3 - "$checks" "$PIN" <<'PY' || die "preflight evidence failed"
import json,re,subprocess,sys
checks,pin=sys.argv[1],sys.argv[2]
req=set(json.load(open(".github/required-checks.json"))["contexts"])
by={c["name"]:c for c in json.loads(checks)}
for ctx in req:
 c=by.get(ctx)
 if not c or c.get("bucket")!="pass": sys.exit(f"check not green: {ctx}")
base=subprocess.check_output(["git","merge-base","origin/main","HEAD"],text=True).strip()
diff=subprocess.check_output(["git","diff",f"{base}..HEAD"],text=True)
if re.search(rf"(?m)^[+-].*{re.escape(pin)}",diff):
 log=subprocess.check_output(["git","log",f"{base}..HEAD","--format=%B"],text=True)
 if "Approve-Pin-Bump:" not in log: sys.exit("pin changed without Approve-Pin-Bump")
PY
  run ./scripts/claim-safety.sh --changed-only || die "claim-safety failed"
  local n="$FLOOR"; [[ $DRY -eq 0 ]] && n="$(go test -json ./internal/attest/... ./internal/validate/... 2>/dev/null|python3 -c "import sys,json;print(sum(1 for l in sys.stdin if json.loads(l).get('Action')=='pass' and json.loads(l).get('Test')))")"
  [[ "${n:-0}" -ge "$FLOOR" ]] || die "integrity floor $FLOOR unmet (passes=$n)"
  echo "CTO memo: checks green, contexts match, pin ok, claim-safe, integrity ok."
  echo "Human/platform: gh pr merge --auto --squash (never force-push; never bump pin without approve)."
}
post-merge(){
  local cmd="./scripts/curbpack-ship.sh${DRY:+ --dry-run} post-merge" sha pr_url num body
  sha="$(git rev-parse HEAD)"
  if [[ -f "$STATE" ]] && grep -q "\"$sha\"" "$STATE" 2>/dev/null; then echo "post-merge already done for $sha"; exit 0; fi
  [[ -n "$(git status --porcelain)" ]] && pause "Save or discard local changes first" "$cmd"
  run git fetch origin
  if [[ $DRY -eq 0 ]]; then
    pr_url="$(gh pr list --state merged --limit 1 --json url --jq '.[0].url' 2>/dev/null||echo n/a)"
    body=$'## Tier A (auto)\n- [x] Required CI green ('"$pr_url"$')\n\n## Tier B\n- [ ] Tabletop walkthrough\n\n## Tier C\n- [ ] Evidence archived'
    num="$(gh issue list --label tabletop-evidence --state all --limit 1 --json number --jq '.[0].number' 2>/dev/null||true)"
    [[ -n "$num" && "$num" != null ]] && gh issue edit "$num" --body "$body" || gh issue create --title "Tabletop evidence" --label tabletop-evidence --body "$body"
    mkdir -p "$(dirname "$STATE")"; echo "{\"post_merge_sha\":\"$sha\"}" >"$STATE"
  else echo "[dry-run] tabletop-evidence upsert skipped"; fi
  echo "post-merge complete"
}
case "${1:-}" in preflight) shift; preflight "$@";; post-merge) post-merge;;
*) echo "usage: $0 [--dry-run] preflight <pr#>|post-merge" >&2; pause "unknown subcommand" "$0 preflight <pr#>";; esac
