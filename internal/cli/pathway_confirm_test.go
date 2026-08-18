package cli

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/pathway"
)

func TestRequireHumanConfirm_failClosedWithoutFlag(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	err := requireHumanConfirm(nil)
	if err == nil {
		t.Fatal("expected refuse without --i-am-human or env")
	}
	if !strings.Contains(err.Error(), "--i-am-human") {
		t.Fatalf("want --i-am-human hint, got %v", err)
	}
}

func TestRequireHumanConfirm_flag(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	if err := requireHumanConfirm([]string{"--i-am-human"}); err != nil {
		t.Fatal(err)
	}
}

func TestRequireHumanConfirm_env(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "1")
	if err := requireHumanConfirm(nil); err != nil {
		t.Fatal(err)
	}
}

func TestRequireHumanConfirm_envNotOne(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "true")
	if err := requireHumanConfirm(nil); err == nil {
		t.Fatal("only CURBPACK_ALLOW_CONFIRM=1 should allow")
	}
}

func TestRequireHumanConfirm_ignoresTTYAlone(t *testing.T) {
	// Document invariant: do not reopen TTY-alone path (agents often have a TTY).
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	if err := requireHumanConfirm([]string{}); err == nil {
		t.Fatal("TTY-alone must not authorize confirm")
	}
}

func TestConfirmProseStdout_NotGroundingOnMixedStub(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "1")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	dir := t.TempDir()
	writeCLIHouseConfirm(t, dir, packs.DefaultScaffoldBody("SECURITY.md"), "Contact: security@example.com\nPreferred-Languages: en\n")

	out := captureCLIStdout(t, func() {
		err := cmdPathwayConfirmProse(dir, nil)
		if err == nil || ExitCode(err) != ExitGates {
			t.Fatalf("want exit 1 informed-consent, got %v code=%d", err, ExitCode(err))
		}
		if !strings.Contains(err.Error(), "informed-consent") {
			t.Fatalf("want informed-consent, got %v", err)
		}
	})
	if !stdoutHasPrefix(out, "not-grounding: SECURITY.md (stub)") {
		t.Fatalf("want not-grounding on informed-consent refuse, got %q", out)
	}
	if stdoutHasPrefix(out, "grounding:") {
		t.Fatalf("refuse must not print grounding: lines, got %q", out)
	}
	if stdoutHasPrefix(out, "not-grounding: .well-known/security.txt") {
		t.Fatalf("independent security.txt must not be labeled not-grounding, got %q", out)
	}
}

func TestConfirmProseStdout_GroundingOnOK(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "1")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	dir := t.TempDir()
	writeCLIHouseConfirm(t, dir, `# Security

House policy reporting and response for this product.

Contact security@example.com with reproduction steps. We acknowledge within two business days.
`, "Contact: security@example.com\nPreferred-Languages: en\n")

	out := captureCLIStdout(t, func() {
		if err := cmdPathwayConfirmProse(dir, nil); err != nil {
			t.Fatalf("confirm-prose: %v", err)
		}
	})
	if !stdoutHasPrefix(out, "grounding: SECURITY.md (path)") {
		t.Fatalf("want grounding: SECURITY.md, got %q", out)
	}
	if !stdoutHasPrefix(out, "grounding: .well-known/security.txt (path)") {
		t.Fatalf("want grounding: security.txt, got %q", out)
	}
	if stdoutHasPrefix(out, "not-grounding:") {
		t.Fatalf("ok path must not print not-grounding:, got %q", out)
	}
}

func writeCLIHouseConfirm(t *testing.T, dir, security, txt string) {
	t.Helper()
	s := pathway.Seed{
		SchemaVersion: pathway.SchemaVersion,
		ProposedPacks: []string{"house-policy"},
		HumanTicks:    pathway.HumanTicks{PacksConfirmed: true},
		Claim:         pathway.ClaimFence,
	}
	if err := pathway.Write(dir, s); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".curbpack.json"), []byte(`{"packs":["house-policy"]}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte(security), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, ".well-known"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(dir, ".well-known", "security.txt"), []byte(txt), 0o644); err != nil {
		t.Fatal(err)
	}
}

func stdoutHasPrefix(out, prefix string) bool {
	for _, line := range strings.Split(out, "\n") {
		if strings.HasPrefix(strings.TrimSpace(line), prefix) {
			return true
		}
	}
	return false
}
