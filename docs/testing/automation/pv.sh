#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
pv_001() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PV-001 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PV-001 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-001 SETUP 2"
		return 1
	fi
	# SETUP 3
	pv_001_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pv_001_setup_status=$?
	printf '%s\n' "$pv_001_setup_output"
	if [ "$pv_001_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pv_001_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pv_001_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pv_001_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pv_001_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PV-001 SETUP 3"
		return 1
	fi
	# SETUP 4
	pv_001_status_output=$(git status --porcelain)
	if [ -n "$pv_001_status_output" ]; then
		printf '%s\n' "$pv_001_status_output"
		echo "PV-001 SETUP 4"
		return 1
	fi
	# SETUP 5
	pv_001_head=$(git rev-parse HEAD)
	printf '%s\n' "$pv_001_head"
	case "$pv_001_head" in
		????????????????????????????????????????) ;;
		*)
			echo "PV-001 SETUP 5"
			return 1
			;;
	esac

	# TEST STEPS 1
	pv_001_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_001_check_status=$?
	printf '%s\n' "$pv_001_check_output"
	if ! printf '%s\n' "$pv_001_check_output" | jq -e --arg head "$pv_001_head" '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none" and
		.concurrency_control.expected_parent_commit_sha == $head
	' >/dev/null; then
		echo "PV-001 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_001_check_status"
	if [ "$pv_001_check_status" -ne 0 ]; then
		echo "PV-001 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	grep -A2 subject_commit .github/curbpack/cache/latest_evaluation.json
	if ! jq -e --arg head "$pv_001_head" '
		.input_identity.subject_commit == $head and
		.input_identity.subject_commit_status == "claimed"
	' .github/curbpack/cache/latest_evaluation.json >/dev/null; then
		echo "PV-001 TEST STEPS 3"
		return 1
	fi
}

pv_002() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PV-002 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PV-002 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-002 SETUP 2"
		return 1
	fi
	# SETUP 3
	pv_002_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pv_002_setup_status=$?
	printf '%s\n' "$pv_002_setup_output"
	if [ "$pv_002_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pv_002_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pv_002_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pv_002_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pv_002_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PV-002 SETUP 3"
		return 1
	fi
	# SETUP 4
	pv_002_status_output=$(git status --porcelain)
	if [ -n "$pv_002_status_output" ]; then
		printf '%s\n' "$pv_002_status_output"
		echo "PV-002 SETUP 4"
		return 1
	fi
	# SETUP 5
	pv_002_head=$(git rev-parse HEAD)
	printf '%s\n' "$pv_002_head"
	case "$pv_002_head" in
		????????????????????????????????????????) ;;
		*)
			echo "PV-002 SETUP 5"
			return 1
			;;
	esac
	# SETUP 6
	printf '\nPV-002 uncommitted marker\n' >> SECURITY.md
	if ! grep -Fxq "PV-002 uncommitted marker" SECURITY.md; then
		echo "PV-002 SETUP 6"
		return 1
	fi
	# SETUP 7
	pv_002_status_output=$(git status --porcelain)
	printf '%s\n' "$pv_002_status_output"
	if [ "$pv_002_status_output" != " M SECURITY.md" ]; then
		echo "PV-002 SETUP 7"
		return 1
	fi

	# TEST STEPS 1
	pv_002_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_002_check_status=$?
	printf '%s\n' "$pv_002_check_output"
	if ! printf '%s\n' "$pv_002_check_output" | jq -e --arg head "$pv_002_head" '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none" and
		.concurrency_control.expected_parent_commit_sha == $head
	' >/dev/null; then
		echo "PV-002 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_002_check_status"
	if [ "$pv_002_check_status" -ne 0 ]; then
		echo "PV-002 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	pv_002_digest_output=$(openssl dgst -sha256 SECURITY.md)
	pv_002_digest_status=$?
	printf '%s\n' "$pv_002_digest_output"
	pv_002_digest=${pv_002_digest_output##* }
	if [ "$pv_002_digest_status" -ne 0 ] || [ -z "$pv_002_digest" ]; then
		echo "PV-002 TEST STEPS 3"
		return 1
	fi
	# TEST STEPS 4
	grep -A6 '"path": "SECURITY.md"' .github/curbpack/cache/latest_evaluation.json
	if ! jq -e --arg digest "$pv_002_digest" --arg head "$pv_002_head" '
		(any(.input_identity.files[]; .path == "SECURITY.md" and .state == "file" and .sha256 == $digest)) and
		.input_identity.subject_commit == $head and
		.input_identity.subject_commit_status == "claimed"
	' .github/curbpack/cache/latest_evaluation.json >/dev/null; then
		echo "PV-002 TEST STEPS 4"
		return 1
	fi
}

pv_003() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PV-003 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PV-003 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-003 SETUP 2"
		return 1
	fi
	# SETUP 3
	pv_003_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pv_003_setup_status=$?
	printf '%s\n' "$pv_003_setup_output"
	if [ "$pv_003_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pv_003_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pv_003_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pv_003_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pv_003_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PV-003 SETUP 3"
		return 1
	fi
	# SETUP 4
	pv_003_status_output=$(git status --porcelain)
	if [ -n "$pv_003_status_output" ]; then
		printf '%s\n' "$pv_003_status_output"
		echo "PV-003 SETUP 4"
		return 1
	fi
	# SETUP 5
	if ! git checkout --detach HEAD; then
		echo "PV-003 SETUP 5"
		return 1
	fi
	# SETUP 6
	git symbolic-ref -q HEAD
	pv_003_symbolic_status=$?
	echo "$pv_003_symbolic_status"
	if [ "$pv_003_symbolic_status" -ne 1 ]; then
		echo "PV-003 SETUP 6"
		return 1
	fi
	# SETUP 7
	pv_003_head=$(git rev-parse HEAD)
	printf '%s\n' "$pv_003_head"
	case "$pv_003_head" in
		????????????????????????????????????????) ;;
		*)
			echo "PV-003 SETUP 7"
			return 1
			;;
	esac

	# TEST STEPS 1
	pv_003_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_003_check_status=$?
	printf '%s\n' "$pv_003_check_output"
	if ! printf '%s\n' "$pv_003_check_output" | jq -e --arg head "$pv_003_head" '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none" and
		.concurrency_control.expected_parent_commit_sha == $head
	' >/dev/null ||
		printf '%s\n' "$pv_003_check_output" | grep -Eq '"branch"[[:space:]]*:'; then
		echo "PV-003 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_003_check_status"
	if [ "$pv_003_check_status" -ne 0 ]; then
		echo "PV-003 TEST STEPS 2"
		return 1
	fi
}

pv_004() {
	echo "PV-004: Not specified yet. Do not run this case."
	return 2
}

pv_005() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PV-005 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PV-005 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-005 SETUP 2"
		return 1
	fi
	# SETUP 3
	pv_005_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pv_005_setup_status=$?
	printf '%s\n' "$pv_005_setup_output"
	if [ "$pv_005_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pv_005_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pv_005_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pv_005_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pv_005_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PV-005 SETUP 3"
		return 1
	fi
	# SETUP 4
	pv_005_status_output=$(git status --porcelain)
	if [ -n "$pv_005_status_output" ]; then
		printf '%s\n' "$pv_005_status_output"
		echo "PV-005 SETUP 4"
		return 1
	fi
	# SETUP 5
	for pv_005_pack in house-policy cra-baseline medtech-iec62304; do
		jq '{id, version}' "external_test/curbpack/packs/$pv_005_pack/pack.json"
	done
	cat external_test/curbpack/packs/SOURCE.txt
	if ! jq -e '.id == "house-policy" and .version == "0.1.0"' external_test/curbpack/packs/house-policy/pack.json >/dev/null ||
		! jq -e '.id == "cra-baseline" and .version == "0.1.0"' external_test/curbpack/packs/cra-baseline/pack.json >/dev/null ||
		! jq -e '.id == "medtech-iec62304" and .version == "0.2.0"' external_test/curbpack/packs/medtech-iec62304/pack.json >/dev/null ||
		! grep -Eq '^source_repo: .+' external_test/curbpack/packs/SOURCE.txt ||
		! grep -Eq '^source_commit: [0-9a-f]{40}$' external_test/curbpack/packs/SOURCE.txt; then
		echo "PV-005 SETUP 5"
		return 1
	fi

	# TEST STEPS 1
	pv_005_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_005_check_status=$?
	printf '%s\n' "$pv_005_check_output"
	if ! printf '%s\n' "$pv_005_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "PV-005 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_005_check_status"
	if [ "$pv_005_check_status" -ne 0 ]; then
		echo "PV-005 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	jq '.input_identity.pack_sources' .github/curbpack/cache/latest_evaluation.json
	if ! jq -e '
		.input_identity.pack_sources == [
			{"id":"house-policy","version":"0.1.0","sha256":"eb74fd06241b79608d614bb27c15e8afccf33ea54a5f9d1629ea09e167391e5d"},
			{"id":"cra-baseline","version":"0.1.0","sha256":"dd8987bcda3765290c8989fd69c97886f911702ba08896605389f5035c515499"},
			{"id":"medtech-iec62304","version":"0.2.0","sha256":"e041b748ee87341603b116763bedaa7269773e6a4c7e035d776da661f08dd469"}
		]
	' .github/curbpack/cache/latest_evaluation.json >/dev/null; then
		echo "PV-005 TEST STEPS 3"
		return 1
	fi
}

pv_006() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PV-006 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PV-006 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-006 SETUP 2"
		return 1
	fi
	# SETUP 3
	pv_006_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pv_006_setup_status=$?
	printf '%s\n' "$pv_006_setup_output"
	if [ "$pv_006_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pv_006_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pv_006_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pv_006_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pv_006_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PV-006 SETUP 3"
		return 1
	fi
	# SETUP 4
	pv_006_status_output=$(git status --porcelain)
	if [ -n "$pv_006_status_output" ]; then
		printf '%s\n' "$pv_006_status_output"
		echo "PV-006 SETUP 4"
		return 1
	fi
	# SETUP 5
	mkdir -p "$CURBPACK_ROOT/tmp/pv-006"
	pv_006_pf01_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_006_pf01_status=$?
	printf '%s\n' "$pv_006_pf01_output"
	jq -r '.comparison_key' .github/curbpack/cache/latest_evaluation.json > "$CURBPACK_ROOT/tmp/pv-006/pf01-comparison_key"
	pv_006_pf01_key=$(cat "$CURBPACK_ROOT/tmp/pv-006/pf01-comparison_key")
	if [ "$pv_006_pf01_status" -ne 0 ] ||
		[ -z "$pv_006_pf01_key" ] ||
		[ "$pv_006_pf01_key" = "null" ]; then
		echo "PV-006 SETUP 5"
		return 1
	fi
	# SETUP 6
	pv_006_mutate_output=$(./external_test/curbpack/mutate_pack.sh PF-06)
	pv_006_mutate_status=$?
	printf '%s\n' "$pv_006_mutate_output"
	if [ "$pv_006_mutate_status" -ne 0 ] ||
		! printf '%s\n' "$pv_006_mutate_output" | grep -Fxq "mutate_pack.sh: PF-06" ||
		[ "$CURBPACK_PACKS_DIR" != "$REFERENCE_PRODUCT_ROOT/external_test/curbpack/packs" ] ||
		[ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-006 SETUP 6"
		return 1
	fi
	# SETUP 7
	if ! ls "$CURBPACK_PACKS_DIR/house-policy/pack.json"; then
		echo "PV-006 SETUP 7"
		return 1
	fi

	# TEST STEPS 1
	pv_006_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_006_check_status=$?
	printf '%s\n' "$pv_006_check_output"
	if ! printf '%s\n' "$pv_006_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' >/dev/null; then
		echo "PV-006 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_006_check_status"
	if [ "$pv_006_check_status" -ne 0 ]; then
		echo "PV-006 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	jq '{pack_sources: .input_identity.pack_sources, comparison_key}' .github/curbpack/cache/latest_evaluation.json
	pv_006_pf06_key=$(jq -r '.comparison_key' .github/curbpack/cache/latest_evaluation.json)
	if ! jq -e '
		.input_identity.pack_sources == [
			{"id":"house-policy","version":"0.1.0","sha256":"36f850200a1f5500d8add750d1567f6f790ff721e6946c2c048eecdb3122e5e8"},
			{"id":"cra-baseline","version":"0.1.0","sha256":"dd8987bcda3765290c8989fd69c97886f911702ba08896605389f5035c515499"},
			{"id":"medtech-iec62304","version":"0.2.0","sha256":"e041b748ee87341603b116763bedaa7269773e6a4c7e035d776da661f08dd469"}
		]
	' .github/curbpack/cache/latest_evaluation.json >/dev/null ||
		[ -z "$pv_006_pf06_key" ] ||
		[ "$pv_006_pf06_key" = "null" ] ||
		[ "$pv_006_pf06_key" = "$pv_006_pf01_key" ]; then
		echo "PV-006 TEST STEPS 3"
		return 1
	fi
}

pv_007() {
	# SETUP 1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "PV-007 SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "PV-007 SETUP 1"
		return 1
	fi
	# SETUP 2
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "PV-007 SETUP 2"
		return 1
	fi
	# SETUP 3
	pv_007_setup_output=$(./external_test/curbpack/setup.sh R1 --commit)
	pv_007_setup_status=$?
	printf '%s\n' "$pv_007_setup_output"
	if [ "$pv_007_setup_status" -ne 0 ] ||
		! printf '%s\n' "$pv_007_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$pv_007_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$pv_007_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$pv_007_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "PV-007 SETUP 3"
		return 1
	fi
	# SETUP 4
	pv_007_status_output=$(git status --porcelain)
	if [ -n "$pv_007_status_output" ]; then
		printf '%s\n' "$pv_007_status_output"
		echo "PV-007 SETUP 4"
		return 1
	fi

	# TEST STEPS 1
	pv_007_check_output=$(curbpack check --json --as-of "$AS_OF_DATE")
	pv_007_check_status=$?
	printf '%s\n' "$pv_007_check_output"
	if ! printf '%s\n' "$pv_007_check_output" | jq -e '
		.failures == null and
		.pack_id == "house-policy,medtech-iec62304" and
		.readiness_score == 100 and
		.outcome == "pass" and
		.evaluated_rules == 15 and
		.conformity_claim == "none"
	' >/dev/null ||
		printf '%s\n' "$pv_007_check_output" | grep -Eq '"(tool_version|method|platform)"[[:space:]]*:'; then
		echo "PV-007 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_007_check_status"
	if [ "$pv_007_check_status" -ne 0 ]; then
		echo "PV-007 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3
	jq '.input_identity' .github/curbpack/cache/latest_evaluation.json
	if ! jq -e '
		.input_identity.method == "curbpack-gates:2" and
		.input_identity.tool_version == "0.5.5"
	' .github/curbpack/cache/latest_evaluation.json >/dev/null ||
		grep -Ei '"[^"]*(home|username|hostname)[^"]*"[[:space:]]*:' .github/curbpack/cache/latest_evaluation.json >/dev/null; then
		echo "PV-007 TEST STEPS 3"
		return 1
	fi
	# TEST STEPS 4
	cat .github/curbpack/cache/latest_receipt.json
	if ! jq -e '
		.tool_version == "0.5.5" and
		(.platform | type == "string" and test("^[^/]+/[^/]+$")) and
		.as_of_source == "explicit"
	' .github/curbpack/cache/latest_receipt.json >/dev/null; then
		echo "PV-007 TEST STEPS 4"
		return 1
	fi
}
