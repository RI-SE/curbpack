package ir_test

import (
	"testing"

	"github.com/afelin/curbpack/internal/ir"
)

func TestLegacyEvaluationAdapterRoundTrip(t *testing.T) {
	legacy := ir.GateFailurePayload{
		SchemaVersion: ir.SchemaVersion,
		Timestamp:     "2024-01-01T00:00:00Z",
		ConcurrencyControl: ir.ConcurrencyControl{
			ExpectedParentCommitSHA: "abc",
			StateVersionToken:       "v3.33-OCC",
		},
		StatechartContext: ir.StatechartContext{
			ActiveParentStatePath:   []string{"Root"},
			FailedOrthogonalRegions: []string{"PackEval"},
		},
		AgentIdentity: ir.AgentIdentity{
			AgentID: "agent-1",
			Source:  "self-declared",
		},
		Failures: []ir.Failure{
			{GateID: "HOUSE-A", Severity: "high", Type: "text_forbid"},
		},
		PackID:         "house-policy",
		ReadinessScore: 80,
		Outcome:        ir.OutcomeFindings,
		SkippedRules:   0,
	}
	eval := ir.EvaluationFromLegacy(legacy)
	if eval.SchemaVersion != ir.EvaluationSchemaVersion {
		t.Fatalf("schema = %q", eval.SchemaVersion)
	}
	digest, err := ir.ComputeEvaluationDigest(eval)
	if err != nil {
		t.Fatal(err)
	}
	receipt := ir.RunReceipt{
		SchemaVersion:    ir.RunReceiptSchemaVersion,
		EvaluationDigest: digest,
		Timestamp:        legacy.Timestamp,
		AgentIdentity:    legacy.AgentIdentity,
	}
	back := ir.LegacyFromEvaluation(eval, receipt)
	if back.Timestamp != legacy.Timestamp {
		t.Fatalf("timestamp = %q want %q", back.Timestamp, legacy.Timestamp)
	}
	if back.AgentIdentity.AgentID != legacy.AgentIdentity.AgentID {
		t.Fatalf("agent = %#v", back.AgentIdentity)
	}
	if back.PackID != legacy.PackID || back.Outcome != legacy.Outcome || back.ReadinessScore != legacy.ReadinessScore {
		t.Fatalf("legacy projection drift: %#v", back)
	}
	if len(back.Failures) != 1 || back.Failures[0].GateID != "HOUSE-A" {
		t.Fatalf("failures = %#v", back.Failures)
	}
}

func TestMarshalCanonicalStable(t *testing.T) {
	e := ir.Evaluation{
		SchemaVersion:  ir.EvaluationSchemaVersion,
		PackID:         "house-policy",
		ReadinessScore: 100,
		Outcome:        ir.OutcomePass,
		Failures:       []ir.Failure{},
	}
	a, err := ir.MarshalCanonical(e)
	if err != nil {
		t.Fatal(err)
	}
	b, err := ir.MarshalCanonical(e)
	if err != nil {
		t.Fatal(err)
	}
	if string(a) != string(b) {
		t.Fatalf("canonical bytes drifted:\n%s\nvs\n%s", a, b)
	}
	da, err := ir.ComputeEvaluationDigest(e)
	if err != nil {
		t.Fatal(err)
	}
	db, err := ir.ComputeEvaluationDigest(e)
	if err != nil {
		t.Fatal(err)
	}
	if da != db {
		t.Fatalf("digest drifted: %s vs %s", da, db)
	}
}
