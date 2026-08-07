package doctor

import (
	"strings"
	"testing"
)

func TestClaimSafe(t *testing.T) {
	if !strings.Contains(Claim, "not a conformity") {
		t.Fatalf("claim must be claim-safe: %q", Claim)
	}
}
