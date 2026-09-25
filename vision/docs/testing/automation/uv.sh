#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
uv_001() {
	echo "UV-001: builder handoff. Do not simulate a builder. Do not run setup.sh."
	return 2
}

uv_002() {
	echo "UV-002: builder interpretation. Do not simulate a builder."
	return 2
}

uv_003() {
	echo "UV-003: builder handoff. Do not simulate a builder."
	return 2
}

uv_004() {
	echo "UV-004: Not specified yet. Do not run."
	return 2
}

uv_005() {
	echo "UV-005: Not specified yet. Do not run."
	return 2
}

uv_006() {
	echo "UV-006: Not specified yet. Do not run."
	return 2
}

uv_007() {
	echo "UV-007: Not specified yet. Do not run."
	return 2
}

uv_008() {
	echo "UV-008: Not specified yet. Do not run."
	return 2
}
