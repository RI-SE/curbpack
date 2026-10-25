#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
rl_001() {
	echo "RL-001: Not specified yet. Do not run this case."
	return 2
}

rl_002() {
	echo "RL-002: Not specified yet. Do not run this case."
	return 2
}

rl_003() {
	echo "RL-003: Not specified yet. Do not run this case."
	return 2
}

rl_004() {
	# SETUP 1–2 not reached: assignment does not name tag, source commit, and shipped artefact.
	# SETUP 3
	echo "RL-004 SETUP 3: the case cannot be run. This case does not invent a tag, commit, or artefact."
	return 2
}

rl_005() {
	echo "RL-005: Not specified yet. Do not run this case."
	return 2
}
