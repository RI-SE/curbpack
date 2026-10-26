#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED/OUTSIDE (runner classifies from the log)

fs_001() {
	echo "outside: FS needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

fs_002() {
	echo "FS-002: Not specified yet. Do not run this case."
	return 2
}

fs_003() {
	echo "FS-003: Not specified yet. Do not run this case."
	return 2
}

fs_004() {
	echo "FS-004: Not specified yet. Do not run this case."
	return 2
}

fs_005() {
	echo "FS-005: Not specified yet. Do not run this case."
	return 2
}

fs_006() {
	echo "FS-006: Not specified yet. Do not run this case."
	return 2
}

fs_007() {
	echo "FS-007: Not specified yet. Do not run this case."
	return 2
}
