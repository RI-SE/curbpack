package gitutil

import (
	"bytes"
	"encoding/json"
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

// HeadSHA returns the current HEAD commit hash.
// On rev-parse failure (e.g. empty repo), returns ("", err) — never zero SHA with nil error.
func HeadSHA(repoRoot string) (string, error) {
	out, err := runGit(repoRoot, "rev-parse", "HEAD")
	if err != nil {
		return "", err
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

// NotesRef is the write ref for attestation capsules.
const NotesRef = "refs/notes/curbpack"

// NotesShow returns note body for commit from curbpack notes, else legacy cyberready notes.
func NotesShow(repoRoot, commit string) (string, error) {
	out, err := runGit(repoRoot, "notes", "--ref=curbpack", "show", commit)
	if err == nil {
		return out, nil
	}
	out, err2 := runGit(repoRoot, "notes", "--ref=cyberready", "show", commit)
	if err2 != nil {
		return "", err
	}
	return out, nil
}

// NotesAdd writes (force) a note on commit under refs/notes/curbpack only.
func NotesAdd(repoRoot, commit, message string) error {
	_, err := runGit(repoRoot, "notes", "--ref=curbpack", "add", "-f", "-m", message, commit)
	return err
}

// ChangedFiles returns paths changed vs HEAD (staged + unstaged + untracked).
// Paths are slash-normalized relative to repo root.
func ChangedFiles(repoRoot string) (map[string]struct{}, error) {
	out := map[string]struct{}{}
	addLines := func(s string) {
		for _, line := range strings.Split(s, "\n") {
			line = strings.TrimSpace(line)
			if line == "" {
				continue
			}
			// status --porcelain: XY PATH or XY ORIG -> PATH
			if len(line) >= 4 {
				rest := strings.TrimSpace(line[3:])
				if i := strings.Index(rest, " -> "); i >= 0 {
					rest = rest[i+4:]
				}
				rest = strings.Trim(rest, `"`)
				out[filepath.ToSlash(rest)] = struct{}{}
			}
		}
	}
	porcelain, err := runGit(repoRoot, "status", "--porcelain")
	if err != nil {
		return nil, err
	}
	addLines(porcelain)
	// Also include files differing from merge-base / HEAD for committed-but-local? porcelain covers WD.
	// For --diff against last commit content changes already staged:
	diff, err := runGit(repoRoot, "diff", "--name-only", "HEAD")
	if err == nil {
		for _, line := range strings.Split(diff, "\n") {
			line = strings.TrimSpace(line)
			if line != "" {
				out[filepath.ToSlash(line)] = struct{}{}
			}
		}
	}
	return out, nil
}

// parentNoteCapsule is the minimal JSON shape read from git notes for Merkle chaining.
type parentNoteCapsule struct {
	StateHash string `json:"state_hash"`
}

// ParentNoteHash reads the previous commit's note state_hash for Merkle chaining.
// It intentionally ignores any existing note on the current commit so re-attest is reproducible.
func ParentNoteHash(repoRoot, commit string) string {
	prev, err := runGit(repoRoot, "rev-parse", commit+"^")
	if err != nil {
		return ""
	}
	body, err := NotesShow(repoRoot, prev)
	if err != nil || body == "" {
		return ""
	}
	var cap parentNoteCapsule
	if json.Unmarshal([]byte(body), &cap) == nil && cap.StateHash != "" {
		return cap.StateHash
	}
	// Legacy string hack for pre-JSON notes.
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

// LatestNoteCommit returns the most recent commit with a curbpack (or legacy cyberready) note.
func LatestNoteCommit(repoRoot string) (string, error) {
	for _, ref := range []string{"curbpack", "cyberready"} {
		out, err := runGit(repoRoot, "log", "-1", "--notes="+ref, "--format=%H")
		if err == nil && out != "" {
			return out, nil
		}
	}
	return "", fmt.Errorf("no attest notes found")
}
