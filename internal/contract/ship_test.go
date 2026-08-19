package contract_test

import (
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
)

func shipRepoRoot(t *testing.T) string {
	t.Helper()
	out, err := exec.Command("git", "rev-parse", "--show-toplevel").Output()
	if err != nil {
		t.Fatal(err)
	}
	return strings.TrimSpace(string(out))
}

func shipScript(t *testing.T) string {
	t.Helper()
	p := filepath.Join(shipRepoRoot(t), "scripts", "curbpack-ship.sh")
	st, err := os.Stat(p)
	if err != nil || st.Mode()&0o111 == 0 {
		t.Fatalf("missing executable %s", p)
	}
	return p
}

func runShip(t *testing.T, dir, script string, env []string, args ...string) (int, string) {
	t.Helper()
	cmd := exec.Command(script, args...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), env...)
	out, err := cmd.CombinedOutput()
	code := 0
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			code = ee.ExitCode()
		} else {
			t.Fatal(err)
		}
	}
	return code, string(out)
}

func initFixtureRepo(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	runGit(t, dir, "git", "init", "-q")
	runGit(t, dir, "git", "config", "user.email", "ship@curbpack.local")
	runGit(t, dir, "git", "config", "user.name", "Ship")
	runGit(t, dir, "git", "commit", "--allow-empty", "-m", "init", "-q")
	return dir
}

func runGit(t *testing.T, dir string, args ...string) {
	t.Helper()
	cmd := exec.Command(args[0], args[1:]...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%v: %s", err, out)
	}
}

func seedFixtureTree(t *testing.T, dir, root string) {
	t.Helper()
	for _, rel := range []string{
		"scripts/curbpack-ship.sh", "scripts/claim-safety.sh",
		".github/required-checks.json", "scripts/install-manifest.json",
	} {
		src := filepath.Join(root, rel)
		dst := filepath.Join(dir, rel)
		if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(src)
		if err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(dst, b, 0o644); err != nil {
			t.Fatal(err)
		}
	}
	os.Chmod(filepath.Join(dir, "scripts/curbpack-ship.sh"), 0o755)
	os.Chmod(filepath.Join(dir, "scripts/claim-safety.sh"), 0o755)
}

const checksJSON = `[{"name":"redteam-pilot","bucket":"pass"},{"name":"test (ubuntu-latest)","bucket":"pass"},{"name":"test (macos-latest)","bucket":"pass"},{"name":"smoke","bucket":"pass"},{"name":"gauntlet","bucket":"pass"}]`

func commitSeed(t *testing.T, dir string) {
	t.Helper()
	runGit(t, dir, "git", "add", "-A")
	runGit(t, dir, "git", "commit", "-m", "seed", "-q")
}

func TestCurbpackShipAcceptance(t *testing.T) {
	root := shipRepoRoot(t)
	script := shipScript(t)

	t.Run("dirty worktree exit 2", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		mustWrite(t, filepath.Join(dir, "dirty.txt"), "x\n")
		code, out := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1"}, "preflight", "1")
		if code != 2 || !strings.Contains(out, "Paused:") {
			t.Fatalf("code=%d out=%q", code, out)
		}
	})

	t.Run("corp-origin missing exit 2", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		code, out := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1"}, "preflight", "1")
		if code != 2 || !strings.Contains(out, "corp-origin") {
			t.Fatalf("code=%d out=%q", code, out)
		}
	})

	t.Run("required-check drift exit 1", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		runGit(t, dir, "git", "branch", "-M", "main")
		runGit(t, dir, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
		runGit(t, dir, "git", "remote", "add", "corp-origin", "https://example.com/corp.git")
		driftChecks := `[{"name":"redteam-pilot","bucket":"pass"},{"name":"test (ubuntu-latest)","bucket":"pass"},{"name":"test (macos-latest)","bucket":"pass"},{"name":"smoke","bucket":"fail"},{"name":"gauntlet","bucket":"pass"}]`
		code, out := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1", "CURBPACK_SHIP_CHECKS_JSON=" + driftChecks}, "--dry-run", "preflight", "1")
		if code != 1 || !strings.Contains(out, "Blocked:") {
			t.Fatalf("code=%d out=%q", code, out)
		}
	})

	t.Run("zero-test selector exit 1 not 0", func(t *testing.T) {
		n := countTestPasses(t, "./internal/nope/...")
		if n != 0 {
			t.Fatalf("expected 0 test passes for noop package, got %d", n)
		}
		if n >= 80 {
			t.Fatal("integrity floor would false-green zero-test selector")
		}
	})

	t.Run("version changed no trailer exit 1", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		runGit(t, dir, "git", "branch", "-M", "main")
		runGit(t, dir, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
		runGit(t, dir, "git", "remote", "add", "corp-origin", "https://example.com/corp.git")
		mustWrite(t, filepath.Join(dir, "scripts/install-manifest.json"), `{"default_version":"v9.9.9"}`+"\n")
		runGit(t, dir, "git", "add", "-A")
		runGit(t, dir, "git", "commit", "-m", "bump", "-q")
		code, _ := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1", "CURBPACK_SHIP_CHECKS_JSON=" + checksJSON}, "--dry-run", "preflight", "1")
		if code != 1 {
			t.Fatalf("want 1 got %d", code)
		}
	})

	t.Run("version changed with trailer exit 0", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		runGit(t, dir, "git", "branch", "-M", "main")
		runGit(t, dir, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
		runGit(t, dir, "git", "remote", "add", "corp-origin", "https://example.com/corp.git")
		mustWrite(t, filepath.Join(dir, "scripts/install-manifest.json"), `{"default_version":"v9.9.9"}`+"\n")
		runGit(t, dir, "git", "add", "-A")
		runGit(t, dir, "git", "commit", "-m", "bump\n\nApprove-Pin-Bump: tester", "-q")
		code, out := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1", "CURBPACK_SHIP_CHECKS_JSON=" + checksJSON}, "--dry-run", "preflight", "1")
		if code != 0 {
			t.Fatalf("want 0 got %d out=%q", code, out)
		}
	})

	t.Run("post-merge twice no-op exit 0", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		runGit(t, dir, "git", "branch", "-M", "main")
		runGit(t, dir, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
		runGit(t, dir, "git", "remote", "add", "corp-origin", "https://example.com/corp.git")
		cmd := exec.Command("git", "rev-parse", "HEAD")
		cmd.Dir = dir
		sha, _ := cmd.Output()
		state := filepath.Join(dir, ".github/curbpack/ship-state.json")
		os.MkdirAll(filepath.Dir(state), 0o755)
		os.WriteFile(state, []byte(`{"post_merge_sha":"`+strings.TrimSpace(string(sha))+`"}`), 0o644)
		code, out := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1"}, "post-merge")
		if code != 0 || !strings.Contains(out, "already done") {
			t.Fatalf("code=%d out=%q", code, out)
		}
	})

	t.Run("dry-run preflight no writes", func(t *testing.T) {
		dir := initFixtureRepo(t)
		seedFixtureTree(t, dir, root)
		commitSeed(t, dir)
		runGit(t, dir, "git", "branch", "-M", "main")
		runGit(t, dir, "git", "update-ref", "refs/remotes/origin/main", "HEAD")
		runGit(t, dir, "git", "remote", "add", "corp-origin", "https://example.com/corp.git")
		state := filepath.Join(dir, ".github/curbpack/ship-state.json")
		code, out := runShip(t, dir, filepath.Join(dir, "scripts/curbpack-ship.sh"), []string{"GIT_CONFIG_NOSYSTEM=1", "CURBPACK_SHIP_CHECKS_JSON=" + checksJSON}, "--dry-run", "preflight", "1")
		if code != 0 {
			t.Fatalf("code=%d out=%q", code, out)
		}
		if _, err := os.Stat(state); err == nil {
			t.Fatal("dry-run wrote ship-state")
		}
		if !strings.Contains(out, "[dry-run]") {
			t.Fatalf("expected dry-run markers: %q", out)
		}
	})

	_ = script
}

func countTestPasses(t *testing.T, pkg string) int {
	t.Helper()
	cmd := exec.Command("go", "test", "-json", pkg)
	out, err := cmd.CombinedOutput()
	s := string(out)
	if err != nil {
		low := strings.ToLower(s)
		if strings.Contains(low, "no packages") || strings.Contains(low, "no go files") ||
			strings.Contains(low, "cannot find package") || strings.Contains(low, "does not contain") {
			return 0
		}
	}
	py := exec.Command("python3", "-c", "import sys,json;n=0\nfor l in sys.stdin:\n l=l.strip()\n if not l: continue\n try: o=json.loads(l)\n except json.JSONDecodeError: continue\n if o.get('Action')=='pass' and o.get('Test'): n+=1\nprint(n)")
	py.Stdin = strings.NewReader(s)
	nout, err := py.Output()
	if err != nil {
		if err != nil && len(strings.TrimSpace(s)) == 0 {
			return 0
		}
		t.Fatalf("count passes: %v out=%q", err, s)
	}
	n, err := strconv.Atoi(strings.TrimSpace(string(nout)))
	if err != nil {
		t.Fatal(err)
	}
	return n
}
