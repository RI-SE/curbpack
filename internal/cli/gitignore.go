package cli

import (
	"os"
	"path/filepath"
	"strings"
)

// curbpackGitignoreEntries are product-repo ignores so cache/evidence writes
// do not dirty OCC on the golden path (check/attest).
var curbpackGitignoreEntries = []string{
	".github/curbpack/cache/",
	".github/curbpack/evidence/",
}

// ensureCurbpackGitignore appends cache/evidence ignores to .gitignore (create if
// missing). Idempotent; never removes or rewrites unrelated lines.
func ensureCurbpackGitignore(root string) (added []string, err error) {
	path := filepath.Join(root, ".gitignore")
	existing := ""
	data, readErr := os.ReadFile(path)
	if readErr == nil {
		existing = string(data)
	} else if !os.IsNotExist(readErr) {
		return nil, readErr
	}

	have := map[string]bool{}
	for _, line := range strings.Split(existing, "\n") {
		have[strings.TrimSpace(line)] = true
	}

	var b strings.Builder
	b.WriteString(existing)
	if existing != "" && !strings.HasSuffix(existing, "\n") {
		b.WriteByte('\n')
	}

	for _, entry := range curbpackGitignoreEntries {
		if have[entry] {
			continue
		}
		b.WriteString(entry)
		b.WriteByte('\n')
		added = append(added, entry)
		have[entry] = true
	}
	if len(added) == 0 {
		return nil, nil
	}
	if err := os.WriteFile(path, []byte(b.String()), 0o644); err != nil {
		return nil, err
	}
	return added, nil
}
