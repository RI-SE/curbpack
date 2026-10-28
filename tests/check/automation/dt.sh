#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)
# Observation is claims[].status in the Packs v2 run-result JSON.

_dt_r1_setup() {
	_id=$1
	if [ -n "${CURBPACK_ROOT:-}" ]; then
		if ! cd "$CURBPACK_ROOT"; then
			echo "$_id SETUP 1"
			return 1
		fi
	fi
	if ! . tmp/verification-run.sh; then
		echo "$_id SETUP 1"
		return 1
	fi
	if ! cd "$REFERENCE_PRODUCT_ROOT" || [ "$(pwd)" != "$REFERENCE_PRODUCT_ROOT" ]; then
		echo "$_id SETUP 2"
		return 1
	fi
	_setup_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R1 --commit)
	_setup_status=$?
	printf '%s\n' "$_setup_output"
	if [ "$_setup_status" -ne 0 ] ||
		! printf '%s\n' "$_setup_output" | grep -Fq "R1 — starting Glucose Log product content" ||
		! printf '%s\n' "$_setup_output" | grep -Fq "## Classification Rationale" ||
		! printf '%s\n' "$_setup_output" | grep -Fq "dependency maps in \`package.json\` are empty" ||
		! printf '%s\n' "$_setup_output" | grep -Fq "contain no banned axios pin"; then
		echo "$_id SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "$_id SETUP 4"
		return 1
	fi
	install_pf01
	return 0
}

_dt_claim_map() {
	jq -c '[.claims[] | {id, status}] | sort_by(.id)' "$1"
}

_dt_all_pass() {
	jq -e 'all(.claims[]; .status == "pass") and (.claims | length) == 7' "$1" >/dev/null
}

dt_001() {
	if ! _dt_r1_setup DT-001; then
		return 1
	fi
	mkdir -p "$CURBPACK_ROOT/tmp/dt-001"
	if [ ! -d "$CURBPACK_ROOT/tmp/dt-001" ] || [ -e "$CURBPACK_ROOT/tmp/dt-001/.git" ]; then
		echo "DT-001 SETUP 5"
		return 1
	fi

	# TEST STEPS 1 — twenty identical runs, every claim pass, exit 0.
	i=1
	while [ "$i" -le 20 ]; do
		CURBCHECK_OUT="$CURBPACK_ROOT/tmp/dt-001/run-$i.json" run_curbcheck_json >/dev/null
		echo $? >"$CURBPACK_ROOT/tmp/dt-001/run-$i.exit"
		if [ ! -f "$CURBPACK_ROOT/tmp/dt-001/run-$i.json" ] ||
			[ "$(cat "$CURBPACK_ROOT/tmp/dt-001/run-$i.exit")" != "0" ] ||
			! _dt_all_pass "$CURBPACK_ROOT/tmp/dt-001/run-$i.json"; then
			echo "DT-001 TEST STEPS 1"
			return 1
		fi
		i=$((i + 1))
	done

	# TEST STEPS 2 — claim-status maps identical across the 20 files.
	dt_001_map=$(_dt_claim_map "$CURBPACK_ROOT/tmp/dt-001/run-1.json")
	i=1
	while [ "$i" -le 20 ]; do
		if [ "$(_dt_claim_map "$CURBPACK_ROOT/tmp/dt-001/run-$i.json")" != "$dt_001_map" ]; then
			echo "DT-001 TEST STEPS 2"
			return 1
		fi
		i=$((i + 1))
	done
	printf 'claim-status map: %s\n' "$dt_001_map"
}

dt_002() {
	echo "DT-002: Not specified yet. Do not run this case."
	return 2
}

dt_003() {
	if ! _dt_r1_setup DT-003; then
		return 1
	fi
	mkdir -p "$CURBPACK_ROOT/tmp/dt-003"
	if [ ! -d "$CURBPACK_ROOT/tmp/dt-003" ] || [ -e "$CURBPACK_ROOT/tmp/dt-003/.git" ]; then
		echo "DT-003 SETUP 5"
		return 1
	fi

	CURBCHECK_OUT="$CURBPACK_ROOT/tmp/dt-003/r1.json" run_curbcheck_json >/dev/null
	echo $? >"$CURBPACK_ROOT/tmp/dt-003/r1.exit"
	if [ ! -f "$CURBPACK_ROOT/tmp/dt-003/r1.json" ] ||
		[ "$(cat "$CURBPACK_ROOT/tmp/dt-003/r1.exit")" != "0" ] ||
		! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "pass")' \
			"$CURBPACK_ROOT/tmp/dt-003/r1.json" >/dev/null; then
		echo "DT-003 SETUP 6"
		return 1
	fi
	# setup.sh R2 refuses a dirty tree; PF-01 files are untracked until removed.
	remove_pf01

	dt_003_r2_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R2 --commit)
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
	if ls SECURITY.md; then
		echo "DT-003 SETUP 9"
		return 1
	fi
	install_pf01

	# TEST STEPS 1 — HOUSE-SECURITY-MD fail after R2.
	CURBCHECK_OUT="$CURBPACK_ROOT/tmp/dt-003/r2.json" run_curbcheck_json >/dev/null
	dt_003_check_status=$?
	if [ ! -f "$CURBPACK_ROOT/tmp/dt-003/r2.json" ] ||
		! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")' \
			"$CURBPACK_ROOT/tmp/dt-003/r2.json" >/dev/null; then
		echo "DT-003 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$dt_003_check_status"
	if [ "$dt_003_check_status" -eq 0 ]; then
		echo "DT-003 TEST STEPS 2"
		return 1
	fi
	# TEST STEPS 3 — R1 pass vs R2 fail; maps differ.
	if ! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "pass")' \
		"$CURBPACK_ROOT/tmp/dt-003/r1.json" >/dev/null ||
		! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")' \
			"$CURBPACK_ROOT/tmp/dt-003/r2.json" >/dev/null; then
		echo "DT-003 TEST STEPS 3"
		return 1
	fi
	dt_003_r1_map=$(_dt_claim_map "$CURBPACK_ROOT/tmp/dt-003/r1.json")
	dt_003_r2_map=$(_dt_claim_map "$CURBPACK_ROOT/tmp/dt-003/r2.json")
	if [ "$dt_003_r1_map" = "$dt_003_r2_map" ]; then
		echo "DT-003 TEST STEPS 3"
		return 1
	fi
	printf 'r1 %s\nr2 %s\n' "$dt_003_r1_map" "$dt_003_r2_map"
}

dt_004() {
	if ! _dt_r1_setup DT-004; then
		return 1
	fi
	mkdir -p "$CURBPACK_ROOT/tmp/dt-004"
	if [ ! -d "$CURBPACK_ROOT/tmp/dt-004" ] || [ -e "$CURBPACK_ROOT/tmp/dt-004/.git" ]; then
		echo "DT-004 SETUP 5"
		return 1
	fi

	i=1
	while [ "$i" -le 20 ]; do
		CURBCHECK_OUT="$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" run_curbcheck_json >/dev/null
		echo $? >"$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.exit"
		if [ ! -f "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" ] ||
			[ "$(cat "$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.exit")" != "0" ] ||
			! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "pass")' \
				"$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" >/dev/null; then
			echo "DT-004 SETUP 6"
			return 1
		fi
		i=$((i + 1))
	done
	remove_pf01

	dt_004_r2_output=$(SUT=curbpack ./external_test/curbpack/setup.sh R2 --commit)
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
	if ls SECURITY.md; then
		echo "DT-004 SETUP 9"
		return 1
	fi
	install_pf01

	CURBCHECK_OUT="$CURBPACK_ROOT/tmp/dt-004/r2.json" run_curbcheck_json >/dev/null
	echo $? >"$CURBPACK_ROOT/tmp/dt-004/r2.exit"
	if [ ! -f "$CURBPACK_ROOT/tmp/dt-004/r2.json" ] ||
		[ "$(cat "$CURBPACK_ROOT/tmp/dt-004/r2.exit")" = "0" ] ||
		! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")' \
			"$CURBPACK_ROOT/tmp/dt-004/r2.json" >/dev/null; then
		echo "DT-004 SETUP 10"
		return 1
	fi

	# TEST STEPS 1 — twenty R1 runs: HOUSE-SECURITY-MD pass.
	i=1
	while [ "$i" -le 20 ]; do
		if ! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "pass")' \
			"$CURBPACK_ROOT/tmp/dt-004/r1-run-$i.json" >/dev/null; then
			echo "DT-004 TEST STEPS 1"
			return 1
		fi
		i=$((i + 1))
	done
	# TEST STEPS 2 — R2: HOUSE-SECURITY-MD fail.
	if ! jq -e 'any(.claims[]; .id == "HOUSE-SECURITY-MD" and .status == "fail")' \
		"$CURBPACK_ROOT/tmp/dt-004/r2.json" >/dev/null; then
		echo "DT-004 TEST STEPS 2"
		return 1
	fi
}
