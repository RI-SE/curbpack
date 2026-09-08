package exportx

import (
	"fmt"
	"path/filepath"
	"sort"
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
	if err := outwrite.Contain(permitted, destAbs); err != nil {
		return err
	}
	lock, err := outwrite.Acquire(permitted)
	if err != nil {
		return err
	}
	defer func() { _ = lock.Release() }()
	return outwrite.WriteFile(permitted, destAbs, data, 0o644)
}

// writeContainedSetAt retains one lease while staging a related file set.
func writeContainedSetAt(repoRoot string, files map[string][]byte) error {
	repoAbs, err := filepath.Abs(repoRoot)
	if err != nil {
		return err
	}
	var names []string
	for name := range files {
		names = append(names, name)
	}
	sort.Strings(names)
	var artifacts []outwrite.Artifact
	permitted := ""
	for _, name := range names {
		dest, err := filepath.Abs(name)
		if err != nil {
			return err
		}
		root := repoAbs
		if rel, err := filepath.Rel(repoAbs, dest); err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
			root = filepath.Dir(dest)
		}
		if permitted != "" && permitted != root {
			return fmt.Errorf("related output files require one permitted root")
		}
		permitted = root
		if err := outwrite.Contain(root, dest); err != nil {
			return err
		}
		artifacts = append(artifacts, outwrite.Artifact{PermittedRoot: root, Path: dest, Data: files[name]})
	}
	if len(artifacts) == 0 {
		return nil
	}
	lock, err := outwrite.Acquire(permitted)
	if err != nil {
		return err
	}
	defer lock.Release()
	return outwrite.Publish(artifacts)
}
