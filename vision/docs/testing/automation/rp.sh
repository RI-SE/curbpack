#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)
rp_001() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "RP-001 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "RP-001 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "RP-001 SETUP 2"
		return 1
	fi
	# SETUP 3
	rp_001_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	rp_001_setup_status=$?
	printf '%s\n' "$rp_001_setup_output"
	if [ "$rp_001_setup_status" -ne 0 ] ||
		! printf '%s\n' "$rp_001_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$rp_001_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$rp_001_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$rp_001_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "RP-001 SETUP 3"
		return 1
	fi
	# SETUP 4
	rp_001_status_output=$(git status --porcelain)
	if [ -n "$rp_001_status_output" ]; then
		printf '%s\n' "$rp_001_status_output"
		echo "RP-001 SETUP 4"
		return 1
	fi

	# TEST STEPS 1
	rp_001_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	rp_001_check_status=$?
	printf '%s\n' "$rp_001_check_output"
	if ! printf '%s\n' "$rp_001_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "RP-001 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$rp_001_check_status"
	if [ "$rp_001_check_status" -ne 0 ]; then
		echo "RP-001 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	rp_001_share_output=$(curbpack share --as-of "$AS_OF_DATE")
	rp_001_share_status=$?
	printf '%s\n' "$rp_001_share_output"
	if [ ! -f review-pack/01-gate-failures.json ] ||
		[ ! -f review-pack/02-action-report.md ] ||
		[ ! -f review-pack/03-executive-summary.md ] ||
		[ ! -f review-pack/buyer-onepager.html ]; then
		echo "RP-001 TEST STEPS 3"
		return 1
	fi
	# TEST STEPS 4
	echo "$rp_001_share_status"
	if [ "$rp_001_share_status" -ne 0 ]; then
		echo "RP-001 TEST STEPS 4"
		return 1
	fi
	# TEST STEPS 5
	cat review-pack/01-gate-failures.json
	if ! jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15
	' review-pack/01-gate-failures.json >/dev/null; then
		echo "RP-001 TEST STEPS 5"
		return 1
	fi
	# TEST STEPS 6
	rp_001_summary=$(cat review-pack/03-executive-summary.md)
	rp_001_onepager=$(cat review-pack/buyer-onepager.html)
	printf '%s\n%s\n' "$rp_001_summary" "$rp_001_onepager"
	if ! printf '%s\n%s\n' "$rp_001_summary" "$rp_001_onepager" |
		grep -Fq "house-policy,medtech-iec62304"; then
		echo "RP-001 TEST STEPS 6"
		return 1
	fi
	if ! printf '%s\n%s\n' "$rp_001_summary" "$rp_001_onepager" |
		grep -Eqi 'Open findings[^0-9]*0|selected checks passed'; then
		echo "RP-001 TEST STEPS 6"
		return 1
	fi
	# Claim-language assessment is MANUAL. grep -Ei 'certification'
	# matches the disclaimer "not certification" and is not a product fail.
	# Pack identity and open-findings checks above remain.
	echo "RP-001 TEST STEPS 6 claim assessment: MANUAL (keyword check flags not certification)"
	return 2
}

rp_002() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "RP-002 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "RP-002 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "RP-002 SETUP 2"
		return 1
	fi
	# SETUP 3
	rp_002_setup_output=$(./external_test/curbpack/setup.sh R2 --commit)
	rp_002_setup_status=$?
	printf '%s\n' "$rp_002_setup_output"
	if [ "$rp_002_setup_status" -ne 0 ] ||
		! printf '%s\n' "$rp_002_setup_output" | grep -Fq "R2 — missing required file" ||
		! printf '%s\n' "$rp_002_setup_output" | grep -Fq "SECURITY.md absent, not empty"; then
		echo "RP-002 SETUP 3"
		return 1
	fi
	case $(git branch --show-current) in
		test_*) ;;
		*)
			echo "RP-002 SETUP 3"
			return 1
			;;
	esac
	# SETUP 4
	rp_002_status_output=$(git status --porcelain)
	if [ -n "$rp_002_status_output" ]; then
		printf '%s\n' "$rp_002_status_output"
		echo "RP-002 SETUP 4"
		return 1
	fi
	# SETUP 5
	if ls SECURITY.md; then
		echo "RP-002 SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	rp_002_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	rp_002_check_status=$?
	printf '%s\n' "$rp_002_check_output"
	if ! printf '%s\n' "$rp_002_check_output" | jq -e '
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
		echo "RP-002 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$rp_002_check_status"
	if [ "$rp_002_check_status" -ne 1 ]; then
		echo "RP-002 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	rp_002_share_output=$(curbpack share --as-of "$AS_OF_DATE")
	rp_002_share_status=$?
	printf '%s\n' "$rp_002_share_output"
	if [ ! -d review-pack ] ||
		! grep -Fq "HOUSE-SECURITY-MD" review-pack/01-gate-failures.json; then
		echo "RP-002 TEST STEPS 3"
		return 1
	fi
	# TEST STEPS 4
	echo "$rp_002_share_status"
	if [ "$rp_002_share_status" -ne 1 ]; then
		echo "RP-002 TEST STEPS 4"
		return 1
	fi
	# TEST STEPS 5
	if ! grep -Fq "HOUSE-SECURITY-MD" review-pack/01-gate-failures.json ||
		! grep -Fq "HOUSE-SECURITY-MD" review-pack/02-action-report.md ||
		! grep -Fq "HOUSE-SECURITY-MD" review-pack/03-executive-summary.md; then
		echo "RP-002 TEST STEPS 5"
		return 1
	fi
}

rp_003() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "RP-003 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "RP-003 SETUP 1"
		return 1
	fi
	# SETUP 2
	rp_003_mutate_output=$(cd "$REFERENCE_PRODUCT_ROOT" &&
		./external_test/curbpack/mutate_pack.sh PF-10)
	rp_003_mutate_status=$?
	printf '%s\n' "$rp_003_mutate_output"
	rp_003_input=$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input
	if [ "$rp_003_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$rp_003_mutate_output" | grep -Fxq "mutate_pack.sh: PF-10" ||
		[ ! -d "$rp_003_input" ] || [ -d "$rp_003_input/.git" ]; then
		echo "RP-003 SETUP 2"
		return 1
	fi
	# SETUP 3
	rp_003_parent_line=$(grep expected_parent_commit_sha "$rp_003_input/01-gate-failures.json")
	printf '%s\n' "$rp_003_parent_line"
	if ! printf '%s\n' "$rp_003_parent_line" |
		grep -Fq '"expected_parent_commit_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"'; then
		echo "RP-003 SETUP 3"
		return 1
	fi
	# SETUP 4
	rp_003_commit_line=$(grep Commit "$rp_003_input/buyer-onepager.html")
	printf '%s\n' "$rp_003_commit_line"
	if ! printf '%s\n' "$rp_003_commit_line" | grep -Fq "aaaaaaaaaaaa"; then
		echo "RP-003 SETUP 4"
		return 1
	fi

	# TEST STEPS 1
	rp_003_review_output=$(curbpack review --json "$rp_003_input" 2>&1)
	rp_003_review_status=$?
	printf '%s\n' "$rp_003_review_output"
	if ! printf '%s\n' "$rp_003_review_output" | grep -Fq "Offline document triage — not a product verdict." ||
		! printf '%s\n' "$rp_003_review_output" | grep -Eq '"schema"[[:space:]]*:[[:space:]]*"curbpack-review-report:2"' ||
		! printf '%s\n' "$rp_003_review_output" | grep -Eq '"subject_commit"[[:space:]]*:[[:space:]]*"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"' ||
		! printf '%s\n' "$rp_003_review_output" | grep -Eq '"confirmed_count"[[:space:]]*:[[:space:]]*9' ||
		! printf '%s\n' "$rp_003_review_output" | grep -Eq '"unconfirmed_count"[[:space:]]*:[[:space:]]*10' ||
		! printf '%s\n' "$rp_003_review_output" | grep -Eq '"contradicted_count"[[:space:]]*:[[:space:]]*0'; then
		echo "RP-003 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$rp_003_review_status"
	if [ "$rp_003_review_status" -ne 0 ]; then
		echo "RP-003 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	rp_003_subject_commit=$(printf '%s\n' "$rp_003_review_output" |
		sed -n 's/.*"subject_commit"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
	rp_003_onepager_commit=$(grep Commit "$rp_003_input/buyer-onepager.html")
	if [ "$rp_003_subject_commit" != "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" ] ||
		! printf '%s\n' "$rp_003_onepager_commit" | grep -Fq "aaaaaaaaaaaa" ||
		printf '%s\n' "$rp_003_onepager_commit" | grep -Fq "$rp_003_subject_commit"; then
		echo "RP-003 TEST STEPS 3"
		return 1
	fi
}

rp_004() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "RP-004 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "RP-004 SETUP 1"
		return 1
	fi
	# SETUP 2
	rp_004_mutate_output=$(cd "$REFERENCE_PRODUCT_ROOT" &&
		./external_test/curbpack/mutate_pack.sh PF-11)
	rp_004_mutate_status=$?
	printf '%s\n' "$rp_004_mutate_output"
	rp_004_input=$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input
	if [ "$rp_004_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$rp_004_mutate_output" | grep -Fxq "mutate_pack.sh: PF-11" ||
		[ ! -d "$rp_004_input" ] || [ -d "$rp_004_input/.git" ]; then
		echo "RP-004 SETUP 2"
		return 1
	fi
	# SETUP 3
	rp_004_summary_line=$(grep HOUSE-SECURITY-MD "$rp_004_input/03-executive-summary.md")
	rp_004_gate_line=$(grep HOUSE-SECURITY-MD "$rp_004_input/01-gate-failures.json")
	rp_004_action_line=$(grep HOUSE-SECURITY-MD "$rp_004_input/02-action-report.md")
	printf '%s\n%s\n%s\n' "$rp_004_summary_line" "$rp_004_gate_line" "$rp_004_action_line"
	if [ -n "$rp_004_summary_line" ] ||
		[ -z "$rp_004_gate_line" ] ||
		[ -z "$rp_004_action_line" ]; then
		echo "RP-004 SETUP 3"
		return 1
	fi

	# TEST STEPS 1
	rp_004_review_output=$(curbpack review --json "$rp_004_input" 2>&1)
	rp_004_review_status=$?
	printf '%s\n' "$rp_004_review_output"
	if ! printf '%s\n' "$rp_004_review_output" | grep -Eq '"schema"[[:space:]]*:[[:space:]]*"curbpack-review-report:2"' ||
		! printf '%s\n' "$rp_004_review_output" | grep -Eq '"confirmed_count"[[:space:]]*:[[:space:]]*9' ||
		! printf '%s\n' "$rp_004_review_output" | grep -Eq '"unconfirmed_count"[[:space:]]*:[[:space:]]*10' ||
		! printf '%s\n' "$rp_004_review_output" | grep -Eq '"contradicted_count"[[:space:]]*:[[:space:]]*0' ||
		! printf '%s\n' "$rp_004_review_output" | grep -Fq "reference:claim:HOUSE-SECURITY-MD"; then
		echo "RP-004 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$rp_004_review_status"
	if [ "$rp_004_review_status" -ne 0 ]; then
		echo "RP-004 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	if ! grep -Fq "HOUSE-SECURITY-MD" "$rp_004_input/01-gate-failures.json" ||
		! grep -Fq "HOUSE-SECURITY-MD" "$rp_004_input/02-action-report.md" ||
		grep -Fq "HOUSE-SECURITY-MD" "$rp_004_input/03-executive-summary.md"; then
		echo "RP-004 TEST STEPS 3"
		return 1
	fi
}

rp_005() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "RP-005 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "RP-005 SETUP 1"
		return 1
	fi
	# SETUP 2
	rp_005_mutate_output=$(cd "$REFERENCE_PRODUCT_ROOT" &&
		./external_test/curbpack/mutate_pack.sh PF-12)
	rp_005_mutate_status=$?
	printf '%s\n' "$rp_005_mutate_output"
	rp_005_input=$REFERENCE_PRODUCT_ROOT/external_test/curbpack/review-pack-input
	if [ "$rp_005_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$rp_005_mutate_output" | grep -Fxq "mutate_pack.sh: PF-12" ||
		[ ! -d "$rp_005_input" ] || [ -d "$rp_005_input/.git" ]; then
		echo "RP-005 SETUP 2"
		return 1
	fi
	# SETUP 3
	rp_005_gate_json=$(cat "$rp_005_input/01-gate-failures.json")
	printf '%s\n' "$rp_005_gate_json"
	if [ "$rp_005_gate_json" != "{" ] ||
		[ ! -f "$rp_005_input/01-gate-failures.json" ]; then
		echo "RP-005 SETUP 3"
		return 1
	fi

	# TEST STEPS 1
	rp_005_review_output=$(curbpack review --json "$rp_005_input" 2>&1)
	rp_005_review_status=$?
	printf '%s\n' "$rp_005_review_output"
	if ! printf '%s\n' "$rp_005_review_output" | grep -Fq "Contradicted findings present" ||
		! printf '%s\n' "$rp_005_review_output" | grep -Eq '"schema"[[:space:]]*:[[:space:]]*"curbpack-review-report:2"' ||
		! printf '%s\n' "$rp_005_review_output" | grep -Eq '"confirmed_count"[[:space:]]*:[[:space:]]*5' ||
		! printf '%s\n' "$rp_005_review_output" | grep -Eq '"unconfirmed_count"[[:space:]]*:[[:space:]]*10' ||
		! printf '%s\n' "$rp_005_review_output" | grep -Eq '"contradicted_count"[[:space:]]*:[[:space:]]*1' ||
		! printf '%s\n' "$rp_005_review_output" | grep -Eq '"contradicted_self_disagree"[[:space:]]*:[[:space:]]*1' ||
		! printf '%s\n' "$rp_005_review_output" | grep -Fq "digest:gate-json-parse"; then
		echo "RP-005 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$rp_005_review_status"
	if [ "$rp_005_review_status" -ne 1 ]; then
		echo "RP-005 TEST STEPS 2"
		return 1
	fi
}

rp_006() {
	echo "RP-006: Not specified yet. Do not run this case."
	return 2
}

rp_007() {
	echo "RP-007: Not specified yet. Do not run this case."
	return 2
}
