package platform

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

const MarkerSchema = "curbpack-install-marker:1"

// InstallMarker records a local install (written by install.sh / install.ps1).
type InstallMarker struct {
	Schema     string `json:"schema"`
	Version    string `json:"version"`
	InstallDir string `json:"install_dir"`
	Binary     string `json:"binary"`
	InstalledAt string `json:"installed_at"`
	GOOS       string `json:"goos"`
	GOARCH     string `json:"goarch,omitempty"`
}

// MarkerPath returns the OS-specific install-marker.json path.
func MarkerPath() (string, error) {
	switch runtime.GOOS {
	case "windows":
		base := os.Getenv("LOCALAPPDATA")
		if base == "" {
			home, err := os.UserHomeDir()
			if err != nil {
				return "", err
			}
			base = filepath.Join(home, "AppData", "Local")
		}
		return filepath.Join(base, "Programs", "Curbpack", "install-marker.json"), nil
	default:
		base := os.Getenv("XDG_DATA_HOME")
		if base == "" {
			home, err := os.UserHomeDir()
			if err != nil {
				return "", err
			}
			base = filepath.Join(home, ".local", "share")
		}
		return filepath.Join(base, "curbpack", "install-marker.json"), nil
	}
}

// DefaultInstallDir returns the conventional install directory for this OS.
func DefaultInstallDir() (string, error) {
	switch runtime.GOOS {
	case "windows":
		base := os.Getenv("LOCALAPPDATA")
		if base == "" {
			home, err := os.UserHomeDir()
			if err != nil {
				return "", err
			}
			base = filepath.Join(home, "AppData", "Local")
		}
		return filepath.Join(base, "Programs", "Curbpack"), nil
	default:
		home, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		return filepath.Join(home, ".local", "bin"), nil
	}
}

// BinaryName is curbpack or curbpack.exe.
func BinaryName() string {
	if runtime.GOOS == "windows" {
		return "curbpack.exe"
	}
	return "curbpack"
}

// AliasName is curb or curb.exe.
func AliasName() string {
	if runtime.GOOS == "windows" {
		return "curb.exe"
	}
	return "curb"
}

// ReadMarker loads install-marker.json if present.
func ReadMarker() (*InstallMarker, error) {
	p, err := MarkerPath()
	if err != nil {
		return nil, err
	}
	b, err := os.ReadFile(p)
	if err != nil {
		return nil, err
	}
	var m InstallMarker
	if err := json.Unmarshal(b, &m); err != nil {
		return nil, err
	}
	return &m, nil
}

// WriteMarker writes install-marker.json (used by doctor --repair refresh + tests).
func WriteMarker(version, installDir, binary string) error {
	p, err := MarkerPath()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		return err
	}
	m := InstallMarker{
		Schema:      MarkerSchema,
		Version:     version,
		InstallDir:  installDir,
		Binary:      binary,
		InstalledAt: time.Now().UTC().Format(time.RFC3339),
		GOOS:        runtime.GOOS,
		GOARCH:      runtime.GOARCH,
	}
	b, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	return os.WriteFile(p, b, 0o644)
}

// InstallCommandHint returns the pinned reinstall one-liner for this OS.
func InstallCommandHint() string {
	switch runtime.GOOS {
	case "windows":
		return `irm https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.ps1 | iex`
	default:
		return `curl -fsSL https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.sh | sh`
	}
}

// FormatMarkerDetail is a one-line doctor detail.
func FormatMarkerDetail(m *InstallMarker) string {
	if m == nil {
		return "absent"
	}
	return fmt.Sprintf("schema=%s version=%s dir=%s", m.Schema, m.Version, m.InstallDir)
}
