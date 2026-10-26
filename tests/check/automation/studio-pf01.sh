#!/bin/sh
# PF-01 product input for Packs v2 (docs/testing/procedures/README.md).
# Call after R-state SETUP when porcelain must still prove the state alone.

install_pf01() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_fixture=$_product/external_test/curbpack-studio
	printf '%s\n' '{"packs":["cra-baseline","house-policy","medtech-iec62304"]}' >"$_product/curbpack.json"
	mkdir -p "$_product/claims"
	for _cid in \
		CRA-ANNEX-VII-MANUAL \
		CRA-ANNEX-VII-RISK \
		CRA-ANNEX-VII-SUPPORT \
		CRA-ART14-PATH \
		HOUSE-ANTI-PLACEHOLDER \
		HOUSE-SECURITY-MD \
		HOUSE-SECURITY-TXT
	do
		cp "$_fixture/claims/$_cid.json" "$_product/claims/$_cid.json"
	done
}

# Run curbcheck; print only the Packs v2 run-result JSON on stdout (summary goes to stderr).
# Exit status is curbcheck's. Usage: run_curbcheck_json [extra curbcheck args…]
run_curbcheck_json() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_packs=${CURBCHECK_PACKS:-$_product/external_test/curbpack-studio/packs}
	_out=${CURBCHECK_OUT:-$_product/.curbpack/run-result.json}
	mkdir -p "$(dirname "$_out")"
	curbcheck --repo "$_product" --packs "$_packs" --out "$_out" "$@" >&2
	_code=$?
	cat "$_out"
	return "$_code"
}
