package githook

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCurrentPreCommitHasNoHeal(t *testing.T) {
	if strings.Contains(CurrentPreCommit, "--heal") {
		t.Fatal("current hook must not heal")
	}
	if strings.Contains(CurrentPreCommit, "\r") {
		t.Fatal("current hook must be LF-only")
	}
	if !strings.Contains(CurrentPreCommit, "exec curbpack check\n") {
		t.Fatal("current hook must exec curbpack check")
	}
}

func TestLegacyHealBodyPinsExactBytes(t *testing.T) {
	if !strings.Contains(LegacyHealPreCommitV052to054, "exec curbpack check --heal\n") {
		t.Fatal("legacy body must call check --heal")
	}
	if !strings.Contains(LegacyHealPreCommitV052to054, "—") {
		t.Fatal("legacy body must keep shipped unicode em dash")
	}
	if !strings.Contains(LegacyHealPreCommitV052to054, "⇒") {
		t.Fatal("legacy body must keep shipped unicode double arrow")
	}
	if Classify([]byte(LegacyHealPreCommitV052to054)) != KindLegacyHeal {
		t.Fatal("legacy constant must classify as KindLegacyHeal")
	}
	if Classify([]byte(CurrentPreCommit)) != KindCurrent {
		t.Fatal("current constant must classify as KindCurrent")
	}
	tweaked := strings.Replace(LegacyHealPreCommitV052to054, "fail commit", "FAIL COMMIT", 1)
	if Classify([]byte(tweaked)) != KindCustom {
		t.Fatal("any edit must classify as KindCustom")
	}
}

func TestInstallReplacesExactLegacyOnly(t *testing.T) {
	root := t.TempDir()
	hookDir := filepath.Join(root, ".git", "hooks")
	if err := os.MkdirAll(hookDir, 0o755); err != nil {
		t.Fatal(err)
	}
	path := Path(root)
	if err := os.WriteFile(path, []byte(LegacyHealPreCommitV052to054), 0o755); err != nil {
		t.Fatal(err)
	}

	res, err := Install(root)
	if err != nil {
		t.Fatalf("install legacy: %v", err)
	}
	if !res.ReplacedLegacy {
		t.Fatal("expected ReplacedLegacy")
	}
	got, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != CurrentPreCommit {
		t.Fatalf("hook body after migrate:\n%s", got)
	}
	bak, err := os.ReadFile(path + ".curbpack-legacy.bak")
	if err != nil {
		t.Fatalf("expected legacy backup: %v", err)
	}
	if string(bak) != LegacyHealPreCommitV052to054 {
		t.Fatal("backup must preserve exact legacy bytes")
	}
}

func TestInstallRefusesCustomHook(t *testing.T) {
	root := t.TempDir()
	hookDir := filepath.Join(root, ".git", "hooks")
	if err := os.MkdirAll(hookDir, 0o755); err != nil {
		t.Fatal(err)
	}
	path := Path(root)
	custom := "#!/bin/sh\necho custom\nexec curbpack check --heal\n"
	if err := os.WriteFile(path, []byte(custom), 0o755); err != nil {
		t.Fatal(err)
	}

	_, err := Install(root)
	if err == nil {
		t.Fatal("expected refuse on custom hook")
	}
	if !strings.Contains(err.Error(), "refusing to overwrite custom") {
		t.Fatalf("unexpected error: %v", err)
	}
	got, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != custom {
		t.Fatal("custom hook must remain unchanged")
	}
}

func TestInstallWritesWhenMissingAndIdempotent(t *testing.T) {
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, ".git", "hooks"), 0o755); err != nil {
		t.Fatal(err)
	}

	res, err := Install(root)
	if err != nil {
		t.Fatal(err)
	}
	if !res.WroteNew {
		t.Fatal("expected WroteNew")
	}
	res2, err := Install(root)
	if err != nil {
		t.Fatal(err)
	}
	if !res2.AlreadyCurrent {
		t.Fatal("expected AlreadyCurrent on second install")
	}
}
