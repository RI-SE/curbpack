package doctor

import (
	"bytes"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/githook"
)

func TestDoctorFailsLegacyHealHook(t *testing.T) {
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, ".git", "hooks"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, ".curbpack.json"), []byte(`{"packs":["house-policy"],"hooks":true}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(githook.Path(root), []byte(githook.LegacyHealPreCommitV052to054), 0o755); err != nil {
		t.Fatal(err)
	}

	out := captureDoctor(t, root)
	if strings.Contains(out, "Doctor OK") {
		t.Fatalf("legacy --heal hook must not yield Doctor OK:\n%s", out)
	}
	if !strings.Contains(out, "legacy curbpack check --heal") {
		t.Fatalf("expected legacy heal failure detail:\n%s", out)
	}
	if !strings.Contains(out, "Doctor found issues") {
		t.Fatalf("expected Doctor found issues:\n%s", out)
	}
}

func TestDoctorPassesCurrentHook(t *testing.T) {
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, ".git", "hooks"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(root, ".curbpack.json"), []byte(`{"packs":["house-policy"],"hooks":true}`+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(githook.Path(root), []byte(githook.CurrentPreCommit), 0o755); err != nil {
		t.Fatal(err)
	}

	out := captureDoctor(t, root)
	if !strings.Contains(out, "Doctor OK") {
		t.Fatalf("current hook should be healthy:\n%s", out)
	}
	if strings.Contains(out, "--heal") {
		t.Fatalf("current healthy path must not mention --heal:\n%s", out)
	}
}

func captureDoctor(t *testing.T, root string) string {
	t.Helper()
	old := os.Stdout
	r, w, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	os.Stdout = w
	errRun := Run(Options{RepoRoot: root, Version: "test"})
	_ = w.Close()
	os.Stdout = old
	var buf bytes.Buffer
	_, _ = io.Copy(&buf, r)
	_ = r.Close()
	if errRun != nil {
		t.Fatalf("doctor: %v\n%s", errRun, buf.String())
	}
	return buf.String()
}
