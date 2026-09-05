package validate

import (
	"fmt"
	"os"
	"path/filepath"

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
	if err = os.MkdirAll(dir, 0755); err != nil {
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
	tmp, err := os.CreateTemp(filepath.Dir(path), ".evaluation-*.tmp")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	defer tmp.Close()
	if err = tmp.Chmod(0644); err != nil {
		return err
	}
	if _, err = tmp.Write(body); err != nil {
		return err
	}
	if err = tmp.Sync(); err != nil {
		return err
	}
	if err = tmp.Close(); err != nil {
		return err
	}
	if _, _, err = pathjail.Join(root, rel); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}
