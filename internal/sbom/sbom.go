package sbom

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

// Summary is a lightweight SBOM digest (not full CycloneDX unless expanded later).
type Summary struct {
	Status      string   `json:"status"`
	Format      string   `json:"format"`
	GeneratedAt string   `json:"generated_at"`
	Source      string   `json:"source,omitempty"`
	PackageCount int     `json:"package_count"`
	Packages    []string `json:"packages,omitempty"`
	Note        string   `json:"note"`
}

// FromLockfiles scans npm/pnpm lockfiles if present.
func FromLockfiles(root string) (Summary, error) {
	now := time.Now().UTC().Format(time.RFC3339)
	base := Summary{
		GeneratedAt: now,
		Note:        "Draft inventory for human review. Not a signed SBOM attestation.",
	}

	if p := filepath.Join(root, "pnpm-lock.yaml"); fileExists(p) {
		pkgs, err := parsePnpmLock(p)
		if err != nil {
			return Summary{}, err
		}
		base.Status = "ok"
		base.Format = "pnpm-lock-summary"
		base.Source = "pnpm-lock.yaml"
		base.PackageCount = len(pkgs)
		base.Packages = truncate(pkgs, 40)
		return base, nil
	}

	if p := filepath.Join(root, "package-lock.json"); fileExists(p) {
		pkgs, err := parseNPMLock(p)
		if err != nil {
			return Summary{}, err
		}
		base.Status = "ok"
		base.Format = "npm-lock-summary"
		base.Source = "package-lock.json"
		base.PackageCount = len(pkgs)
		base.Packages = truncate(pkgs, 40)
		return base, nil
	}

	if p := filepath.Join(root, "package.json"); fileExists(p) {
		pkgs, err := parsePackageJSONDeps(p)
		if err != nil {
			return Summary{}, err
		}
		base.Status = "ok"
		base.Format = "package-json-deps"
		base.Source = "package.json"
		base.PackageCount = len(pkgs)
		base.Packages = pkgs
		base.Note += " No lockfile found — versions may be ranges."
		return base, nil
	}

	return Summary{}, fmt.Errorf("no package-lock.json, pnpm-lock.yaml, or package.json")
}

func fileExists(p string) bool {
	_, err := os.Stat(p)
	return err == nil
}

func truncate(in []string, n int) []string {
	if len(in) <= n {
		return in
	}
	return append(in[:n], fmt.Sprintf("…+%d more", len(in)-n))
}

func parsePackageJSONDeps(path string) ([]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var m struct {
		Dependencies    map[string]string `json:"dependencies"`
		DevDependencies map[string]string `json:"devDependencies"`
	}
	if err := json.Unmarshal(data, &m); err != nil {
		return nil, err
	}
	var out []string
	for k, v := range m.Dependencies {
		out = append(out, k+"@"+v)
	}
	for k, v := range m.DevDependencies {
		out = append(out, k+"@"+v+" (dev)")
	}
	return out, nil
}

func parseNPMLock(path string) ([]string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var lock struct {
		Packages map[string]struct {
			Version string `json:"version"`
		} `json:"packages"`
		Dependencies map[string]struct {
			Version string `json:"version"`
		} `json:"dependencies"`
	}
	if err := json.Unmarshal(data, &lock); err != nil {
		return nil, err
	}
	var out []string
	if len(lock.Packages) > 0 {
		for name, meta := range lock.Packages {
			if name == "" {
				continue
			}
			n := strings.TrimPrefix(name, "node_modules/")
			if strings.Contains(n, "node_modules/") {
				continue
			}
			out = append(out, n+"@"+meta.Version)
		}
		return out, nil
	}
	for name, meta := range lock.Dependencies {
		out = append(out, name+"@"+meta.Version)
	}
	return out, nil
}

func parsePnpmLock(path string) ([]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []string
	inPackages := false
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if strings.HasPrefix(line, "packages:") {
			inPackages = true
			continue
		}
		if inPackages {
			if len(line) > 0 && line[0] != ' ' && line[0] != '\t' && !strings.HasPrefix(line, "packages") {
				break
			}
			trim := strings.TrimSpace(line)
			if strings.HasPrefix(trim, "/") && strings.HasSuffix(trim, ":") {
				pkg := strings.TrimSuffix(trim, ":")
				out = append(out, pkg)
			}
		}
	}
	return out, sc.Err()
}
