# Verification-run configuration template
#
# This file is version-controlled. At the start of a test run, copy it to
# tmp/verification-run.sh and fill in the five values selected for that run.
# tmp/verification-run.sh is run-specific working material; do not check the
# filled copy into the repository.
#
# Source the filled copy from the Curbpack repository root:
#
#   source tmp/verification-run.sh
#
# Do not execute it as a separate child process.
#
# This file validates the selected test-run configuration and restores the
# disposable reference-product clone to the frozen baseline.
#
# Curbpack: verify that HEAD is still CURBPACK_COMMIT. Do not checkout,
# reset, or clean the Curbpack repository.
#
# Reference product: confirm REFERENCE_PRODUCT_ROOT is this run's
# disposable clone ($CURBPACK_ROOT/tmp/cyberready-test-product), read
# that clone's origin URL, delete the directory, clone the repository
# again into the same path, and checkout/detach exactly
# REFERENCE_PRODUCT_COMMIT. Do not pull, reset, or clean an old checkout.
# Local test_* refs are discarded with the directory. The previously
# checked-out branch does not select the baseline. Later R-state setup
# may then modify the product working tree.
#
# It prepends $CURBPACK_ROOT/tmp to PATH in the sourcing shell so
# `curbpack` is tmp/curbpack, not an installed release.

CURBPACK_COMMIT=""
REFERENCE_PRODUCT_COMMIT=""
AS_OF_DATE=""
CURBPACK_ROOT=""
REFERENCE_PRODUCT_ROOT=""

export CURBPACK_COMMIT
export REFERENCE_PRODUCT_COMMIT
export AS_OF_DATE
export CURBPACK_ROOT
export REFERENCE_PRODUCT_ROOT
export CURBPACK_PACKS_DIR="$REFERENCE_PRODUCT_ROOT/external_test/curbpack/packs"

if [ -z "$CURBPACK_COMMIT" ]; then
	echo "error: CURBPACK_COMMIT is empty" >&2
	return 1 2>/dev/null || exit 1
fi
if [ -z "$REFERENCE_PRODUCT_COMMIT" ]; then
	echo "error: REFERENCE_PRODUCT_COMMIT is empty" >&2
	return 1 2>/dev/null || exit 1
fi
if [ -z "$AS_OF_DATE" ]; then
	echo "error: AS_OF_DATE is empty" >&2
	return 1 2>/dev/null || exit 1
fi
if [ -z "$CURBPACK_ROOT" ]; then
	echo "error: CURBPACK_ROOT is empty" >&2
	return 1 2>/dev/null || exit 1
fi
if [ -z "$REFERENCE_PRODUCT_ROOT" ]; then
	echo "error: REFERENCE_PRODUCT_ROOT is empty" >&2
	return 1 2>/dev/null || exit 1
fi

if [ "$(git -C "$CURBPACK_ROOT" rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]; then
	echo "error: CURBPACK_ROOT is not a Git repository: $CURBPACK_ROOT" >&2
	return 1 2>/dev/null || exit 1
fi

if ! curbpack_head=$(git -C "$CURBPACK_ROOT" rev-parse HEAD); then
	echo "error: could not read HEAD from CURBPACK_ROOT: $CURBPACK_ROOT" >&2
	return 1 2>/dev/null || exit 1
fi
if [ "$curbpack_head" != "$CURBPACK_COMMIT" ]; then
	echo "error: Curbpack repo is at $curbpack_head, but the baseline states $CURBPACK_COMMIT" >&2
	return 1 2>/dev/null || exit 1
fi

curbpack_root=$(git -C "$CURBPACK_ROOT" rev-parse --show-toplevel)
expected_product_root=$curbpack_root/tmp/cyberready-test-product
if [ "$(git -C "$REFERENCE_PRODUCT_ROOT" rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]; then
	echo "error: REFERENCE_PRODUCT_ROOT is not a Git repository: $REFERENCE_PRODUCT_ROOT" >&2
	return 1 2>/dev/null || exit 1
fi
product_root=$(git -C "$REFERENCE_PRODUCT_ROOT" rev-parse --show-toplevel)
if [ "$product_root" != "$expected_product_root" ]; then
	echo "error: REFERENCE_PRODUCT_ROOT is $product_root, not this verification run's disposable clone $expected_product_root" >&2
	return 1 2>/dev/null || exit 1
fi
if ! product_origin=$(git -C "$product_root" remote get-url origin 2>/dev/null) || [ -z "$product_origin" ]; then
	echo "error: disposable clone has no origin URL; cannot recreate $expected_product_root" >&2
	return 1 2>/dev/null || exit 1
fi

rm -rf "$expected_product_root"
if [ -e "$expected_product_root" ]; then
	echo "error: could not remove disposable reference-product checkout: $expected_product_root" >&2
	return 1 2>/dev/null || exit 1
fi
if ! git clone --no-checkout --quiet "$product_origin" "$expected_product_root"; then
	echo "error: could not clone $product_origin into $expected_product_root" >&2
	return 1 2>/dev/null || exit 1
fi

if ! expected_commit=$(git -C "$expected_product_root" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}" 2>/dev/null); then
	echo "error: REFERENCE_PRODUCT_COMMIT is not a commit in the fresh clone: $REFERENCE_PRODUCT_COMMIT" >&2
	return 1 2>/dev/null || exit 1
fi
if ! git -C "$expected_product_root" -c advice.detachedHead=false checkout --force --quiet --detach "$expected_commit"; then
	echo "error: could not checkout REFERENCE_PRODUCT_COMMIT in $expected_product_root: $REFERENCE_PRODUCT_COMMIT" >&2
	return 1 2>/dev/null || exit 1
fi

if ! product_head=$(git -C "$expected_product_root" rev-parse HEAD); then
	echo "error: could not read HEAD from REFERENCE_PRODUCT_ROOT: $expected_product_root" >&2
	return 1 2>/dev/null || exit 1
fi
if [ "$product_head" != "$expected_commit" ]; then
	echo "error: reference-product repo is at $product_head, but the baseline states $REFERENCE_PRODUCT_COMMIT" >&2
	return 1 2>/dev/null || exit 1
fi
product_status=$(git -C "$expected_product_root" status --porcelain)
if [ -n "$product_status" ]; then
	echo "error: reference-product working tree is not clean after restore: $expected_product_root" >&2
	printf '%s\n' "$product_status" >&2
	return 1 2>/dev/null || exit 1
fi

expected_curbpack_bin="$CURBPACK_ROOT/tmp/curbpack"
if [ ! -x "$expected_curbpack_bin" ]; then
	echo "error: missing executable $expected_curbpack_bin" >&2
	echo "From $CURBPACK_ROOT build the recorded commit with:" >&2
	echo "  make build" >&2
	return 1 2>/dev/null || exit 1
fi
curbpack_bin=$(command -v curbpack 2>/dev/null || true)
if [ "$curbpack_bin" != "$expected_curbpack_bin" ]; then
	PATH="$CURBPACK_ROOT/tmp:$PATH"
	export PATH
	hash -r 2>/dev/null || true
fi
if ! curbpack_bin=$(command -v curbpack); then
	echo "error: curbpack is not on PATH after prepending $CURBPACK_ROOT/tmp" >&2
	return 1 2>/dev/null || exit 1
fi
if [ "$curbpack_bin" != "$expected_curbpack_bin" ]; then
	echo "error: curbpack is at $curbpack_bin, but the baseline states $expected_curbpack_bin" >&2
	return 1 2>/dev/null || exit 1
fi
export CURBPACK_BIN="$expected_curbpack_bin"

case "$AS_OF_DATE" in
[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
*)
	echo "error: AS_OF_DATE is not YYYY-MM-DD: $AS_OF_DATE" >&2
	return 1 2>/dev/null || exit 1
	;;
esac

echo "Verification run configuration: OK"
printf '%-25s %s\n' \
	"Curbpack root:" "$CURBPACK_ROOT" \
	"Curbpack commit:" "$CURBPACK_COMMIT" \
	"Curbpack binary:" "$CURBPACK_BIN" \
	"Reference-product root:" "$REFERENCE_PRODUCT_ROOT" \
	"Reference-product commit:" "$REFERENCE_PRODUCT_COMMIT" \
	"As-of date:" "$AS_OF_DATE" \
	"Packs dir:" "$CURBPACK_PACKS_DIR"
