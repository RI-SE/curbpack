# Verification-run configuration template
#
# Version-controlled. make test-curbcheck copies it to tmp/verification-run.sh
# and fills the five values. Do not commit the filled copy.
#
# Source the filled copy from the Studio repository root:
#
#   source tmp/verification-run.sh
#
# That checks Studio HEAD is still the recorded commit, deletes
# tmp/cyberready-test-product, clones it again, and checks out the pin.
# It does not export CURBPACK_PACKS_DIR. It does not put a curbpack binary
# on PATH. It does not start the Studio application.

STUDIO_COMMIT=""
REFERENCE_PRODUCT_COMMIT=""
AS_OF_DATE=""
STUDIO_ROOT=""
REFERENCE_PRODUCT_ROOT=""

export STUDIO_COMMIT
export REFERENCE_PRODUCT_COMMIT
export AS_OF_DATE
export STUDIO_ROOT
export REFERENCE_PRODUCT_ROOT

if [ -z "$STUDIO_COMMIT" ]; then
	echo "error: STUDIO_COMMIT is empty" >&2
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
if [ -z "$STUDIO_ROOT" ]; then
	echo "error: STUDIO_ROOT is empty" >&2
	return 1 2>/dev/null || exit 1
fi
if [ -z "$REFERENCE_PRODUCT_ROOT" ]; then
	echo "error: REFERENCE_PRODUCT_ROOT is empty" >&2
	return 1 2>/dev/null || exit 1
fi

if [ "$(git -C "$STUDIO_ROOT" rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]; then
	echo "error: STUDIO_ROOT is not a Git repository: $STUDIO_ROOT" >&2
	return 1 2>/dev/null || exit 1
fi
if ! studio_head=$(git -C "$STUDIO_ROOT" rev-parse HEAD); then
	echo "error: could not read HEAD from STUDIO_ROOT: $STUDIO_ROOT" >&2
	return 1 2>/dev/null || exit 1
fi
if [ "$studio_head" != "$STUDIO_COMMIT" ]; then
	echo "error: Studio repo is at $studio_head, but the baseline states $STUDIO_COMMIT" >&2
	return 1 2>/dev/null || exit 1
fi

studio_root=$(git -C "$STUDIO_ROOT" rev-parse --show-toplevel)
expected_product_root=$studio_root/tmp/cyberready-test-product
if [ "$(git -C "$REFERENCE_PRODUCT_ROOT" rev-parse --is-inside-work-tree 2>/dev/null)" != "true" ]; then
	echo "error: REFERENCE_PRODUCT_ROOT is not a Git repository: $REFERENCE_PRODUCT_ROOT" >&2
	return 1 2>/dev/null || exit 1
fi
product_root=$(git -C "$REFERENCE_PRODUCT_ROOT" rev-parse --show-toplevel)
if [ "$product_root" != "$expected_product_root" ]; then
	echo "error: REFERENCE_PRODUCT_ROOT is $product_root, not this run's clone $expected_product_root" >&2
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

case "$AS_OF_DATE" in
[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) ;;
*)
	echo "error: AS_OF_DATE is not YYYY-MM-DD: $AS_OF_DATE" >&2
	return 1 2>/dev/null || exit 1
	;;
esac

echo "Verification run configuration: OK"
printf '%-25s %s\n' \
	"Studio root:" "$STUDIO_ROOT" \
	"Studio commit:" "$STUDIO_COMMIT" \
	"Reference-product root:" "$REFERENCE_PRODUCT_ROOT" \
	"Reference-product commit:" "$REFERENCE_PRODUCT_COMMIT" \
	"As-of date:" "$AS_OF_DATE"
