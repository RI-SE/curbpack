package platform

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

const MarkerSchema = "curbpack-install-marker:1"

// utf8BOM is stripped on read so PowerShell UTF-8 with BOM markers still parse.
var utf8BOM = []byte{0xEF, 0xBB, 0xBF}

// InstallMarker records a local install (written by install.sh / install.ps1).
type InstallMarker struct {
	Schema      string `json:"schema"`
	Version     string `json:"version"`
	InstallDir  string `json:"install_dir"`
	Binary      string `json:"binary"`
	InstalledAt string `json:"installed_at"`
	GOOS        string `json:"goos"`
	GOARCH      string `json:"goarch,omitempty"`
}

// MarkerPath returns the preferred OS-specific install-marker.json path
// (install dir when CURBPACK_INSTALL_DIR / default applies; else XDG / Programs layout).
func MarkerPath() (string, error) {
	cands, err := markerCandidates()
	if err != nil {
		return "", err
	}
	if len(cands) == 0 {
		return "", fmt.Errorf("no marker path candidates")
	}
	// Prefer an existing marker; else the first candidate (write target).
	for _, p := range cands {
		if _, err := os.Stat(p); err == nil {
			return p, nil
		}
	}
	return cands[0], nil
}

// markerCandidates lists paths to try, in preference order:
// CURBPACK_INSTALL_DIR, default install dir, then conventional data-dir marker.
func markerCandidates() ([]string, error) {
	var out []string
	seen := map[string]bool{}
	add := func(p string) {
		p = filepath.Clean(p)
		if p == "" || p == "." || seen[p] {
			return
		}
		seen[p] = true
		out = append(out, p)
	}

	if d := os.Getenv("CURBPACK_INSTALL_DIR"); d != "" {
		add(filepath.Join(d, "install-marker.json"))
	}
	if def, err := DefaultInstallDir(); err == nil {
		add(filepath.Join(def, "install-marker.json"))
	}
	if conv, err := conventionalMarkerPath(); err == nil {
		add(conv)
	}
	return out, nil
}

// conventionalMarkerPath is the historical XDG / Programs location (Unix data dir;
// Windows default install dir — same as DefaultInstallDir for the default case).
func conventionalMarkerPath() (string, error) {
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
	if d := os.Getenv("CURBPACK_INSTALL_DIR"); d != "" {
		return d, nil
	}
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

// ReadMarker loads install-marker.json if present (BOM-tolerant; custom InstallDir aware).
func ReadMarker() (*InstallMarker, error) {
	cands, err := markerCandidates()
	if err != nil {
		return nil, err
	}
	var lastErr error
	for _, p := range cands {
		b, err := os.ReadFile(p)
		if err != nil {
			lastErr = err
			continue
		}
		b = bytes.TrimPrefix(b, utf8BOM)
		var m InstallMarker
		if err := json.Unmarshal(b, &m); err != nil {
			lastErr = err
			continue
		}
		return &m, nil
	}
	if lastErr != nil {
		return nil, lastErr
	}
	return nil, os.ErrNotExist
}

// WriteMarker writes install-marker.json (used by doctor --repair refresh + tests).
// Prefer CURBPACK_INSTALL_DIR / default install dir so custom InstallDir round-trips.
func WriteMarker(version, installDir, binary string) error {
	var p string
	var err error
	if installDir != "" {
		p = filepath.Join(installDir, "install-marker.json")
	} else {
		p, err = MarkerPath()
		if err != nil {
			return err
		}
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

// DefaultInstallPin is the smoke-verified CLI install tag (scripts/install-manifest.json).
// Action/examples pin remains @v0.5.2 until human tabletop approves bump.
const DefaultInstallPin = "v0.5.4"

// InstallCommandHint returns the reinstall one-liner for this OS (canonical installer on main → smoke-verified binary).
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
