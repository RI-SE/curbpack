package ir_test

import (
	"github.com/afelin/curbpack/internal/ir"
	"testing"
)

func TestResultDigestBindsCompleteness(t *testing.T) {
	p := ir.GateFailurePayload{PackID: "house-policy", ReadinessScore: 100, Outcome: ir.OutcomePass}
	base := ir.ComputeResultDigest(p)
	p.Outcome = ir.OutcomeIncomplete
	if ir.ComputeResultDigest(p) == base {
		t.Fatal("incomplete outcome must change result digest")
	}
	base = ir.ComputeResultDigest(p)
	p.SkippedRules = 1
	if ir.ComputeResultDigest(p) == base {
		t.Fatal("skipped-rule count must change result digest")
	}
}

func TestResultDigestSameGateFailureOrder(t *testing.T) {
	a := ir.Failure{GateID: "A", Severity: "high", Type: "missing", ASTCoordinates: ir.ASTCoordinates{TargetFile: "a.md"}}
	b := a
	b.ASTCoordinates.TargetFile = "b.md"
	p := ir.GateFailurePayload{Outcome: ir.OutcomeFindings, Failures: []ir.Failure{a, b}}
	q := p
	q.Failures = []ir.Failure{b, a}
	if ir.ComputeResultDigest(p) != ir.ComputeResultDigest(q) {
		t.Fatal("ordering of same-gate failures must not change digest")
	}
}
