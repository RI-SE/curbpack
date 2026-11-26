#!/bin/sh
# make test-curbcheck. Follows docs/testing/: start verification run, source,
# R1 via the Studio fixture, then curbcheck on the clone's own curbpack.json.
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

if [ ! -f "$product/curbpack.json" ]; then
	echo "error: pin has no curbpack.json" >&2
	exit 1
fi

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

printf '%s\n' "$checks_out" | grep -q 'claims 13 exit 0' || {
	echo "error: expected claims 13 exit 0" >&2
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
