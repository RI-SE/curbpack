#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)

ev_001() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-001 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-001 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-001 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_001_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_001_setup_status=$?
	printf '%s\n' "$ev_001_setup_output"
	if [ "$ev_001_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_001_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$ev_001_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$ev_001_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$ev_001_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "EV-001 SETUP 3"
		return 1
	fi
	# SETUP 4
	ev_001_status_output=$(git status --porcelain)
	if [ -n "$ev_001_status_output" ]; then
		printf '%s\n' "$ev_001_status_output"
		echo "EV-001 SETUP 4"
		return 1
	fi

	# TEST STEPS 1
	ev_001_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	ev_001_check_status=$?
	printf '%s\n' "$ev_001_check_output"
	if ! printf '%s\n' "$ev_001_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "EV-001 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_001_check_status"
	if [ "$ev_001_check_status" -ne 0 ]; then
		echo "EV-001 TEST STEPS 2"
		return 1
	fi
}

ev_002() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-002 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-002 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-002 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_002_setup_output=$(./external_test/curbpack/setup.sh R2 --commit)
	ev_002_setup_status=$?
	printf '%s\n' "$ev_002_setup_output"
	if [ "$ev_002_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_002_setup_output" | grep -Fq "R2 — missing required file" ||
		! printf '%s\n' "$ev_002_setup_output" | grep -Fq "SECURITY.md absent, not empty"; then
		echo "EV-002 SETUP 3"
		return 1
	fi
	case $(git branch --show-current) in
		test_*) ;;
		*)
			echo "EV-002 SETUP 3"
			return 1
			;;
	esac
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-002 SETUP 4"
		return 1
	fi
	# SETUP 5
	if ls SECURITY.md; then
		echo "EV-002 SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	ev_002_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	ev_002_check_status=$?
	printf '%s\n' "$ev_002_check_output"
	if ! printf '%s\n' "$ev_002_check_output" | jq -e '
		.failures == [{
			"gate_id": "HOUSE-SECURITY-MD",
			"severity": "high",
			"type": "POLICY_VIOLATION",
			"sanitized_description": "SECURITY.md missing, too short, or lacking required header.",
			"ast_coordinates": {
				"target_file": "SECURITY.md",
				"node_path": "",
				"target_symbol": "",
				"fallback_lines": ""
			},
			"remediation": {
				"action_required": "Add SECURITY.md with vulnerability reporting and response expectations.",
				"expected_state": "SECURITY.md present with Security header and substantive content."
			}
		}] and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 80 and
		.outcome == "findings" and
		.failed_rules == 1 and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "EV-002 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_002_check_status"
	if [ "$ev_002_check_status" -ne 1 ]; then
		echo "EV-002 TEST STEPS 2"
		return 1
	fi
}

ev_003() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-003 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-003 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-003 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_003_setup_output=$(./external_test/curbpack/setup.sh R3 --commit)
	ev_003_setup_status=$?
	printf '%s\n' "$ev_003_setup_output"
	if [ "$ev_003_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_003_setup_output" | grep -Fq "R3 — missing required section"; then
		echo "EV-003 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-003 SETUP 4"
		return 1
	fi
	# SETUP 5
	if [ ! -f docs/medtech/software_safety_class.md ]; then
		echo "EV-003 SETUP 5"
		return 1
	fi
	# SETUP 6
	if grep -F "## Classification Rationale" docs/medtech/software_safety_class.md; then
		echo "EV-003 SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	ev_003_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	ev_003_check_status=$?
	printf '%s\n' "$ev_003_check_output"
	if ! printf '%s\n' "$ev_003_check_output" | jq -e '
		.failures == [{
			"gate_id": "MD-SW-CLASS",
			"severity": "high",
			"type": "POLICY_VIOLATION",
			"sanitized_description": "IEC 62304 software safety classification rationale missing. (missing header: ## Classification Rationale)",
			"ast_coordinates": {
				"target_file": "docs/medtech/software_safety_class.md",
				"node_path": "",
				"target_symbol": "",
				"fallback_lines": ""
			},
			"remediation": {
				"action_required": "Document Class A/B/C rationale in docs/medtech/software_safety_class.md.",
				"expected_state": "Safety class declared with rationale."
			}
		}] and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 80 and
		.outcome == "findings" and
		.failed_rules == 1 and
		.evaluated_rules == 15 and
		.conformity_claim == "none" and
		([.failures[].gate_id] | index("HOUSE-SECURITY-MD") | not)
	' >/dev/null; then
		echo "EV-003 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_003_check_status"
	if [ "$ev_003_check_status" -ne 1 ]; then
		echo "EV-003 TEST STEPS 2"
		return 1
	fi
}

ev_004() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-004 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-004 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-004 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_004_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_004_setup_status=$?
	printf '%s\n' "$ev_004_setup_output"
	if [ "$ev_004_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_004_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-004 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-004 SETUP 4"
		return 1
	fi
	# SETUP 5
	if [ ! -f SECURITY.md ]; then
		echo "EV-004 SETUP 5"
		return 1
	fi
	# SETUP 6
	chmod 000 SECURITY.md
	ev_004_mode=$(ls -l SECURITY.md)
	printf '%s\n' "$ev_004_mode"
	if [ ! -f SECURITY.md ] || ! printf '%s\n' "$ev_004_mode" | grep -q '^----------'; then
		echo "EV-004 SETUP 6"
		return 1
	fi
	# SETUP 7
	if test -r SECURITY.md; then
		echo "EV-004 SETUP 7: this machine can still read SECURITY.md. The case cannot be run."
		return 1
	fi
	echo 1
	# SETUP 8
	ev_004_git=$(git status --porcelain)
	printf '%s\n' "$ev_004_git"
	if ! printf '%s\n' "$ev_004_git" | grep -Fq 'SECURITY.md'; then
		echo "EV-004 SETUP 8"
		return 1
	fi

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/ev-004"
	curbpack check --json --as-of "$AS_OF_DATE" >"$CURBPACK_ROOT/tmp/ev-004/stdout" 2>"$CURBPACK_ROOT/tmp/ev-004/stderr"
	ev_004_status=$?
	cat "$CURBPACK_ROOT/tmp/ev-004/stdout"
	cat "$CURBPACK_ROOT/tmp/ev-004/stderr" >&2
	ev_004_stdout=$(cat "$CURBPACK_ROOT/tmp/ev-004/stdout")
	ev_004_stderr=$(cat "$CURBPACK_ROOT/tmp/ev-004/stderr")
	if [ -n "$ev_004_stdout" ] ||
		! printf '%s\n' "$ev_004_stderr" | grep -Fq 'read input SECURITY.md' ||
		! printf '%s\n' "$ev_004_stderr" | grep -Fq 'permission denied' ||
		! printf '%s\n' "$ev_004_stderr" | grep -Fq "$REFERENCE_PRODUCT_ROOT/SECURITY.md"; then
		echo "EV-004 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_004_status"
	if [ "$ev_004_status" -ne 1 ]; then
		echo "EV-004 TEST STEPS 2"
		return 1
	fi
}

ev_005() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-005 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-005 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-005 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_005_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_005_setup_status=$?
	printf '%s\n' "$ev_005_setup_output"
	if [ "$ev_005_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_005_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-005 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-005 SETUP 4"
		return 1
	fi
	# SETUP 5
	printf '%s\n' '# EV-005 skip stimulus' 'This file is not a pack target.' > docs/ev005-skip.md
	if [ ! -f docs/ev005-skip.md ]; then
		echo "EV-005 SETUP 5"
		return 1
	fi
	# SETUP 6
	ev_005_git=$(git status --porcelain)
	printf '%s\n' "$ev_005_git"
	if ! printf '%s\n' "$ev_005_git" | grep -Fq '?? docs/ev005-skip.md'; then
		echo "EV-005 SETUP 6"
		return 1
	fi

	# TEST STEPS 1
	ev_005_check_output=$(curbpack check --diff --json --as-of "$AS_OF_DATE")
	ev_005_check_status=$?
	printf '%s\n' "$ev_005_check_output"
	if ! printf '%s\n' "$ev_005_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "incomplete" and
		.skipped_rules == 1 and
		.evaluated_rules == 14 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "EV-005 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_005_check_status"
	if [ "$ev_005_check_status" -ne 1 ]; then
		echo "EV-005 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	ev_005_skip=$(grep -A2 skipped_rule_ids .github/curbpack/cache/latest_evaluation.json)
	printf '%s\n' "$ev_005_skip"
	if ! printf '%s\n' "$ev_005_skip" | grep -Fq 'HOUSE-SECRET-PATHS'; then
		echo "EV-005 TEST STEPS 3"
		return 1
	fi
	# TEST STEPS 4
	ev_005_report=$(cat .github/curbpack/cache/latest_action_report.md)
	printf '%s\n' "$ev_005_report"
	if ! printf '%s\n' "$ev_005_report" | grep -Fq 'Outcome: incomplete' ||
		! printf '%s\n' "$ev_005_report" | grep -Fq 'Failed / evaluated / skipped: 0 / 14 / 1' ||
		! printf '%s\n' "$ev_005_report" | grep -Fq 'Evaluation incomplete: some rules were skipped'; then
		echo "EV-005 TEST STEPS 4"
		return 1
	fi
}

ev_006() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-006 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-006 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-006 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_006_setup_output=$(./external_test/curbpack/setup.sh R4 --commit)
	ev_006_setup_status=$?
	printf '%s\n' "$ev_006_setup_output"
	if [ "$ev_006_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_006_setup_output" | grep -Fq "R4 — token-only house-policy tree"; then
		echo "EV-006 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-006 SETUP 4"
		return 1
	fi
	# SETUP 5
	if ! grep -F '"name": "acme-widget"' package.json; then
		echo "EV-006 SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -Fx acme-widget SECURITY.md; then
		echo "EV-006 SETUP 6"
		return 1
	fi
	# SETUP 7
	if test -e src/app.py; then
		echo "EV-006 SETUP 7"
		return 1
	fi
	echo 0

	# TEST STEPS 1
	ev_006_check_output=$(curbpack check --packs house-policy --json --as-of "$AS_OF_DATE")
	ev_006_check_status=$?
	printf '%s\n' "$ev_006_check_output"
	if ! printf '%s\n' "$ev_006_check_output" | jq -e '
		.failures[0].gate_id == "HOUSE-ANTI-PLACEHOLDER" and
		.pack_id == "house-policy" and
		.readiness_score == 80 and
		.outcome == "findings" and
		.failed_rules == 1 and
		.evaluated_rules == 5 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "EV-006 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_006_check_status"
	if [ "$ev_006_check_status" -ne 1 ]; then
		echo "EV-006 TEST STEPS 2"
		return 1
	fi
}

ev_007_a() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-A SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-A SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-A SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_a_setup_output=$(./external_test/curbpack/setup.sh R2 --commit)
	ev_007_a_setup_status=$?
	printf '%s\n' "$ev_007_a_setup_output"
	if [ "$ev_007_a_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_a_setup_output" | grep -Fq "R2 — missing required file"; then
		echo "EV-007-A SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-A SETUP 4"
		return 1
	fi
	# SETUP 5
	if ls SECURITY.md; then
		echo "EV-007-A SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	ev_007_a_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	ev_007_a_check_status=$?
	printf '%s\n' "$ev_007_a_check_output"
	if ! printf '%s\n' "$ev_007_a_check_output" | jq -e '
		.outcome == "findings" and
		.failed_rules == 1 and
		.evaluated_rules == 15 and
		.conformity_claim == "none" and
		.pack_id == "house-policy,medtech-iec62304" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "HOUSE-SECURITY-MD"
	' >/dev/null; then
		echo "EV-007-A TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_a_check_status"
	if [ "$ev_007_a_check_status" -ne 1 ]; then
		echo "EV-007-A TEST STEPS 2"
		return 1
	fi
}

ev_007_b() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-B SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-B SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-B SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_b_setup_output=$(./external_test/curbpack/setup.sh R3 --commit)
	ev_007_b_setup_status=$?
	printf '%s\n' "$ev_007_b_setup_output"
	if [ "$ev_007_b_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_b_setup_output" | grep -Fq "R3 — missing required section"; then
		echo "EV-007-B SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-B SETUP 4"
		return 1
	fi
	# SETUP 5
	if grep -F "## Classification Rationale" docs/medtech/software_safety_class.md; then
		echo "EV-007-B SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	ev_007_b_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	ev_007_b_check_status=$?
	printf '%s\n' "$ev_007_b_check_output"
	if ! printf '%s\n' "$ev_007_b_check_output" | jq -e '
		.outcome == "findings" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "MD-SW-CLASS"
	' >/dev/null; then
		echo "EV-007-B TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_b_check_status"
	if [ "$ev_007_b_check_status" -ne 1 ]; then
		echo "EV-007-B TEST STEPS 2"
		return 1
	fi
}

ev_007_c() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-C SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-C SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-C SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_c_setup_output=$(./external_test/curbpack/setup.sh R4 --commit)
	ev_007_c_setup_status=$?
	printf '%s\n' "$ev_007_c_setup_output"
	if [ "$ev_007_c_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_c_setup_output" | grep -Fq "R4 — token-only house-policy tree"; then
		echo "EV-007-C SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-C SETUP 4"
		return 1
	fi

	# TEST STEPS 1
	ev_007_c_check_output=$(curbpack check --packs house-policy --json --as-of "$AS_OF_DATE")
	ev_007_c_check_status=$?
	printf '%s\n' "$ev_007_c_check_output"
	if ! printf '%s\n' "$ev_007_c_check_output" | jq -e '
		.outcome == "findings" and
		.pack_id == "house-policy" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "HOUSE-ANTI-PLACEHOLDER"
	' >/dev/null; then
		echo "EV-007-C TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_c_check_status"
	if [ "$ev_007_c_check_status" -ne 1 ]; then
		echo "EV-007-C TEST STEPS 2"
		return 1
	fi
}

ev_007_d() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-D SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-D SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-D SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_d_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_007_d_setup_status=$?
	printf '%s\n' "$ev_007_d_setup_output"
	if [ "$ev_007_d_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_d_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-007-D SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-D SETUP 4"
		return 1
	fi
	# SETUP 5
	python3 -c 'import json; p="package.json"; d=json.load(open(p)); d["dependencies"]={"axios":"1.6.0"}; json.dump(d, open(p,"w"), indent=2); open(p,"a").write("\n")'
	if ! grep -F '"axios": "1.6.0"' package.json || [ -z "$(git status --porcelain)" ]; then
		echo "EV-007-D SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	ev_007_d_check_output=$(curbpack check --packs house-policy --json --as-of "$AS_OF_DATE")
	ev_007_d_check_status=$?
	printf '%s\n' "$ev_007_d_check_output"
	if ! printf '%s\n' "$ev_007_d_check_output" | jq -e '
		.outcome == "findings" and
		.pack_id == "house-policy" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "HOUSE-DEP-AXIOS-PIN"
	' >/dev/null; then
		echo "EV-007-D TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_d_check_status"
	if [ "$ev_007_d_check_status" -ne 1 ]; then
		echo "EV-007-D TEST STEPS 2"
		return 1
	fi
}

ev_007_e() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-E SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-E SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-E SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_e_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_007_e_setup_status=$?
	printf '%s\n' "$ev_007_e_setup_output"
	if [ "$ev_007_e_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_e_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-007-E SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-E SETUP 4"
		return 1
	fi
	# SETUP 5
	python3 -c 'import json; p="package.json"; d=json.load(open(p)); d["dependencies"]={"axios":"1.6.0"}; json.dump(d, open(p,"w"), indent=2); open(p,"a").write("\n")'
	if ! grep -F '"axios": "1.6.0"' package.json || [ -z "$(git status --porcelain)" ]; then
		echo "EV-007-E SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	ev_007_e_check_output=$(curbpack check --packs cra-baseline --json --as-of "$AS_OF_DATE")
	ev_007_e_check_status=$?
	printf '%s\n' "$ev_007_e_check_output"
	if ! printf '%s\n' "$ev_007_e_check_output" | jq -e '
		.outcome == "findings" and
		.pack_id == "cra-baseline" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "CRA-DEP-AXIOS-PIN"
	' >/dev/null; then
		echo "EV-007-E TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_e_check_status"
	if [ "$ev_007_e_check_status" -ne 1 ]; then
		echo "EV-007-E TEST STEPS 2"
		return 1
	fi
}

ev_007_f() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-F SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-F SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-F SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_f_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_007_f_setup_status=$?
	printf '%s\n' "$ev_007_f_setup_output"
	if [ "$ev_007_f_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_f_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-007-F SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-F SETUP 4"
		return 1
	fi
	# SETUP 5
	printf '%s\n' '' '-----BEGIN RSA PRIVATE KEY-----' 'fixture-only' '-----END RSA PRIVATE KEY-----' >> SECURITY.md
	if ! grep -F -- '-----BEGIN RSA PRIVATE KEY-----' SECURITY.md ||
		! git status --porcelain | grep -Fq 'SECURITY.md'; then
		echo "EV-007-F SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	ev_007_f_check_output=$(curbpack check --packs house-policy --json --as-of "$AS_OF_DATE")
	ev_007_f_check_status=$?
	printf '%s\n' "$ev_007_f_check_output"
	if ! printf '%s\n' "$ev_007_f_check_output" | jq -e '
		.outcome == "findings" and
		.pack_id == "house-policy" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "HOUSE-SECRET-PATHS"
	' >/dev/null; then
		echo "EV-007-F TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_f_check_status"
	if [ "$ev_007_f_check_status" -ne 1 ]; then
		echo "EV-007-F TEST STEPS 2"
		return 1
	fi
}

ev_007_g() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-G SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-G SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-G SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_g_setup_output=$(./external_test/curbpack/setup.sh R6 --commit)
	ev_007_g_setup_status=$?
	printf '%s\n' "$ev_007_g_setup_output"
	if [ "$ev_007_g_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_g_setup_output" | grep -Fq "R6 — stale fresh/owned fixture docs"; then
		echo "EV-007-G SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-G SETUP 4"
		return 1
	fi
	# SETUP 5
	if ! test -f docs/review-log.md || ! test -f docs/owned-policy.md; then
		echo "EV-007-G SETUP 5"
		return 1
	fi
	echo 0
	# SETUP 6
	ev_007_g_log=$(git log -1 --format='%ae %aI' -- docs/review-log.md)
	printf '%s\n' "$ev_007_g_log"
	if ! printf '%s\n' "$ev_007_g_log" | grep -q '^owner@example.com 2022-01-01T00:00:00'; then
		echo "EV-007-G SETUP 6"
		return 1
	fi
	# SETUP 7
	ev_007_g_packs=$CURBPACK_PACKS_DIR
	ev_007_g_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-07)
	printf '%s\n' "$ev_007_g_mutate_output"
	if ! printf '%s\n' "$ev_007_g_mutate_output" | grep -Fxq "mutate_pack.sh: PF-07" ||
		[ "$CURBPACK_PACKS_DIR" != "$ev_007_g_packs" ]; then
		echo "EV-007-G SETUP 7"
		return 1
	fi

	# TEST STEPS 1
	ev_007_g_check_output=$(curbpack check --packs fresh-owned-test --json --as-of "$AS_OF_DATE")
	ev_007_g_check_status=$?
	printf '%s\n' "$ev_007_g_check_output"
	if ! printf '%s\n' "$ev_007_g_check_output" | jq -e '
		.outcome == "findings" and
		.pack_id == "fresh-owned-test" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "FIX-FRESH-REVIEW"
	' >/dev/null; then
		echo "EV-007-G TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_g_check_status"
	if [ "$ev_007_g_check_status" -ne 1 ]; then
		echo "EV-007-G TEST STEPS 2"
		return 1
	fi
}

ev_007_h() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-007-H SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-007-H SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-H SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_007_h_setup_output=$(./external_test/curbpack/setup.sh R7 --commit)
	ev_007_h_setup_status=$?
	printf '%s\n' "$ev_007_h_setup_output"
	if [ "$ev_007_h_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_h_setup_output" | grep -Fq "R7 — wrong-author fresh/owned fixture docs"; then
		echo "EV-007-H SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-H SETUP 4"
		return 1
	fi
	# SETUP 5
	if ! test -f docs/review-log.md || ! test -f docs/owned-policy.md; then
		echo "EV-007-H SETUP 5"
		return 1
	fi
	echo 0
	# SETUP 6
	ev_007_h_log=$(git log -1 --format='%ae %aI' -- docs/owned-policy.md)
	printf '%s\n' "$ev_007_h_log"
	if ! printf '%s\n' "$ev_007_h_log" | grep -q '^wrong@example.com 2026-09-13T12:00:00'; then
		echo "EV-007-H SETUP 6"
		return 1
	fi
	# SETUP 7
	ev_007_h_packs=$CURBPACK_PACKS_DIR
	ev_007_h_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-07)
	printf '%s\n' "$ev_007_h_mutate_output"
	if ! printf '%s\n' "$ev_007_h_mutate_output" | grep -Fxq "mutate_pack.sh: PF-07" ||
		[ "$CURBPACK_PACKS_DIR" != "$ev_007_h_packs" ]; then
		echo "EV-007-H SETUP 7"
		return 1
	fi

	# TEST STEPS 1
	ev_007_h_check_output=$(curbpack check --packs fresh-owned-test --json --as-of "$AS_OF_DATE")
	ev_007_h_check_status=$?
	printf '%s\n' "$ev_007_h_check_output"
	if ! printf '%s\n' "$ev_007_h_check_output" | jq -e '
		.outcome == "findings" and
		.pack_id == "fresh-owned-test" and
		(.failures | length) == 1 and
		.failures[0].gate_id == "FIX-OWNED-POLICY"
	' >/dev/null; then
		echo "EV-007-H TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_h_check_status"
	if [ "$ev_007_h_check_status" -ne 1 ]; then
		echo "EV-007-H TEST STEPS 2"
		return 1
	fi
}

ev_008_a() {
	mkdir -p "${CURBPACK_ROOT:-.}/tmp/ev-008"
	# SETUP pack A 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-008-A SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-008-A SETUP 1"
		return 1
	fi
	# SETUP pack A 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-008-A SETUP 2"
		return 1
	fi
	# SETUP pack A 3
	ev_008_a_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_008_a_setup_status=$?
	printf '%s\n' "$ev_008_a_setup_output"
	if [ "$ev_008_a_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_008_a_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-008-A SETUP 3"
		return 1
	fi
	# SETUP pack A 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-008-A SETUP 4"
		return 1
	fi
	# SETUP pack A 5
	ev_008_a_packs=$CURBPACK_PACKS_DIR
	ev_008_a_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-08)
	printf '%s\n' "$ev_008_a_mutate_output"
	if ! printf '%s\n' "$ev_008_a_mutate_output" | grep -Fxq "mutate_pack.sh: PF-08" ||
		[ "$CURBPACK_PACKS_DIR" != "$ev_008_a_packs" ]; then
		echo "EV-008-A SETUP 5"
		return 1
	fi
	# SETUP pack A 6
	if test -e docs/ev008-alpha.md || test -e docs/ev008-beta.md; then
		echo "EV-008-A SETUP 6"
		return 1
	fi
	echo 0

	# TEST STEPS pack A 1
	ev_008_obs_a=$(curbpack check --packs ev-008-rule-order-a --json --as-of "$AS_OF_DATE")
	ev_008_st_a=$?
	printf '%s\n' "$ev_008_obs_a"
	printf '%s\n' "$ev_008_obs_a" >"$CURBPACK_ROOT/tmp/ev-008/obs-a.json"
	if ! printf '%s\n' "$ev_008_obs_a" | jq -e '
		.outcome == "findings" and
		.conformity_claim == "none" and
		.failed_rules == 2 and
		.evaluated_rules == 2 and
		((.failures | map(.gate_id) | sort) == ["EV008-ALPHA","EV008-BETA"])
	' >/dev/null; then
		echo "EV-008-A TEST STEPS 1"
		return 1
	fi
	# TEST STEPS pack A 2
	echo "$ev_008_st_a"
	if [ "$ev_008_st_a" -ne 1 ]; then
		echo "EV-008-A TEST STEPS 2"
		return 1
	fi

	# SETUP pack B 1 (independent restore)
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-008-A SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-008-A SETUP 1"
		return 1
	fi
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-008-A SETUP 2"
		return 1
	fi
	ev_008_b_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	ev_008_b_setup_status=$?
	printf '%s\n' "$ev_008_b_setup_output"
	if [ "$ev_008_b_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_008_b_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-008-A SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-008-A SETUP 4"
		return 1
	fi
	ev_008_b_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-09)
	printf '%s\n' "$ev_008_b_mutate_output"
	if ! printf '%s\n' "$ev_008_b_mutate_output" | grep -Fxq "mutate_pack.sh: PF-09"; then
		echo "EV-008-A SETUP 5"
		return 1
	fi
	if test -e docs/ev008-alpha.md || test -e docs/ev008-beta.md; then
		echo "EV-008-A SETUP 6"
		return 1
	fi

	# TEST STEPS pack B 1
	ev_008_obs_b=$(curbpack check --packs ev-008-rule-order-b --json --as-of "$AS_OF_DATE")
	ev_008_st_b=$?
	printf '%s\n' "$ev_008_obs_b"
	printf '%s\n' "$ev_008_obs_b" >"$CURBPACK_ROOT/tmp/ev-008/obs-b.json"
	if ! printf '%s\n' "$ev_008_obs_b" | jq -e '
		.outcome == "findings" and
		.conformity_claim == "none" and
		.failed_rules == 2 and
		.evaluated_rules == 2 and
		((.failures | map(.gate_id) | sort) == ["EV008-ALPHA","EV008-BETA"])
	' >/dev/null; then
		echo "EV-008-A TEST STEPS 1"
		return 1
	fi
	# TEST STEPS pack B 2
	echo "$ev_008_st_b"
	if [ "$ev_008_st_b" -ne 1 ]; then
		echo "EV-008-A TEST STEPS 2"
		return 1
	fi
	# TEST STEPS pack B 3
	ev_008_norm_a=$(jq -c '[.failures[] | {gate_id, sanitized_description, target_file: .ast_coordinates.target_file}] | sort_by(.gate_id,.sanitized_description,.target_file)' "$CURBPACK_ROOT/tmp/ev-008/obs-a.json")
	ev_008_norm_b=$(jq -c '[.failures[] | {gate_id, sanitized_description, target_file: .ast_coordinates.target_file}] | sort_by(.gate_id,.sanitized_description,.target_file)' "$CURBPACK_ROOT/tmp/ev-008/obs-b.json")
	ev_008_out_a=$(jq -r '.outcome + " " + .conformity_claim' "$CURBPACK_ROOT/tmp/ev-008/obs-a.json")
	ev_008_out_b=$(jq -r '.outcome + " " + .conformity_claim' "$CURBPACK_ROOT/tmp/ev-008/obs-b.json")
	printf '%s\n%s\n' "$ev_008_norm_a" "$ev_008_norm_b"
	if [ "$ev_008_st_a" -ne 1 ] || [ "$ev_008_st_b" -ne 1 ] ||
		[ "$ev_008_out_a" != "$ev_008_out_b" ] ||
		[ "$ev_008_norm_a" != "$ev_008_norm_b" ]; then
		echo "EV-008-A TEST STEPS 3"
		return 1
	fi
}

ev_008_b() {
	echo "EV-008-B: Blocked. Missing test seam. The case cannot be run. Do not run this variant."
	return 2
}

ev_009() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-009 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-009 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-009 SETUP 2"
		return 1
	fi
	# SETUP 3
	ev_009_setup_output=$(./external_test/curbpack/setup.sh R5 --commit)
	ev_009_setup_status=$?
	printf '%s\n' "$ev_009_setup_output"
	if [ "$ev_009_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_009_setup_output" | grep -Fq "R5 — thin rule-satisfying house-policy tree"; then
		echo "EV-009 SETUP 3"
		return 1
	fi
	# SETUP 4
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-009 SETUP 4"
		return 1
	fi
	# SETUP 5
	if ! grep -F '"name": "demo-app"' package.json; then
		echo "EV-009 SETUP 5"
		return 1
	fi
	# SETUP 6
	if ! grep -F 'warehouse controller firmware' SECURITY.md; then
		echo "EV-009 SETUP 6"
		return 1
	fi
	# SETUP 7
	if test -e src/app.py; then
		echo "EV-009 SETUP 7"
		return 1
	fi
	echo 0

	# TEST STEPS 1
	ev_009_check_output=$(curbpack check --packs house-policy --json --as-of "$AS_OF_DATE")
	ev_009_check_status=$?
	printf '%s\n' "$ev_009_check_output"
	if ! printf '%s\n' "$ev_009_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 5 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "EV-009 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_009_check_status"
	if [ "$ev_009_check_status" -ne 0 ]; then
		echo "EV-009 TEST STEPS 2"
		return 1
	fi
}
