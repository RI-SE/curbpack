package exportx

import (
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/outwrite"
)

// writeContained resolves dest and stages a single-file write under output policy.
func writeContained(repoRoot, outPath, defaultRel string, data []byte) (string, error) {
	permitted, dest, err := outwrite.FileDest(repoRoot, outPath, defaultRel)
	if err != nil {
		return "", err
	}
	lock, err := outwrite.Acquire(permitted)
	if err != nil {
		return "", err
	}
	defer func() { _ = lock.Release() }()
	if err := outwrite.WriteFile(permitted, dest, data, 0o644); err != nil {
		return "", err
	}
	return dest, nil
}

// writeContainedAt stages a write to an already-resolved path using output policy.
func writeContainedAt(repoRoot, destAbs string, data []byte) error {
	repoAbs, err := filepath.Abs(repoRoot)
	if err != nil {
		return err
	}
	destAbs, err = filepath.Abs(destAbs)
	if err != nil {
		return err
	}
	permitted := repoAbs
	if rel, rerr := filepath.Rel(repoAbs, destAbs); rerr != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		permitted = filepath.Dir(destAbs)
	}
	lock, err := outwrite.Acquire(permitted)
	if err != nil {
		return err
	}
	defer func() { _ = lock.Release() }()
	return outwrite.WriteFile(permitted, destAbs, data, 0o644)
}
