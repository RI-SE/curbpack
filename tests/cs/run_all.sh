#!/bin/sh
# Convenience only. Each check is independently executable, including in CI.
set -u
cd "$(dirname "$0")/../.." || exit 1
failed=0
for check in path_boundary review_signature check_result_integrity git_provenance workspace_selector; do
  echo "== $check =="
  python3 "tests/cs/$check.py" || failed=$((failed + 1))
done
if [ "$failed" -eq 0 ]; then
  echo '[PASS] security boundary suite'
else
  echo "[FAIL] security boundary suite: $failed scripts failed"
fi
if [ "$failed" -eq 0 ]; then exit 0; else exit 1; fi
