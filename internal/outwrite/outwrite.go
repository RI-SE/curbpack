// Package outwrite is the shared output containment policy for release packs,
// exports, evidence, and caches.
//
// Policy:
//   - Default destinations stay inside the repository (permitted root = repo).
//   - An explicit output directory is its own permitted root.
//   - Symlink escapes and .git destinations are refused before any write.
//   - Writes are staged, synced, then published by rename.
//   - ExclusiveLock serializes concurrent friendly writers only; O_EXCL is not a
//     hostile filesystem race barrier.
package outwrite

import (
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/afelin/curbpack/internal/pathjail"
)

const (
	// LockFileName is placed under the permitted root for exclusive writers.
	LockFileName = ".curbpack-outwrite.lock"
)

// DirDest resolves a directory destination.
// Empty outDir → dest = repo/defaultRel with permitted root = repo.
// Non-empty outDir → dest = abs(outDir) and permitted root = that directory.
func DirDest(repoRoot, outDir, defaultRel string) (permitted, dest string, err error) {
	repoAbs, err := filepath.Abs(repoRoot)
	if err != nil {
		return "", "", err
	}
	outDir = strings.TrimSpace(outDir)
	if outDir == "" {
		if strings.TrimSpace(defaultRel) == "" {
			return "", "", fmt.Errorf("empty default output path")
		}
		dest, _, err = pathjail.Join(repoAbs, defaultRel)
		if err != nil {
			return "", "", fmt.Errorf("output destination: %w", err)
		}
		return repoAbs, dest, nil
	}
	if pathjail.IsWindowsAbs(outDir) && !filepath.IsAbs(outDir) {
		// Drive/UNC form on a non-Windows host: refuse rather than mis-join.
		return "", "", fmt.Errorf("absolute path refused")
	}
	destAbs, err := filepath.Abs(outDir)
	if err != nil {
		return "", "", err
	}
	if err := ensureContainableDir(destAbs); err != nil {
		return "", "", err
	}
	// Explicit out-dir is its own permitted root; still refuse .git / reserved.
	if err := refuseGitOrReservedAbs(destAbs); err != nil {
		return "", "", err
	}
	return destAbs, destAbs, nil
}

// FileDest resolves a file destination.
// Empty outPath → dest = repo/defaultRel, permitted = repo.
// Relative outPath → dest under repo, permitted = repo.
// Absolute outPath → dest = that path, permitted = its parent directory.
func FileDest(repoRoot, outPath, defaultRel string) (permitted, dest string, err error) {
	repoAbs, err := filepath.Abs(repoRoot)
	if err != nil {
		return "", "", err
	}
	outPath = strings.TrimSpace(outPath)
	if outPath == "" {
		if strings.TrimSpace(defaultRel) == "" {
			return "", "", fmt.Errorf("empty default output path")
		}
		dest, _, err = pathjail.Join(repoAbs, defaultRel)
		if err != nil {
			return "", "", fmt.Errorf("output destination: %w", err)
		}
		return repoAbs, dest, nil
	}
	if pathjail.IsWindowsAbs(outPath) && !filepath.IsAbs(outPath) {
		return "", "", fmt.Errorf("absolute path refused")
	}
	if filepath.IsAbs(outPath) {
		destAbs, err := filepath.Abs(outPath)
		if err != nil {
			return "", "", err
		}
		parent := filepath.Dir(destAbs)
		if err := ensureContainableDir(parent); err != nil {
			return "", "", err
		}
		if err := Contain(parent, destAbs); err != nil {
			return "", "", err
		}
		return parent, destAbs, nil
	}
	dest, _, err = pathjail.Join(repoAbs, outPath)
	if err != nil {
		return "", "", fmt.Errorf("output destination: %w", err)
	}
	return repoAbs, dest, nil
}

// Contain refuses paths that escape permittedRoot after symlink evaluation
// or resolve under .git.
func Contain(permittedRoot, fullPath string) error {
	rootAbs, err := filepath.Abs(permittedRoot)
	if err != nil {
		return err
	}
	fullAbs, err := filepath.Abs(fullPath)
	if err != nil {
		return err
	}
	if err := refuseGitOrReservedAbs(fullAbs); err != nil {
		return err
	}
	return pathjail.ContainAbs(rootAbs, fullAbs)
}

// EnsureDir creates dirAbs when missing, after containment under permittedRoot.
func EnsureDir(permittedRoot, dirAbs string) error {
	if err := Contain(permittedRoot, dirAbs); err != nil {
		return err
	}
	if st, err := os.Lstat(dirAbs); err == nil {
		if st.Mode()&os.ModeSymlink != 0 {
			if err := Contain(permittedRoot, dirAbs); err != nil {
				return err
			}
			return nil
		}
		if !st.IsDir() {
			return fmt.Errorf("output path exists and is not a directory")
		}
		return nil
	} else if !os.IsNotExist(err) {
		return err
	}
	if err := os.MkdirAll(dirAbs, 0o755); err != nil {
		return err
	}
	return Contain(permittedRoot, dirAbs)
}

// WriteFile stages complete contents, syncs, re-checks containment, then renames.
func WriteFile(permittedRoot, destAbs string, data []byte, mode os.FileMode) error {
	if mode == 0 {
		mode = 0o644
	}
	if err := Contain(permittedRoot, destAbs); err != nil {
		return err
	}
	parent := filepath.Dir(destAbs)
	if err := EnsureDir(permittedRoot, parent); err != nil {
		return err
	}
	if st, err := os.Lstat(destAbs); err == nil {
		if st.Mode()&os.ModeSymlink != 0 {
			if err := Contain(permittedRoot, destAbs); err != nil {
				return err
			}
		} else if !st.Mode().IsRegular() {
			return fmt.Errorf("destination must be a regular file")
		}
	} else if !os.IsNotExist(err) {
		return err
	}

	tmp, err := os.CreateTemp(parent, ".curbpack-out-*.tmp")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	defer func() { _ = os.Remove(tmpName) }()

	if err := tmp.Chmod(mode); err != nil {
		_ = tmp.Close()
		return err
	}
	if _, err := tmp.Write(data); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	if err := Contain(permittedRoot, destAbs); err != nil {
		return err
	}
	return os.Rename(tmpName, destAbs)
}

// ExclusiveLock serializes cooperative writers, including separate goroutines.
// A caller must retain the handle for the entire operation; PID equality never
// grants another caller ownership. This is not a hostile filesystem race barrier.
type ExclusiveLock struct {
	mu   sync.Mutex
	path string
	f    *os.File
}

// Acquire takes an exclusive lock. Recovery is always an explicit operation;
// neither the age of a lock nor sharing its PID permits taking it over.
func Acquire(permittedRoot string) (*ExclusiveLock, error) {
	rootAbs, err := filepath.Abs(permittedRoot)
	if err != nil {
		return nil, err
	}
	if err := EnsureDir(rootAbs, rootAbs); err != nil {
		return nil, err
	}
	lockPath := filepath.Join(rootAbs, LockFileName)
	if err := Contain(rootAbs, lockPath); err != nil {
		return nil, err
	}
	f, err := os.OpenFile(lockPath, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		if os.IsExist(err) {
			return nil, fmt.Errorf("exclusive writer lock busy at %s; after the owner exits, use curbpack recover-lock %q", lockPath, rootAbs)
		}
		return nil, err
	}
	lock := &ExclusiveLock{path: lockPath, f: f}
	body := fmt.Sprintf("pid=%d\nstarted=%s\nnote=cooperative-lock-not-hostile-fs-barrier\n", os.Getpid(), time.Now().UTC().Format(time.RFC3339))
	if _, err := f.WriteString(body); err != nil {
		_ = lock.Release()
		return nil, err
	}
	if err := f.Sync(); err != nil {
		_ = lock.Release()
		return nil, err
	}
	return lock, nil
}

// Release is idempotent and refuses to delete a replacement lock.
func (l *ExclusiveLock) Release() error {
	if l == nil {
		return nil
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	if l.f == nil {
		return nil
	}
	f := l.f
	l.f = nil
	owned, err := f.Stat()
	current, statErr := os.Lstat(l.path)
	closeErr := f.Close()
	if err != nil {
		return err
	}
	if os.IsNotExist(statErr) {
		return closeErr
	}
	if statErr != nil {
		return statErr
	}
	if !os.SameFile(owned, current) {
		return fmt.Errorf("writer lock changed; replacement preserved")
	}
	if err := os.Remove(l.path); err != nil {
		return err
	}
	return closeErr
}

// RecoverStale explicitly removes a lock whose recorded process is known dead.
// Live, unreadable, malformed and symlink locks require operator investigation.
// A separate exclusive guard serializes cooperative recovery attempts. If a
// recovery itself is interrupted, its guard must be inspected by the operator.
func RecoverStale(permittedRoot string) error {
	root, err := filepath.Abs(permittedRoot)
	if err != nil {
		return err
	}
	path := filepath.Join(root, LockFileName)
	if err := Contain(root, path); err != nil {
		return err
	}
	guard, err := os.OpenFile(path+".recovery", os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
	if err != nil {
		return fmt.Errorf("recovery guard: %w", err)
	}
	defer func() { _ = guard.Close(); _ = os.Remove(path + ".recovery") }()
	st, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if !st.Mode().IsRegular() {
		return fmt.Errorf("lock must be a regular file; inspect manually")
	}
	body, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	pid := 0
	for _, line := range strings.Split(string(body), "\n") {
		if strings.HasPrefix(line, "pid=") {
			pid, err = strconv.Atoi(strings.TrimPrefix(line, "pid="))
			break
		}
	}
	if err != nil || pid <= 0 {
		return fmt.Errorf("lock owner is unknown; inspect manually")
	}
	if pidAlive(pid) {
		return fmt.Errorf("lock owner PID %d is alive or cannot be verified dead", pid)
	}
	current, err := os.Lstat(path)
	if err != nil {
		return err
	}
	if !os.SameFile(st, current) {
		return fmt.Errorf("lock changed during recovery; preserved")
	}
	return os.Remove(path)
}

func ensureContainableDir(dirAbs string) error {
	if err := refuseGitOrReservedAbs(dirAbs); err != nil {
		return err
	}
	return pathjail.ContainAbs(dirAbs, dirAbs)
}

func refuseGitOrReservedAbs(abs string) error {
	slash := strings.ReplaceAll(filepath.ToSlash(abs), `\`, `/`)
	slash = strings.TrimPrefix(slash, filepath.ToSlash(filepath.VolumeName(abs)))
	if strings.Contains(slash, ":") {
		return fmt.Errorf("Windows drive-relative or alternate stream path refused")
	}
	for _, p := range strings.Split(slash, "/") {
		if pathjail.IsReservedDeviceName(p) {
			return fmt.Errorf("reserved device name refused")
		}
		if strings.EqualFold(pathjail.NormalizeSegment(p), ".git") {
			return fmt.Errorf("path under .git refused")
		}
	}
	return nil
}

// SaveFile resolves an explicitly supplied destination (or repository default),
// holds the writer lock and publishes complete bytes. Callers already holding
// a lock use WriteFile with that operation's original permitted root.
func SaveFile(repoRoot, outPath, defaultRel string, data []byte, mode os.FileMode) (string, error) {
	permitted, dest, err := FileDest(repoRoot, outPath, defaultRel)
	if err != nil {
		return "", err
	}
	lock, err := Acquire(permitted)
	if err != nil {
		return "", err
	}
	defer lock.Release()
	if err := WriteFile(permitted, dest, data, mode); err != nil {
		return "", err
	}
	return dest, nil
}

// Holds verifies the explicit lease belongs to this exact permitted root and
// still owns its lock. It does not infer ownership from the calling process.
func (l *ExclusiveLock) Holds(root string) error {
	if l == nil {
		return fmt.Errorf("writer lease is required")
	}
	l.mu.Lock()
	defer l.mu.Unlock()
	abs, err := filepath.Abs(root)
	if err != nil {
		return err
	}
	if l.f == nil || l.path != filepath.Join(abs, LockFileName) {
		return fmt.Errorf("writer lease does not own permitted root")
	}
	owned, err := l.f.Stat()
	if err != nil {
		return err
	}
	current, err := os.Lstat(l.path)
	if err != nil {
		return err
	}
	if !os.SameFile(owned, current) {
		return fmt.Errorf("writer lease replaced")
	}
	return nil
}
