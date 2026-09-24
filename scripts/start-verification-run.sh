#!/bin/sh
# Start a verification run, recreate repo tmp/, clone the reference product,
# build Curbpack, and fill tmp/verification-run.sh.
#
# Normal mode requires a clean Curbpack tree and may select another commit.
# DEVELOPER_MODE=TRUE uses the current Curbpack HEAD and working tree as-is,
# including local changes. It never checks out/reset/cleans Curbpack.
#
# If tmp/verification-run.sh already exists, replacement requires explicit
# confirmation. Never touches /tmp or a sibling product checkout.
# Origin fetch cannot see unpushed commits in another checkout (note 1).
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
# Always default from the recorded reference-product revision. An existing
# disposable clone may sit on a generated test_* branch after a prior case;
# that HEAD is not a valid baseline selection.
def_product=$pin_commit
def_curbpack=$(git rev-parse HEAD)
def_date=$(date +%F)

ask() {
	_def=$3
	if [ -t 0 ]; then
		printf '%s [%s]: ' "$2" "$_def" >&2
		read -r _ans || _ans=
		eval "$1=\${_ans:-$_def}"
	else
		eval "$1=\$_def"
	fi
}

ask_yes() {
	_def=no
	printf '%s [%s]: ' "$1" "$_def" >&2
	read -r _ans || _ans=
	_ans=${_ans:-$_def}
	case $_ans in
	y | Y | yes | YES) return 0 ;;
	*) return 1 ;;
	esac
}

dirty=$(git status --porcelain | grep -vE '^\?\? (cases\.zip|\.DS_Store)$' || true)

if [ "$developer_mode" -eq 1 ]; then

    CURBPACK_COMMIT=$def_curbpack

    if [ -n "$dirty" ]; then
        CURBPACK_DIRTY=true
        CURBPACK_STATE="${CURBPACK_COMMIT}-dirty"
    else
        CURBPACK_DIRTY=false
        CURBPACK_STATE="$CURBPACK_COMMIT"
    fi

    REFERENCE_PRODUCT_COMMIT=$def_product
    AS_OF_DATE=$def_date

else

    ask CURBPACK_COMMIT "Curbpack commit" "$def_curbpack"
    ask REFERENCE_PRODUCT_COMMIT "Reference-product commit" "$def_product"
    ask AS_OF_DATE "As-of date" "$def_date"

    CURBPACK_COMMIT=$(git rev-parse --verify "${CURBPACK_COMMIT}^{commit}")

    if [ -n "$dirty" ]; then
        echo "error: Curbpack has local changes; a verification run needs a clean tree at $CURBPACK_COMMIT" >&2
        echo "Commit them, or: git stash push -m 'before verification run'" >&2
        printf '%s\n' "$dirty" >&2
        exit 2
    fi

    CURBPACK_DIRTY=false
    CURBPACK_STATE="$CURBPACK_COMMIT"

fi

CURBPACK_ROOT=$root
REFERENCE_PRODUCT_ROOT=$product

if [ -e "$tmp" ]; then
	if [ "$confirm_wipe" -eq 1 ]; then
		echo "deleting $tmp (CONFIRM_TMP_WIPE=1 / --yes)"
	elif [ -t 0 ]; then
		if [ -f "$out" ]; then
			prompt="tmp/verification-run.sh already exists. Replace it and recreate tmp?"
		else
			prompt="tmp already exists. Delete and recreate it?"
		fi
		if ! ask_yes "$prompt"; then
			echo "error: existing tmp was not replaced; stop" >&2
			exit 2
		fi
	else
		echo "error: $tmp exists; confirm a full wipe on a TTY, or CONFIRM_TMP_WIPE=1" >&2
		exit 2
	fi
	rm -rf "$tmp"
fi

mkdir -p "$tmp"

echo "cloning RI-SE/cyberready-test-product into tmp/cyberready-test-product"
git clone -q git@github.com:RI-SE/cyberready-test-product.git "$product"
if ! git -C "$product" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}" >/dev/null 2>&1; then
	git -C "$product" fetch -q origin
fi
if ! git -C "$product" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}" >/dev/null 2>&1; then
	echo "error: $REFERENCE_PRODUCT_COMMIT is not in tmp/cyberready-test-product after clone/fetch" >&2
	echo "note 1: origin does not see unpushed commits from another checkout; push the product, then retry" >&2
	exit 2
fi
REFERENCE_PRODUCT_COMMIT=$(git -C "$product" rev-parse --verify "${REFERENCE_PRODUCT_COMMIT}^{commit}")
git -C "$product" -c advice.detachedHead=false checkout --quiet "$REFERENCE_PRODUCT_COMMIT"

cp "$template" "$out"
python3 - "$out" "$CURBPACK_COMMIT" "$REFERENCE_PRODUCT_COMMIT" "$AS_OF_DATE" "$CURBPACK_ROOT" "$REFERENCE_PRODUCT_ROOT" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text()
keys = (
    "CURBPACK_COMMIT",
    "REFERENCE_PRODUCT_COMMIT",
    "AS_OF_DATE",
    "CURBPACK_ROOT",
    "REFERENCE_PRODUCT_ROOT",
)
for key, raw in zip(keys, sys.argv[2:]):
    needle = f'{key}=""'
    if needle not in text:
        raise SystemExit(f"missing {needle} in {path}")
    text = text.replace(needle, f"{key}={json.dumps(raw)}", 1)
path.write_text(text)
PY

if [ "$developer_mode" -eq 1 ]; then
	if [ -n "$dirty" ]; then
		CURBPACK_DIRTY=true
		CURBPACK_STATE="${CURBPACK_COMMIT}-dirty"
	else
		CURBPACK_DIRTY=false
		CURBPACK_STATE=$CURBPACK_COMMIT
	fi
	{
		printf '\n# Developer-mode run metadata\n'
		printf 'CURBPACK_DIRTY=%s\n' "$CURBPACK_DIRTY"
		printf 'CURBPACK_STATE=%s\n' "$CURBPACK_STATE"
		printf 'export CURBPACK_DIRTY CURBPACK_STATE\n'
	} >>"$out"
else
	if [ "$(git rev-parse HEAD)" != "$CURBPACK_COMMIT" ]; then
		echo "checking out Curbpack $CURBPACK_COMMIT"
		git -c advice.detachedHead=false checkout --quiet "$CURBPACK_COMMIT"
	fi
fi

make build

echo
echo "Verification run"
if [ "$developer_mode" -eq 1 ]; then
	run_mode=developer
else
	run_mode=verification
fi
printf '%-28s %s\n' \
	"Mode:" "$run_mode" \
	"Curbpack root:" "$CURBPACK_ROOT" \
	"Curbpack commit:" "$CURBPACK_COMMIT" \
	"Curbpack HEAD:" "$(git rev-parse HEAD)" \
	"Curbpack binary:" "$root/tmp/curbpack" \
	"Reference-product root:" "$REFERENCE_PRODUCT_ROOT" \
	"Reference-product commit:" "$REFERENCE_PRODUCT_COMMIT" \
	"Reference-product HEAD:" "$(git -C "$product" rev-parse HEAD)" \
	"As-of date:" "$AS_OF_DATE" \
	"Filled file:" "$out"
echo
echo "For each terminal used for running the test cases, please run"
echo
printf '\033[1m%s\033[0m\n' "source tmp/verification-run.sh"
echo
