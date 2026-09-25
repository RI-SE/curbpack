#!/bin/sh

# return 0 PASS, 1 FAIL, 2 SKIP
cl_001() {
	echo "CL-001: TEST STEPS 1 requires human review for implied overclaim language. Do not run this case automatically."
	return 2
}

cl_002() {
	echo "CL-002: R1 recorded. TEST STEPS 5 requires human comparison of boundary statements. Do not run this case automatically."
	return 2
}

cl_003() {
	echo "CL-003: Not specified yet. Do not run this case."
	return 2
}

cl_004() {
	echo "CL-004: Not specified yet. Do not run this case."
	return 2
}
