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

# Three house-policy claims. R4 and R5 delete the clone's fixture, so the
# claim files and the pack directory come from the Studio tree.
install_house_claims() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	printf '%s\n' '{"packs":["house-policy"]}' >"$_product/curbpack.json"
	mkdir -p "$_product/claims"
	for _cid in HOUSE-ANTI-PLACEHOLDER HOUSE-SECURITY-MD HOUSE-SECURITY-TXT
	do
		cp "$_claims/$_cid.json" "$_product/claims/$_cid.json"
	done
}

run_house_curbcheck_json() {
	CURBCHECK_PACKS="${CURBPACK_ROOT:?}/docs/reference/test-packs" run_curbcheck_json "$@"
}

# MD-SW-CLASS translated from curbpack medtech-iec62304 annex_file rule.
# Requirement lives in Studio docs/reference/test-packs (clone fixture pack is
# metadata-only). Packs root must be that Studio tree.
install_md_sw_class() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	printf '%s\n' '{"packs":["cra-baseline","house-policy","medtech-iec62304"]}' >"$_product/curbpack.json"
	mkdir -p "$_product/claims"
	cp "$_claims/MD-SW-CLASS.json" "$_product/claims/MD-SW-CLASS.json"
}

run_studio_packs_curbcheck_json() {
	CURBCHECK_PACKS="${CURBPACK_ROOT:?}/docs/reference/test-packs" run_curbcheck_json "$@"
}

install_claim() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_cid=$1
	_packs_json=$2
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	printf '%s\n' "$_packs_json" >"$_product/curbpack.json"
	mkdir -p "$_product/claims"
	# Drop other claims so this case observes one row.
	rm -f "$_product/claims"/*.json
	cp "$_claims/$_cid.json" "$_product/claims/$_cid.json"
}

# Rewrite git_fresh as_of from the verification-run date (YYYY-MM-DD → RFC3339).
install_fix_fresh_review() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_as_of=${AS_OF_DATE:?}
	install_claim FIX-FRESH-REVIEW '{"packs":["fresh-owned-test"]}'
	python3 - "$_product/claims/FIX-FRESH-REVIEW.json" "$_as_of" <<'PY'
import json, sys
path, day = sys.argv[1], sys.argv[2]
data = json.loads(open(path, encoding="utf-8").read())
for check in data["checks"]:
    if check.get("check") == "git_fresh":
        check["args"]["as_of"] = f"{day}T23:59:59Z"
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
PY
}

install_fix_owned_policy() {
	install_claim FIX-OWNED-POLICY '{"packs":["fresh-owned-test"]}'
}

install_house_dep_axios() {
	install_claim HOUSE-DEP-AXIOS-PIN '{"packs":["house-policy"]}'
}

install_cra_dep_axios() {
	install_claim CRA-DEP-AXIOS-PIN '{"packs":["cra-baseline"]}'
}

# Pin a banned axios version into package.json (EV-007-D/E).
pin_banned_axios() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	python3 - "$_product/package.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.loads(open(path, encoding="utf-8").read())
deps = data.setdefault("dependencies", {})
if not isinstance(deps, dict):
    deps = {}
    data["dependencies"] = deps
deps["axios"] = "^1.6.0"
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
PY
}

install_ev008_rule_order_claims() {
	# $1 = ALPHA then BETA, or BETA then ALPHA (claim file basenames written in that order).
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	_order=$1
	printf '%s\n' '{"packs":["ev-008-order"]}' >"$_product/curbpack.json"
	mkdir -p "$_product/claims"
	find "$_product/claims" -maxdepth 1 -type f -name '*.json' -exec rm -f {} +
	case $_order in
		alpha-beta)
			cp "$_claims/EV008-ALPHA.json" "$_product/claims/EV008-ALPHA.json"
			cp "$_claims/EV008-BETA.json" "$_product/claims/EV008-BETA.json"
			;;
		beta-alpha)
			# Lexical order of filenames decides load order; prefix forces BETA first.
			cp "$_claims/EV008-BETA.json" "$_product/claims/01-EV008-BETA.json"
			cp "$_claims/EV008-ALPHA.json" "$_product/claims/02-EV008-ALPHA.json"
			# Claim id stays inside JSON; filenames only control sorted load order.
			;;
		*)
			echo "install_ev008_rule_order_claims: want alpha-beta or beta-alpha" >&2
			return 1
			;;
	esac
}

install_ev008_file_order_claim() {
	# $1 = alpha-beta or beta-alpha path list inside the single exist Check.
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	_order=$1
	printf '%s\n' '{"packs":["ev-008-order"]}' >"$_product/curbpack.json"
	mkdir -p "$_product/claims"
	find "$_product/claims" -maxdepth 1 -type f -name '*.json' -exec rm -f {} +
	cp "$_claims/EV008-BOTH-PATHS.json" "$_product/claims/EV008-BOTH-PATHS.json"
	case $_order in
		alpha-beta)
			_paths='["docs/ev008-alpha.md","docs/ev008-beta.md"]'
			;;
		beta-alpha)
			_paths='["docs/ev008-beta.md","docs/ev008-alpha.md"]'
			;;
		*)
			echo "install_ev008_file_order_claim: want alpha-beta or beta-alpha" >&2
			return 1
			;;
	esac
	python3 - "$_product/claims/EV008-BOTH-PATHS.json" "$_paths" <<'PY'
import json, sys
path, paths_json = sys.argv[1], sys.argv[2]
data = json.loads(open(path, encoding="utf-8").read())
paths = json.loads(paths_json)
data["args"]["paths"] = paths
data["checks"][0]["args"]["paths"] = paths
open(path, "w", encoding="utf-8").write(json.dumps(data, indent=2) + "\n")
PY
}

install_house_secret_paths() {
	install_claim HOUSE-SECRET-PATHS '{"packs":["house-policy"]}'
	# Packs v2 contents fails on absent paths; create empty stand-ins so the
	# pattern probe on SECURITY.md is what fails (legacy text_forbid skipped absent).
	_product=${REFERENCE_PRODUCT_ROOT:?}
	for _p in .env .env.local credentials.json service-account.json id_rsa; do
		printf '\n' >"$_product/$_p"
	done
}

# Commit PF-01 files so Git reports a clean worktree (PV-001).
commit_pf01() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	git -C "$_product" add curbpack.json claims
	git -C "$_product" \
		-c user.email=curbpack-test@example.com \
		-c user.name=curbpack-test \
		commit -m "studio pf01 selection and claims" >/dev/null
}

# Drop untracked PF-01 files so setup.sh R2 can require a clean tree.
remove_pf01() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	rm -f "$_product/curbpack.json"
	rm -rf "$_product/claims"
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
