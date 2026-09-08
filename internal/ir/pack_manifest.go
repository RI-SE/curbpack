package ir

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"sort"
)

const PackManifestSchemaVersion = "curbpack-pack-manifest:1"
const PackManifestFile = "pack-manifest.json"

// PackArtifact binds exact published bytes; hashes establish self-consistency,
// not who produced the pack or whether the underlying claims are true.
type PackArtifact struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Size   int64  `json:"size"`
}

type PackManifest struct {
	SchemaVersion    string         `json:"schema_version"`
	ConformityClaim  string         `json:"conformity_claim"`
	EvaluationDigest string         `json:"evaluation_digest"`
	ReceiptDigest    string         `json:"receipt_digest"`
	Artifacts        []PackArtifact `json:"artifacts"`
}

func RequiredPackArtifacts() []string {
	return []string{"01-gate-failures.json", "02-action-report.md", "03-executive-summary.md", "04-sbom-summary.json", "05-vex-draft.json", "06-gate-failures.sarif", "07-watchlist-sbom-join.json", "buyer-onepager.html", "proof-index.html", "evaluation.json", "run-receipt.json"}
}

func BytesDigest(raw []byte) string { return fmt.Sprintf("%x", sha256.Sum256(raw)) }

func NewPackManifest(files map[string][]byte) (PackManifest, error) {
	m := PackManifest{SchemaVersion: PackManifestSchemaVersion, ConformityClaim: ConformityClaimNone, EvaluationDigest: BytesDigest(files["evaluation.json"]), ReceiptDigest: BytesDigest(files["run-receipt.json"]), Artifacts: []PackArtifact{}}
	for name, raw := range files {
		m.Artifacts = append(m.Artifacts, PackArtifact{Path: name, SHA256: BytesDigest(raw), Size: int64(len(raw))})
	}
	sort.Slice(m.Artifacts, func(i, j int) bool { return m.Artifacts[i].Path < m.Artifacts[j].Path })
	return m, ValidatePackManifest(m)
}

func ValidatePackManifest(m PackManifest) error {
	if m.SchemaVersion != PackManifestSchemaVersion || m.ConformityClaim != ConformityClaimNone || !fullSHA256.MatchString(m.EvaluationDigest) || !fullSHA256.MatchString(m.ReceiptDigest) {
		return fmt.Errorf("invalid pack manifest contract")
	}
	seen := map[string]PackArtifact{}
	prev := ""
	for _, a := range m.Artifacts {
		if !validInputPath(a.Path) || a.Path == "." || a.Path == PackManifestFile || a.Path <= prev || a.Size < 0 || !fullSHA256.MatchString(a.SHA256) {
			return fmt.Errorf("invalid, duplicate or unsorted artifact")
		}
		seen[a.Path] = a
		prev = a.Path
	}
	for _, name := range RequiredPackArtifacts() {
		if _, ok := seen[name]; !ok {
			return fmt.Errorf("manifest omits required artifact %s", name)
		}
	}
	if seen["evaluation.json"].SHA256 != m.EvaluationDigest || seen["run-receipt.json"].SHA256 != m.ReceiptDigest {
		return fmt.Errorf("manifest object binding mismatch")
	}
	return nil
}

func MarshalPackManifest(m PackManifest) ([]byte, error) {
	if err := ValidatePackManifest(m); err != nil {
		return nil, err
	}
	b, err := json.MarshalIndent(m, "", "  ")
	return append(b, '\n'), err
}

func ParsePackManifest(raw []byte) (PackManifest, error) {
	var m PackManifest
	if err := json.Unmarshal(raw, &m); err != nil {
		return m, err
	}
	canonical, err := MarshalPackManifest(m)
	if err != nil {
		return m, err
	}
	if !bytes.Equal(raw, canonical) {
		return m, fmt.Errorf("noncanonical or unrecognized manifest fields")
	}
	return m, nil
}

func VerifyPackArtifact(a PackArtifact, raw []byte) error {
	if int64(len(raw)) != a.Size || BytesDigest(raw) != a.SHA256 {
		return fmt.Errorf("artifact size or SHA-256 mismatch")
	}
	return nil
}
