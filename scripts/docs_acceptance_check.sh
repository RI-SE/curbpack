#!/usr/bin/env bash
# Documentation acceptance check.
# Checks repository documentation/text surfaces for misleading compliance wording,
# forbidden nomenclature, stale CLI verbs, stale npx usage, and broken blob/main links.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CHANGED_ONLY=0; for arg in "$@"; do [[ "$arg" == --changed-only ]] && CHANGED_ONLY=1; done

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

echo "== docs-acceptance: wording and nomenclature =="
DOC_FILES=()
while IFS= read -r f; do
  DOC_FILES+=("$f")
done < <(
  find README.md SECURITY.md NOTICE LICENSE AGENTS.md CLAUDE.md docs papers vision/site .cursor/skills internal/skilldata action.yml examples \
    .github/ISSUE_TEMPLATE .github/workflows .github/copilot-instructions.md scripts \
    \( -type f \( -name '*.md' -o -name '*.yml' -o -name '*.yaml' -o -name '*.sh' -o -name '*.ps1' -o -name '*.html' -o -name '*.txt' -o -name 'LICENSE' -o -name 'NOTICE' -o -name 'copilot-instructions.md' \) \) \
    2>/dev/null | grep -v 'scripts/claim-safety\.sh$' | grep -v 'scripts/docs_acceptance_check\.sh$' | grep -v '/gtm-oss/' | grep -v 'workflows/pages\.yml$' | sort -u
)

if [[ "$CHANGED_ONLY" -eq 1 ]]; then
  mapfile -t CHANGED < <(git diff --name-only origin/main...HEAD 2>/dev/null || git diff --name-only HEAD~1)
  NEXT=(); for f in "${DOC_FILES[@]}"; do for c in "${CHANGED[@]}"; do [[ "$f" == "$c" ]] && NEXT+=("$f") && break; done; done; DOC_FILES=("${NEXT[@]}")
fi

for f in "${DOC_FILES[@]}"; do
  if ! scan_both "$f" "$f"; then
    FAIL=1
  fi
done

echo "== docs-acceptance: CLI/document consistency =="
if ! python3 - "$ROOT" <<'PY'
import os, re, sys
root = sys.argv[1]
reg_path = os.path.join(root, "internal/cli/registry.go")
reg_text = open(reg_path, errors="replace").read()
verbs = set(re.findall(r'\{name:\s*"([a-z][a-z0-9-]*)"', reg_text))
aliases = set(re.findall(r'aliases:\s*\[\]string\{"([^"]+)"\}', reg_text))
allowed = verbs | aliases | {"version", "help", "curb"}
skip_verb_files = {
    "docs/software-design-document.md",
    "docs/internal/sdd-gap-analysis.md",
    "docs/internal/historical-verify-target.md",  # fences phantom verify; not a ship verb
}
doc_globs = ["README.md", "docs", "vision/site", "papers", "AGENTS.md", "CLAUDE.md"]
paths = []
for g in doc_globs:
    p = os.path.join(root, g)
    if os.path.isfile(p):
        paths.append(p)
    elif os.path.isdir(p):
        for dp, dns, fns in os.walk(p):
            if "gtm-oss" in dp.replace("\\", "/"):
                continue
            for fn in fns:
                if fn.endswith((".md", ".html", ".txt")):
                    paths.append(os.path.join(dp, fn))
fail = 0
verb_re = re.compile(r"`curbpack ([a-z][a-z0-9-]*)")
blob_re = re.compile(r"github\.com/(?:afelin|RI-SE)/curbpack/blob/main/([^)\s\"'#]+)")
for path in sorted(set(paths)):
    rel = os.path.relpath(path, root).replace("\\", "/")
    try:
        text = open(path, errors="replace").read()
    except OSError:
        continue
    if re.search(r"npx curbpack", text, re.I) and "deferred" not in text.lower():
        print(f"DOC-TRUTH FAIL [{rel}]: npx curbpack without deferred", file=sys.stderr)
        fail = 1
    if rel not in skip_verb_files:
        for i, line in enumerate(text.splitlines(), 1):
            for m in verb_re.finditer(line):
                v = m.group(1)
                if v not in allowed:
                    print(f"DOC-TRUTH FAIL [{rel}:{i}]: unknown verb `curbpack {v}`", file=sys.stderr)
                    fail = 1
    for m in blob_re.finditer(text):
        target = os.path.join(root, m.group(1))
        if not os.path.isfile(target):
            print(f"DOC-TRUTH FAIL [{rel}]: missing blob/main target {m.group(1)}", file=sys.stderr)
            fail = 1
sys.exit(fail)
PY
then
  FAIL=1
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "docs-acceptance: FAILED" >&2
  exit 1
fi

echo "docs-acceptance: OK"
exit 0
