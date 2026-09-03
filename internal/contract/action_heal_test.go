package contract_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/config"
	"github.com/afelin/curbpack/internal/formhints"
	"github.com/afelin/curbpack/internal/remediation"
	"github.com/afelin/curbpack/internal/validate"
)

// Action-equivalent smoke: uninitialized repo (no .curbpack.json) + heal stubs.
// Mirrors Action with heal:true opt-in (Action default is false) — ResolvePackIDs falls back to house-policy.
func TestUninitializedHealRemainsDeterministicRed(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Product\n")

	if _, err := os.Stat(filepath.Join(dir, ".curbpack.json")); err == nil {
		t.Fatal("fixture must start without .curbpack.json")
	}

	ids, err := config.ResolvePackIDs(dir, nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(ids) != 1 || ids[0] != "house-policy" {
		t.Fatalf("uninitialized ResolvePackIDs=%v want [house-policy]", ids)
	}

	res, err := validate.Run(validate.Options{RepoRoot: dir, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("expected initial red without security stubs")
	}

	cache, _ := remediation.Load(dir)
	hints := formhints.ForFailuresCached(res.Payload.Failures, cache)
	hints, err = formhints.ApplyStubs(dir, hints)
	if err != nil {
		t.Fatal(err)
	}
	applied := 0
	for _, h := range hints {
		if h.Applied {
			applied++
		}
	}
	if applied == 0 {
		t.Fatal("heal must apply at least one missing stub")
	}
	_ = formhints.PersistCache(dir, hints)

	res2, err := validate.Run(validate.Options{RepoRoot: dir, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if res2.Passed {
		t.Fatalf("generated stubs must remain red, got %#v", res2.Payload)
	}
	if len(res2.Payload.Failures) == 0 {
		t.Fatal("red without failures is not deterministic")
	}
	if _, err := os.Stat(filepath.Join(dir, "SECURITY.md")); err != nil {
		t.Fatalf("expected SECURITY.md stub after heal: %v", err)
	}
	if _, err := os.Stat(filepath.Join(dir, ".curbpack.json")); err == nil {
		t.Fatal("heal must not invent .curbpack.json (Action path stays config-free)")
	}
}

func TestCLICheckHealUninitialized(t *testing.T) {
	bin := buildCyberready(t)
	dir := t.TempDir()
	mustRealGit(t, dir)
	mustWrite(t, filepath.Join(dir, "README.md"), "# Product\n")

	cmd := exec.Command(bin, "check", "--heal")
	cmd.Dir = dir
	out, err := cmd.CombinedOutput()
	if err == nil {
		t.Fatalf("check --heal must remain red for generated policy stubs:\n%s", out)
	}
	if _, statErr := os.Stat(filepath.Join(dir, "SECURITY.md")); statErr != nil {
		t.Fatalf("check --heal failed without stubs: %v\n%s", statErr, out)
	}
	text := string(out)
	if !strings.Contains(text, "HOUSE-ANTI-PLACEHOLDER") {
		t.Fatalf("check --heal must report post-heal placeholder failures:\n%s", text)
	}
	if strings.Contains(text, "scaffold green") {
		t.Fatalf("check --heal must not describe a red result as green:\n%s", text)
	}
}

func TestActionHealPreservesRedResult(t *testing.T) {
	body, err := os.ReadFile(filepath.Join(repoRoot(t), "action.yml"))
	if err != nil {
		t.Fatal(err)
	}
	text := string(body)
	for _, want := range []string{
		`EXTRA+=(--heal)`,
		`echo "passed=false" >> "$GITHUB_OUTPUT"`,
		`if: steps.run.outputs.passed != 'true'`,
		`exit 1`,
	} {
		if !strings.Contains(text, want) {
			t.Fatalf("action.yml must preserve a red heal result; missing %q", want)
		}
	}
	if strings.Contains(text, "scaffold green") {
		t.Fatal("action.yml must not describe generated scaffold as green")
	}
}

func buildCyberready(t *testing.T) string {
	t.Helper()
	name := "curbpack"
	if runtime.GOOS == "windows" {
		name = "curbpack.exe"
	}
	bin := filepath.Join(t.TempDir(), name)
	cmd := exec.Command("go", "build", "-o", bin, "./cmd/curbpack")
	cmd.Dir = repoRoot(t)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("go build: %v\n%s", err, out)
	}
	return bin
}

func repoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	// internal/contract → repo root
	return filepath.Clean(filepath.Join(wd, "..", ".."))
}
