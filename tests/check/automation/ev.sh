#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED/OUTSIDE (runner classifies from the log)

ev_001() {
	if ! studio_begin EV-001; then
		return 1
	fi
	ev_001_setup_output=$(studio_setup R1 --commit)
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
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-001 SETUP 4"
		return 1
	fi

	studio_claims_seven
	out=$REFERENCE_PRODUCT_ROOT/run-result.json
	ev_001_check_output=$(studio_curbcheck "$out")
	ev_001_check_status=$?
	printf '%s\n' "$ev_001_check_output"
	if ! printf '%s\n' "$ev_001_check_output" | grep -Fq 'claims 7 exit 0'; then
		echo "EV-001 TEST STEPS 1"
		return 1
	fi
	for id in \
		CRA-ANNEX-VII-MANUAL \
		CRA-ANNEX-VII-RISK \
		CRA-ANNEX-VII-SUPPORT \
		CRA-ART14-PATH \
		HOUSE-ANTI-PLACEHOLDER \
		HOUSE-SECURITY-MD \
		HOUSE-SECURITY-TXT
	do
		if ! claim_is "$out" "$id" pass; then
			echo "EV-001 TEST STEPS 1"
			return 1
		fi
	done
	echo "$ev_001_check_status"
	if [ "$ev_001_check_status" -ne 0 ]; then
		echo "EV-001 TEST STEPS 2"
		return 1
	fi
}

ev_002() {
	if ! studio_begin EV-002; then
		return 1
	fi
	ev_002_setup_output=$(studio_setup R2 --commit)
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
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-002 SETUP 4"
		return 1
	fi
	if ls SECURITY.md; then
		echo "EV-002 SETUP 5"
		return 1
	fi

	studio_claims_seven
	out=$REFERENCE_PRODUCT_ROOT/run-result.json
	ev_002_check_output=$(studio_curbcheck "$out")
	ev_002_check_status=$?
	printf '%s\n' "$ev_002_check_output"
	if ! claim_is "$out" HOUSE-SECURITY-MD fail; then
		echo "EV-002 TEST STEPS 1"
		return 1
	fi
	echo "$ev_002_check_status"
	if [ "$ev_002_check_status" -eq 0 ]; then
		echo "EV-002 TEST STEPS 2"
		return 1
	fi
}

ev_003() {
	echo "outside: MD-SW-CLASS claim does not exist in the Studio fixture; old curbpack observation is not used"
	return 2
}

ev_004() {
	echo "outside: unreadable target raises PermissionError in contents; old curbpack stderr observation is not used"
	return 2
}

ev_005() {
	echo "outside: needs --diff / skipped_rules / .curbpack cache fields Studio does not write; old curbpack observation is not used"
	return 2
}

ev_006() {
	# R4 token-only no longer fails Studio's placeholder probe (no scaffold-overlap).
	# Stimulus for the current probe: append a listed placeholder token after R4.
	if ! studio_begin EV-006; then
		return 1
	fi
	ev_006_setup_output=$(studio_setup R4 --commit)
	ev_006_setup_status=$?
	printf '%s\n' "$ev_006_setup_output"
	if [ "$ev_006_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_006_setup_output" | grep -Fq "R4 — token-only house-policy tree"; then
		echo "EV-006 SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-006 SETUP 4"
		return 1
	fi
	if ! grep -F '"name": "acme-widget"' package.json; then
		echo "EV-006 SETUP 5"
		return 1
	fi
	printf '\nTODO replace contact details\n' >>SECURITY.md
	if ! grep -Fq 'TODO replace contact details' SECURITY.md; then
		echo "EV-006 SETUP 6"
		return 1
	fi

	studio_claims_house
	out=$REFERENCE_PRODUCT_ROOT/run-result.json
	ev_006_check_output=$(studio_curbcheck "$out")
	ev_006_check_status=$?
	printf '%s\n' "$ev_006_check_output"
	if ! claim_is "$out" HOUSE-ANTI-PLACEHOLDER fail; then
		echo "EV-006 TEST STEPS 1"
		return 1
	fi
	echo "$ev_006_check_status"
	if [ "$ev_006_check_status" -eq 0 ]; then
		echo "EV-006 TEST STEPS 2"
		return 1
	fi
}

ev_007_a() {
	if ! studio_begin EV-007-A; then
		return 1
	fi
	ev_007_a_setup_output=$(studio_setup R2 --commit)
	ev_007_a_setup_status=$?
	printf '%s\n' "$ev_007_a_setup_output"
	if [ "$ev_007_a_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_a_setup_output" | grep -Fq "R2 — missing required file"; then
		echo "EV-007-A SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-A SETUP 4"
		return 1
	fi
	if ls SECURITY.md; then
		echo "EV-007-A SETUP 5"
		return 1
	fi

	studio_claims_seven
	out=$REFERENCE_PRODUCT_ROOT/run-result.json
	ev_007_a_check_output=$(studio_curbcheck "$out")
	ev_007_a_check_status=$?
	printf '%s\n' "$ev_007_a_check_output"
	if ! claim_is "$out" HOUSE-SECURITY-MD fail; then
		echo "EV-007-A TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_a_check_status"
	if [ "$ev_007_a_check_status" -eq 0 ]; then
		echo "EV-007-A TEST STEPS 2"
		return 1
	fi
}

ev_007_b() {
	echo "outside: MD-SW-CLASS claim does not exist in the Studio fixture; old curbpack observation is not used"
	return 2
}

ev_007_c() {
	if ! studio_begin EV-007-C; then
		return 1
	fi
	ev_007_c_setup_output=$(studio_setup R4 --commit)
	ev_007_c_setup_status=$?
	printf '%s\n' "$ev_007_c_setup_output"
	if [ "$ev_007_c_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_007_c_setup_output" | grep -Fq "R4 — token-only house-policy tree"; then
		echo "EV-007-C SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-007-C SETUP 4"
		return 1
	fi
	printf '\nTODO replace contact details\n' >>SECURITY.md
	if ! grep -Fq 'TODO replace contact details' SECURITY.md; then
		echo "EV-007-C SETUP 5"
		return 1
	fi

	studio_claims_house
	out=$REFERENCE_PRODUCT_ROOT/run-result.json
	ev_007_c_check_output=$(studio_curbcheck "$out")
	ev_007_c_check_status=$?
	printf '%s\n' "$ev_007_c_check_output"
	if ! claim_is "$out" HOUSE-ANTI-PLACEHOLDER fail; then
		echo "EV-007-C TEST STEPS 1"
		return 1
	fi
	echo "$ev_007_c_check_status"
	if [ "$ev_007_c_check_status" -eq 0 ]; then
		echo "EV-007-C TEST STEPS 2"
		return 1
	fi
}

ev_007_d() {
	echo "outside: needs dep_ban / HOUSE-DEP-AXIOS-PIN; dep_ban command is not installed"
	return 2
}

ev_007_e() {
	echo "outside: needs dep_ban / CRA-DEP-AXIOS-PIN; dep_ban command is not installed"
	return 2
}

ev_007_f() {
	echo "outside: HOUSE-SECRET-PATHS claim fails on absent secret paths before pattern; old curbpack pattern observation is not used"
	return 2
}

ev_007_g() {
	echo "outside: missing checkers fresh/owned/git_signed/git_signer; not implemented for this case"
	return 2
}

ev_007_h() {
	echo "outside: missing checkers fresh/owned/git_signed/git_signer; not implemented for this case"
	return 2
}

ev_008_a() {
	echo "outside: EV-008 special rule-order packs are not rewritten to Packs v2; old curbpack observation is not used"
	return 2
}

ev_008_b() {
	echo "EV-008-B: Blocked. Missing test seam. The case cannot be run. Do not run this variant."
	return 2
}

ev_009() {
	if ! studio_begin EV-009; then
		return 1
	fi
	ev_009_setup_output=$(studio_setup R5 --commit)
	ev_009_setup_status=$?
	printf '%s\n' "$ev_009_setup_output"
	if [ "$ev_009_setup_status" -ne 0 ] ||
		! printf '%s\n' "$ev_009_setup_output" | grep -Fq "R5 — thin rule-satisfying house-policy tree"; then
		echo "EV-009 SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "EV-009 SETUP 4"
		return 1
	fi
	if ! grep -F '"name": "demo-app"' package.json; then
		echo "EV-009 SETUP 5"
		return 1
	fi
	if ! grep -F 'warehouse controller firmware' SECURITY.md; then
		echo "EV-009 SETUP 6"
		return 1
	fi
	if test -e src/app.py; then
		echo "EV-009 SETUP 7"
		return 1
	fi

	studio_claims_house
	out=$REFERENCE_PRODUCT_ROOT/run-result.json
	ev_009_check_output=$(studio_curbcheck "$out")
	ev_009_check_status=$?
	printf '%s\n' "$ev_009_check_output"
	for id in HOUSE-ANTI-PLACEHOLDER HOUSE-SECURITY-MD HOUSE-SECURITY-TXT; do
		if ! claim_is "$out" "$id" pass; then
			echo "EV-009 TEST STEPS 1"
			return 1
		fi
	done
	if ! printf '%s\n' "$ev_009_check_output" | grep -Fq 'claims 3 exit 0'; then
		echo "EV-009 TEST STEPS 1"
		return 1
	fi
	echo "$ev_009_check_status"
	if [ "$ev_009_check_status" -ne 0 ]; then
		echo "EV-009 TEST STEPS 2"
		return 1
	fi
}
