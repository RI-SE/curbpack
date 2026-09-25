#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
fs_001() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "FS-001 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "FS-001 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "FS-001 SETUP 2"
		return 1
	fi
	# SETUP 3
	fs_001_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	fs_001_setup_status=$?
	printf '%s\n' "$fs_001_setup_output"
	if [ "$fs_001_setup_status" -ne 0 ] ||
		! printf '%s\n' "$fs_001_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$fs_001_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$fs_001_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$fs_001_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "FS-001 SETUP 3"
		return 1
	fi
	# SETUP 4
	fs_001_status_output=$(git status --porcelain)
	if [ -n "$fs_001_status_output" ]; then
		printf '%s\n' "$fs_001_status_output"
		echo "FS-001 SETUP 4"
		return 1
	fi
	# SETUP 5
	fs_001_packs_dir=$CURBPACK_PACKS_DIR
	fs_001_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-05)
	fs_001_mutate_status=$?
	printf '%s\n' "$fs_001_mutate_output"
	if [ "$fs_001_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$fs_001_mutate_output" | grep -Fxq "mutate_pack.sh: PF-05" ||
		[ ! -f "$CURBPACK_PACKS_DIR/path-traversal/pack.json" ] ||
		[ "$CURBPACK_PACKS_DIR" != "$fs_001_packs_dir" ] ||
		[ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "FS-001 SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -F '../../../etc/passwd' "$CURBPACK_PACKS_DIR/path-traversal/pack.json"; then
		echo "FS-001 SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/fs-001"
	curbpack check --packs path-traversal >"$CURBPACK_ROOT/tmp/fs-001/stdout" 2>"$CURBPACK_ROOT/tmp/fs-001/stderr"
	fs_001_status=$?
	cat "$CURBPACK_ROOT/tmp/fs-001/stdout"
	cat "$CURBPACK_ROOT/tmp/fs-001/stderr" >&2
	fs_001_stderr=$(cat "$CURBPACK_ROOT/tmp/fs-001/stderr")
	if [ "$fs_001_status" -eq 0 ] ||
		! printf '%s\n' "$fs_001_stderr" | grep -Fq 'ADV-TRAVERSAL' ||
		! printf '%s\n' "$fs_001_stderr" | grep -Fq 'path traversal refused' ||
		[ "$fs_001_stderr" != 'pack "path-traversal" rule "ADV-TRAVERSAL": path traversal refused' ]; then
		echo "FS-001 TEST STEPS 1"
		return 1
	fi
}

fs_002() {
	echo "FS-002: Not specified yet. Do not run this case."
	return 2
}

fs_003() {
	echo "FS-003: Not specified yet. Do not run this case."
	return 2
}

fs_004() {
	echo "FS-004: Not specified yet. Do not run this case."
	return 2
}

fs_005() {
	echo "FS-005: Not specified yet. Do not run this case."
	return 2
}

fs_006() {
	echo "FS-006: Not specified yet. Do not run this case."
	return 2
}

fs_007() {
	echo "FS-007: Not specified yet. Do not run this case."
	return 2
}
