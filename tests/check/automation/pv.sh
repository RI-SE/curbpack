#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)
# Packs v2 run-result fields: commit, worktree, packs[].{id,version,digest}, tool_version.
# Cases that need the old .curbpack cache layout are blocked (see suites/PV.md).

_pv_r1_setup() {
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
	_setup_output=$(./external_test/curbpack-studio/setup.sh R1 --commit)
	_setup_status=$?
	printf '%s\n' "$_setup_output"
	if [ "$_setup_status" -ne 0 ] ||
		! printf '%s\n' "$_setup_output" | grep -Fq "R1 — starting Glucose Log product content"; then
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

pv_001() {
	if ! _pv_r1_setup PV-001; then
		return 1
	fi
	# PF-01 files must be committed or worktree is dirty by construction.
	commit_pf01
	if [ -n "$(git status --porcelain)" ]; then
		echo "PV-001 SETUP 5"
		return 1
	fi
	pv_001_sha=$(git rev-parse HEAD)
	printf '%s\n' "$pv_001_sha"
	case $pv_001_sha in
		[0-9a-f][0-9a-f][0-9a-f][0-9a-f]*) ;;
		*)
			echo "PV-001 SETUP 5"
			return 1
			;;
	esac

	# TEST STEPS 1 — run-result.commit equals HEAD; worktree clean.
	mkdir -p "$CURBPACK_ROOT/tmp/pv-001"
	pv_001_check_output=$(CURBCHECK_OUT="$CURBPACK_ROOT/tmp/pv-001/run-result.json" run_curbcheck_json)
	pv_001_check_status=$?
	printf '%s\n' "$pv_001_check_output"
	if ! printf '%s\n' "$pv_001_check_output" | jq -e \
		--arg sha "$pv_001_sha" \
		'.commit == $sha and .worktree == "clean" and all(.claims[]; .status == "pass")' >/dev/null; then
		echo "PV-001 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_001_check_status"
	if [ "$pv_001_check_status" -ne 0 ]; then
		echo "PV-001 TEST STEPS 2"
		return 1
	fi
}

pv_002() {
	if ! _pv_r1_setup PV-002; then
		return 1
	fi
	pv_002_sha=$(git rev-parse HEAD)
	printf '%s\n' "$pv_002_sha"
	printf '\nPV-002 uncommitted marker\n' >>SECURITY.md
	pv_002_git=$(git status --porcelain)
	printf '%s\n' "$pv_002_git"
	if ! printf '%s\n' "$pv_002_git" | grep -Fq 'SECURITY.md'; then
		echo "PV-002 SETUP 7"
		return 1
	fi

	# TEST STEPS 1 — dirty worktree is recorded; HEAD commit still present.
	mkdir -p "$CURBPACK_ROOT/tmp/pv-002"
	pv_002_check_output=$(CURBCHECK_OUT="$CURBPACK_ROOT/tmp/pv-002/run-result.json" run_curbcheck_json)
	pv_002_check_status=$?
	printf '%s\n' "$pv_002_check_output"
	if ! printf '%s\n' "$pv_002_check_output" | jq -e \
		--arg sha "$pv_002_sha" \
		'.commit == $sha and .worktree == "dirty"' >/dev/null; then
		echo "PV-002 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2 — dirty tree may still exit 0 when checks pass.
	echo "$pv_002_check_status"
	if [ "$pv_002_check_status" -ne 0 ]; then
		echo "PV-002 TEST STEPS 2"
		return 1
	fi
}

pv_003() {
	if ! _pv_r1_setup PV-003; then
		return 1
	fi
	git checkout --detach HEAD
	if git symbolic-ref -q HEAD >/dev/null; then
		echo "PV-003 SETUP 6: HEAD still names a branch. The case cannot be run."
		return 1
	fi
	pv_003_sha=$(git rev-parse HEAD)
	printf '%s\n' "$pv_003_sha"

	# TEST STEPS 1 — commit is the detached SHA; JSON has no branch field.
	mkdir -p "$CURBPACK_ROOT/tmp/pv-003"
	pv_003_check_output=$(CURBCHECK_OUT="$CURBPACK_ROOT/tmp/pv-003/run-result.json" run_curbcheck_json)
	pv_003_check_status=$?
	printf '%s\n' "$pv_003_check_output"
	if ! printf '%s\n' "$pv_003_check_output" | jq -e \
		--arg sha "$pv_003_sha" \
		'.commit == $sha and (has("branch") | not) and all(.claims[]; .status == "pass")' >/dev/null; then
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
	if ! _pv_r1_setup PV-005; then
		return 1
	fi

	# TEST STEPS 1 — packs[] carries id, version, and directory digest.
	mkdir -p "$CURBPACK_ROOT/tmp/pv-005"
	pv_005_check_output=$(CURBCHECK_OUT="$CURBPACK_ROOT/tmp/pv-005/run-result.json" run_curbcheck_json)
	pv_005_check_status=$?
	printf '%s\n' "$pv_005_check_output"
	if ! printf '%s\n' "$pv_005_check_output" | jq -e '
		(([.packs[].id] | sort) == ["cra-baseline","house-policy","medtech-iec62304"])
		and all(.packs[];
			(.id | type) == "string" and (.id | length) > 0
			and (.version | type) == "string" and (.version | length) > 0
			and (.digest | type) == "string" and (.digest | length) == 64
		)
		and all(.claims[]; .status == "pass")
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
}

pv_006() {
	echo "PV-006: Blocked. Pack-byte substitution via mutate_pack is outside Packs v2 observation. The case cannot be run. Do not run this case."
	return 2
}

pv_007() {
	if ! _pv_r1_setup PV-007; then
		return 1
	fi

	# TEST STEPS 1 — tool and tool_version identify the checker build.
	mkdir -p "$CURBPACK_ROOT/tmp/pv-007"
	pv_007_check_output=$(CURBCHECK_OUT="$CURBPACK_ROOT/tmp/pv-007/run-result.json" run_curbcheck_json)
	pv_007_check_status=$?
	printf '%s\n' "$pv_007_check_output"
	if ! printf '%s\n' "$pv_007_check_output" | jq -e '
		.tool == "curbcheck"
		and (.tool_version | type) == "string" and (.tool_version | length) > 0
		and all(.claims[]; .status == "pass")
	' >/dev/null; then
		echo "PV-007 TEST STEPS 1"
		return 1
	fi
	# TEST STEPS 2
	echo "$pv_007_check_status"
	if [ "$pv_007_check_status" -ne 0 ]; then
		echo "PV-007 TEST STEPS 2"
		return 1
	fi
}
