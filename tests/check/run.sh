#!/bin/sh
# make test-curbcheck. Follows docs/testing/: start verification run, source,
# R1 via the Studio fixture, packs from that fixture, then the catalogue.
set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"

# start-verification-run wipes tmp/. Keep developer mode from the environment
# or from an already-filled run (after DEVELOPER_MODE=TRUE make start-verification-run).
developer_mode=${DEVELOPER_MODE:-}
if [ -z "$developer_mode" ] && [ -f "$root/tmp/verification-run.sh" ]; then
	developer_mode=$(
		sed -n 's/^DEVELOPER_MODE="\(.*\)"$/\1/p' "$root/tmp/verification-run.sh" | head -n 1
	)
fi
CONFIRM_TMP_WIPE=1 DEVELOPER_MODE="$developer_mode" \
	"$root/scripts/start-verification-run.sh" --yes
# shellcheck disable=SC1091
. "$root/tmp/verification-run.sh"

product=$REFERENCE_PRODUCT_ROOT
fixture=$product/external_test/curbpack
if [ ! -d "$fixture/packs" ] || [ ! -d "$fixture/claims" ]; then
	echo "error: pin is missing external_test/curbpack packs/claims" >&2
	exit 1
fi

(
	cd "$fixture"
	SUT=curbpack ./setup.sh R1 --commit
)
if ! git -C "$product" diff --quiet -- external_test/curbpack/states/R1.sh; then
	echo "error: states/R1.sh changed inside the clone" >&2
	exit 1
fi

python3 - "$fixture/packs" "$product/curbpack/packs" cra-baseline house-policy medtech-iec62304 <<'PY'
import json, shutil, sys
from pathlib import Path

src, dest = Path(sys.argv[1]), Path(sys.argv[2])
for pack_id in sys.argv[3:]:
    root = src / pack_id
    direct = root / "pack.json"
    if direct.is_file():
        pack = json.loads(direct.read_text(encoding="utf-8"))
        source_dir = root
    else:
        found = sorted(path.parent for path in root.glob("*/pack.json") if path.is_file())
        if len(found) != 1:
            raise SystemExit(f"need one version directory under {root}")
        pack = json.loads((found[0] / "pack.json").read_text(encoding="utf-8"))
        source_dir = found[0]
    target = dest / pack_id / pack["version"]
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source_dir, target)
PY
PYTHONPATH="$root${PYTHONPATH:+:$PYTHONPATH}" python3 - "$product" <<'PY'
from pathlib import Path
import sys
from checks.defaults import created_curbpack
from common.jsonio import write_json

write_json(
    Path(sys.argv[1]) / "curbpack.json",
    created_curbpack(packs=["cra-baseline", "house-policy", "medtech-iec62304"]),
)
PY
mkdir -p "$product/curbpack/claims"
for id in \
	CRA-ANNEX-VII-MANUAL \
	CRA-ANNEX-VII-RISK \
	CRA-ANNEX-VII-SUPPORT \
	CRA-ART14-PATH \
	HOUSE-ANTI-PLACEHOLDER \
	HOUSE-SECURITY-MD \
	HOUSE-SECURITY-TXT
do
	cp "$fixture/claims/$id.json" "$product/curbpack/claims/$id.json"
done

out=$product/run-result.json
set +e
checks_out=$("$root/scripts/bin/curbcheck" --repo "$product" -o "$out")
checks_code=$?
set -e
printf '%s\n' "$checks_out"

echo
echo "manual rows (not a pass):"
while IFS= read -r line || [ -n "$line" ]; do
	case $line in
		'' | \#*) continue ;;
	esac
	printf 'manual %s\n' "$line"
done <"$root/tests/check/manual.ids"

printf '%s\n' "$checks_out" | grep -q 'claims 7 exit 0' || {
	echo "error: expected claims 7 exit 0" >&2
	exit 1
}
if printf '%s\n' "$checks_out" | grep -E '^fail '; then
	echo "error: a claim failed" >&2
	exit 1
fi
if [ "$checks_code" -ne 0 ]; then
	exit "$checks_code"
fi

mkdir -p "$root/tmp/suit-runner"
printf '%s\n' "carried" >"$root/tmp/suit-runner/EV-001.carried"
echo
echo "catalogue from tests/check/suites:"
sh "$root/tests/check/automation/suit-runner.sh" all
