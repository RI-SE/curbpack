# Shared helpers for suite scripts. Source from suit-runner.
# Studio root is STUDIO_ROOT (or git toplevel). Product is REFERENCE_PRODUCT_ROOT
# after sourcing tmp/verification-run.sh. Do not export CURBPACK_PACKS_DIR.
# Do not call curbpack check/share/review.

studio_root() {
	if [ -n "${STUDIO_ROOT:-}" ]; then
		printf '%s\n' "$STUDIO_ROOT"
	else
		git rev-parse --show-toplevel
	fi
}

# R4/R5 fixture scripts read CURBPACK_ROOT/testdata (Studio checkout).
export_studio_as_curbpack_root() {
	CURBPACK_ROOT=$(studio_root)
	export CURBPACK_ROOT
}

fixture_dir() {
	printf '%s/external_test/curbpack-studio\n' "$REFERENCE_PRODUCT_ROOT"
}

# R4/R5 replace the product tree and remove external_test/curbpack-studio.
# Keep a Studio-side copy of packs/claims for --packs and claim install.
fixture_stash() {
	printf '%s/tmp/verification-fixture\n' "$(studio_root)"
}

preserve_fixture_assets() {
	src=$(fixture_dir)
	stash=$(fixture_stash)
	mkdir -p "$stash"
	if [ -d "$src/packs" ] && [ -d "$src/claims" ]; then
		rm -rf "$stash/packs" "$stash/claims"
		cp -R "$src/packs" "$stash/packs"
		cp -R "$src/claims" "$stash/claims"
	fi
}

packs_dir() {
	if [ -d "$(fixture_dir)/packs/house-policy" ]; then
		printf '%s/packs\n' "$(fixture_dir)"
	else
		printf '%s/packs\n' "$(fixture_stash)"
	fi
}

claims_src() {
	if [ -f "$(fixture_dir)/claims/HOUSE-SECURITY-MD.json" ]; then
		printf '%s/claims\n' "$(fixture_dir)"
	else
		printf '%s/claims\n' "$(fixture_stash)"
	fi
}

# Restore product via verification-run.sh, then ensure Studio root for testdata.
studio_begin() {
	case_id=$1
	root=$(studio_root)
	if ! cd "$root"; then
		echo "$case_id SETUP 1"
		return 1
	fi
	if ! . tmp/verification-run.sh; then
		echo "$case_id SETUP 1"
		return 1
	fi
	export_studio_as_curbpack_root
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "$case_id SETUP 2"
		return 1
	fi
	preserve_fixture_assets
	return 0
}

# Apply an R-state through the Studio fixture. Prints setup stdout.
studio_setup() {
	state=$1
	shift
	(
		cd "$(fixture_dir)" || exit 1
		SUT=curbpack-studio ./setup.sh "$state" "$@"
	)
}

# Write curbpack.json and copy claim ids into product claims/.
# Usage: studio_claims id [id ...]
studio_claims() {
	src=$(claims_src)
	printf '%s\n' '{"packs":["cra-baseline","house-policy","medtech-iec62304"]}' >"$REFERENCE_PRODUCT_ROOT/curbpack.json"
	mkdir -p "$REFERENCE_PRODUCT_ROOT/claims"
	rm -f "$REFERENCE_PRODUCT_ROOT/claims"/*.json
	for id in "$@"; do
		cp "$src/$id.json" "$REFERENCE_PRODUCT_ROOT/claims/$id.json"
	done
}

studio_claims_seven() {
	studio_claims \
		CRA-ANNEX-VII-MANUAL \
		CRA-ANNEX-VII-RISK \
		CRA-ANNEX-VII-SUPPORT \
		CRA-ART14-PATH \
		HOUSE-ANTI-PLACEHOLDER \
		HOUSE-SECURITY-MD \
		HOUSE-SECURITY-TXT
}

# House exist/contents claims that current checks can evaluate (no dep_ban).
studio_claims_house() {
	src=$(claims_src)
	printf '%s\n' '{"packs":["house-policy"]}' >"$REFERENCE_PRODUCT_ROOT/curbpack.json"
	mkdir -p "$REFERENCE_PRODUCT_ROOT/claims"
	rm -f "$REFERENCE_PRODUCT_ROOT/claims"/*.json
	for id in HOUSE-ANTI-PLACEHOLDER HOUSE-SECURITY-MD HOUSE-SECURITY-TXT; do
		cp "$src/$id.json" "$REFERENCE_PRODUCT_ROOT/claims/$id.json"
	done
}

# Run curbcheck. Writes run-result JSON to $1 (default product run-result.json).
# Prints the human summary on stdout. Exit status is process_exit_code.
studio_curbcheck() {
	out=${1:-$REFERENCE_PRODUCT_ROOT/run-result.json}
	root=$(studio_root)
	(
		cd "$root" || exit 1
		python3 -m checks \
			--repo "$REFERENCE_PRODUCT_ROOT" \
			--packs "$(packs_dir)" \
			--out "$out"
	)
}

claim_status() {
	file=$1
	id=$2
	jq -r --arg id "$id" '.claims[] | select(.id == $id) | .status' "$file"
}

claim_is() {
	file=$1
	id=$2
	want=$3
	got=$(claim_status "$file" "$id")
	[ "$got" = "$want" ]
}

# Stable claim-status map for determinism comparisons.
claim_status_map() {
	jq -c '[.claims[] | {id, status}] | sort_by(.id)' "$1"
}
