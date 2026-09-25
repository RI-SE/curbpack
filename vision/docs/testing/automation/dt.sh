#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
dt_001() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "DT-001 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "DT-001 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "DT-001 SETUP 2"
		return 1
	fi
	# SETUP 3
	dt_001_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	dt_001_setup_status=$?
	printf '%s\n' "$dt_001_setup_output"
	if [ "$dt_001_setup_status" -ne 0 ] ||
		! printf '%s\n' "$dt_001_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$dt_001_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$dt_001_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$dt_001_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "DT-001 SETUP 3"
		return 1
	fi
	# SETUP 4
	dt_001_status_output=$(git status --porcelain)
	if [ -n "$dt_001_status_output" ]; then
		printf '%s\n' "$dt_001_status_output"
		echo "DT-001 SETUP 4"
		return 1
	fi
	# SETUP 5
	mkdir -p "$CURBPACK_ROOT/tmp/dt-001"
	if [ ! -d "$CURBPACK_ROOT/tmp/dt-001" ] || [ -e "$CURBPACK_ROOT/tmp/dt-001/.git" ]; then
		echo "DT-001 SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	i=1; while [ "$i" -le 20 ]; do curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-001/run-$i.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-001/run-$i.exit"; jq -r '.evaluation_digest' .github/curbpack/cache/latest_receipt.json > "$CURBPACK_ROOT/tmp/dt-001/run-$i.evaluation_digest"; i=$((i+1)); done
	i=1
	while [ "$i" -le 20 ]; do
		dt_001_eval_digest=$(cat "$CURBPACK_ROOT/tmp/dt-001/run-$i.evaluation_digest")
		if [ ! -f "$CURBPACK_ROOT/tmp/dt-001/run-$i.json" ] ||
			[ "$(cat "$CURBPACK_ROOT/tmp/dt-001/run-$i.exit")" != "0" ] ||
			[ -z "$dt_001_eval_digest" ] ||
			[ "$dt_001_eval_digest" = "null" ] ||
			! jq -e '
				.failures == null and
				.pack_id == "house-policy,medtech-iec62304" and
				.readiness_score == 100 and
				.outcome == "pass" and
				.evaluated_rules == 15 and
				.conformity_claim == "none"
			' "$CURBPACK_ROOT/tmp/dt-001/run-$i.json" >/dev/null; then
			echo "DT-001 TEST STEPS 1"
			return 1
		fi
		i=$((i+1))
	done
	# TEST STEPS 2
	dt_001_fields=$(jq -c '{failures, pack_id, outcome, readiness_score, evaluated_rules, conformity_claim}' "$CURBPACK_ROOT/tmp/dt-001/run-1.json")
	dt_001_digest=$(cat "$CURBPACK_ROOT/tmp/dt-001/run-1.evaluation_digest")
	if [ -z "$dt_001_digest" ] || [ "$dt_001_digest" = "null" ]; then
		echo "DT-001 TEST STEPS 2"
		return 1
	fi
	dt_001_digest_identical=true
	i=1
	while [ "$i" -le 20 ]; do
		dt_001_run_digest=$(cat "$CURBPACK_ROOT/tmp/dt-001/run-$i.evaluation_digest")
		if [ "$(jq -c '{failures, pack_id, outcome, readiness_score, evaluated_rules, conformity_claim}' "$CURBPACK_ROOT/tmp/dt-001/run-$i.json")" != "$dt_001_fields" ] ||
			[ "$(cat "$CURBPACK_ROOT/tmp/dt-001/run-$i.exit")" != "0" ] ||
			[ -z "$dt_001_run_digest" ] ||
			[ "$dt_001_run_digest" = "null" ]; then
			echo "DT-001 TEST STEPS 2"
			return 1
		fi
		if [ "$dt_001_run_digest" != "$dt_001_digest" ]; then
			dt_001_digest_identical=false
		fi
		i=$((i+1))
	done
	printf 'evaluation_digest identical: %s\n' "$dt_001_digest_identical"
}

dt_002() {
	echo "DT-002: Not specified yet. Do not run this case."
	return 2
}

dt_003() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "DT-003 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "DT-003 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "DT-003 SETUP 2"
		return 1
	fi
	# SETUP 3
	dt_003_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	dt_003_setup_status=$?
	printf '%s\n' "$dt_003_setup_output"
	if [ "$dt_003_setup_status" -ne 0 ] ||
		! printf '%s\n' "$dt_003_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$dt_003_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$dt_003_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$dt_003_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "DT-003 SETUP 3"
		return 1
	fi
	# SETUP 4
	dt_003_status_output=$(git status --porcelain)
	if [ -n "$dt_003_status_output" ]; then
		printf '%s\n' "$dt_003_status_output"
		echo "DT-003 SETUP 4"
		return 1
	fi
	# SETUP 5
	mkdir -p "$CURBPACK_ROOT/tmp/dt-003"
	if [ ! -d "$CURBPACK_ROOT/tmp/dt-003" ] || [ -e "$CURBPACK_ROOT/tmp/dt-003/.git" ]; then
		echo "DT-003 SETUP 5"
		return 1
	fi
	# SETUP 6
	curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-003/r1.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-003/r1.exit"
	if [ ! -f "$CURBPACK_ROOT/tmp/dt-003/r1.json" ] ||
		[ "$(cat "$CURBPACK_ROOT/tmp/dt-003/r1.exit")" != "0" ] ||
		! jq -e '
			.failures == null and
			.pack_id == "house-policy,medtech-iec62304" and
			.readiness_score == 100 and
			.outcome == "pass" and
			.evaluated_rules == 15 and
			.conformity_claim == "none"
		' "$CURBPACK_ROOT/tmp/dt-003/r1.json" >/dev/null; then
		echo "DT-003 SETUP 6"
		return 1
	fi
	# SETUP 7
	dt_003_r2_output=$(./external_test/curbpack/setup.sh R2 --commit)
	dt_003_r2_status=$?
	printf '%s\n' "$dt_003_r2_output"
	if [ "$dt_003_r2_status" -ne 0 ] ||
		! printf '%s\n' "$dt_003_r2_output" | grep -Fq "R2 — missing required file" ||
		! printf '%s\n' "$dt_003_r2_output" | grep -Fq "SECURITY.md absent, not empty"; then
		echo "DT-003 SETUP 7"
		return 1
	fi
	case $(git branch --show-current) in
		test_*) ;;
		*)
			echo "DT-003 SETUP 7"
			return 1
			;;
	esac
	# SETUP 8
	dt_003_status_output=$(git status --porcelain)
	if [ -n "$dt_003_status_output" ]; then
		printf '%s\n' "$dt_003_status_output"
		echo "DT-003 SETUP 8"
		return 1
	fi
	# SETUP 9
	if ls SECURITY.md; then
		echo "DT-003 SETUP 9"
		return 1
	fi

	# TEST STEPS 1
	curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-003/r2.json"
	dt_003_check_status=$?
	if [ ! -f "$CURBPACK_ROOT/tmp/dt-003/r2.json" ] ||
		! jq -e '
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
		' "$CURBPACK_ROOT/tmp/dt-003/r2.json" >/dev/null; then
		echo "DT-003 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$dt_003_check_status"
	if [ "$dt_003_check_status" -ne 1 ]; then
		echo "DT-003 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	if ! jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' "$CURBPACK_ROOT/tmp/dt-003/r1.json" >/dev/null ||
		! jq -e '
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
		' "$CURBPACK_ROOT/tmp/dt-003/r2.json" >/dev/null; then
		echo "DT-003 TEST STEPS 3"
		return 1
	fi
	dt_003_r1_same=$(jq -c '{pack_id, evaluated_rules, conformity_claim}' "$CURBPACK_ROOT/tmp/dt-003/r1.json")
	dt_003_r2_same=$(jq -c '{pack_id, evaluated_rules, conformity_claim}' "$CURBPACK_ROOT/tmp/dt-003/r2.json")
	dt_003_r1_diff=$(jq -c '{failures, outcome, readiness_score, failed_rules}' "$CURBPACK_ROOT/tmp/dt-003/r1.json")
	dt_003_r2_diff=$(jq -c '{failures, outcome, readiness_score, failed_rules}' "$CURBPACK_ROOT/tmp/dt-003/r2.json")
	if [ "$dt_003_r1_same" != "$dt_003_r2_same" ] || [ "$dt_003_r1_diff" = "$dt_003_r2_diff" ]; then
		echo "DT-003 TEST STEPS 3"
		return 1
	fi
}

dt_004() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "DT-004 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "DT-004 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "DT-004 SETUP 2"
		return 1
	fi
	# SETUP 3
	dt_004_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	dt_004_setup_status=$?
	printf '%s\n' "$dt_004_setup_output"
	if [ "$dt_004_setup_status" -ne 0 ] ||
		! printf '%s\n' "$dt_004_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$dt_004_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$dt_004_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$dt_004_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "DT-004 SETUP 3"
		return 1
	fi
	# SETUP 4
	dt_004_status_output=$(git status --porcelain)
	if [ -n "$dt_004_status_output" ]; then
		printf '%s\n' "$dt_004_status_output"
		echo "DT-004 SETUP 4"
		return 1
	fi
	# SETUP 5
	mkdir -p "$CURBPACK_ROOT/tmp/dt-004"
	if [ ! -d "$CURBPACK_ROOT/tmp/dt-004" ] || [ -e "$CURBPACK_ROOT/tmp/dt-004/.git" ]; then
		echo "DT-004 SETUP 5"
		return 1
	fi
	# SETUP 6
	i=1; while [ "$i" -le 20 ]; do curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.exit"; i=$((i+1)); done
	i=1
	while [ "$i" -le 20 ]; do
		if [ ! -f "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" ] ||
			[ "$(cat "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.exit")" != "0" ] ||
			! jq -e '
				.failures == null and
				.pack_id == "house-policy,medtech-iec62304" and
				.readiness_score == 100 and
				.outcome == "pass" and
				.evaluated_rules == 15 and
				.conformity_claim == "none"
			' "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" >/dev/null; then
			echo "DT-004 SETUP 6"
			return 1
		fi
		i=$((i+1))
	done
	# SETUP 7
	dt_004_r2_output=$(./external_test/curbpack/setup.sh R2 --commit)
	dt_004_r2_status=$?
	printf '%s\n' "$dt_004_r2_output"
	if [ "$dt_004_r2_status" -ne 0 ] ||
		! printf '%s\n' "$dt_004_r2_output" | grep -Fq "R2 — missing required file" ||
		! printf '%s\n' "$dt_004_r2_output" | grep -Fq "SECURITY.md absent, not empty"; then
		echo "DT-004 SETUP 7"
		return 1
	fi
	case $(git branch --show-current) in
		test_*) ;;
		*)
			echo "DT-004 SETUP 7"
			return 1
			;;
	esac
	# SETUP 8
	dt_004_status_output=$(git status --porcelain)
	if [ -n "$dt_004_status_output" ]; then
		printf '%s\n' "$dt_004_status_output"
		echo "DT-004 SETUP 8"
		return 1
	fi
	# SETUP 9
	if ls SECURITY.md; then
		echo "DT-004 SETUP 9"
		return 1
	fi
	# SETUP 10
	curbpack check --json --as-of "$AS_OF_DATE" > "$CURBPACK_ROOT/tmp/dt-004/r2.json"; echo $? > "$CURBPACK_ROOT/tmp/dt-004/r2.exit"
	if [ ! -f "$CURBPACK_ROOT/tmp/dt-004/r2.json" ] ||
		[ "$(cat "$CURBPACK_ROOT/tmp/dt-004/r2.exit")" != "1" ] ||
		! jq -e '
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
		' "$CURBPACK_ROOT/tmp/dt-004/r2.json" >/dev/null; then
		echo "DT-004 SETUP 10"
		return 1
	fi

	# TEST STEPS 1
	dt_004_ids=$(jq -c 'if .failures == null then [] else [.failures[].gate_id] end' "$CURBPACK_ROOT/tmp/dt-004/r1-run-1.json")
	i=1
	while [ "$i" -le 20 ]; do
		if ! jq -e '.failures == null' "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" >/dev/null ||
			[ "$(jq -c 'if .failures == null then [] else [.failures[].gate_id] end' "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json")" != "$dt_004_ids" ]; then
			echo "DT-004 TEST STEPS 1"
			return 1
		fi
		i=$((i+1))
	done
	if [ "$dt_004_ids" != "[]" ]; then
		echo "DT-004 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	if [ "$(jq -c 'if .failures == null then [] else [.failures[].gate_id] end' "$CURBPACK_ROOT/tmp/dt-004/r1-run-1.json")" != "[]" ] ||
		! jq -e '[.failures[].gate_id] == ["HOUSE-SECURITY-MD"]' "$CURBPACK_ROOT/tmp/dt-004/r2.json" >/dev/null; then
		echo "DT-004 TEST STEPS 2"
		return 1
	fi
}
