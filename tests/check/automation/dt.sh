#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED/OUTSIDE (runner classifies from the log)

dt_001() {
	if ! studio_begin DT-001; then
		return 1
	fi
	dt_001_setup_output=$(studio_setup R1 --commit)
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
	if [ -n "$(git status --porcelain)" ]; then
		echo "DT-001 SETUP 4"
		return 1
	fi
	mkdir -p "$STUDIO_ROOT/tmp/dt-001"
	if [ ! -d "$STUDIO_ROOT/tmp/dt-001" ] || [ -e "$STUDIO_ROOT/tmp/dt-001/.git" ]; then
		echo "DT-001 SETUP 5"
		return 1
	fi

	studio_claims_seven
	i=1
	while [ "$i" -le 20 ]; do
		out=$STUDIO_ROOT/tmp/dt-001/run-$i.json
		studio_curbcheck "$out" >"$STUDIO_ROOT/tmp/dt-001/run-$i.summary"
		echo $? >"$STUDIO_ROOT/tmp/dt-001/run-$i.exit"
		i=$((i + 1))
	done
	i=1
	while [ "$i" -le 20 ]; do
		out=$STUDIO_ROOT/tmp/dt-001/run-$i.json
		if [ ! -f "$out" ] ||
			[ "$(cat "$STUDIO_ROOT/tmp/dt-001/run-$i.exit")" != "0" ] ||
			[ "$(claim_status_map "$out")" != "$(claim_status_map "$STUDIO_ROOT/tmp/dt-001/run-1.json")" ]; then
			echo "DT-001 TEST STEPS 1"
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
				echo "DT-001 TEST STEPS 1"
				return 1
			fi
		done
		i=$((i + 1))
	done
	printf 'claim status map identical across 20 runs: true\n'
}

dt_002() {
	echo "DT-002: Not specified yet. Do not run this case."
	return 2
}

dt_003() {
	if ! studio_begin DT-003; then
		return 1
	fi
	dt_003_setup_output=$(studio_setup R1 --commit)
	dt_003_setup_status=$?
	printf '%s\n' "$dt_003_setup_output"
	if [ "$dt_003_setup_status" -ne 0 ] ||
		! printf '%s\n' "$dt_003_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "DT-003 SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "DT-003 SETUP 4"
		return 1
	fi
	mkdir -p "$STUDIO_ROOT/tmp/dt-003"
	studio_claims_seven
	studio_curbcheck "$STUDIO_ROOT/tmp/dt-003/r1.json" >"$STUDIO_ROOT/tmp/dt-003/r1.summary"
	echo $? >"$STUDIO_ROOT/tmp/dt-003/r1.exit"
	if [ "$(cat "$STUDIO_ROOT/tmp/dt-003/r1.exit")" != "0" ] ||
		! claim_is "$STUDIO_ROOT/tmp/dt-003/r1.json" HOUSE-SECURITY-MD pass; then
		echo "DT-003 SETUP 6"
		return 1
	fi

	# Restore and apply R2 on a fresh baseline.
	if ! studio_begin DT-003; then
		return 1
	fi
	dt_003_r2_output=$(studio_setup R2 --commit)
	dt_003_r2_status=$?
	printf '%s\n' "$dt_003_r2_output"
	if [ "$dt_003_r2_status" -ne 0 ] ||
		! printf '%s\n' "$dt_003_r2_output" | grep -Fq "R2 — missing required file"; then
		echo "DT-003 SETUP 7"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "DT-003 SETUP 8"
		return 1
	fi
	if ls SECURITY.md; then
		echo "DT-003 SETUP 9"
		return 1
	fi

	studio_claims_seven
	studio_curbcheck "$STUDIO_ROOT/tmp/dt-003/r2.json" >"$STUDIO_ROOT/tmp/dt-003/r2.summary"
	dt_003_check_status=$?
	echo "$dt_003_check_status" >"$STUDIO_ROOT/tmp/dt-003/r2.exit"
	if ! claim_is "$STUDIO_ROOT/tmp/dt-003/r2.json" HOUSE-SECURITY-MD fail; then
		echo "DT-003 TEST STEPS 1"
		return 1
	fi
	echo "$dt_003_check_status"
	if [ "$dt_003_check_status" -eq 0 ]; then
		echo "DT-003 TEST STEPS 2"
		return 1
	fi
	if ! claim_is "$STUDIO_ROOT/tmp/dt-003/r1.json" HOUSE-SECURITY-MD pass ||
		! claim_is "$STUDIO_ROOT/tmp/dt-003/r2.json" HOUSE-SECURITY-MD fail; then
		echo "DT-003 TEST STEPS 3"
		return 1
	fi
	r1_map=$(claim_status_map "$STUDIO_ROOT/tmp/dt-003/r1.json")
	r2_map=$(claim_status_map "$STUDIO_ROOT/tmp/dt-003/r2.json")
	if [ "$r1_map" = "$r2_map" ]; then
		echo "DT-003 TEST STEPS 3"
		return 1
	fi
}

dt_004() {
	if ! studio_begin DT-004; then
		return 1
	fi
	dt_004_setup_output=$(studio_setup R1 --commit)
	dt_004_setup_status=$?
	printf '%s\n' "$dt_004_setup_output"
	if [ "$dt_004_setup_status" -ne 0 ] ||
		! printf '%s\n' "$dt_004_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
		echo "DT-004 SETUP 3"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "DT-004 SETUP 4"
		return 1
	fi
	mkdir -p "$STUDIO_ROOT/tmp/dt-004"
	studio_claims_seven
	i=1
	while [ "$i" -le 20 ]; do
		out=$STUDIO_ROOT/tmp/dt-004/r1-run-$i.json
		studio_curbcheck "$out" >"$STUDIO_ROOT/tmp/dt-004/r1-run-$i.summary"
		echo $? >"$STUDIO_ROOT/tmp/dt-004/r1-run-$i.exit"
		i=$((i + 1))
	done
	i=1
	while [ "$i" -le 20 ]; do
		out=$STUDIO_ROOT/tmp/dt-004/r1-run-$i.json
		if [ "$(cat "$STUDIO_ROOT/tmp/dt-004/r1-run-$i.exit")" != "0" ] ||
			! claim_is "$out" HOUSE-SECURITY-MD pass; then
			echo "DT-004 SETUP 6"
			return 1
		fi
		i=$((i + 1))
	done

	if ! studio_begin DT-004; then
		return 1
	fi
	dt_004_r2_output=$(studio_setup R2 --commit)
	dt_004_r2_status=$?
	printf '%s\n' "$dt_004_r2_output"
	if [ "$dt_004_r2_status" -ne 0 ] ||
		! printf '%s\n' "$dt_004_r2_output" | grep -Fq "R2 — missing required file"; then
		echo "DT-004 SETUP 7"
		return 1
	fi
	if [ -n "$(git status --porcelain)" ]; then
		echo "DT-004 SETUP 8"
		return 1
	fi
	if ls SECURITY.md; then
		echo "DT-004 SETUP 9"
		return 1
	fi

	studio_claims_seven
	studio_curbcheck "$STUDIO_ROOT/tmp/dt-004/r2.json" >"$STUDIO_ROOT/tmp/dt-004/r2.summary"
	echo $? >"$STUDIO_ROOT/tmp/dt-004/r2.exit"
	if [ "$(cat "$STUDIO_ROOT/tmp/dt-004/r2.exit")" = "0" ] ||
		! claim_is "$STUDIO_ROOT/tmp/dt-004/r2.json" HOUSE-SECURITY-MD fail; then
		echo "DT-004 SETUP 10"
		return 1
	fi

	i=1
	while [ "$i" -le 20 ]; do
		if ! claim_is "$STUDIO_ROOT/tmp/dt-004/r1-run-$i.json" HOUSE-SECURITY-MD pass; then
			echo "DT-004 TEST STEPS 1"
			return 1
		fi
		i=$((i + 1))
	done
	if ! claim_is "$STUDIO_ROOT/tmp/dt-004/r1-run-1.json" HOUSE-SECURITY-MD pass ||
		! claim_is "$STUDIO_ROOT/tmp/dt-004/r2.json" HOUSE-SECURITY-MD fail; then
		echo "DT-004 TEST STEPS 2"
		return 1
	fi
}
