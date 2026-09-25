#!/usr/bin/env bash
# Claim-safety runtime/output checks. Documentation checks live in docs_acceptance_check.sh.
# Tool does not prevent regulatory action; it must not present as conformity.
# Brand: product mark is Curbpack. "CyberReady" allowed only in migration / NOTICE /
# changelog historical lines (and this script's allowlist).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BIN="${CURBPACK_BIN:-${CYBERREADY_BIN:-$ROOT/bin/curbpack}}"
go build -o "$BIN" ./cmd/curbpack

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Combined deny patterns (positive certification theater).
# Lines with claim-safe negation framing are filtered out in Python.
DENY_RE='we are (CE[- ])?certified|product is certified|officially certified|curbpack certifies|cyberready certifies|notified[- ]body approved|approved by (a )?notified body|conformity assessment (complete|passed|successful)|CE marking (issued|granted|obtained)|is CE[- ]marked|has been CE[- ]marked|certified conformity|EU CRA Baseline|we are CRA compliant|CRA compliant|RISE[- ]approved|RISE[- ]certified|FRA[- ]approved|NCSC[- ]approved|agency[- ]endorsed|accredited (procedure|method|assessment)|designation[- ]ready|qualifies (you|your body) as a notified body|meets Article 39|Article 39 compliant|accreditation (granted|achieved)|proficiency[- ]tested|equivalent to a notified[- ]body (assessment|opinion)|recognised by (Swedac|a national accreditation body)'

SAFE_RE='not (a |an )?(conformity|certif|CE)|does not certify|never claim|no certification|not CE|replace a notified|notified-body approval|certification_claimed.: false|Certification claimed: \*\*no\*\*|not a certification product|Not a certification|informational|draft structure|not essential-requirements|structural_draft|structural (file/header )?gates|not conformity assessment|funder, not certifier|not product certifier|not (this product.s )?certifier|does not (make|render) (you|your body) a notified body|not accreditation|does not confer|Article 39 is a requirement on the body, not on this tool'

# Nomenclature fence: never describe what curbpack does as measurement.
# Do NOT deny stem "measur" alone — NIS 2 quotes say "measures".
NOMEN_DENY_RE='\bmeasurement\b|\bmeasurands?\b|\bmetrolog(y|ical)\b|\bmätning(en|ar)?\b|\bmätosäkerhet\b|\briksmätplats|signal density|\bmeasurement uncertainty\b'
NOMEN_SAFE_RE='never claim|do not claim|reject|not a measurement|is not measurement|not metrolog|forbidden|deny|nomenclature'

scan_text() {
  local label="$1"
  local file="$2"
  local deny_s="${3:-$DENY_RE}"
  local safe_s="${4:-$SAFE_RE}"
  python3 - "$label" "$file" "$deny_s" "$safe_s" <<'PY'
import re, sys
label, path, deny_s, safe_s = sys.argv[1:5]
deny = re.compile(deny_s, re.I)
safe = re.compile(safe_s, re.I)
hit = 0
try:
    text = open(path, errors="replace").read()
except FileNotFoundError:
    sys.exit(0)
for i, line in enumerate(text.splitlines(), 1):
    if safe.search(line):
        continue
    m = deny.search(line)
    if m:
        print(f"CLAIM-SAFETY FAIL [{label}:{i}]: /{m.group(0)}/ → {line}", file=sys.stderr)
        hit = 1
sys.exit(hit)
PY
}

# Run certification + nomenclature deny families (same scanner).
scan_both() {
  local label="$1"
  local file="$2"
  local rc=0
  scan_text "$label" "$file" || rc=1
  scan_text "nomen:$label" "$file" "$NOMEN_DENY_RE" "$NOMEN_SAFE_RE" || rc=1
  return "$rc"
}

FAIL=0

echo "== runtime-wording-acceptance: pack.json display strings =="
PACK_FILES=()
while IFS= read -r f; do
  PACK_FILES+=("$f")
done < <(
  find packs internal/packs/data \
    \( -type f -name 'pack.json' \) \
    2>/dev/null | sort -u
)
for f in "${PACK_FILES[@]}"; do
  scan_both "$f" "$f" || FAIL=1
done

echo "== runtime-wording-acceptance: CLI outputs =="
"$BIN" doctor >"$TMP/doctor.out" 2>&1 || true
scan_both "doctor" "$TMP/doctor.out" || FAIL=1

DEMO="$TMP/demo"
"$BIN" demo --out "$DEMO" --keep >"$TMP/demo.out" 2>&1
scan_both "demo" "$TMP/demo.out" || FAIL=1
if [[ -f "$DEMO/review-pack/buyer-onepager.html" ]]; then
  scan_both "buyer-onepager" "$DEMO/review-pack/buyer-onepager.html" || FAIL=1
fi

FIX="$TMP/fix"
mkdir -p "$FIX"
(
  cd "$FIX"
  git init -q
  git config user.email "ci@curbpack.local"
  git config user.name "CI"
  git commit --allow-empty -m init -q
  "$BIN" init --packs house-policy --yes >"$TMP/init.out" 2>&1
  "$BIN" check >"$TMP/check.out" 2>&1 || true
  "$BIN" prepare-release >"$TMP/prepare.out" 2>&1 || true
)
scan_both "init" "$TMP/init.out" || FAIL=1
scan_both "check" "$TMP/check.out" || FAIL=1
scan_both "prepare-release" "$TMP/prepare.out" || FAIL=1
if [[ -f "$FIX/review-pack/buyer-onepager.html" ]]; then
  scan_both "prepare-onepager" "$FIX/review-pack/buyer-onepager.html" || FAIL=1
fi
(
  cd "$FIX"
  "$BIN" share --bundle >"$TMP/share-bundle.out" 2>&1 || true
)
scan_both "share-bundle" "$TMP/share-bundle.out" || FAIL=1
if [[ -f "$FIX/review-pack/buyer-questions.md" ]]; then
  scan_both "buyer-questions" "$FIX/review-pack/buyer-questions.md" || FAIL=1
fi
if [[ -f "$FIX/.github/curbpack/cache/buyer-questions.md" ]]; then
  scan_both "buyer-questions-cache" "$FIX/.github/curbpack/cache/buyer-questions.md" || FAIL=1
fi
if [[ -f "$FIX/review-pack/evidence-bundle.html" ]]; then
  scan_both "evidence-bundle" "$FIX/review-pack/evidence-bundle.html" || FAIL=1
fi
if [[ -f "$FIX/.github/curbpack/cache/latest_action_report.md" ]]; then
  scan_both "action-report" "$FIX/.github/curbpack/cache/latest_action_report.md" || FAIL=1
fi

"$BIN" help >"$TMP/help.out" 2>&1 || true
scan_both "help" "$TMP/help.out" || FAIL=1

"$BIN" review "$ROOT/testdata/sample-review-pack" >"$TMP/review.out" 2>&1 || true
scan_both "review" "$TMP/review.out" || FAIL=1

"$BIN" review --repo "$ROOT" --json >"$TMP/review-repo.json" 2>"$TMP/review-repo.err" || true
scan_both "review-repo" "$TMP/review-repo.json" || FAIL=1
scan_both "review-repo-err" "$TMP/review-repo.err" || FAIL=1

BADGE="$TMP/badge"
mkdir -p "$BADGE"
(
  cd "$BADGE"
  git init -q
  git config user.email "ci@curbpack.local"
  git config user.name "CI"
  git commit --allow-empty -m init -q
  echo '{"name":"badgeco","version":"1.0.0"}' > package.json
  "$BIN" scan --badge >"$TMP/badge-cold.out" 2>&1 || true
  "$BIN" fix --art14 --yes >"$TMP/badge-fix.out" 2>&1 || true
  "$BIN" scan --badge >"$TMP/badge-postfix.out" 2>&1 || true
)
scan_both "scan-badge-cold" "$TMP/badge-cold.out" || FAIL=1
scan_both "scan-badge-postfix" "$TMP/badge-postfix.out" || FAIL=1

if [[ "$FAIL" -ne 0 ]]; then
  echo "runtime-wording-acceptance: FAILED" >&2
  exit 1
fi

echo "runtime-wording-acceptance: OK"
exit 0
