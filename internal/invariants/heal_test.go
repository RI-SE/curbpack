package invariants_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/formhints"
	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/validate"
)

// Heal / --apply-stub must never write Git Notes capsules (fake self-certification).
func TestHealNeverAttests(t *testing.T) {
	dir := t.TempDir()
	mustGit(t, dir)
	// Missing SECURITY.md → house-policy failure; heal via ApplyStubs only.
	mustWrite(t, filepath.Join(dir, ".well-known/security.txt"), "Contact: mailto:a@b.c\nExpires: 2027-01-01T00:00:00.000Z\nPreferred-Languages: en\n")
	mustWrite(t, filepath.Join(dir, "README.md"), "# Project\n")

	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if res.Passed {
		t.Fatal("expected failure before heal")
	}
	hints := formhints.ForFailures(res.Payload.Failures)
	hints, err = formhints.ApplyStubs(dir, hints)
	if err != nil {
		t.Fatal(err)
	}
	applied := false
	for _, h := range hints {
		if h.Applied {
			applied = true
		}
	}
	if !applied {
		t.Fatal("expected at least one stub applied")
	}

	// No Git Notes ref / capsule after heal.
	out, _ := exec.Command("git", "-C", dir, "notes", "--ref=cyberready", "list").CombinedOutput()
	if strings.TrimSpace(string(out)) != "" && !strings.Contains(string(out), "No notes") {
		// Empty list is OK; any note object is not.
		if lines := strings.TrimSpace(string(out)); lines != "" && !strings.Contains(lines, "fatal") {
			// notes list with content would look like "<hash> <commit>"
			for _, line := range strings.Split(lines, "\n") {
				if fields := strings.Fields(line); len(fields) >= 2 {
					t.Fatalf("heal must not write Git Notes; got: %s", lines)
				}
			}
		}
	}
	if _, err := os.Stat(filepath.Join(dir, ".github/cyberready/evidence/hpurl-pointer.json")); err == nil {
		t.Fatal("heal must not write hpurl-pointer (attest artifact)")
	}
}

func TestApplyStubNeverOverwritesFilled(t *testing.T) {
	dir := t.TempDir()
	body := "# Security Policy\n\n" + strings.Repeat("word ", 80) + "\n"
	mustWrite(t, filepath.Join(dir, "SECURITY.md"), body)
	hints := []formhints.Hint{{
		GateID:  "HOUSE-SECURITY-MD",
		File:    "SECURITY.md",
		Snippet: "# OVERWRITE ME\n",
	}}
	out, err := formhints.ApplyStubs(dir, hints)
	if err != nil {
		t.Fatal(err)
	}
	if out[0].Applied {
		t.Fatal("must not overwrite non-empty SECURITY.md")
	}
	got, _ := os.ReadFile(filepath.Join(dir, "SECURITY.md"))
	if string(got) != body {
		t.Fatal("file content changed")
	}
}

func TestApplyStubRefusesTraversal(t *testing.T) {
	dir := t.TempDir()
	_, err := formhints.ApplyStubs(dir, []formhints.Hint{{
		GateID:  "X",
		File:    "../outside.md",
		Snippet: "nope\n",
	}})
	if err == nil {
		t.Fatal("expected traversal refuse")
	}
}

func TestClaimStringsPresent(t *testing.T) {
	// Static claim text used on human TTY paths; --json payloads omit banners by design.
	claim := "Prepares evidence for human review — not a conformity assessment."
	failures := []ir.Failure{{GateID: "X", Severity: "low", Type: "T", SanitizedDescription: "d"}}
	md := validate.ActionReportMarkdown(ir.GateFailurePayload{Failures: failures, PackID: "house-policy"}, 0)
	if !strings.Contains(md, "human review") || strings.Contains(strings.ToLower(md), "certified") {
		t.Fatalf("action report must stay claim-safe: %s", md)
	}
	_ = claim
}

func mustGit(t *testing.T, dir string) {
	t.Helper()
	run := func(args ...string) {
		t.Helper()
		cmd := exec.Command(args[0], args[1:]...)
		cmd.Dir = dir
		cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
		if out, err := cmd.CombinedOutput(); err != nil {
			t.Fatalf("%v: %s", err, out)
		}
	}
	run("git", "init", "-q")
	run("git", "config", "user.email", "inv@cyberready.local")
	run("git", "config", "user.name", "Invariants")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}

func mustWrite(t *testing.T, path, body string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
}
