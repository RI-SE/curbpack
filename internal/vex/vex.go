package vex

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/afelin/cyberready/internal/ir"
)

// Document is a pending OpenVEX draft bound to gate findings.
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
	Vulnerability Vulnerability `json:"vulnerability"`
	Products      []Product     `json:"products"`
	Status        string        `json:"status"`
	Justification string        `json:"justification,omitempty"`
	ActionStatement string      `json:"action_statement,omitempty"`
}

// Vulnerability identifies a finding-derived advisory id.
type Vulnerability struct {
	ID          string `json:"@id"`
	Name        string `json:"name"`
	Description string `json:"description,omitempty"`
}

// Product is the product under assessment.
type Product struct {
	ID string `json:"@id"`
}

// FromGateFailures builds pending OpenVEX statements from gate failures.
func FromGateFailures(product string, payload ir.GateFailurePayload) Document {
	stmts := make([]Statement, 0, len(payload.Failures))
	for _, f := range payload.Failures {
		id := "https://cyberready.local/vuln/" + f.GateID
		stmts = append(stmts, Statement{
			Vulnerability: Vulnerability{
				ID:          id,
				Name:        f.GateID,
				Description: f.SanitizedDescription,
			},
			Products:        []Product{{ID: "pkg:generic/" + product}},
			Status:          "under_investigation",
			ActionStatement: f.Remediation.ActionRequired,
		})
	}
	gateBytes, _ := json.Marshal(payload.Failures)
	gateDigest := fmt.Sprintf("%x", sha256.Sum256(gateBytes))
	body, _ := json.Marshal(stmts)
	digest := fmt.Sprintf("%x", sha256.Sum256(body))
	doc := Document{
		Context:    "https://openvex.dev/ns/v0.2.0",
		ID:         "https://cyberready.local/vex/" + gateDigest[:16],
		Author:     "cyberready",
		Timestamp:  "2024-01-01T00:00:00Z",
		Version:    1,
		Statements: stmts,
		Status:     "draft_pending_attest",
		Note:       "Pending OpenVEX draft from pack gates. Bind digest into attest capsule before treating as release evidence. Not a certification.",
		GateDigest: gateDigest,
		Digest:     digest,
	}
	return doc
}

// Write writes the VEX draft JSON to path (default evidence dir).
func Write(root string, doc Document, outPath string) (string, error) {
	if outPath == "" {
		outPath = filepath.Join(root, ".github", "cyberready", "evidence", "vex-pending.json")
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
