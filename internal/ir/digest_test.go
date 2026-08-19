package ir_test

import (
	"testing"

	"github.com/afelin/curbpack/internal/ir"
)

func TestComputeResultDigestStable(t *testing.T) {
	p := ir.GateFailurePayload{
		PackID:         "house-policy,cra-baseline",
		ReadinessScore: 80,
		Failures: []ir.Failure{
			{GateID: "B", Severity: "high", Type: "X", ASTCoordinates: ir.ASTCoordinates{TargetFile: "b.md"}},
			{GateID: "A", Severity: "low", Type: "Y", ASTCoordinates: ir.ASTCoordinates{TargetFile: "a.md"}},
		},
	}
	a := ir.ComputeResultDigest(p)
	b := ir.ComputeResultDigest(p)
	if a != b {
		t.Fatalf("digest not stable: %s vs %s", a, b)
	}
	p2 := p
	p2.ReadinessScore = 81
	if ir.ComputeResultDigest(p2) == a {
		t.Fatal("score change must affect digest")
	}
}
