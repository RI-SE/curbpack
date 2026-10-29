#!/bin/sh
# PF-01 product input for Packs v2 (docs/testing/procedures/README.md).
# Call after R-state SETUP when porcelain must still prove the state alone.

_write_curbpack() {
	_product=$1
	_partial=$2
	_packs_dir=${3-}
	PYTHONPATH="${CURBPACK_ROOT:?}${PYTHONPATH:+:$PYTHONPATH}" python3 - "$_product" "$_partial" "$_packs_dir" <<'PY'
from pathlib import Path
import json, sys
from checks.defaults import created_curbpack
from common.jsonio import write_json

product = Path(sys.argv[1])
kwargs = json.loads(sys.argv[2])
if sys.argv[3]:
    kwargs["packs_dir"] = sys.argv[3]
write_json(product / "curbpack.json", created_curbpack(**kwargs))
PY
}

_install_versioned_packs() {
	_src=$1
	_dest=$2
	shift 2
	python3 - "$_src" "$_dest" "$@" <<'PY'
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
}

_install_studio_packs() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_install_versioned_packs "${CURBPACK_ROOT:?}/docs/reference/test-packs" "$_product/curbpack/packs" "$@"
}

install_pf01() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_fixture=$_product/external_test/curbpack
	_install_versioned_packs "$_fixture/packs" "$_product/curbpack/packs" cra-baseline house-policy medtech-iec62304
	_write_curbpack "$_product" '{"packs":["cra-baseline","house-policy","medtech-iec62304"]}'
	mkdir -p "$_product/curbpack/claims"
	for _cid in \
		CRA-ANNEX-VII-MANUAL \
		CRA-ANNEX-VII-RISK \
		CRA-ANNEX-VII-SUPPORT \
		CRA-ART14-PATH \
		HOUSE-ANTI-PLACEHOLDER \
		HOUSE-SECURITY-MD \
		HOUSE-SECURITY-TXT
	do
		cp "$_fixture/claims/$_cid.json" "$_product/curbpack/claims/$_cid.json"
	done
}

# Three house-policy claims. R4 and R5 delete the clone's fixture, so the
# claim files and the pack directory come from the Studio tree.
install_house_claims() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	_install_studio_packs house-policy
	_write_curbpack "$_product" '{"packs":["house-policy"]}'
	mkdir -p "$_product/curbpack/claims"
	for _cid in HOUSE-ANTI-PLACEHOLDER HOUSE-SECURITY-MD HOUSE-SECURITY-TXT
	do
		cp "$_claims/$_cid.json" "$_product/curbpack/claims/$_cid.json"
	done
}

run_house_curbcheck_json() {
	run_curbcheck_json "$@"
}

# MD-SW-CLASS translated from curbpack medtech-iec62304 annex_file rule.
# Requirement lives in Studio docs/reference/test-packs (clone fixture pack is
# metadata-only). Copy that Studio tree into the product packs_dir.
install_md_sw_class() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	_install_studio_packs cra-baseline house-policy medtech-iec62304
	_write_curbpack "$_product" '{"packs":["cra-baseline","house-policy","medtech-iec62304"]}'
	mkdir -p "$_product/curbpack/claims"
	cp "$_claims/MD-SW-CLASS.json" "$_product/curbpack/claims/MD-SW-CLASS.json"
}

run_studio_packs_curbcheck_json() {
	run_curbcheck_json "$@"
}

install_claim() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_cid=$1
	_packs_json=$2
	_claims=${CURBPACK_ROOT:?}/docs/reference/test-packs/claims
	_write_curbpack "$_product" "$_packs_json"
	_ids=$(python3 -c "import json,sys; print(' '.join(json.loads(sys.argv[1]).get('packs') or []))" "$_packs_json")
	# shellcheck disable=SC2086
	_install_studio_packs $_ids
	mkdir -p "$_product/curbpack/claims"
	# Drop other claims so this case observes one row.
	rm -f "$_product/curbpack/claims"/*.json
	cp "$_claims/$_cid.json" "$_product/curbpack/claims/$_cid.json"
}

# Rewrite git_fresh as_of from the verification-run date (YYYY-MM-DD → RFC3339).
install_fix_fresh_review() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_as_of=${AS_OF_DATE:?}
	install_claim FIX-FRESH-REVIEW '{"packs":["fresh-owned-test"]}'
	python3 - "$_product/curbpack/claims/FIX-FRESH-REVIEW.json" "$_as_of" <<'PY'
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
	_install_studio_packs ev-008-order
	_write_curbpack "$_product" '{"packs":["ev-008-order"]}'
	mkdir -p "$_product/curbpack/claims"
	find "$_product/curbpack/claims" -maxdepth 1 -type f -name '*.json' -exec rm -f {} +
	case $_order in
		alpha-beta)
			cp "$_claims/EV008-ALPHA.json" "$_product/curbpack/claims/EV008-ALPHA.json"
			cp "$_claims/EV008-BETA.json" "$_product/curbpack/claims/EV008-BETA.json"
			;;
		beta-alpha)
			# Lexical order of filenames decides load order; prefix forces BETA first.
			cp "$_claims/EV008-BETA.json" "$_product/curbpack/claims/01-EV008-BETA.json"
			cp "$_claims/EV008-ALPHA.json" "$_product/curbpack/claims/02-EV008-ALPHA.json"
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
	_install_studio_packs ev-008-order
	_write_curbpack "$_product" '{"packs":["ev-008-order"]}'
	mkdir -p "$_product/curbpack/claims"
	find "$_product/curbpack/claims" -maxdepth 1 -type f -name '*.json' -exec rm -f {} +
	cp "$_claims/EV008-BOTH-PATHS.json" "$_product/curbpack/claims/EV008-BOTH-PATHS.json"
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
	python3 - "$_product/curbpack/claims/EV008-BOTH-PATHS.json" "$_paths" <<'PY'
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
	git -C "$_product" add curbpack.json curbpack/claims curbpack/packs
	git -C "$_product" \
		-c user.email=curbpack-test@example.com \
		-c user.name=curbpack-test \
		commit -m "studio pf01 selection and claims" >/dev/null
}

# Drop untracked PF-01 files so setup.sh R2 can require a clean tree.
remove_pf01() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	rm -f "$_product/curbpack.json"
	rm -rf "$_product/curbpack/claims" "$_product/curbpack/packs"
}

# Run curbcheck; print only the Packs v2 run-result JSON on stdout (summary goes to stderr).
# Exit status is curbcheck's. Usage: run_curbcheck_json [extra curbcheck args…]
run_curbcheck_json() {
	_product=${REFERENCE_PRODUCT_ROOT:?}
	_out=${CURBCHECK_OUT:-$_product/.curbpack/run-result.json}
	mkdir -p "$(dirname "$_out")"
	curbcheck --repo "$_product" -o "$_out" "$@" >&2
	_code=$?
	cat "$_out"
	return "$_code"
}
