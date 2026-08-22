#!/usr/bin/env bash
# Pilot Receipt v0 — orchestrate existing CLI only:
#   check → export/share → fingerprint → assemble receipt → structural validate
#
# Usage:
#   ./scripts/pilot-receipt.sh path/to/request.json
#   CURBPACK_BIN=./bin/curbpack OUT_DIR=/tmp/out ALLOW_RED=1 ./scripts/pilot-receipt.sh …
#
# Not a conformity assessment. Fails clearly on missing tools / validate errors.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RECEIPT_PY="${ROOT}/scripts/lib/receipt_v0.py"
CLAIM='Prepares evidence for human review — not a conformity assessment.'

die() { echo "pilot-receipt: $*" >&2; exit 1; }

REQUEST="${1:-}"
[[ -n "$REQUEST" ]] || die "usage: $0 request.json"
REQUEST="$(cd "$(dirname "$REQUEST")" && pwd)/$(basename "$REQUEST")"
[[ -f "$REQUEST" ]] || die "request not found: $REQUEST"
[[ -f "$RECEIPT_PY" ]] || die "missing $RECEIPT_PY"
command -v python3 >/dev/null || die "python3 required"
command -v git >/dev/null || die "git required"

REPO_ROOT="$(git -C "${CURBPACK_REPO_ROOT:-$PWD}" rev-parse --show-toplevel 2>/dev/null)" \
  || die "must run inside a git repository (or set CURBPACK_REPO_ROOT)"

OUT_DIR="${OUT_DIR:-${REPO_ROOT}/.github/curbpack/cache/pilot-receipt}"
mkdir -p "$OUT_DIR"

resolve_bin() {
  if [[ -n "${CURBPACK_BIN:-}" ]]; then
    [[ -x "$CURBPACK_BIN" ]] || die "CURBPACK_BIN not executable: $CURBPACK_BIN"
    return
  fi
  if command -v curbpack >/dev/null 2>&1; then
    CURBPACK_BIN="$(command -v curbpack)"
    return
  fi
  mkdir -p "$ROOT/bin"
  (cd "$ROOT" && go build -o "$ROOT/bin/curbpack" ./cmd/curbpack) \
    || die "could not build curbpack (set CURBPACK_BIN)"
  CURBPACK_BIN="$ROOT/bin/curbpack"
}

echo "== pilot-receipt (Receipt v0) =="
echo "  $CLAIM"
echo "  request: $REQUEST"
echo "  repo:    $REPO_ROOT"
resolve_bin
echo "  binary:  $CURBPACK_BIN"

COMMIT="$(git -C "$REPO_ROOT" rev-parse HEAD)"
EVAL_VER="$("$CURBPACK_BIN" version 2>/dev/null | head -n1 | sed -E 's/^curbpack[[:space:]]+//;s/^v//')"
[[ -n "$EVAL_VER" ]] || EVAL_VER="unknown"

PACK_ID="${CURBPACK_PACK:-house-policy}"
# Prefer pack id from request if present.
REQ_PACK="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print((d.get("profile") or {}).get("pack_id") or "")' "$REQUEST" 2>/dev/null || true)"
[[ -n "$REQ_PACK" ]] && PACK_ID="$REQ_PACK"

CHECK_LOG="$OUT_DIR/check.log"
set +e
(
  cd "$REPO_ROOT"
  "$CURBPACK_BIN" check --pack "$PACK_ID"
) >"$CHECK_LOG" 2>&1
CHECK_EC=$?
set -e

PASSED=false
[[ "$CHECK_EC" -eq 0 ]] && PASSED=true
if [[ "$PASSED" != true && "${ALLOW_RED:-0}" != "1" ]]; then
  echo "pilot-receipt: check failed (exit $CHECK_EC). Re-run with ALLOW_RED=1 to assemble a red receipt, or heal first." >&2
  tail -n 40 "$CHECK_LOG" >&2 || true
  exit "$CHECK_EC"
fi

# export / share — prefer thin export; share is optional fuller recipe.
set +e
(
  cd "$REPO_ROOT"
  "$CURBPACK_BIN" export --context-pack --packs "$PACK_ID"
) >"$OUT_DIR/export.log" 2>&1
EXPORT_EC=$?
set -e
if [[ "$EXPORT_EC" -ne 0 ]]; then
  echo "pilot-receipt: export --context-pack failed (exit $EXPORT_EC)" >&2
  cat "$OUT_DIR/export.log" >&2 || true
  exit "$EXPORT_EC"
fi

if [[ "${SKIP_SHARE:-0}" != "1" ]]; then
  set +e
  (
    cd "$REPO_ROOT"
    "$CURBPACK_BIN" share --packs "$PACK_ID" --skip-prepare-release
  ) >"$OUT_DIR/share.log" 2>&1
  SHARE_EC=$?
  set -e
  # share exits non-zero on red check; still useful for artefacts when ALLOW_RED=1
  if [[ "$SHARE_EC" -ne 0 && "$PASSED" == true ]]; then
    echo "pilot-receipt: share failed (exit $SHARE_EC)" >&2
    cat "$OUT_DIR/share.log" >&2 || true
    exit "$SHARE_EC"
  fi
fi

CP_JSON="${REPO_ROOT}/.github/curbpack/cache/context-pack.json"
[[ -f "$CP_JSON" ]] || die "expected context-pack at $CP_JSON"

ARTEFACTS=(".github/curbpack/cache/context-pack.json")
BQ_MD="${REPO_ROOT}/.github/curbpack/cache/buyer-questions.md"
[[ -f "$BQ_MD" ]] && ARTEFACTS+=(".github/curbpack/cache/buyer-questions.md")
ONEPAGER="${REPO_ROOT}/review-pack/buyer-onepager.html"
[[ -f "$ONEPAGER" ]] && ARTEFACTS+=("review-pack/buyer-onepager.html")

PACK_DIGEST=""
if [[ -f "$CP_JSON" ]]; then
  PACK_DIGEST="sha256:$(python3 -c 'import hashlib,sys; print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$CP_JSON")"
fi

SCORE=""
if command -v jq >/dev/null 2>&1; then
  SCORE="$(jq -r '.readiness_score // empty' "$CP_JSON" 2>/dev/null || true)"
fi

RECEIPT_OUT="${OUT_DIR}/receipt.json"
ASM_ARGS=(
  "$RECEIPT_PY" assemble
  --root "$REPO_ROOT"
  --request "$REQUEST"
  --out "$RECEIPT_OUT"
  --evaluator-version "$EVAL_VER"
  --pack-id "$PACK_ID"
  --pack-digest "$PACK_DIGEST"
  --commit "$COMMIT"
  --check-passed "$([[ "$PASSED" == true ]] && echo true || echo false)"
)
[[ -n "$SCORE" ]] && ASM_ARGS+=(--readiness-score "$SCORE")
for a in "${ARTEFACTS[@]}"; do
  ASM_ARGS+=(--artefact "$a")
done

python3 "${ASM_ARGS[@]}"
python3 "$RECEIPT_PY" validate "$RECEIPT_OUT" \
  --root "$REPO_ROOT" \
  --request "$REQUEST" \
  --recompute-digests

echo "pilot-receipt OK"
echo "  receipt: $RECEIPT_OUT"
echo "  Next: human disposition + docs/getting-started/pilot-decision-log.md"
echo "  $CLAIM"
