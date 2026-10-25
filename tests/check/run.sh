#!/bin/sh
# make test-curbcheck. Clone, restore, apply R1, run the seven carried checks.
# Manual rows are printed and are not a pass.
set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"

"$root/scripts/start-verification-run.sh" --yes
# shellcheck disable=SC1091
. "$root/tmp/verification-run.sh"

product=$REFERENCE_PRODUCT_ROOT
(
	cd "$product"
	./external_test/curbpack/setup.sh R1 --commit
)
if ! git -C "$product" diff --quiet -- external_test/curbpack/states/R1.sh; then
	echo "error: states/R1.sh changed inside the clone" >&2
	exit 1
fi

printf '%s\n' '{"packs":["cra-baseline","house-policy","medtech-iec62304"]}' >"$product/curbpack.json"
mkdir -p "$product/claims"
for id in \
	CRA-ANNEX-VII-MANUAL \
	CRA-ANNEX-VII-RISK \
	CRA-ANNEX-VII-SUPPORT \
	CRA-ART14-PATH \
	HOUSE-ANTI-PLACEHOLDER \
	HOUSE-SECURITY-MD \
	HOUSE-SECURITY-TXT
do
	cp "$root/docs/reference/test-packs/claims/$id.json" "$product/claims/$id.json"
done

out=$product/run-result.json
set +e
checks_out=$(python3 -m checks --repo "$product" --packs "$root/docs/reference/test-packs" --out "$out")
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
