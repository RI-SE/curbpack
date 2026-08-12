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

func TestErrMissingBinaryMessage(t *testing.T) {
	err := &ErrMissingBinary{Hint: "curl … | sh"}
	if !strings.Contains(err.Error(), "reinstall") {
		t.Fatalf("expected reinstall hint: %v", err)
	}
	if !strings.Contains(err.Error(), "curl") {
		t.Fatalf("expected hint in error: %v", err)
	}
}

func TestInstallHealthHelpers(t *testing.T) {
	// Run without repair should not panic / should return nil.
	if err := Run(Options{Version: "0.5.2", Repair: false}); err != nil {
		t.Fatalf("doctor: %v", err)
	}
}
