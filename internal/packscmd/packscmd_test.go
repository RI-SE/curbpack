package packscmd_test

import (
	"os"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/packscmd"
)

func TestUpdateRequiresSHA256Pin(t *testing.T) {
	t.Setenv("CYBERREADY_PACKS_URL", "https://example.invalid/bundle.json")
	t.Setenv("CYBERREADY_PACKS_SHA256", "")
	err := packscmd.UpdateStub()
	if err == nil {
		t.Fatal("expected refuse without sha256 pin")
	}
	if !strings.Contains(err.Error(), "CYBERREADY_PACKS_SHA256") {
		t.Fatalf("got %v", err)
	}
}

func TestUpdateOfflineInstructions(t *testing.T) {
	t.Setenv("CYBERREADY_PACKS_URL", "")
	t.Setenv("CYBERREADY_PACKS_SHA256", "")
	// Capture via ensuring no panic / nil error when URL unset.
	if err := packscmd.UpdateStub(); err != nil {
		t.Fatal(err)
	}
	_ = os.Getenv // keep os used for clarity in parallel tests
}
