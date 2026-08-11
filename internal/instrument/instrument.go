// Package instrument records a lightweight per-check map: deps + secret-hit count.
// Informational only — not a vulnerability determination or security program.
package instrument

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/afelin/curbpack/internal/paths"
	"github.com/afelin/curbpack/internal/sbom"
)

const (
	schemaVersion   = "1"
	maxFileBytes    = 256 * 1024
	maxFilesScanned = 200
	maxWalkDepth    = 8
	cacheRelDir     = ".github/curbpack/cache"
	instrumentFile  = "instrument.json"
	// Bytes that appear in high-signal secretRE families (PEM -, AKIA A, api_key =/_).
	secretPrefilter = "-Aa="
)

// Same high-signal families as house-policy text_forbid (count-only whisper).
var secretRE = regexp.MustCompile(`(?i)(AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----|api[_-]?key\s*[:=]\s*['"]?[a-zA-Z0-9]{20,})`)

// Dep is one normalized dependency row in the instrument snapshot.
type Dep struct {
	Name    string `json:"name"`
	Version string `json:"version"`
	Eco     string `json:"eco"`
}

// Snapshot is written beside IR cache as instrument.json.
type Snapshot struct {
	SchemaVersion string `json:"schema_version"`
	Deps          []Dep  `json:"deps"`
	DepsFP        string `json:"deps_fp"`
	SecretHits    int    `json:"secret_hits"`
	At            string `json:"at"`
	Note          string `json:"note"`
}

// Path returns the write path for instrument.json under root.
func Path(root string) string {
	return filepath.Join(paths.CacheDir(root), instrumentFile)
}

// Load reads prior instrument.json (new or legacy cache); OK=false when missing/corrupt.
func Load(root string) (Snapshot, bool) {
	b, err := os.ReadFile(paths.ResolveUnderCache(root, instrumentFile))
	if err != nil {
		return Snapshot{}, false
	}
	var s Snapshot
	if err := json.Unmarshal(b, &s); err != nil {
		return Snapshot{}, false
	}
	return s, true
}

// Compute builds a fresh snapshot from the repo tree.
func Compute(root string) Snapshot {
	deps := collectDeps(root)
	fp := fingerprintDeps(deps)
	hits := CountSecretHits(root)
	return Snapshot{
		SchemaVersion: schemaVersion,
		Deps:          deps,
		DepsFP:        fp,
		SecretHits:    hits,
		At:            time.Now().UTC().Format(time.RFC3339),
		Note:          "Instrument panel map — not a security program · not conformity assessment",
	}
}

// Write persists snapshot to cache/instrument.json.
func Write(root string, s Snapshot) error {
	path := Path(root)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	b, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(b, '\n'), 0o644)
}

func collectDeps(root string) []Dep {
	pkgs, _, err := sbom.CollectPackages(root)
	if err != nil {
		return nil
	}
	out := make([]Dep, 0, len(pkgs))
	for _, p := range pkgs {
		eco := p.Ecosystem
		if eco == "" {
			eco = "npm"
		}
		out = append(out, Dep{Name: p.Name, Version: p.Version, Eco: eco})
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Eco != out[j].Eco {
			return out[i].Eco < out[j].Eco
		}
		if out[i].Name != out[j].Name {
			return out[i].Name < out[j].Name
		}
		return out[i].Version < out[j].Version
	})
	return out
}

func fingerprintDeps(deps []Dep) string {
	h := sha256.New()
	for _, d := range deps {
		fmt.Fprintf(h, "%s|%s@%s\n", d.Eco, d.Name, d.Version)
	}
	return hex.EncodeToString(h.Sum(nil))[:16]
}

// CountSecretHits walks capped high-signal paths and counts pattern matches.
// Prefers git ls-files when available; on git failure falls back to WalkDir
// (never returns 0 solely because git failed).
func CountSecretHits(root string) int {
	root = filepath.Clean(root)
	if paths, ok := gitTrackedCandidates(root); ok {
		return countSecretHitsFiles(root, paths)
	}
	return countSecretHitsWalk(root)
}

func gitTrackedCandidates(root string) ([]string, bool) {
	cmd := exec.Command("git", "-C", root, "ls-files", "-z")
	out, err := cmd.Output()
	if err != nil {
		return nil, false
	}
	parts := bytes.Split(out, []byte{0})
	cands := make([]string, 0, 32)
	for _, p := range parts {
		if len(p) == 0 {
			continue
		}
		slash := filepath.ToSlash(string(p))
		if secretScanCandidate(slash) {
			cands = append(cands, slash)
			if len(cands) >= maxFilesScanned {
				break
			}
		}
	}
	return cands, true
}

func countSecretHitsFiles(root string, rels []string) int {
	hits := 0
	for i, rel := range rels {
		if i >= maxFilesScanned {
			break
		}
		path := filepath.Join(root, filepath.FromSlash(rel))
		if matchSecretFile(path) {
			hits++
		}
	}
	return hits
}

func countSecretHitsWalk(root string) int {
	hits := 0
	scanned := 0
	_ = filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil || scanned >= maxFilesScanned {
			if scanned >= maxFilesScanned {
				return filepath.SkipAll
			}
			return nil
		}
		rel, err := filepath.Rel(root, path)
		if err != nil {
			return nil
		}
		slash := filepath.ToSlash(rel)
		if d.IsDir() {
			base := d.Name()
			if base == ".git" || base == "node_modules" || base == "vendor" || base == ".cursor" {
				return filepath.SkipDir
			}
			depth := strings.Count(slash, "/")
			if slash != "." && depth >= maxWalkDepth {
				return filepath.SkipDir
			}
			return nil
		}
		if !secretScanCandidate(slash) {
			return nil
		}
		scanned++
		if matchSecretFile(path) {
			hits++
		}
		return nil
	})
	return hits
}

func matchSecretFile(path string) bool {
	data, err := os.ReadFile(path)
	if err != nil {
		return false
	}
	if len(data) > maxFileBytes {
		data = data[:maxFileBytes]
	}
	if !bytes.ContainsAny(data, secretPrefilter) {
		return false
	}
	return secretRE.Match(data)
}

func secretScanCandidate(rel string) bool {
	base := filepath.Base(rel)
	lower := strings.ToLower(base)
	// Exact / prefix agent-oops paths + plan globs (basename match).
	if strings.HasPrefix(lower, ".env") {
		return true
	}
	if strings.HasSuffix(lower, ".pem") || strings.HasSuffix(lower, ".key") {
		return true
	}
	if strings.Contains(lower, "credential") {
		return true
	}
	switch lower {
	case "id_rsa", "id_ed25519", "credentials.json", "service-account.json":
		return true
	}
	// Existing house-policy doc paths (whisper parity).
	switch rel {
	case "README.md", "SECURITY.md", ".well-known/security.txt":
		return true
	}
	return false
}

// DepDelta returns +added/−removed package name counts between two fingerprints/sets.
func DepDelta(prior, now Snapshot) (added, removed int) {
	if prior.DepsFP == now.DepsFP {
		return 0, 0
	}
	prev := map[string]struct{}{}
	for _, d := range prior.Deps {
		prev[d.Eco+"|"+d.Name] = struct{}{}
	}
	cur := map[string]struct{}{}
	for _, d := range now.Deps {
		cur[d.Eco+"|"+d.Name] = struct{}{}
	}
	for k := range cur {
		if _, ok := prev[k]; !ok {
			added++
		}
	}
	for k := range prev {
		if _, ok := cur[k]; !ok {
			removed++
		}
	}
	return added, removed
}
