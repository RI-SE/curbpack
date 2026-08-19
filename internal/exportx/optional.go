package exportx

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	"github.com/afelin/curbpack/internal/clock"
	"github.com/afelin/curbpack/internal/sbom"
	"github.com/afelin/curbpack/internal/validate"
)

// WriteSPDXOptional writes a minimal SPDX-JSON mirror of components (opt-in; default off).
func WriteSPDXOptional(root, outPath string) (string, error) {
	pkgs, source, err := sbom.CollectPackages(root)
	if err != nil && !sbom.IsUnavailable(err) {
		return "", err
	}
	if outPath == "" {
		outPath = filepath.Join(root, ".github", "curbpack", "evidence", "sbom.spdx.json")
	}
	docs := map[string]any{
		"spdxVersion":       "SPDX-2.3",
		"dataLicense":       "CC0-1.0",
		"SPDXID":            "SPDXRef-DOCUMENT",
		"name":              filepath.Base(root) + "-sbom",
		"documentNamespace": "https://curbpack.local/spdx/" + filepath.Base(root),
		"creationInfo": map[string]any{
			"created":  clock.RFC3339(),
			"creators": []string{"Tool: curbpack"},
			"comment":  "Optional SPDX mirror of component list — not a certification. Source=" + source,
		},
		"packages": spdxPackages(pkgs),
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return "", err
	}
	b, err := json.MarshalIndent(docs, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(outPath, append(b, '\n'), 0o644); err != nil {
		return "", err
	}
	return outPath, nil
}

func spdxPackages(pkgs []sbom.Package) []map[string]any {
	sorted := append([]sbom.Package(nil), pkgs...)
	sort.Slice(sorted, func(i, j int) bool {
		if sorted[i].Name != sorted[j].Name {
			return sorted[i].Name < sorted[j].Name
		}
		return sorted[i].Version < sorted[j].Version
	})
	out := make([]map[string]any, 0, len(sorted))
	for i, p := range sorted {
		out = append(out, map[string]any{
			"SPDXID":           fmt.Sprintf("SPDXRef-Package-%d", i+1),
			"name":             p.Name,
			"versionInfo":      p.Version,
			"downloadLocation": "NOASSERTION",
		})
	}
	return out
}

// WriteSLSAOptional writes a minimal in-toto/SLSA-shaped sidecar around state digests (opt-in).
func WriteSLSAOptional(root, outPath string) (string, error) {
	res, err := validate.Run(validate.Options{RepoRoot: root, Quiet: true})
	if err != nil {
		return "", err
	}
	gateBytes, _ := json.Marshal(res.Payload.Failures)
	gateDigest := fmt.Sprintf("%x", sha256.Sum256(gateBytes))
	sbomPath := filepath.Join(root, ".github", "curbpack", "evidence", "sbom.cdx.json")
	sbomDig := sbom.FileDigest(sbomPath)
	predicate := map[string]any{
		"_type": "https://slsa.dev/provenance/v0.2",
		"buildType": "https://curbpack.local/slsa/prepare-release",
		"builder": map[string]any{"id": "curbpack"},
		"invocation": map[string]any{
			"configSource": map[string]any{"uri": "local", "digest": map[string]string{"sha256": gateDigest}},
		},
		"materials": []map[string]any{
			{"uri": "gate_failures", "digest": map[string]string{"sha256": gateDigest}},
			{"uri": "sbom.cdx.json", "digest": map[string]string{"sha256": sbomDig}},
		},
		"metadata": map[string]any{
			"buildFinishedOn": clock.RFC3339(),
			"completeness":    map[string]any{"parameters": false, "environment": false, "materials": false},
			"comment":         "Optional SLSA-shaped sidecar wrapping local digests — does not replace Git Notes attest honesty. Not a certification.",
		},
	}
	doc := map[string]any{
		"_type": "https://in-toto.io/Statement/v0.1",
		"subject": []map[string]any{
			{"name": filepath.Base(root), "digest": map[string]string{"sha256": gateDigest}},
		},
		"predicateType": "https://slsa.dev/provenance/v0.2",
		"predicate":     predicate,
	}
	if outPath == "" {
		outPath = filepath.Join(root, ".github", "curbpack", "evidence", "slsa-sidecar.json")
	}
	if err := os.MkdirAll(filepath.Dir(outPath), 0o755); err != nil {
		return "", err
	}
	b, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(outPath, append(b, '\n'), 0o644); err != nil {
		return "", err
	}
	return outPath, nil
}
