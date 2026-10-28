#!/bin/sh

# PK-001 has no execution procedure. The runner treats it as a reference to EV-001.
# PK mutate/pack.json cases are outside Packs v2 (see suites/PK.md). Do not invent
# a pass from the old curbpack observation.

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED (runner classifies from the log)

pk_002_a() {
	echo "PK-002-A: Blocked. Pack mutate cases are outside Packs v2. The case cannot be run. Do not run this variant."
	return 2
}

pk_002_b() {
	echo "PK-002-B: Blocked. Pack mutate cases are outside Packs v2. The case cannot be run. Do not run this variant."
	return 2
}

pk_003_a() {
	echo "PK-003-A: Blocked. Pack mutate cases are outside Packs v2. The case cannot be run. Do not run this variant."
	return 2
}

pk_003_b() {
	echo "PK-003-B: Blocked. Pack mutate cases are outside Packs v2. The case cannot be run. Do not run this variant."
	return 2
}

pk_003_c() {
	echo "PK-003-C: Blocked. Pack mutate cases are outside Packs v2. The case cannot be run. Do not run this variant."
	return 2
}

pk_003_d() {
	echo "PK-003-D: Not specified yet. Do not run this variant. No version-selection syntax exists."
	return 2
}

pk_004() {
	echo "PK-004: Blocked. Unsupported-check pack mutate is outside Packs v2. The case cannot be run. Do not run this case."
	return 2
}

pk_005() {
	echo "PK-005: Blocked. Invalid-regex pack mutate is outside Packs v2. The case cannot be run. Do not run this case."
	return 2
}
