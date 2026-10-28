#!/bin/sh
# Record this Studio commit and the product pin, clone the reference product
# into tmp/cyberready-test-product, and fill tmp/verification-run.sh.
#
# Does not check out another Studio commit. Does not build a binary.
# Does not export CURBPACK_PACKS_DIR.
#
# DEVELOPER_MODE=TRUE uses the current Studio HEAD and working tree as-is,
# including local changes. It never checks out/reset/cleans Studio. When the
# filled tmp/verification-run.sh is sourced, that mode also skips the Studio
# HEAD==baseline lock so a dirty or moved Studio checkout can keep iterating.
#
# Non-interactive wipe: CONFIRM_TMP_WIPE=1 or --yes.
set -eu

root=$(git rev-parse --show-toplevel)
cd "$root"
tmp=$root/tmp
template=$root/testing/verification_run_template.sh
out=$tmp/verification-run.sh
product=$tmp/cyberready-test-product
pin=$root/tests/cyberready-test-product.pin
confirm_wipe=0
developer_mode=0
case "${DEVELOPER_MODE:-}" in
	TRUE | true | 1 | yes | YES) developer_mode=1 ;;
esac
for arg in "$@"; do
	case "$arg" in
		--yes | -y) confirm_wipe=1 ;;
		*)
			echo "error: unknown argument: $arg" >&2
			echo "usage: scripts/start-verification-run.sh [--yes]" >&2
			exit 2
			;;
	esac
done
if [ "${CONFIRM_TMP_WIPE:-}" = "1" ]; then
	confirm_wipe=1
fi

if [ ! -f "$template" ]; then
	echo "error: missing $template" >&2
	exit 2
fi

pin_commit=$(awk '/^commit / { print $2; exit }' "$pin")
pin_url=$(awk '/^url / { print $2; exit }' "$pin")
if [ -z "$pin_commit" ] || [ -z "$pin_url" ]; then
	echo "error: $pin needs a commit line and a url line" >&2
	exit 2
fi

STUDIO_COMMIT=$(git rev-parse HEAD)
REFERENCE_PRODUCT_COMMIT=$pin_commit
AS_OF_DATE=$(date +%F)
STUDIO_ROOT=$root
REFERENCE_PRODUCT_ROOT=$product
studio_status=$(git status --porcelain)
if [ "$developer_mode" -eq 1 ]; then
	if [ -n "$studio_status" ]; then
		echo "DEVELOPER_MODE: Studio working tree is dirty; recording HEAD $STUDIO_COMMIT as-is"
	else
		echo "DEVELOPER_MODE: Studio HEAD $STUDIO_COMMIT (clean)"
	fi
elif [ -n "$studio_status" ]; then
	tracked_dirty=$(printf '%s\n' "$studio_status" | grep -vE '^\?\?' || true)
	if [ -n "$tracked_dirty" ]; then
		echo "error: Studio has tracked local changes; a verification run needs those files to match $STUDIO_COMMIT" >&2
		echo "Commit them, stash them, or: DEVELOPER_MODE=TRUE make start-verification-run" >&2
		printf '%s\n' "$tracked_dirty" >&2
		exit 2
	fi
fi

if [ -e "$tmp" ]; then
	if [ "$confirm_wipe" -eq 1 ]; then
		echo "deleting $tmp (--yes)"
	elif [ -t 0 ]; then
		printf '%s [%s]: ' "tmp exists. Delete it and start again?" "no" >&2
		read -r _ans || _ans=
		case ${_ans:-no} in
			y | Y | yes | YES) ;;
			*)
				echo "error: existing tmp was not replaced; stop" >&2
				exit 2
				;;
		esac
	else
		echo "error: $tmp exists; confirm a full wipe on a TTY, or pass --yes" >&2
		exit 2
	fi
	rm -rf "$tmp"
fi

mkdir -p "$tmp"

echo "cloning $pin_url into tmp/cyberready-test-product"
git clone -q "$pin_url" "$product"
if ! git -C "$product" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}" >/dev/null 2>&1; then
	git -C "$product" fetch -q origin
fi
if ! git -C "$product" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}" >/dev/null 2>&1; then
	echo "error: $REFERENCE_PRODUCT_COMMIT is not in the clone after fetch" >&2
	echo "origin does not see unpushed commits from another checkout" >&2
	exit 2
fi
if ! git -C "$product" merge-base --is-ancestor "$REFERENCE_PRODUCT_COMMIT" origin/main; then
	echo "error: $REFERENCE_PRODUCT_COMMIT is not on origin/main" >&2
	exit 2
fi
REFERENCE_PRODUCT_COMMIT=$(git -C "$product" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}")
git -C "$product" -c advice.detachedHead=false checkout --quiet "$REFERENCE_PRODUCT_COMMIT"

if [ "$developer_mode" -eq 1 ]; then
	DEVELOPER_MODE_VALUE=TRUE
else
	DEVELOPER_MODE_VALUE=
fi

cp "$template" "$out"
python3 - "$out" "$STUDIO_COMMIT" "$REFERENCE_PRODUCT_COMMIT" "$AS_OF_DATE" "$STUDIO_ROOT" "$REFERENCE_PRODUCT_ROOT" "$DEVELOPER_MODE_VALUE" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text()
keys = (
    "STUDIO_COMMIT",
    "REFERENCE_PRODUCT_COMMIT",
    "AS_OF_DATE",
    "STUDIO_ROOT",
    "REFERENCE_PRODUCT_ROOT",
    "DEVELOPER_MODE",
)
for key, raw in zip(keys, sys.argv[2:]):
    needle = f'{key}=""'
    if needle not in text:
        raise SystemExit(f"missing {needle} in {path}")
    text = text.replace(needle, f"{key}={json.dumps(raw)}", 1)
path.write_text(text)
PY

echo
echo "Verification run"
printf '%-28s %s\n' \
	"Studio root:" "$STUDIO_ROOT" \
	"Studio commit:" "$STUDIO_COMMIT" \
	"Reference-product root:" "$REFERENCE_PRODUCT_ROOT" \
	"Reference-product commit:" "$REFERENCE_PRODUCT_COMMIT" \
	"As-of date:" "$AS_OF_DATE" \
	"Developer mode:" "${DEVELOPER_MODE_VALUE:-off}" \
	"Filled file:" "$out"
echo
echo "source tmp/verification-run.sh"
