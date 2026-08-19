package vex

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/clock"
	"github.com/afelin/curbpack/internal/ir"
)

// Document is a pending OpenVEX draft for dependency/advisory rows only.
type Document struct {
	Context    string      `json:"@context"`
	ID         string      `json:"@id"`
	Author     string      `json:"author"`
	Timestamp  string      `json:"timestamp"`
	Version    int         `json:"version"`
	Statements []Statement `json:"statements"`
	Status     string      `json:"status"`
	Note       string      `json:"note"`
	Digest     string      `json:"digest,omitempty"`
	GateDigest string      `json:"gate_digest,omitempty"`
}

// Statement is one OpenVEX statement (pending until attest).
type Statement struct {
	Vulnerability   Vulnerability `json:"vulnerability"`
	Products        []Product     `json:"products"`
	Status          string        `json:"status"`
	Justification   string        `json:"justification,omitempty"`
	ActionStatement string        `json:"action_statement,omitempty"`
}

// Vulnerability identifies an advisory id (not a documentation gate).
type Vulnerability struct {
	ID          string `json:"@id"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

// Product is the product or component under assessment.
type Product struct {
	ID string `json:"@id"`
}

// Advisory is a dependency/advisory row suitable for OpenVEX (PURL-bearing).
type Advisory struct {
	ID          string
	Name        string
	Description string
	PURL        string
	Action      string
}

// FromAdvisories builds pending OpenVEX from dependency/advisory rows only.
// Documentation gate failures belong in GateFailure IR — not as fake CVEs.
func FromAdvisories(product string, advisories []Advisory) Document {
	stmts := make([]Statement, 0, len(advisories))
	for _, a := range advisories {
		id := "https://curbpack.local/advisory/" + a.ID
		prod := "pkg:generic/" + product
		if strings.TrimSpace(a.PURL) != "" {
			prod = a.PURL
		}
		stmts = append(stmts, Statement{
			Vulnerability: Vulnerability{
				ID:          id,
				Name:        firstNonEmpty(a.Name, a.ID),
				Description: a.Description,
			},
			Products:        []Product{{ID: prod}},
			Status:          "under_investigation",
			ActionStatement: a.Action,
		})
	}
	body, _ := json.Marshal(stmts)
	digest := fmt.Sprintf("%x", sha256.Sum256(body))
	seed := digest
	if len(seed) > 16 {
		seed = seed[:16]
	}
	return Document{
		Context:    "https://openvex.dev/ns/v0.2.0",
		ID:         "https://curbpack.local/vex/" + seed,
		Author:     "curbpack",
		Timestamp:  clock.RFC3339(),
		Version:    1,
		Statements: stmts,
		Status:     "draft_pending_attest",
		Note:       "Pending OpenVEX draft for dependency/advisory rows with PURLs only. Documentation gates stay in GateFailure IR — not emitted as CVEs. Bind digest into attest capsule before treating as release evidence. Not a certification.",
		GateDigest: digest,
		Digest:     digest,
	}
}

// FromGateFailures retains compatibility but only maps dependency-shaped gate failures
// (DEP / npm_dep / manifest_dep / SYS_TRACE). Prefer FromAdvisories + watchlist join.
func FromGateFailures(product string, payload ir.GateFailurePayload) Document {
	var adv []Advisory
	for _, f := range payload.Failures {
		if !isDepShaped(f) {
			continue
		}
		purl := ""
		if file := f.ASTCoordinates.TargetFile; strings.Contains(file, "package.json") || strings.HasSuffix(file, "go.mod") {
			purl = "pkg:generic/" + product
		}
		adv = append(adv, Advisory{
			ID:          f.GateID,
			Name:        f.GateID,
			Description: f.SanitizedDescription,
			PURL:        purl,
			Action:      f.Remediation.ActionRequired,
		})
	}
	doc := FromAdvisories(product, adv)
	gateBytes, _ := json.Marshal(payload.Failures)
	doc.GateDigest = fmt.Sprintf("%x", sha256.Sum256(gateBytes))
	return doc
}

func isDepShaped(f ir.Failure) bool {
	id := strings.ToUpper(f.GateID)
	if strings.Contains(id, "DEP") || strings.Contains(id, "AXIOS") || strings.HasPrefix(id, "WL-") {
		return true
	}
	if f.Type == "SYS_TRACE_VIOLATION" {
		return true
	}
	file := f.ASTCoordinates.TargetFile
	return strings.Contains(file, "package.json") || strings.HasSuffix(file, "go.mod") || strings.Contains(file, "lock")
}

func firstNonEmpty(a, b string) string {
	if strings.TrimSpace(a) != "" {
		return a
	}
	return b
}

// Write writes the VEX draft JSON to path (default evidence dir).
func Write(root string, doc Document, outPath string) (string, error) {
	if outPath == "" {
		outPath = filepath.Join(root, ".github", "curbpack", "evidence", "vex-pending.json")
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
