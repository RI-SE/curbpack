#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
# FS pack mutate cases are outside Packs v2 (see suites/FS.md).

fs_001() {
	echo "FS-001: Blocked. Path-traversal pack mutate is outside Packs v2. The case cannot be run. Do not run this case."
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
