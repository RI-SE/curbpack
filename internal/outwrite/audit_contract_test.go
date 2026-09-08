package outwrite_test

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/outwrite"
)

func TestAuditLiveOwnerIsNotStale(t *testing.T) {
	child := exec.Command(os.Args[0], "-test.run=^TestLockOwnerProcess$")
	child.Env = append(os.Environ(), "CURBPACK_TEST_LOCK_OWNER=1")
	stdout, err := child.StdoutPipe()
	if err != nil {
		t.Fatal(err)
	}
	if err := child.Start(); err != nil {
		t.Fatal(err)
	}
	defer func() { _ = child.Process.Kill(); _ = child.Wait() }()
	if _, err := bufio.NewReader(stdout).ReadString('\n'); err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	p := filepath.Join(root, outwrite.LockFileName)
	if err := os.WriteFile(p, []byte(fmt.Sprintf("pid=%d\n", child.Process.Pid)), 0600); err != nil {
		t.Fatal(err)
	}
	old := time.Now().Add(-time.Hour)
	_ = os.Chtimes(p, old, old)
	lock, err := outwrite.Acquire(root)
	if err == nil {
		_ = lock.Release()
		t.Fatal("stole lock of live foreign owner based only on age")
	}
}
func TestAuditConcurrentGoroutineIsNotNestedOwner(t *testing.T) {
	root := t.TempDir()
	lock, err := outwrite.Acquire(root)
	if err != nil {
		t.Fatal(err)
	}
	defer lock.Release()
	result := make(chan error, 1)
	go func() {
		second, e := outwrite.Acquire(root)
		if e == nil {
			_ = second.Release()
		}
		result <- e
	}()
	if <-result == nil {
		t.Fatal("independent goroutine entered held exclusive lock")
	}
}
func TestAuditDoubleReleasePreservesSuccessor(t *testing.T) {
	root := t.TempDir()
	first, e := outwrite.Acquire(root)
	if e != nil {
		t.Fatal(e)
	}
	_ = first.Release()
	second, e := outwrite.Acquire(root)
	if e != nil {
		t.Fatal(e)
	}
	defer second.Release()
	_ = first.Release()
	if _, e := os.Stat(filepath.Join(root, outwrite.LockFileName)); e != nil {
		t.Fatal("released handle deleted successor lock", e)
	}
}
func TestAuditRefuseGitBeforeCreatingDirectories(t *testing.T) {
	root := t.TempDir()
	if e := os.Mkdir(filepath.Join(root, ".git"), 0700); e != nil {
		t.Fatal(e)
	}
	dest := filepath.Join(root, ".git", "must-not-exist")
	lock, e := outwrite.Acquire(dest)
	if e == nil {
		_ = lock.Release()
		t.Fatal("accepted git root")
	}
	if _, e := os.Stat(dest); !os.IsNotExist(e) {
		t.Fatal("refused operation created directory inside .git")
	}
}
func TestAuditDeepExplicitRootDoesNotFollowGitAlias(t *testing.T) {
	root := t.TempDir()
	gitdir := filepath.Join(root, ".git")
	if e := os.Mkdir(gitdir, 0700); e != nil {
		t.Fatal(e)
	}
	if e := os.Symlink(gitdir, filepath.Join(root, "alias")); e != nil {
		t.Skip(e)
	}
	permitted, dest, e := outwrite.DirDest(root, filepath.Join(root, "alias", "new", "deep"), "review-pack")
	if e != nil {
		return
	}
	e = outwrite.WriteFile(permitted, filepath.Join(dest, "sentinel"), []byte("audit"), 0600)
	if e == nil {
		t.Fatal("explicit root followed ancestor alias and wrote inside .git")
	}
}

// Run the test binary itself so process ownership is exercised on every OS.
func TestLockOwnerProcess(t *testing.T) {
	if os.Getenv("CURBPACK_TEST_LOCK_OWNER") != "1" {
		return
	}
	fmt.Println("ready")
	time.Sleep(30 * time.Second)
	os.Exit(0)
}

func TestExplicitRecoveryAfterOwnerExits(t *testing.T) {
	child := exec.Command(os.Args[0], "-test.run=^TestLockOwnerProcess$")
	if err := child.Run(); err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	path := filepath.Join(root, outwrite.LockFileName)
	if err := os.WriteFile(path, []byte(fmt.Sprintf("pid=%d\n", child.Process.Pid)), 0600); err != nil {
		t.Fatal(err)
	}
	if lock, err := outwrite.Acquire(root); err == nil {
		lock.Release()
		t.Fatal("implicitly recovered dead owner")
	}
	if err := outwrite.RecoverStale(root); err != nil {
		t.Fatal(err)
	}
	lock, err := outwrite.Acquire(root)
	if err != nil {
		t.Fatal(err)
	}
	defer lock.Release()
	if err := outwrite.RecoverStale(root); err == nil {
		t.Fatal("recovered live owner")
	}
}

func TestReleasePreservesReplacedLock(t *testing.T) {
	root := t.TempDir()
	lock, err := outwrite.Acquire(root)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(root, outwrite.LockFileName)
	if err := os.Rename(path, path+".old"); err != nil {
		lock.Release()
		t.Skip(err)
	}
	if err := os.WriteFile(path, []byte("replacement"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := lock.Release(); err == nil {
		t.Fatal("did not report changed ownership")
	}
	b, err := os.ReadFile(path)
	if err != nil || string(b) != "replacement" {
		t.Fatalf("replacement lost: %q, %v", b, err)
	}
}
