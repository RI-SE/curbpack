#!/bin/sh

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED/OUTSIDE (runner classifies from the log)

pv_001() {
	echo "outside: needs old .curbpack cache fields (subject_commit / concurrency_control) that Studio does not write"
	return 2
}

pv_002() {
	echo "outside: needs old .curbpack cache fields (input_identity.files sha256) that Studio does not write"
	return 2
}

pv_003() {
	echo "outside: needs old .curbpack cache fields (concurrency_control) that Studio does not write"
	return 2
}

pv_004() {
	echo "PV-004: Not specified yet. Do not run this case."
	return 2
}

pv_005() {
	echo "outside: needs old .curbpack cache fields (input_identity.pack_sources) that Studio does not write"
	return 2
}

pv_006() {
	echo "outside: needs old .curbpack cache fields (comparison_key) that Studio does not write"
	return 2
}

pv_007() {
	echo "outside: needs old .curbpack cache fields (input_identity / latest_receipt) that Studio does not write"
	return 2
}
