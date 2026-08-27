package claimid_test

import (
	"testing"

	"github.com/afelin/curbpack/internal/claimid"
)

func TestIsClaimProvisional(t *testing.T) {
	cases := []struct {
		in   string
		want bool
	}{
		{"HOUSE-SECURITY-MD", true},
		{"CRA-ANNEX-VII-RISK", true},
		{"MD-SW-CLASS", true},
		{"ACME-SEC-1", true},
		{"MEDTECH-FOO", true},
		{"RFC-2119", false},
		{"SHA-256", false},
		{"SPDX-License-Identifier", false},
		{"SPDX-Apache-2.0", false},
		{"not-a-claim", false},
		{"", false},
	}
	for _, tc := range cases {
		if got := claimid.IsClaim(tc.in); got != tc.want {
			t.Fatalf("%q IsClaim=%v want %v", tc.in, got, tc.want)
		}
	}
}

func TestFormatDrop(t *testing.T) {
	got := claimid.FormatDrop("FOO-BAR", claimid.DropUnknownNamespace)
	if got != "FOO-BAR [unknown-claim-namespace]" {
		t.Fatalf("got %q", got)
	}
}
