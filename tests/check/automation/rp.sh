#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)
# RP share/review cases are outside (see suites/RP.md). Studio curbcheck does
# not write a Review Pack. Do not invent a pass from the old curbpack observation.

rp_001() {
	echo "RP-001: Blocked. Review Pack output is outside this runner. The case cannot be run. Do not run this case."
	return 2
}

rp_002() {
	echo "RP-002: Blocked. Review Pack output is outside this runner. The case cannot be run. Do not run this case."
	return 2
}

rp_003() {
	echo "RP-003: Blocked. Review Pack share/review is outside this runner. The case cannot be run. Do not run this case."
	return 2
}

rp_004() {
	echo "RP-004: Blocked. Review Pack share/review is outside this runner. The case cannot be run. Do not run this case."
	return 2
}

rp_005() {
	echo "RP-005: Blocked. Review Pack share/review is outside this runner. The case cannot be run. Do not run this case."
	return 2
}

rp_006() {
	echo "RP-006: Not specified yet. Do not run this case."
	return 2
}

rp_007() {
	echo "RP-007: Not specified yet. Do not run this case."
	return 2
}
