package drift_test

import (
	"bytes"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/drift"
	"github.com/afelin/curbpack/internal/gitutil"
)

func initRepo(t *testing.T, dir string) {
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
	run("git", "config", "user.email", "drift@curbpack.local")
	run("git", "config", "user.name", "Drift")
	run("git", "commit", "--allow-empty", "-m", "init", "-q")
}

func TestDrift_never_boolean_summary(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	var report drift.Report
	if err := json.Unmarshal(buf.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if drift.ContainsForbiddenSummary(report) {
		t.Fatal("drift report contains forbidden boolean summary fields")
	}
	for _, f := range drift.ForbiddenSummaryFields {
		if strings.Contains(buf.String(), `"`+f+`"`) {
			t.Fatalf("forbidden field %q in output", f)
		}
	}
}

func TestDrift_attest_commit_behind(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	head1, _ := gitutil.HeadSHA(dir)
	cap := attest.Capsule{CommitSHA: head1, StateHash: "h1", Signer: "local-unsigned", UserTouch: "not-verified"}
	body, _ := json.Marshal(cap)
	_ = gitutil.NotesAdd(dir, head1, string(body))
	evidence := filepath.Join(dir, ".github", "curbpack", "evidence")
	_ = os.MkdirAll(evidence, 0o755)
	ptr := map[string]string{"state_hash": "h1", "commit_sha": head1}
	pb, _ := json.Marshal(ptr)
	_ = os.WriteFile(filepath.Join(evidence, "hpurl-pointer.json"), pb, 0o644)

	cmd := exec.Command("git", "commit", "--allow-empty", "-m", "after", "-q")
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	_ = cmd.Run()

	var buf bytes.Buffer
	_ = drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf})
	var report drift.Report
	_ = json.Unmarshal(buf.Bytes(), &report)
	found := false
	for _, s := range report.Signals {
		if s.ID == "attest_commit_behind" {
			found = true
		}
	}
	if !found {
		t.Fatalf("want attest_commit_behind in %v", report.Signals)
	}
}

func TestDrift_attest_none(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	var buf bytes.Buffer
	_ = drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf})
	if !strings.Contains(buf.String(), "attest_none") {
		t.Fatalf("want attest_none: %s", buf.String())
	}
	if strings.Contains(buf.String(), "docs_changed_since_attest") || strings.Contains(buf.String(), "docs_unchanged_since_attest") {
		t.Fatalf("docs_* requires a bind: %s", buf.String())
	}
}

func writeBind(t *testing.T, dir, sha string) {
	t.Helper()
	cap := attest.Capsule{CommitSHA: sha, StateHash: "h1", Signer: "local-unsigned", UserTouch: "not-verified"}
	body, _ := json.Marshal(cap)
	if err := gitutil.NotesAdd(dir, sha, string(body)); err != nil {
		t.Fatal(err)
	}
	evidence := filepath.Join(dir, ".github", "curbpack", "evidence")
	if err := os.MkdirAll(evidence, 0o755); err != nil {
		t.Fatal(err)
	}
	ptr := map[string]string{"state_hash": "h1", "commit_sha": sha}
	pb, _ := json.Marshal(ptr)
	if err := os.WriteFile(filepath.Join(evidence, "hpurl-pointer.json"), pb, 0o644); err != nil {
		t.Fatal(err)
	}
}

func gitCommit(t *testing.T, dir string, rels []string, msg string) {
	t.Helper()
	args := append([]string{"add"}, rels...)
	cmd := exec.Command("git", args...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git add: %v: %s", err, out)
	}
	cmd = exec.Command("git", "commit", "-m", msg, "-q")
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("git commit: %v: %s", err, out)
	}
}

func signalIDs(report drift.Report) []string {
	var ids []string
	for _, s := range report.Signals {
		ids = append(ids, s.ID)
	}
	return ids
}

func hasSignal(report drift.Report, id string) bool {
	for _, s := range report.Signals {
		if s.ID == id {
			return true
		}
	}
	return false
}

func TestDrift_docs_changed_since_attest(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("v1 reporting process here"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitCommit(t, dir, []string{"SECURITY.md"}, "docs v1")
	head1, _ := gitutil.HeadSHA(dir)
	writeBind(t, dir, head1)

	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("v2 reporting process updated"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitCommit(t, dir, []string{"SECURITY.md"}, "docs v2")

	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	var report drift.Report
	if err := json.Unmarshal(buf.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if !hasSignal(report, "docs_changed_since_attest") {
		t.Fatalf("want docs_changed_since_attest in %v", signalIDs(report))
	}
	if hasSignal(report, "docs_unchanged_since_attest") {
		t.Fatalf("did not want docs_unchanged: %v", report.Signals)
	}
	found := false
	for _, s := range report.Signals {
		if s.ID == "docs_changed_since_attest" && strings.Contains(s.Detail, "SECURITY.md") {
			found = true
		}
	}
	if !found {
		t.Fatalf("want SECURITY.md in docs_changed detail: %v", report.Signals)
	}
	wantAction := false
	for _, a := range report.SuggestedActions {
		if strings.Contains(a, "check") && strings.Contains(a, "share") && strings.Contains(strings.ToLower(a), "attest") {
			wantAction = true
		}
	}
	if !wantAction {
		t.Fatalf("want re-check/re-share/re-attest action: %v", report.SuggestedActions)
	}
}

func TestDrift_docs_unchanged_since_attest(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	if err := os.WriteFile(filepath.Join(dir, "SECURITY.md"), []byte("v1 reporting process here"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitCommit(t, dir, []string{"SECURITY.md"}, "docs v1")
	head1, _ := gitutil.HeadSHA(dir)
	writeBind(t, dir, head1)

	if err := os.WriteFile(filepath.Join(dir, "unrelated.txt"), []byte("not a pack path"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitCommit(t, dir, []string{"unrelated.txt"}, "other")

	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	var report drift.Report
	if err := json.Unmarshal(buf.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if !hasSignal(report, "docs_unchanged_since_attest") {
		t.Fatalf("want docs_unchanged_since_attest in %v", signalIDs(report))
	}
	if hasSignal(report, "docs_changed_since_attest") {
		t.Fatalf("unrelated.txt must not count as pack docs: %v", report.Signals)
	}
	if !hasSignal(report, "attest_commit_behind") {
		t.Fatalf("want attest_commit_behind alongside unchanged docs: %v", signalIDs(report))
	}
}

func TestDrift_contact_expires_past(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	p := filepath.Join(dir, ".well-known", "security.txt")
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	body := "Contact: mailto:a@b.c\nExpires: 2020-01-01T00:00:00.000Z\n"
	if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	var report drift.Report
	if err := json.Unmarshal(buf.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if !hasSignal(report, "contact_expires_past") {
		t.Fatalf("want contact_expires_past in %v", signalIDs(report))
	}
	if hasSignal(report, "contact_missing") {
		t.Fatalf("Contact present: %v", report.Signals)
	}
}

func TestDrift_contact_missing(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	p := filepath.Join(dir, ".well-known", "security.txt")
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(p, []byte("Expires: 2027-01-01T00:00:00.000Z\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	var report drift.Report
	if err := json.Unmarshal(buf.Bytes(), &report); err != nil {
		t.Fatal(err)
	}
	if !hasSignal(report, "contact_missing") {
		t.Fatalf("want contact_missing in %v", signalIDs(report))
	}
}

func TestDrift_contact_absent_file_no_signal(t *testing.T) {
	dir := t.TempDir()
	initRepo(t, dir)
	var buf bytes.Buffer
	if err := drift.Run(drift.Options{RepoRoot: dir, JSONOut: true, Writer: &buf}); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(buf.String(), "contact_expires_past") || strings.Contains(buf.String(), "contact_missing") {
		t.Fatalf("no security.txt → no contact_*: %s", buf.String())
	}
}
