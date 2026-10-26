#!/bin/sh

# PK-001 has no execution procedure. The runner treats it as a reference to EV-001.

# return 0 PASS, 1 FAIL, 2 MANUAL/TBD/BLOCKED/OUTSIDE (runner classifies from the log)

pk_002_a() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_002_b() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_003_not_pf01_pass() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_003_a() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_003_b() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_003_c() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_003_d() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_004() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}

pk_005() {
	echo "outside: PK needs old pack.json mutate fixtures that are not Packs v2; old curbpack observation is not used"
	return 2
}
