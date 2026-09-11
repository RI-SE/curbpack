package cli_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
)

const testProductPinFile = "tests/cyberready-test-product.pin"

func TestProductEV002RemovesSecurityMd(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("product fixture scripts are POSIX sh")
	}
	pin := productPin(t)
	clone := clonePinnedProduct(t, pin)
	pin = strings.TrimSpace(mustGit(t, clone, "rev-parse", "HEAD"))

	restoreFrozenProduct(t, clone, pin)
	if err := runSetup(t, clone, pin, "R2", true); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(clone, "SECURITY.md")); !os.IsNotExist(err) {
		t.Fatalf("R2 should remove SECURITY.md, err=%v", err)
	}
	branch := strings.TrimSpace(mustGit(t, clone, "rev-parse", "--abbrev-ref", "HEAD"))
	if !strings.HasPrefix(branch, "test_") {
		t.Fatalf("R2 --commit should be on test_<user>_<date>_<id>, got %q", branch)
	}
	if st := strings.TrimSpace(mustGit(t, clone, "status", "--porcelain")); st != "" {
		t.Fatalf("R2 --commit should leave a clean tree:\n%s", st)
	}

	bin := buildCLI(t)
	cmd := exec.Command(bin, "check", "--json", "--as-of", "2026-09-09")
	cmd.Dir = clone
	cmd.Env = append(os.Environ(),
		"CURBPACK_PACKS_DIR="+filepath.Join(clone, "external_test/curbpack/packs"),
	)
	out, err := cmd.CombinedOutput()
	if err == nil {
		t.Fatalf("check after R2: want non-zero exit, got 0\n%s", out)
	}
	var payload ir.GateFailurePayload
	if jerr := json.Unmarshal(out, &payload); jerr != nil {
		t.Fatalf("check JSON: %v\n%s", jerr, out)
	}
	found := false
	for _, f := range payload.Failures {
		if f.GateID == "HOUSE-SECURITY-MD" {
			found = true
			break
		}
	}
	if !found {
		t.Fatalf("EV-002 (state R2) expected HOUSE-SECURITY-MD in failures: %+v", payload.Failures)
	}

	restoreFrozenProduct(t, clone, pin)
	if _, err := os.Stat(filepath.Join(clone, "SECURITY.md")); err != nil {
		t.Fatalf("verification-run restore should restore SECURITY.md: %v", err)
	}
	if out, err := git(t, clone, "show-ref", "--verify", "--quiet", "refs/heads/"+branch); err != nil {
		t.Fatalf("verification-run restore must leave %s: %v%s", branch, err, out)
	}
}

func TestProductRStateIsolation(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("product fixture scripts are POSIX sh")
	}
	pin := productPin(t)
	clone := clonePinnedProduct(t, pin)
	pin = strings.TrimSpace(mustGit(t, clone, "rev-parse", "HEAD"))
	assertPinnedSetupDoesNotRestore(t, clone)

	restoreFrozenProduct(t, clone, pin)
	if err := runSetup(t, clone, pin, "R2", true); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(clone, "SECURITY.md")); !os.IsNotExist(err) {
		t.Fatalf("R2 should remove SECURITY.md, err=%v", err)
	}
	if err := runSetup(t, clone, pin, "R3", true); err == nil {
		t.Fatal("setup.sh R3 --commit without restore should be rejected")
	}

	restoreFrozenProduct(t, clone, pin)
	if err := runSetup(t, clone, pin, "R3", true); err != nil {
		t.Fatal(err)
	}
	class := filepath.Join(clone, "docs/medtech/software_safety_class.md")
	if strings.Contains(string(mustRead(t, class)), "## Classification Rationale") {
		t.Fatal("R3 should remove ## Classification Rationale")
	}
	if _, err := os.Stat(filepath.Join(clone, "SECURITY.md")); err != nil {
		t.Fatalf("R3 must keep SECURITY.md: %v", err)
	}
	if st := strings.TrimSpace(mustGit(t, clone, "status", "--porcelain")); st != "" {
		t.Fatalf("R3 --commit should leave a clean tree:\n%s", st)
	}

	restoreFrozenProduct(t, clone, pin)
	if err := runSetup(t, clone, pin, "R1", false); err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(filepath.Join(clone, "SECURITY.md")); err != nil {
		t.Fatalf("R1 requires SECURITY.md: %v", err)
	}
	if !strings.Contains(string(mustRead(t, class)), "## Classification Rationale") {
		t.Fatal("R1 requires ## Classification Rationale")
	}
	if st := strings.TrimSpace(mustGit(t, clone, "status", "--porcelain")); st != "" {
		t.Fatalf("R1 should leave a clean tree:\n%s", st)
	}
	head := strings.TrimSpace(mustGit(t, clone, "rev-parse", "HEAD"))
	if head != pin {
		t.Fatalf("R1 HEAD=%s want pin %s", head, pin)
	}
}

func TestProductR2DefaultIsDirty(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("product fixture scripts are POSIX sh")
	}
	pin := productPin(t)
	clone := clonePinnedProduct(t, pin)
	pin = strings.TrimSpace(mustGit(t, clone, "rev-parse", "HEAD"))
	restoreFrozenProduct(t, clone, pin)
	if err := runSetup(t, clone, pin, "R2", false); err != nil {
		t.Fatal(err)
	}
	status := strings.TrimSpace(mustGit(t, clone, "status", "--porcelain"))
	if status == "" {
		t.Fatal("R2 without --commit should leave a dirty working tree")
	}
	head := strings.TrimSpace(mustGit(t, clone, "rev-parse", "--abbrev-ref", "HEAD"))
	if strings.HasPrefix(head, "test_") {
		t.Fatalf("R2 without --commit should not create a test_ branch, HEAD=%s", head)
	}
}

func TestProductR1CleanCheck(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("product fixture scripts are POSIX sh")
	}
	pin := productPin(t)
	clone := clonePinnedProduct(t, pin)
	pin = strings.TrimSpace(mustGit(t, clone, "rev-parse", "HEAD"))
	restoreFrozenProduct(t, clone, pin)
	if err := runSetup(t, clone, pin, "R1", false); err != nil {
		t.Fatal(err)
	}
	bin := buildCLI(t)
	cmd := exec.Command(bin, "check", "--json", "--as-of", "2026-09-09")
	cmd.Dir = clone
	cmd.Env = append(os.Environ(),
		"CURBPACK_PACKS_DIR="+filepath.Join(clone, "external_test/curbpack/packs"),
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("EV-001 (state R1) check should pass: %v\n%s", err, out)
	}
}

func TestProductSetupRejectsUnknownState(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("product fixture scripts are POSIX sh")
	}
	pin := productPin(t)
	clone := clonePinnedProduct(t, pin)
	pin = strings.TrimSpace(mustGit(t, clone, "rev-parse", "HEAD"))
	restoreFrozenProduct(t, clone, pin)
	err := runSetup(t, clone, pin, "EV-002", false)
	if err == nil {
		t.Fatal("setup.sh EV-002 should fail: suite ids are not repository states")
	}
	if !strings.Contains(err.Error(), "unknown state") {
		t.Fatalf("setup.sh EV-002 should refuse as unknown state, got: %v", err)
	}
}

func assertPinnedSetupDoesNotRestore(t *testing.T, clone string) {
	t.Helper()
	body := string(mustRead(t, filepath.Join(clone, "external_test/curbpack/setup.sh")))
	if strings.Contains(body, "reset.sh") {
		t.Fatal("pinned setup.sh still invokes reset.sh")
	}
	for _, needle := range []string{"git fetch", "git pull", "reset --hard", "git clean", "mktemp"} {
		if strings.Contains(body, needle) {
			t.Fatalf("pinned setup.sh still restores or fetches (%q)", needle)
		}
	}
}

func restoreFrozenProduct(t *testing.T, productRoot, pin string) {
	t.Helper()
	curbpackRoot := repoRoot(t)
	ensureTmpCurbpack(t, curbpackRoot)
	curbpackCommit := strings.TrimSpace(mustGit(t, curbpackRoot, "rev-parse", "HEAD"))
	pin = strings.TrimSpace(mustGit(t, productRoot, "rev-parse", pin+"^{commit}"))
	filled := writeFilledVerificationRun(t, curbpackRoot, curbpackCommit, productRoot, pin, "2026-09-09")
	before := curbpackCommit
	cmd := exec.Command("sh", "-c", `. "$1"`, "verification-run", filled)
	cmd.Dir = curbpackRoot
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("source verification-run: %v\n%s", err, out)
	}
	after := strings.TrimSpace(mustGit(t, curbpackRoot, "rev-parse", "HEAD"))
	if after != before {
		t.Fatalf("verification-run restore modified Curbpack HEAD: before=%s after=%s", before, after)
	}
	got := strings.TrimSpace(mustGit(t, productRoot, "rev-parse", "HEAD"))
	if got != pin {
		t.Fatalf("product HEAD after restore: got %s want %s", got, pin)
	}
	if st := strings.TrimSpace(mustGit(t, productRoot, "status", "--porcelain")); st != "" {
		t.Fatalf("product dirty after restore:\n%s", st)
	}
}

func writeFilledVerificationRun(t *testing.T, curbpackRoot, curbpackCommit, productRoot, productCommit, asOf string) string {
	t.Helper()
	template := filepath.Join(curbpackRoot, "docs/testing/verification_run_template.sh")
	body, err := os.ReadFile(template)
	if err != nil {
		t.Fatal(err)
	}
	s := string(body)
	repl := []struct{ old, new string }{
		{`CURBPACK_COMMIT=""`, `CURBPACK_COMMIT="` + curbpackCommit + `"`},
		{`REFERENCE_PRODUCT_COMMIT=""`, `REFERENCE_PRODUCT_COMMIT="` + productCommit + `"`},
		{`AS_OF_DATE=""`, `AS_OF_DATE="` + asOf + `"`},
		{`CURBPACK_ROOT=""`, `CURBPACK_ROOT="` + curbpackRoot + `"`},
		{`REFERENCE_PRODUCT_ROOT=""`, `REFERENCE_PRODUCT_ROOT="` + productRoot + `"`},
	}
	for _, r := range repl {
		if n := strings.Count(s, r.old); n != 1 {
			t.Fatalf("%s: want 1 assignment %q, got %d", template, r.old, n)
		}
		s = strings.Replace(s, r.old, r.new, 1)
	}
	out := filepath.Join(t.TempDir(), "verification-run.sh")
	if err := os.WriteFile(out, []byte(s), 0o644); err != nil {
		t.Fatal(err)
	}
	return out
}

func ensureTmpCurbpack(t *testing.T, root string) {
	t.Helper()
	bin := filepath.Join(root, "tmp", "curbpack")
	if info, err := os.Stat(bin); err == nil && !info.IsDir() && info.Mode()&0o111 != 0 {
		return
	}
	if err := os.MkdirAll(filepath.Join(root, "tmp"), 0o755); err != nil {
		t.Fatal(err)
	}
	cmd := exec.Command("go", "build", "-o", bin, filepath.Join(root, "cmd/curbpack"))
	cmd.Dir = root
	out, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("build tmp/curbpack: %v\n%s", err, out)
	}
}

func runSetup(t *testing.T, productRoot, pin, state string, commit bool) error {
	t.Helper()
	setup := filepath.Join(productRoot, "external_test/curbpack/setup.sh")
	args := []string{state}
	if commit {
		args = append(args, "--commit")
	}
	cmd := exec.Command(setup, args...)
	cmd.Dir = productRoot
	cmd.Env = append(os.Environ(),
		"REFERENCE_PRODUCT_ROOT="+productRoot,
		"REFERENCE_PRODUCT_COMMIT="+pin,
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return outputError{err: err, out: string(out)}
	}
	return nil
}

func mustRead(t *testing.T, path string) []byte {
	t.Helper()
	body, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	return body
}

func productPin(t *testing.T) string {
	t.Helper()
	body, err := os.ReadFile(filepath.Join(repoRoot(t), filepath.FromSlash(testProductPinFile)))
	if err != nil {
		t.Fatal(err)
	}
	for _, line := range strings.Split(string(body), "\n") {
		if sha, ok := strings.CutPrefix(strings.TrimSpace(line), "commit "); ok {
			return strings.TrimSpace(sha)
		}
	}
	t.Fatalf("%s has no commit line", testProductPinFile)
	return ""
}

func clonePinnedProduct(t *testing.T, pin string) string {
	t.Helper()
	source := os.Getenv("CURBPACK_TEST_PRODUCT")
	if source == "" {
		source = filepath.Join(filepath.Dir(repoRoot(t)), "cyberready-test-product")
	}
	if _, err := os.Stat(filepath.Join(source, ".git")); err != nil {
		t.Skipf("cyberready-test-product is not at %s; clone it there or set CURBPACK_TEST_PRODUCT", source)
	}
	if out, err := git(t, source, "cat-file", "-e", pin+"^{commit}"); err != nil {
		t.Fatalf("pin %s is not in %s: %v%s", pin, source, err, out)
	}
	clone := filepath.Join(t.TempDir(), "product")
	if out, err := git(t, "", "clone", "--quiet", "--no-checkout", source, clone); err != nil {
		t.Fatalf("clone: %v%s", err, out)
	}
	if out, err := git(t, clone, "checkout", "--quiet", "--detach", pin); err != nil {
		t.Fatalf("checkout %s: %v%s", pin, err, out)
	}
	// setup.sh compares git toplevel to REFERENCE_PRODUCT_ROOT as strings.
	// On macOS t.TempDir() may be /var/folders while git reports /private/var/folders.
	return strings.TrimSpace(mustGit(t, clone, "rev-parse", "--show-toplevel"))
}

func mustGit(t *testing.T, repo string, args ...string) string {
	t.Helper()
	out, err := git(t, repo, args...)
	if err != nil {
		t.Fatalf("git %s: %v%s", strings.Join(args, " "), err, out)
	}
	return out
}

func git(t *testing.T, repo string, args ...string) (string, error) {
	t.Helper()
	if repo != "" {
		args = append([]string{"-C", repo}, args...)
	}
	cmd := exec.Command("git", args...)
	cmd.Env = append(os.Environ(), "GIT_TERMINAL_PROMPT=0")
	out, err := cmd.CombinedOutput()
	return string(out), err
}

func repoRoot(t *testing.T) string {
	t.Helper()
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("caller")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "../.."))
}

type outputError struct {
	err error
	out string
}

func (e outputError) Error() string {
	return e.err.Error() + ": " + e.out
}
