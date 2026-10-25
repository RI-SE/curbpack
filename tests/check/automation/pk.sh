#!/bin/sh

# PK-001 has no execution procedure. The runner treats it as a reference to EV-001.

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)

pk_002_a() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-002-A SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-002-A SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-002-A SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_002_a_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_002_a_setup_status=$?
	printf '%s\n' "$pk_002_a_setup_output"
	if [ "$pk_002_a_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_002_a_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pk_002_a_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pk_002_a_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pk_002_a_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PK-002-A SETUP 3"
		return 1
	fi
	# SETUP 4
	pk_002_a_status_output=$(git status --porcelain)
	if [ -n "$pk_002_a_status_output" ]; then
		printf '%s\n' "$pk_002_a_status_output"
		echo "PK-002-A SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_002_a_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-13)
	pk_002_a_mutate_status=$?
	printf '%s\n' "$pk_002_a_mutate_output"
	if [ "$pk_002_a_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$pk_002_a_mutate_output" | grep -Fxq "mutate_pack.sh: PF-13" ||
		[ ! -f "$CURBPACK_PACKS_DIR/house-policy/pack.json" ] ||
		[ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-002-A SETUP 5"
		return 1
	fi
	# SETUP 6
	pk_002_a_ver=$(grep -F '"version": "0.1.0"' "$CURBPACK_PACKS_DIR/house-policy/pack.json")
	printf '%s\n' "$pk_002_a_ver"
	if [ -z "$pk_002_a_ver" ] || printf '%s\n' "$pk_002_a_ver" | grep -q ',[[:space:]]*$'; then
		echo "PK-002-A SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/pk-002-a"
	curbpack check --json --as-of "$AS_OF_DATE" >"$CURBPACK_ROOT/tmp/pk-002-a/stdout" 2>"$CURBPACK_ROOT/tmp/pk-002-a/stderr"
	pk_002_a_status=$?
	cat "$CURBPACK_ROOT/tmp/pk-002-a/stdout"
	cat "$CURBPACK_ROOT/tmp/pk-002-a/stderr" >&2
	pk_002_a_stdout=$(cat "$CURBPACK_ROOT/tmp/pk-002-a/stdout")
	pk_002_a_stderr=$(cat "$CURBPACK_ROOT/tmp/pk-002-a/stderr")
	if [ -n "$pk_002_a_stdout" ] ||
		! printf '%s\n' "$pk_002_a_stderr" | grep -qi 'json' ||
		! printf '%s\n' "$pk_002_a_stderr" | grep -Fq 'house-policy' ||
		printf '%s\n' "$pk_002_a_stderr" | grep -Eqi 'missing path|missing-file|no such file'; then
		echo "PK-002-A TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_002_a_status"
	if [ "$pk_002_a_status" -eq 0 ]; then
		echo "PK-002-A TEST STEPS 2"
		return 1
	fi
}

pk_002_b() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-002-B SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-002-B SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-002-B SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_002_b_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_002_b_setup_status=$?
	printf '%s\n' "$pk_002_b_setup_output"
	if [ "$pk_002_b_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_002_b_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pk_002_b_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pk_002_b_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pk_002_b_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PK-002-B SETUP 3"
		return 1
	fi
	# SETUP 4
	pk_002_b_status_output=$(git status --porcelain)
	if [ -n "$pk_002_b_status_output" ]; then
		printf '%s\n' "$pk_002_b_status_output"
		echo "PK-002-B SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_002_b_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-14)
	pk_002_b_mutate_status=$?
	printf '%s\n' "$pk_002_b_mutate_output"
	if [ "$pk_002_b_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$pk_002_b_mutate_output" | grep -Fxq "mutate_pack.sh: PF-14" ||
		[ ! -f "$CURBPACK_PACKS_DIR/house-policy/pack.json" ] ||
		[ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-002-B SETUP 5"
		return 1
	fi
	# SETUP 6
	pk_002_b_bytes=$(wc -c <"$CURBPACK_PACKS_DIR/house-policy/pack.json")
	echo "$pk_002_b_bytes"
	if [ "$pk_002_b_bytes" -ne 120 ]; then
		echo "PK-002-B SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/pk-002-b"
	curbpack check --json --as-of "$AS_OF_DATE" >"$CURBPACK_ROOT/tmp/pk-002-b/stdout" 2>"$CURBPACK_ROOT/tmp/pk-002-b/stderr"
	pk_002_b_status=$?
	cat "$CURBPACK_ROOT/tmp/pk-002-b/stdout"
	cat "$CURBPACK_ROOT/tmp/pk-002-b/stderr" >&2
	pk_002_b_stdout=$(cat "$CURBPACK_ROOT/tmp/pk-002-b/stdout")
	pk_002_b_stderr=$(cat "$CURBPACK_ROOT/tmp/pk-002-b/stderr")
	if [ -n "$pk_002_b_stdout" ] ||
		! printf '%s\n' "$pk_002_b_stderr" | grep -qi 'json' ||
		! printf '%s\n' "$pk_002_b_stderr" | grep -Fq 'house-policy' ||
		printf '%s\n' "$pk_002_b_stderr" | grep -Eqi 'missing path|missing-file|no such file'; then
		echo "PK-002-B TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_002_b_status"
	if [ "$pk_002_b_status" -eq 0 ]; then
		echo "PK-002-B TEST STEPS 2"
		return 1
	fi
}

pk_003_not_pf01_pass() {
	pk_003_out=$1
	pk_003_st=$2
	if [ "$pk_003_st" -eq 0 ] &&
		printf '%s\n' "$pk_003_out" | jq -e '
			.failures == null and
			.pack_id == "house-policy,medtech-iec62304" and
			.readiness_score == 100 and
			.outcome == "pass" and
			.evaluated_rules == 15
		' >/dev/null 2>&1; then
		return 1
	fi
	return 0
}

pk_003_a() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-003-A SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-003-A SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-003-A SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_003_a_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_003_a_setup_status=$?
	printf '%s\n' "$pk_003_a_setup_output"
	if [ "$pk_003_a_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_003_a_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pk_003_a_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pk_003_a_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pk_003_a_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PK-003-A SETUP 3"
		return 1
	fi
	# SETUP 4
	pk_003_a_status_output=$(git status --porcelain)
	if [ -n "$pk_003_a_status_output" ]; then
		printf '%s\n' "$pk_003_a_status_output"
		echo "PK-003-A SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_003_a_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-15)
	pk_003_a_mutate_status=$?
	printf '%s\n' "$pk_003_a_mutate_output"
	if [ "$pk_003_a_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$pk_003_a_mutate_output" | grep -Fxq "mutate_pack.sh: PF-15"; then
		echo "PK-003-A SETUP 5"
		return 1
	fi
	# SETUP 6
	pk_003_a_count=$(grep -c '"id": "HOUSE-SECURITY-MD"' "$CURBPACK_PACKS_DIR/house-policy/pack.json")
	echo "$pk_003_a_count"
	if [ "$pk_003_a_count" -ne 2 ]; then
		echo "PK-003-A SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	pk_003_a_check_output=$(curbpack check --json --as-of "$AS_OF_DATE" 2>&1)
	pk_003_a_check_status=$?
	printf '%s\n' "$pk_003_a_check_output"
	if ! pk_003_not_pf01_pass "$pk_003_a_check_output" "$pk_003_a_check_status"; then
		echo "PK-003-A TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_003_a_check_status"
	if [ "$pk_003_a_check_status" -eq 0 ] &&
		! pk_003_not_pf01_pass "$pk_003_a_check_output" "$pk_003_a_check_status"; then
		echo "PK-003-A TEST STEPS 2"
		return 1
	fi
}

pk_003_b() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-003-B SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-003-B SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-003-B SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_003_b_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_003_b_setup_status=$?
	printf '%s\n' "$pk_003_b_setup_output"
	if [ "$pk_003_b_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_003_b_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "PK-003-B SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "PK-003-B SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_003_b_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-16)
	printf '%s\n' "$pk_003_b_mutate_output"
	if ! printf '%s\n' "$pk_003_b_mutate_output" | grep -Fxq "mutate_pack.sh: PF-16"; then
		echo "PK-003-B SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -n 'docs/pk003-absent.md' "$CURBPACK_PACKS_DIR/house-policy/pack.json"; then
		echo "PK-003-B SETUP 6"
		return 1
	fi
	pk_003_b_first=$(awk '/"id": "HOUSE-SECURITY-MD"/{p=1} p && /"path"/{print; exit}' "$CURBPACK_PACKS_DIR/house-policy/pack.json")
	printf '%s\n' "$pk_003_b_first"
	if ! printf '%s\n' "$pk_003_b_first" | grep -Fq 'SECURITY.md' ||
		printf '%s\n' "$pk_003_b_first" | grep -Fq 'pk003-absent'; then
		echo "PK-003-B SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	pk_003_b_check_output=$(curbpack check --json --as-of "$AS_OF_DATE" 2>&1)
	pk_003_b_check_status=$?
	printf '%s\n' "$pk_003_b_check_output"
	if ! pk_003_not_pf01_pass "$pk_003_b_check_output" "$pk_003_b_check_status"; then
		echo "PK-003-B TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_003_b_check_status"
}

pk_003_c() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-003-C SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-003-C SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-003-C SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_003_c_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_003_c_setup_status=$?
	printf '%s\n' "$pk_003_c_setup_output"
	if [ "$pk_003_c_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_003_c_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "PK-003-C SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "PK-003-C SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_003_c_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-17)
	printf '%s\n' "$pk_003_c_mutate_output"
	if ! printf '%s\n' "$pk_003_c_mutate_output" | grep -Fxq "mutate_pack.sh: PF-17"; then
		echo "PK-003-C SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -n 'docs/pk003-absent.md' "$CURBPACK_PACKS_DIR/house-policy/pack.json"; then
		echo "PK-003-C SETUP 6"
		return 1
	fi
	pk_003_c_first=$(awk '/"id": "HOUSE-SECURITY-MD"/{p=1} p && /"path"/{print; exit}' "$CURBPACK_PACKS_DIR/house-policy/pack.json")
	printf '%s\n' "$pk_003_c_first"
	if ! printf '%s\n' "$pk_003_c_first" | grep -Fq 'docs/pk003-absent.md'; then
		echo "PK-003-C SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	pk_003_c_check_output=$(curbpack check --json --as-of "$AS_OF_DATE" 2>&1)
	pk_003_c_check_status=$?
	printf '%s\n' "$pk_003_c_check_output"
	if ! pk_003_not_pf01_pass "$pk_003_c_check_output" "$pk_003_c_check_status"; then
		echo "PK-003-C TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_003_c_check_status"
}

pk_003_d() {
	echo "PK-003-D: Not specified yet. Do not run this variant. No version-selection syntax exists."
	return 2
}

pk_004() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-004 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-004 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-004 SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_004_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_004_setup_status=$?
	printf '%s\n' "$pk_004_setup_output"
	if [ "$pk_004_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_004_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pk_004_setup_output" | grep -Fq "## Classification Rationale"; then
		echo "PK-004 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "PK-004 SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_004_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-03)
	pk_004_mutate_status=$?
	printf '%s\n' "$pk_004_mutate_output"
	if [ "$pk_004_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$pk_004_mutate_output" | grep -Fxq "mutate_pack.sh: PF-03" ||
		[ ! -f "$CURBPACK_PACKS_DIR/unknown-check/pack.json" ]; then
		echo "PK-004 SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -F '"check": "llm_judge"' "$CURBPACK_PACKS_DIR/unknown-check/pack.json"; then
		echo "PK-004 SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/pk-004"
	curbpack check --packs unknown-check --json --as-of "$AS_OF_DATE" >"$CURBPACK_ROOT/tmp/pk-004/stdout" 2>"$CURBPACK_ROOT/tmp/pk-004/stderr"
	pk_004_status=$?
	cat "$CURBPACK_ROOT/tmp/pk-004/stdout"
	cat "$CURBPACK_ROOT/tmp/pk-004/stderr" >&2
	pk_004_stdout=$(cat "$CURBPACK_ROOT/tmp/pk-004/stdout")
	pk_004_stderr=$(cat "$CURBPACK_ROOT/tmp/pk-004/stderr")
	if [ -n "$pk_004_stdout" ] ||
		! printf '%s\n' "$pk_004_stderr" | grep -Fq 'unsupported check' ||
		! printf '%s\n' "$pk_004_stderr" | grep -Fq 'llm_judge'; then
		echo "PK-004 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_004_status"
	if [ "$pk_004_status" -ne 1 ]; then
		echo "PK-004 TEST STEPS 2"
		return 1
	fi
}

pk_005() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PK-005 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PK-005 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PK-005 SETUP 2"
		return 1
	fi
	# SETUP 3
	pk_005_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pk_005_setup_status=$?
	printf '%s\n' "$pk_005_setup_output"
	if [ "$pk_005_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pk_005_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "PK-005 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "PK-005 SETUP 4"
		return 1
	fi
	# SETUP 5
	pk_005_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-04)
	pk_005_mutate_status=$?
	printf '%s\n' "$pk_005_mutate_output"
	if [ "$pk_005_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$pk_005_mutate_output" | grep -Fxq "mutate_pack.sh: PF-04" ||
		[ ! -f "$CURBPACK_PACKS_DIR/bad-regex/pack.json" ]; then
		echo "PK-005 SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -F '(?P<unterminated' "$CURBPACK_PACKS_DIR/bad-regex/pack.json"; then
		echo "PK-005 SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/pk-005"
	curbpack check --packs bad-regex --json --as-of "$AS_OF_DATE" >"$CURBPACK_ROOT/tmp/pk-005/stdout" 2>"$CURBPACK_ROOT/tmp/pk-005/stderr"
	pk_005_status=$?
	cat "$CURBPACK_ROOT/tmp/pk-005/stdout"
	cat "$CURBPACK_ROOT/tmp/pk-005/stderr" >&2
	pk_005_stdout=$(cat "$CURBPACK_ROOT/tmp/pk-005/stdout")
	pk_005_stderr=$(cat "$CURBPACK_ROOT/tmp/pk-005/stderr")
	if [ -n "$pk_005_stdout" ] ||
		! printf '%s\n' "$pk_005_stderr" | grep -Fq 'invalid pattern' ||
		! printf '%s\n' "$pk_005_stderr" | grep -Fq 'invalid named capture'; then
		echo "PK-005 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pk_005_status"
	if [ "$pk_005_status" -ne 1 ]; then
		echo "PK-005 TEST STEPS 2"
		return 1
	fi
}
