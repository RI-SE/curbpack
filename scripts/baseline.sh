#!/bin/sh
# Three-repository baseline tags. Does not run tests.
# Owned by Curbpack (main verification repo).
#
# Expected to have already passed, separately:
#   Curbpack:                  make test
#   CTAM:                      make test && make demo
#   cyberready-test-product:   make test
#
# Create:   make baseline NAME=<name> CONFIRM_TESTS_PASSED=TRUE
# Check:    make baseline-check NAME=<name>
# Checkout: make checkout-baseline NAME=<name>
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
CTAM=$(CDPATH= cd -- "$ROOT/../ctam" && pwd)
PRODUCT=$(CDPATH= cd -- "$ROOT/../cyberready-test-product" && pwd)
REGISTRY=$ROOT/BASELINES.md

die() {
    printf '%s\n' "$*" >&2
    exit 1
}

mode=create
case "${1:-}" in
check) mode=check ;;
checkout) mode=checkout ;;
esac

[ -n "${NAME:-}" ] || die "usage: make baseline NAME=<name> CONFIRM_TESTS_PASSED=TRUE
       make baseline-check NAME=<name>
       make checkout-baseline NAME=<name>"

case $NAME in
*[!A-Za-z0-9._-]* | "" | .* | -*)
    die "NAME must be a simple token (letters, digits, '.', '_', '-')"
    ;;
esac

[ -d "$CTAM/.git" ] || die "CTAM not found at $CTAM"
[ -d "$PRODUCT/.git" ] || die "reference product not found at $PRODUCT"

entry_for_name() {
    [ -f "$REGISTRY" ] || return 1
    awk -v name="$NAME" '
        /^## / {
            if (keep) out = block
            block = $0 "\n"
            keep = 0
            next
        }
        {
            block = block $0 "\n"
            if ($0 == "- name: " name) keep = 1
        }
        END {
            if (keep) out = block
            if (out != "") printf "%s", out
        }
    ' "$REGISTRY"
}

field() {
    printf '%s\n' "$1" | awk -v key="$2" '
        index($0, "- " key ": ") == 1 {
            print substr($0, length("- " key ": ") + 1)
            exit
        }
    '
}

require_clean() {
    repo=$1
    label=$2
    if [ -n "$(git -C "$repo" status --porcelain)" ]; then
        die "$label is not clean: $repo"
    fi
}

check_tag() {
    repo=$1
    label=$2
    want=$3
    if ! git -C "$repo" show-ref --verify --quiet "refs/tags/$tag"; then
        printf 'FAIL  %s: missing tag %s\n' "$label" "$tag" >&2
        fail=1
        return
    fi
    kind=$(git -C "$repo" cat-file -t "refs/tags/$tag")
    if [ "$kind" != "tag" ]; then
        printf 'FAIL  %s: %s is not an annotated tag\n' "$label" "$tag" >&2
        fail=1
        return
    fi
    got=$(git -C "$repo" rev-parse "$tag^{commit}")
    if [ "$got" != "$want" ]; then
        printf 'FAIL  %s: %s is %s, BASELINES.md has %s\n' "$label" "$tag" "$got" "$want" >&2
        fail=1
        return
    fi
    printf 'OK    %s  %s\n' "$label" "$got"
}

load_entry() {
    entry=$(entry_for_name) || true
    [ -n "$entry" ] || die "no BASELINES.md entry for NAME=$NAME"

    tag=$(field "$entry" tag)
    want_curb=$(field "$entry" curbpack)
    want_ctam=$(field "$entry" ctam)
    want_product=$(field "$entry" reference-product)

    [ -n "$tag" ] && [ -n "$want_curb" ] && [ -n "$want_ctam" ] && [ -n "$want_product" ] ||
        die "BASELINES.md entry for NAME=$NAME is incomplete"
}

if [ "$mode" = "check" ]; then
    load_entry
    fail=0
    printf 'tag   %s\n' "$tag"
    check_tag "$ROOT" "Curbpack" "$want_curb"
    check_tag "$CTAM" "CTAM" "$want_ctam"
    check_tag "$PRODUCT" "reference-product" "$want_product"
    [ "$fail" -eq 0 ] || exit 1
    exit 0
fi

if [ "$mode" = "checkout" ]; then
    load_entry
    fail=0
    printf 'baseline %s\n' "$NAME"
    printf 'tag      %s\n' "$tag"

    check_tag "$ROOT" "Curbpack" "$want_curb"
    check_tag "$CTAM" "CTAM" "$want_ctam"
    check_tag "$PRODUCT" "reference-product" "$want_product"
    [ "$fail" -eq 0 ] || exit 1

    require_clean "$ROOT" "Curbpack"
    require_clean "$CTAM" "CTAM"
    require_clean "$PRODUCT" "reference-product"

    git -C "$ROOT" checkout --detach "$want_curb"
    git -C "$CTAM" checkout --detach "$want_ctam"
    git -C "$PRODUCT" checkout --detach "$want_product"

    printf 'checked out %s (detached HEAD; nothing pushed)\n' "$tag"
    printf 'Curbpack             %s\n' "$(git -C "$ROOT" rev-parse HEAD)"
    printf 'CTAM                 %s\n' "$(git -C "$CTAM" rev-parse HEAD)"
    printf 'reference-product    %s\n' "$(git -C "$PRODUCT" rev-parse HEAD)"
    exit 0
fi

[ "${CONFIRM_TESTS_PASSED:-}" = "TRUE" ] || die "refusing to create a baseline: tests are not run here.

Set CONFIRM_TESTS_PASSED=TRUE only if Curbpack, CTAM, and cyberready-test-product have already been verified.

Example: make baseline NAME=$NAME CONFIRM_TESTS_PASSED=TRUE"

printf 'WARNING: CONFIRM_TESTS_PASSED=TRUE. Tests are not run.\n'
printf 'You are asserting that Curbpack, CTAM, and cyberready-test-product have already been verified.\n'

require_clean "$ROOT" "Curbpack"
require_clean "$CTAM" "CTAM"
require_clean "$PRODUCT" "reference-product"

curb_sha=$(git -C "$ROOT" rev-parse HEAD)
ctam_sha=$(git -C "$CTAM" rev-parse HEAD)
product_sha=$(git -C "$PRODUCT" rev-parse HEAD)
date=$(date +%Y-%m-%d)
tag=baseline/$date-$NAME

printf 'Curbpack             %s\n' "$curb_sha"
printf 'CTAM                 %s\n' "$ctam_sha"
printf 'reference-product    %s\n' "$product_sha"
printf 'tag                  %s\n' "$tag"

if [ -f "$REGISTRY" ] && grep -q "^## $tag\$" "$REGISTRY"; then
    die "BASELINES.md already has $tag"
fi

for repo in "$ROOT" "$CTAM" "$PRODUCT"; do
    if git -C "$repo" show-ref --verify --quiet "refs/tags/$tag"; then
        die "tag $tag already exists in $repo"
    fi
done

msg=$(cat <<EOF
baseline name: $NAME
date: $date
Curbpack: $curb_sha
CTAM: $ctam_sha
reference-product: $product_sha
verification: tests were externally verified; CONFIRM_TESTS_PASSED=TRUE
EOF
)

git -C "$ROOT" tag -a "$tag" -m "$msg"
git -C "$CTAM" tag -a "$tag" -m "$msg"
git -C "$PRODUCT" tag -a "$tag" -m "$msg"

if [ ! -f "$REGISTRY" ]; then
    cat >"$REGISTRY" <<'EOF'
# Baselines

Three-repository tags `baseline/<YYYY-MM-DD>-<NAME>` on Curbpack, CTAM, and cyberready-test-product.

The tagged commits do not include later updates to this registry.

Each create requires `CONFIRM_TESTS_PASSED=TRUE`. Tests are not run by the baseline command.

Checkout: `make checkout-baseline NAME=<name>` then `make start-verification-run`.
EOF
fi

{
    printf '\n## %s\n\n' "$tag"
    printf -- '- tag: %s\n' "$tag"
    printf -- '- date: %s\n' "$date"
    printf -- '- name: %s\n' "$NAME"
    printf -- '- curbpack: %s\n' "$curb_sha"
    printf -- '- ctam: %s\n' "$ctam_sha"
    printf -- '- reference-product: %s\n' "$product_sha"
    printf -- '- verification: tests were externally verified; CONFIRM_TESTS_PASSED=TRUE\n'
} >>"$REGISTRY"

git -C "$ROOT" add -- BASELINES.md
git -C "$ROOT" commit -m "Record baseline $tag"

printf 'recorded %s (local tags and registry commit only; nothing pushed)\n' "$tag"
