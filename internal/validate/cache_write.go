package validate

import (
	"fmt"
	"os"

	"github.com/afelin/curbpack/internal/outwrite"
	"github.com/afelin/curbpack/internal/pathjail"
)

// writeEvaluationCache replaces each file only after its complete contents have
// been written and synced. The legacy aliases are not a multi-file transaction.
func writeEvaluationCache(root string, payload []byte, action string) error {
	const rel = ".github/curbpack/cache"
	dir, _, err := pathjail.Join(root, rel)
	if err != nil {
		return fmt.Errorf("cache directory: %w", err)
	}
	lock, err := outwrite.Acquire(dir)
	if err != nil {
		return fmt.Errorf("cache lock: %w", err)
	}
	defer func() { _ = lock.Release() }()
	if err = outwrite.EnsureDir(root, dir); err != nil {
		return fmt.Errorf("create cache: %w", err)
	}
	files := []struct {
		name string
		body []byte
	}{
		{"latest_failure.json", payload},
		{"latest_result.json", payload},
		{"latest_action_report.md", []byte(action)},
	}
	// Preflight all destinations before replacing any alias.
	for _, file := range files {
		path, _, err := pathjail.Join(root, rel+"/"+file.name)
		if err != nil {
			return fmt.Errorf("cache %s: %w", file.name, err)
		}
		if st, err := os.Lstat(path); err == nil && !st.Mode().IsRegular() {
			return fmt.Errorf("cache %s: destination must be a regular file", file.name)
		} else if err != nil && !os.IsNotExist(err) {
			return err
		}
	}
	for _, file := range files {
		if err := writeCacheFile(root, rel+"/"+file.name, file.body); err != nil {
			return fmt.Errorf("cache %s: %w", file.name, err)
		}
	}
	return nil
}

func writeCacheFile(root, rel string, body []byte) error {
	path, _, err := pathjail.Join(root, rel)
	if err != nil {
		return err
	}
	return outwrite.WriteFile(root, path, body, 0644)
}
