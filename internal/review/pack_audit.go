package review

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"

	"github.com/afelin/curbpack/internal/ir"
)

// Assessment names one trust dimension. Verification is limited to Detail's
// scope; passing file hashes never establishes authenticity or applicability.
type Assessment struct {
	Status string `json:"status"`
	Detail string `json:"detail"`
}

type PackAudit struct {
	SchemaVersion       string     `json:"schema_version"`
	Integrity           Assessment `json:"integrity"`
	Authenticity        Assessment `json:"authenticity"`
	Completeness        Assessment `json:"completeness"`
	Applicability       Assessment `json:"applicability"`
	SubjectCommitStatus string     `json:"subject_commit_status"`
	EvaluationDigest    string     `json:"evaluation_digest,omitempty"`
	AsOf                string     `json:"as_of,omitempty"`
	ConformityClaim     string     `json:"conformity_claim"`
}

func newPackAudit(subject string) *PackAudit {
	status := "unavailable"
	if subject != "" {
		status = "claimed"
	}
	return &PackAudit{
		SchemaVersion: "curbpack-pack-audit:1", ConformityClaim: ir.ConformityClaimNone,
		Integrity:           Assessment{"unverified", "No complete versioned artifact manifest verified."},
		Authenticity:        Assessment{"unverified", "No independently selected signer trust policy was applied; embedded claims and matching hashes do not identify a trusted producer."},
		Completeness:        Assessment{"unverified", "Required manifest scope has not been established; document presence is not complete product evidence."},
		Applicability:       Assessment{"not_assessed", "The recipient's intended subject, pack policy and time requirements were not supplied."},
		SubjectCommitStatus: status,
	}
}

func auditPack(rep *Report, root string, budget *readBudget, payload ir.GateFailurePayload, payloadOK bool, paths []string) {
	audit := newPackAudit(rep.SubjectCommit)
	rep.Audit = audit
	fail := func(id, detail string) {
		audit.Integrity = Assessment{"failed", detail}
		add(rep, Finding{ID: "integrity:" + id, Category: "digest", State: StateContradicted, Cause: CauseSelfDisagree, Detail: detail})
	}
	raw, truncated, err := readCapped(root, ir.PackManifestFile, budget)
	if err != nil || truncated {
		if os.IsNotExist(err) && payload.EvaluationDigest == "" {
			return
		} // historical adapter: unknown, never invented verification
		audit.Completeness = Assessment{"failed", "Versioned pack manifest is missing, unreadable or exceeds the read limit."}
		fail("manifest-unavailable", audit.Completeness.Detail)
		return
	}
	m, err := ir.ParsePackManifest(raw)
	if err != nil {
		fail("manifest-contract", "Pack manifest schema, fields or bindings are invalid.")
		return
	}
	files := map[string][]byte{}
	complete := true
	for _, a := range m.Artifacts {
		raw, truncated, err := readCapped(root, a.Path, budget)
		if err != nil || truncated {
			complete = false
			fail("artifact:"+a.Path, "Manifest artifact is missing, refused, unreadable or exceeds the read limit: "+a.Path)
			continue
		}
		if err := ir.VerifyPackArtifact(a, raw); err != nil {
			fail("artifact:"+a.Path, "Artifact size or SHA-256 differs from the completion manifest: "+a.Path)
			continue
		}
		files[a.Path] = raw
	}
	if complete {
		audit.Completeness = Assessment{"verified", "All artifacts declared by the supported manifest are present and readable; this does not establish complete product evidence."}
		for _, name := range paths {
			if name == ir.PackManifestFile {
				continue
			}
			declared := false
			for _, a := range m.Artifacts {
				if name == a.Path {
					declared = true
					break
				}
			}
			if !declared {
				audit.Completeness = Assessment{"unverified", "The directory contains artifacts outside the manifest scope; those bytes are not covered by its integrity verdict."}
				break
			}
		}
	} else {
		audit.Completeness = Assessment{"failed", "At least one manifest artifact is unavailable."}
	}
	if audit.Integrity.Status == "failed" {
		return
	}
	e, err := ir.ParseCanonical(files["evaluation.json"])
	if err != nil || e.SchemaVersion != ir.EvaluationSchemaVersion {
		fail("evaluation-contract", "Canonical evaluation schema or bytes are invalid.")
		return
	}
	r, err := ir.ParseReceipt(files["run-receipt.json"])
	if err != nil {
		fail("receipt-contract", "Run receipt schema or bytes are invalid.")
		return
	}
	if err := ir.ValidateReceipt(r, e, m.EvaluationDigest); err != nil {
		fail("receipt-binding", "Run receipt does not bind the supplied evaluation and execution contract.")
		return
	}
	expected := ir.LegacyFromEvaluation(e, r)
	want, _ := json.Marshal(expected)
	got, _ := json.Marshal(payload)
	if !payloadOK || !bytes.Equal(want, got) {
		fail("legacy-binding", "Gate payload differs from the canonical evaluation and receipt adapter.")
		return
	}
	// A supported manifest must not silently accept extra legacy payload claims.
	raw = files["01-gate-failures.json"]
	var generic map[string]json.RawMessage
	if json.Unmarshal(raw, &generic) != nil {
		fail("legacy-contract", "Gate payload is not a JSON object.")
		return
	}
	var expectedFields map[string]json.RawMessage
	_ = json.Unmarshal(got, &expectedFields)
	for field := range generic {
		if _, ok := expectedFields[field]; !ok {
			fail("legacy-contract", "Gate payload contains fields outside the bound adapter contract.")
			return
		}
	}
	audit.Integrity = Assessment{"verified", "Every manifest artifact matches its exact size and SHA-256; evaluation, receipt and legacy adapter contracts agree. The manifest is unsigned."}
	audit.EvaluationDigest = m.EvaluationDigest
	audit.AsOf = e.AsOf
	rep.SubjectCommit = e.Identity.SubjectCommit
	audit.SubjectCommitStatus = e.Identity.SubjectCommitStatus
	add(rep, Finding{ID: "integrity:manifest-verified", Category: "digest", State: StateConfirmed, Detail: "Versioned pack artifacts and evaluation bindings are internally consistent; authenticity and applicability are separate."})
}

func writeAuditMarkdown(b interface{ WriteString(string) (int, error) }, audit *PackAudit) {
	if audit == nil {
		return
	}
	_, _ = b.WriteString(fmt.Sprintf("- **Integrity:** %s — %s\n- **Authenticity:** %s — %s\n- **Completeness:** %s — %s\n- **Applicability:** %s — %s\n- **Subject commit:** %s\n\n", audit.Integrity.Status, audit.Integrity.Detail, audit.Authenticity.Status, audit.Authenticity.Detail, audit.Completeness.Status, audit.Completeness.Detail, audit.Applicability.Status, audit.Applicability.Detail, audit.SubjectCommitStatus))
}
