package outwrite

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

// Artifact is a complete file to publish under its operation's permitted root.
// The caller holds the corresponding writer leases throughout Publish.
type Artifact struct {
	PermittedRoot string
	Path          string
	Data          []byte
	Mode          os.FileMode
}

// Publish preflights every destination and stages all bytes before replacing any
// artifact. Entries are published in order; put a completion manifest last.
// Before that final entry, every preceding file is read back and checked.
// Interrupted renames can leave a mixed set: readers must verify the manifest.
// This is cooperative serialization, not a filesystem transaction or race jail.
func Publish(files []Artifact) error {
	var errs []error
	seen := map[string]bool{}
	for _, f := range files {
		abs, err := filepath.Abs(f.Path)
		if err != nil {
			errs = append(errs, err)
			continue
		}
		if seen[abs] {
			errs = append(errs, fmt.Errorf("duplicate publication destination: %s", f.Path))
		}
		seen[abs] = true
		if err := preflightArtifact(f); err != nil {
			errs = append(errs, fmt.Errorf("publish %s: %w", filepath.Base(f.Path), err))
		}
	}
	if len(errs) > 0 {
		return errors.Join(errs...)
	}
	staged := make([]string, 0, len(files))
	defer func() {
		for _, name := range staged {
			_ = os.Remove(name)
		}
	}()
	for _, f := range files {
		parent := filepath.Dir(f.Path)
		if err := EnsureDir(f.PermittedRoot, parent); err != nil {
			return err
		}
		tmp, err := os.CreateTemp(parent, ".curbpack-out-*.tmp")
		if err != nil {
			return err
		}
		staged = append(staged, tmp.Name())
		mode := f.Mode
		if mode == 0 {
			mode = 0644
		}
		if err = tmp.Chmod(mode); err == nil {
			_, err = tmp.Write(f.Data)
		}
		if err == nil {
			err = tmp.Sync()
		}
		closeErr := tmp.Close()
		if err != nil {
			return err
		}
		if closeErr != nil {
			return closeErr
		}
		raw, err := os.ReadFile(tmp.Name())
		if err != nil {
			return err
		}
		if !bytes.Equal(raw, f.Data) {
			return fmt.Errorf("staged artifact verification failed")
		}
	}
	for i, f := range files {
		if i == len(files)-1 {
			for _, prior := range files[:i] {
				if err := preflightArtifact(prior); err != nil {
					return err
				}
				raw, err := os.ReadFile(prior.Path)
				if err != nil {
					return err
				}
				if !bytes.Equal(raw, prior.Data) {
					return fmt.Errorf("published artifact changed before completion")
				}
			}
		}
		if err := preflightArtifact(f); err != nil {
			return err
		}
		if err := os.Rename(staged[i], f.Path); err != nil {
			return err
		}
	}
	return nil
}

func preflightArtifact(f Artifact) error {
	if err := Contain(f.PermittedRoot, f.Path); err != nil {
		return err
	}
	st, err := os.Lstat(f.Path)
	if err == nil && !st.Mode().IsRegular() {
		return fmt.Errorf("destination must be a regular file")
	}
	if err != nil && !os.IsNotExist(err) {
		return err
	}
	// Check existing ancestors without creating directories.
	for dir := filepath.Dir(f.Path); ; dir = filepath.Dir(dir) {
		st, err := os.Stat(dir)
		if err == nil {
			if !st.IsDir() {
				return fmt.Errorf("destination ancestor is not a directory")
			}
			break
		}
		if !os.IsNotExist(err) {
			return err
		}
		if filepath.Dir(dir) == dir {
			return err
		}
	}
	return nil
}
