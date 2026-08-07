package gitutil

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// RepoRoot walks up from cwd (or start) until .git is found.
func RepoRoot(start string) (string, error) {
	dir := start
	if dir == "" {
		var err error
		dir, err = os.Getwd()
		if err != nil {
			return "", err
		}
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, ".git")); err == nil {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("not a git repository")
		}
		dir = parent
	}
}

func runGit(dir string, args ...string) (string, error) {
	cmd := exec.Command("git", args...)
	cmd.Dir = dir
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = err.Error()
		}
		return "", fmt.Errorf("git %s: %s", strings.Join(args, " "), msg)
	}
	return strings.TrimSpace(stdout.String()), nil
}

// HeadSHA returns the current HEAD commit hash, or zeros if no commits yet.
func HeadSHA(repoRoot string) (string, error) {
	out, err := runGit(repoRoot, "rev-parse", "HEAD")
	if err != nil {
		return "0000000000000000000000000000000000000000", nil
	}
	return out, nil
}

// IsDirty reports uncommitted changes (fail-safe true on error).
func IsDirty(repoRoot string) bool {
	out, err := runGit(repoRoot, "status", "--porcelain")
	if err != nil {
		return true
	}
	return out != ""
}

const NotesRef = "refs/notes/cyberready"

// NotesShow returns note body for commit, or empty if missing.
func NotesShow(repoRoot, commit string) (string, error) {
	out, err := runGit(repoRoot, "notes", "--ref=cyberready", "show", commit)
	if err != nil {
		return "", err
	}
	return out, nil
}

// NotesAdd writes (force) a note on commit.
func NotesAdd(repoRoot, commit, message string) error {
	_, err := runGit(repoRoot, "notes", "--ref=cyberready", "add", "-f", "-m", message, commit)
	return err
}

// ParentNoteHash reads previous note's state_hash for Merkle chaining, if any.
func ParentNoteHash(repoRoot, commit string) string {
	body, err := NotesShow(repoRoot, commit)
	if err != nil || body == "" {
		// Try previous commit's note
		prev, err := runGit(repoRoot, "rev-parse", "HEAD^")
		if err != nil {
			return ""
		}
		body, err = NotesShow(repoRoot, prev)
		if err != nil {
			return ""
		}
	}
	// Best-effort extract "state_hash" from JSON without full unmarshal dependency here
	const key = `"state_hash"`
	idx := strings.Index(body, key)
	if idx < 0 {
		return ""
	}
	rest := body[idx+len(key):]
	q1 := strings.Index(rest, `"`)
	if q1 < 0 {
		return ""
	}
	rest = rest[q1+1:]
	q2 := strings.Index(rest, `"`)
	if q2 < 0 {
		return ""
	}
	return rest[:q2]
}
