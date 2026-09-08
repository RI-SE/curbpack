package ir_test

import (
	"bytes"
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
)

var updateSchemaGoldens = flag.Bool("update-schema", false, "rewrite versioned schema examples")

func TestCompleteEvaluationSchemaGoldens(t *testing.T) {
	identity := ir.InputIdentity{Method: "curbpack-gates:2", ToolVersion: "0.5.5", SubjectCommitStatus: "claimed", SubjectCommit: strings.Repeat("a", 40), PackSources: []ir.PackSource{{ID: "example", Version: "1.0.0", SHA256: strings.Repeat("b", 64)}}, Files: []ir.InputFile{{Path: "policy.md", State: "file", SHA256: strings.Repeat("c", 64)}}, GitInputs: []ir.GitInput{}, Scope: ir.EvaluationScope{Mode: "full", RuleIDs: []string{"EXAMPLE"}, SkippedRuleIDs: []string{}, ChangedPaths: []string{}}, TrustPolicy: "none"}
	e := ir.Evaluation{SchemaVersion: ir.EvaluationSchemaVersion, AsOf: "2024-01-02T00:00:00Z", Identity: identity, Failures: []ir.Failure{}, PackID: "example", ReadinessScore: 100, Outcome: ir.OutcomePass, EvaluatedRules: 1, ConformityClaim: ir.ConformityClaimNone}
	e.ComparisonKey = ir.ComparisonIdentity(identity, e.AsOf)
	if err := ir.ValidateEvaluation(e); err != nil {
		t.Fatal(err)
	}
	evalBytes, err := ir.MarshalCanonical(e)
	if err != nil {
		t.Fatal(err)
	}
	digest, err := ir.ComputeEvaluationDigest(e)
	if err != nil {
		t.Fatal(err)
	}
	receipt := ir.RunReceipt{SchemaVersion: ir.RunReceiptSchemaVersion, EvaluationDigest: digest, Timestamp: "2024-01-02T12:00:00Z", AsOf: e.AsOf, AgentIdentity: ir.AgentIdentity{AgentID: "example", Source: "self-declared"}, ConformityClaim: ir.ConformityClaimNone, AsOfSource: "explicit", Platform: "example/amd64", ToolVersion: "0.5.5", EvaluationDurationMillis: 12, ConcurrencyControl: ir.ConcurrencyControl{ExpectedParentCommitSHA: identity.SubjectCommit, StateVersionToken: "v3.33-OCC"}, StatechartContext: ir.StatechartContext{ActiveParentStatePath: []string{"Root", "ActiveVerification", "PackEval"}, FailedOrthogonalRegions: []string{}}}
	if err := ir.ValidateReceipt(receipt, e, digest); err != nil {
		t.Fatal(err)
	}
	receiptBytes, err := ir.MarshalReceipt(receipt)
	if err != nil {
		t.Fatal(err)
	}
	for name, got := range map[string][]byte{"curbpack-evaluation-2": evalBytes, "curbpack-run-receipt-2": receiptBytes} {
		path := filepath.Join("..", "..", "schema", name+".golden.json")
		if *updateSchemaGoldens {
			if err := os.WriteFile(path, got, 0644); err != nil {
				t.Fatal(err)
			}
		}
		want, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if !bytes.Equal(got, want) {
			t.Fatalf("%s changed; review the contract before updating its golden", name)
		}
	}
}

func TestHistoricalEvaluationRetainsItsOriginalFieldSet(t *testing.T) {
	legacy := ir.Evaluation{SchemaVersion: ir.LegacyEvaluationSchemaVersion, Failures: []ir.Failure{}, PackID: "example", Outcome: ir.OutcomePass}
	raw, err := ir.MarshalCanonical(legacy)
	if err != nil {
		t.Fatal(err)
	}
	if bytes.Contains(raw, []byte("input_identity")) || bytes.Contains(raw, []byte("conformity_claim")) {
		t.Fatal("historical bytes gained new fields")
	}
	if _, err := ir.ParseCanonical(raw); err != nil {
		t.Fatal(err)
	}
	p := ir.GateFailurePayload{PackID: "example", Outcome: ir.OutcomePass}
	before := ir.ComputeResultDigest(p)
	e := ir.EvaluationFromLegacy(p)
	restored := ir.LegacyFromEvaluation(e, ir.RunReceipt{EvaluationDigest: strings.Repeat("f", 64)})
	if ir.ComputeResultDigest(restored) != before {
		t.Fatal("legacy adapter changed historical result digest")
	}
	p.EvaluationDigest = strings.Repeat("f", 64)
	if ir.ComputeResultDigest(p) == before {
		t.Fatal("new result digest omitted evaluation identity")
	}
}

func TestPackManifestSchemaGolden(t *testing.T) {
	files := map[string][]byte{}
	for _, name := range ir.RequiredPackArtifacts() {
		files[name] = []byte("synthetic manifest fixture: " + name)
	}
	manifest, err := ir.NewPackManifest(files)
	if err != nil {
		t.Fatal(err)
	}
	got, err := ir.MarshalPackManifest(manifest)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join("..", "..", "schema", "curbpack-pack-manifest-1.golden.json")
	if *updateSchemaGoldens {
		if err := os.WriteFile(path, got, 0644); err != nil {
			t.Fatal(err)
		}
	}
	want, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, want) {
		t.Fatal("manifest contract drifted")
	}
	if _, err := ir.ParsePackManifest(want); err != nil {
		t.Fatal(err)
	}
}
