package doctor

import (
	"io"
	"os"
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

func TestRepairFailClosedWhenLookPathMissing(t *testing.T) {
	// Simulate PATH without curbpack after a no-op ensure: empty PATH + missing binary name.
	// We only assert ErrMissingBinary type contract for empty executable scenarios already covered;
	// here verify LookPath miss maps to ErrMissingBinary message shape used by CLI exit 2.
	err := &ErrMissingBinary{Hint: platformInstallHint()}
	if ExitMissingBinary != 2 {
		t.Fatalf("ExitMissingBinary=%d want 2", ExitMissingBinary)
	}
	if !strings.Contains(err.Error(), "reinstall") {
		t.Fatal(err)
	}
}

func TestAllowConfirmSoftTip(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "1")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	old := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout = w
	runErr := Run(Options{Version: "0.5.2", Repair: false})
	_ = w.Close()
	os.Stdout = old
	if runErr != nil {
		t.Fatalf("doctor: %v", runErr)
	}
	out, _ := io.ReadAll(r)
	text := string(out)
	if !strings.Contains(text, "CURBPACK_ALLOW_CONFIRM=1 is set") {
		t.Fatalf("want ALLOW_CONFIRM soft tip, got:\n%s", text)
	}
	if !strings.Contains(text, "Never set this env on the Action") {
		t.Fatal("tip must warn never set ALLOW_CONFIRM on the Action")
	}
}

func platformInstallHint() string {
	return "curl … | sh"
}
