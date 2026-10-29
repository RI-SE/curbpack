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
	ev_001_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
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

	# PF-01 after SETUP 4 (docs/testing/procedures).
	install_pf01

	# TEST STEPS 1 — argv: --repo -o; JSON is the run-result file.
	ev_001_check_output=$(run_curbcheck_json)
	ev_001_check_status=$?
	printf '%s\n' "$ev_001_check_output"
	# Field rename: outcome/readiness_score → claims[].status (Packs v2).
	if ! printf '%s\n' "$ev_001_check_output" | jq -e '
		(([.claims[].id] | sort) == [
			"CRA-ANNEX-VII-MANUAL","CRA-ANNEX-VII-RISK","CRA-ANNEX-VII-SUPPORT",
			"CRA-ART14-PATH","HOUSE-ANTI-PLACEHOLDER","HOUSE-SECURITY-MD","HOUSE-SECURITY-TXT"
		])
		and all(.claims[]; .status == "pass")
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
	ev_002_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R2 --commit)
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

	install_pf01

	# TEST STEPS 1 — HOUSE-SECURITY-MD status fail (Packs v2).
	ev_002_check_output=$(run_curbcheck_json)
	ev_002_check_status=$?
	printf '%s\n' "$ev_002_check_output"
	if ! printf '%s\n' "$ev_002_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")
	' >/dev/null; then
		echo "EV-002 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_002_check_status"
	if [ "$ev_002_check_status" -eq 0 ]; then
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
	ev_003_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R3 --commit)
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
	install_md_sw_class

	# TEST STEPS 1 — MD-SW-CLASS status fail (Packs v2 translation of annex_file).
	mkdir -p "$CURBPACK_ROOT/tmp/ev-003"
	ev_003_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-003/summary")
	ev_003_check_status=$?
	printf '%s\n' "$ev_003_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-003/summary"
	if ! printf '%s\n' "$ev_003_check_output" | jq -e '
		any(.claims[]; .id == "MD-SW-CLASS" and .status == "fail")
	' >/dev/null; then
		echo "EV-003 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_003_check_status"
	if [ "$ev_003_check_status" -eq 0 ]; then
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
	# SETUP 3 — R1 then make required SECURITY.md present but unreadable.
	ev_004_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_004_setup_status=$?
	printf '%s\n' "$ev_004_setup_output"
	if [ "$ev_004_setup_status" -ne 0 ]; then
		echo "EV-004 SETUP 3"
		return 1
	fi
	if [ ! -f SECURITY.md ]; then
		echo "EV-004 SETUP 3"
		return 1
	fi
	chmod 000 SECURITY.md
	install_pf01

	# TEST STEPS 1 — claim must not be pass (MUST-24).
	mkdir -p "$CURBPACK_ROOT/tmp/ev-004"
	ev_004_check_output=$(run_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-004/summary")
	ev_004_check_status=$?
	chmod 644 SECURITY.md 2>/dev/null || true
	printf '%s\n' "$ev_004_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-004/summary"
	if ! printf '%s\n' "$ev_004_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")
		and any(.claims[];
			.id == "HOUSE-SECURITY-MD"
			and any(.checks[]; .check == "exist" and .status == "fail"
				and (.detail | test("unreadable")))
		)
		and any(.claims[];
			.id == "HOUSE-SECURITY-MD"
			and any(.checks[]; .check == "contents" and .status == "fail"
				and (.detail | test("unreadable")))
		)
	' >/dev/null; then
		echo "EV-004 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_004_check_status"
	if [ "$ev_004_check_status" -eq 0 ]; then
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
	# SETUP 3 — R1 good tree; skip replaces curbpack --diff skipped_rules.
	ev_005_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_005_setup_status=$?
	printf '%s\n' "$ev_005_setup_output"
	if [ "$ev_005_setup_status" -ne 0 ]; then
		echo "EV-005 SETUP 3"
		return 1
	fi
	install_pf01

	# TEST STEPS 1 — --skip → Claim status skipped, never pass (MUST-23 / Packs v2).
	mkdir -p "$CURBPACK_ROOT/tmp/ev-005"
	ev_005_check_output=$(
		run_curbcheck_json --skip 'HOUSE-SECURITY-MD=EV-005 excluded target' \
			2>"$CURBPACK_ROOT/tmp/ev-005/summary"
	)
	ev_005_check_status=$?
	printf '%s\n' "$ev_005_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-005/summary"
	if ! printf '%s\n' "$ev_005_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "skipped")
		and all(.claims[]; .id != "HOUSE-SECURITY-MD" or .status != "pass")
		and any(.claims[];
			.id == "HOUSE-SECURITY-MD"
			and all(.checks[]; .status == "skipped")
		)
	' >/dev/null; then
		echo "EV-005 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_005_check_status"
	if [ "$ev_005_check_status" -eq 0 ]; then
		echo "EV-005 TEST STEPS 2"
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
	ev_006_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R4 --commit)
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
	# SETUP 8 — R4 token-only text does not trip the placeholder probe.
	printf '\nTODO\n' >> SECURITY.md
	if ! grep -q 'TODO' SECURITY.md; then
		echo "EV-006 SETUP 8"
		return 1
	fi
	install_house_claims

	# TEST STEPS 1 — HOUSE-ANTI-PLACEHOLDER status fail.
	mkdir -p "$CURBPACK_ROOT/tmp/ev-006"
	ev_006_check_output=$(run_house_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-006/summary")
	ev_006_check_status=$?
	printf '%s\n' "$ev_006_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-006/summary"
	if ! printf '%s\n' "$ev_006_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-ANTI-PLACEHOLDER" and .status == "fail")
	' >/dev/null; then
		echo "EV-006 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_006_check_status"
	if [ "$ev_006_check_status" -eq 0 ]; then
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
	ev_007_a_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R2 --commit)
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

	install_pf01

	# TEST STEPS 1 — HOUSE-SECURITY-MD status fail.
	ev_007_a_check_output=$(run_curbcheck_json)
	ev_007_a_check_status=$?
	printf '%s\n' "$ev_007_a_check_output"
	if ! printf '%s\n' "$ev_007_a_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")
	' >/dev/null; then
		echo "EV-007-A TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_a_check_status"
	if [ "$ev_007_a_check_status" -eq 0 ]; then
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
	ev_007_b_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R3 --commit)
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
	install_md_sw_class

	# TEST STEPS 1
	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-b"
	ev_007_b_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-b/summary")
	ev_007_b_check_status=$?
	printf '%s\n' "$ev_007_b_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-b/summary"
	if ! printf '%s\n' "$ev_007_b_check_output" | jq -e '
		any(.claims[]; .id == "MD-SW-CLASS" and .status == "fail")
	' >/dev/null; then
		echo "EV-007-B TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_b_check_status"
	if [ "$ev_007_b_check_status" -eq 0 ]; then
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
	ev_007_c_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R4 --commit)
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

	# SETUP 5 — R4 token-only text does not trip the placeholder probe.
	printf '\nTODO\n' >> SECURITY.md
	if ! grep -q 'TODO' SECURITY.md; then
		echo "EV-007-C SETUP 5"
		return 1
	fi
	install_house_claims

	# TEST STEPS 1 — HOUSE-ANTI-PLACEHOLDER status fail.
	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-c"
	ev_007_c_check_output=$(run_house_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-c/summary")
	ev_007_c_check_status=$?
	printf '%s\n' "$ev_007_c_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-c/summary"
	if ! printf '%s\n' "$ev_007_c_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-ANTI-PLACEHOLDER" and .status == "fail")
	' >/dev/null; then
		echo "EV-007-C TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$ev_007_c_check_status"
	if [ "$ev_007_c_check_status" -eq 0 ]; then
		echo "EV-007-C TEST STEPS 2"
		return 1
	fi
}

ev_007_d() {
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
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-D SETUP 2"
		return 1
	fi
	ev_007_d_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_007_d_setup_status=$?
	printf '%s\n' "$ev_007_d_setup_output"
	if [ "$ev_007_d_setup_status" -ne 0 ]; then
		echo "EV-007-D SETUP 3"
		return 1
	fi
	pin_banned_axios
	if ! grep -F '"axios": "^1.6.0"' package.json; then
		echo "EV-007-D SETUP 4"
		return 1
	fi
	install_house_dep_axios

	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-d"
	ev_007_d_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-d/summary")
	ev_007_d_check_status=$?
	printf '%s\n' "$ev_007_d_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-d/summary"
	if ! printf '%s\n' "$ev_007_d_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-DEP-AXIOS-PIN" and .status == "fail")
		and any(.claims[];
			.id == "HOUSE-DEP-AXIOS-PIN"
			and any(.checks[]; .check == "dep_ban" and .status == "fail"
				and (.detail | test("banned pin")))
		)
	' >/dev/null; then
		echo "EV-007-D TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_d_check_status"
	if [ "$ev_007_d_check_status" -eq 0 ]; then
		echo "EV-007-D TEST STEPS 2"
		return 1
	fi
}

ev_007_e() {
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
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-E SETUP 2"
		return 1
	fi
	ev_007_e_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_007_e_setup_status=$?
	printf '%s\n' "$ev_007_e_setup_output"
	if [ "$ev_007_e_setup_status" -ne 0 ]; then
		echo "EV-007-E SETUP 3"
		return 1
	fi
	pin_banned_axios
	if ! grep -F '"axios": "^1.6.0"' package.json; then
		echo "EV-007-E SETUP 4"
		return 1
	fi
	install_cra_dep_axios

	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-e"
	ev_007_e_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-e/summary")
	ev_007_e_check_status=$?
	printf '%s\n' "$ev_007_e_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-e/summary"
	if ! printf '%s\n' "$ev_007_e_check_output" | jq -e '
		any(.claims[]; .id == "CRA-DEP-AXIOS-PIN" and .status == "fail")
		and any(.claims[];
			.id == "CRA-DEP-AXIOS-PIN"
			and any(.checks[]; .check == "dep_ban" and .status == "fail"
				and (.detail | test("banned pin")))
		)
	' >/dev/null; then
		echo "EV-007-E TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_e_check_status"
	if [ "$ev_007_e_check_status" -eq 0 ]; then
		echo "EV-007-E TEST STEPS 2"
		return 1
	fi
}

ev_007_f() {
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
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-F SETUP 2"
		return 1
	fi
	ev_007_f_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_007_f_setup_status=$?
	printf '%s\n' "$ev_007_f_setup_output"
	if [ "$ev_007_f_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_f_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "EV-007-F SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-F SETUP 4"
		return 1
	fi
	printf '%s\n' '' '-----BEGIN RSA PRIVATE KEY-----' 'fixture-only' '-----END RSA PRIVATE KEY-----' >> SECURITY.md
	if ! grep -F -- '-----BEGIN RSA PRIVATE KEY-----' SECURITY.md ||
		! git status --porcelain | grep -Fq 'SECURITY.md'; then
		echo "EV-007-F SETUP 5"
		return 1
	fi
	install_house_secret_paths

	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-f"
	ev_007_f_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-f/summary")
	ev_007_f_check_status=$?
	printf '%s\n' "$ev_007_f_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-f/summary"
	if ! printf '%s\n' "$ev_007_f_check_output" | jq -e '
		any(.claims[]; .id == "HOUSE-SECRET-PATHS" and .status == "fail")
	' >/dev/null; then
		echo "EV-007-F TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_f_check_status"
	if [ "$ev_007_f_check_status" -eq 0 ]; then
		echo "EV-007-F TEST STEPS 2"
		return 1
	fi
}

ev_007_g() {
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
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-G SETUP 2"
		return 1
	fi
	ev_007_g_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R6 --commit)
	ev_007_g_setup_status=$?
	printf '%s\n' "$ev_007_g_setup_output"
	if [ "$ev_007_g_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_g_setup_output" | grep -Fq "R6 — stale fresh/owned fixture docs"; then
		echo "EV-007-G SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-G SETUP 4"
		return 1
	fi
	if ! test -f docs/review-log.md || ! test -f docs/owned-policy.md; then
		echo "EV-007-G SETUP 5"
		return 1
	fi
	ev_007_g_log=$(git log -1 --format='%ae %aI' -- docs/review-log.md)
	printf '%s\n' "$ev_007_g_log"
	if ! printf '%s\n' "$ev_007_g_log" | grep -q '^owner@example.com 2022-01-01T00:00:00'; then
		echo "EV-007-G SETUP 6"
		return 1
	fi
	install_fix_fresh_review

	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-g"
	ev_007_g_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-g/summary")
	ev_007_g_check_status=$?
	printf '%s\n' "$ev_007_g_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-g/summary"
	if ! printf '%s\n' "$ev_007_g_check_output" | jq -e '
		any(.claims[]; .id == "FIX-FRESH-REVIEW" and .status == "fail")
	' >/dev/null; then
		echo "EV-007-G TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_g_check_status"
	if [ "$ev_007_g_check_status" -eq 0 ]; then
		echo "EV-007-G TEST STEPS 2"
		return 1
	fi
}

ev_007_h() {
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
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-007-H SETUP 2"
		return 1
	fi
	ev_007_h_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R7 --commit)
	ev_007_h_setup_status=$?
	printf '%s\n' "$ev_007_h_setup_output"
	if [ "$ev_007_h_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_h_setup_output" | grep -Fq "R7 — wrong-author fresh/owned fixture docs"; then
		echo "EV-007-H SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-H SETUP 4"
		return 1
	fi
	if ! test -f docs/review-log.md || ! test -f docs/owned-policy.md; then
		echo "EV-007-H SETUP 5"
		return 1
	fi
	ev_007_h_log=$(git log -1 --format='%ae %aI' -- docs/owned-policy.md)
	printf '%s\n' "$ev_007_h_log"
	if ! printf '%s\n' "$ev_007_h_log" | grep -q '^wrong@example.com 2026-09-13T12:00:00'; then
		echo "EV-007-H SETUP 6"
		return 1
	fi
	install_fix_owned_policy

	mkdir -p "$CURBPACK_ROOT/tmp/ev-007-h"
	ev_007_h_check_output=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-007-h/summary")
	ev_007_h_check_status=$?
	printf '%s\n' "$ev_007_h_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-007-h/summary"
	if ! printf '%s\n' "$ev_007_h_check_output" | jq -e '
		any(.claims[]; .id == "FIX-OWNED-POLICY" and .status == "fail")
	' >/dev/null; then
		echo "EV-007-H TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_h_check_status"
	if [ "$ev_007_h_check_status" -eq 0 ]; then
		echo "EV-007-H TEST STEPS 2"
		return 1
	fi
}

ev_008_a() {
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
	ev_008_a_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_008_a_setup_status=$?
	printf '%s\n' "$ev_008_a_setup_output"
	if [ "$ev_008_a_setup_status" -ne 0 ]; then
		echo "EV-008-A SETUP 3"
		return 1
	fi
	# Both targets absent — two Claims, ALPHA-then-BETA vs BETA-then-ALPHA load order.
	mkdir -p "$CURBPACK_ROOT/tmp/ev-008-a"
	install_ev008_rule_order_claims alpha-beta
	ev_008_a_ab=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-008-a/summary-ab")
	ev_008_a_ab_status=$?
	printf '%s\n' "$ev_008_a_ab" >"$CURBPACK_ROOT/tmp/ev-008-a/ab.json"
	cat "$CURBPACK_ROOT/tmp/ev-008-a/summary-ab"
	install_ev008_rule_order_claims beta-alpha
	ev_008_a_ba=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-008-a/summary-ba")
	ev_008_a_ba_status=$?
	printf '%s\n' "$ev_008_a_ba" >"$CURBPACK_ROOT/tmp/ev-008-a/ba.json"
	cat "$CURBPACK_ROOT/tmp/ev-008-a/summary-ba"
	if ! jq -n -e \
		--slurpfile ab "$CURBPACK_ROOT/tmp/ev-008-a/ab.json" \
		--slurpfile ba "$CURBPACK_ROOT/tmp/ev-008-a/ba.json" '
		($ab[0].claims | map({key: .id, value: .status}) | from_entries) as $a
		| ($ba[0].claims | map({key: .id, value: .status}) | from_entries) as $b
		| ($a == $b)
		and ($a["EV008-ALPHA"] == "fail")
		and ($a["EV008-BETA"] == "fail")
	'; then
		echo "EV-008-A TEST STEPS 1"
		return 1
	fi
	echo "$ev_008_a_ab_status $ev_008_a_ba_status"
	if [ "$ev_008_a_ab_status" -eq 0 ] || [ "$ev_008_a_ba_status" -eq 0 ]; then
		echo "EV-008-A TEST STEPS 2"
		return 1
	fi
}

ev_008_b() {
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "EV-008-B SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "EV-008-B SETUP 1"
		return 1
	fi
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "EV-008-B SETUP 2"
		return 1
	fi
	ev_008_b_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	ev_008_b_setup_status=$?
	printf '%s\n' "$ev_008_b_setup_output"
	if [ "$ev_008_b_setup_status" -ne 0 ]; then
		echo "EV-008-B SETUP 3"
		return 1
	fi
	mkdir -p "$CURBPACK_ROOT/tmp/ev-008-b"
	install_ev008_file_order_claim alpha-beta
	ev_008_b_ab=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-008-b/summary-ab")
	ev_008_b_ab_status=$?
	printf '%s\n' "$ev_008_b_ab" >"$CURBPACK_ROOT/tmp/ev-008-b/ab.json"
	cat "$CURBPACK_ROOT/tmp/ev-008-b/summary-ab"
	install_ev008_file_order_claim beta-alpha
	ev_008_b_ba=$(run_studio_packs_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-008-b/summary-ba")
	ev_008_b_ba_status=$?
	printf '%s\n' "$ev_008_b_ba" >"$CURBPACK_ROOT/tmp/ev-008-b/ba.json"
	cat "$CURBPACK_ROOT/tmp/ev-008-b/summary-ba"
	# Same Claim id, both fail; missing-path set in detail is order-independent.
	if ! jq -n -e \
		--slurpfile ab "$CURBPACK_ROOT/tmp/ev-008-b/ab.json" \
		--slurpfile ba "$CURBPACK_ROOT/tmp/ev-008-b/ba.json" '
		($ab[0].claims[0]) as $a
		| ($ba[0].claims[0]) as $b
		| ($a.id == "EV008-BOTH-PATHS")
		and ($b.id == "EV008-BOTH-PATHS")
		and ($a.status == "fail")
		and ($b.status == "fail")
		and ($a.checks[0].status == "fail")
		and ($b.checks[0].status == "fail")
		and (($a.checks[0].detail | split("; ") | sort)
			== ($b.checks[0].detail | split("; ") | sort))
		and ($a.checks[0].detail | test("ev008-alpha"))
		and ($a.checks[0].detail | test("ev008-beta"))
	'; then
		echo "EV-008-B TEST STEPS 1"
		return 1
	fi
	echo "$ev_008_b_ab_status $ev_008_b_ba_status"
	if [ "$ev_008_b_ab_status" -eq 0 ] || [ "$ev_008_b_ba_status" -eq 0 ]; then
		echo "EV-008-B TEST STEPS 2"
		return 1
	fi
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
	ev_009_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R5 --commit)
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
	install_house_claims

	# TEST STEPS 1 — three house claims pass. Summary includes "claims 3 exit 0".
	mkdir -p "$CURBPACK_ROOT/tmp/ev-009"
	ev_009_check_output=$(run_house_curbcheck_json 2>"$CURBPACK_ROOT/tmp/ev-009/summary")
	ev_009_check_status=$?
	printf '%s\n' "$ev_009_check_output"
	cat "$CURBPACK_ROOT/tmp/ev-009/summary"
	if ! grep -Fq "claims 3 exit 0" "$CURBPACK_ROOT/tmp/ev-009/summary" ||
		! printf '%s\n' "$ev_009_check_output" | jq -e '
			(([.claims[].id] | sort) == [
				"HOUSE-ANTI-PLACEHOLDER","HOUSE-SECURITY-MD","HOUSE-SECURITY-TXT"
			])
			and all(.claims[]; .status == "pass")
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
