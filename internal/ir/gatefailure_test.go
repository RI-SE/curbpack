package ir_test

import (
	"encoding/json"
	"testing"

	"github.com/afelin/cyberready/internal/ir"
)

func TestGateFailureRoundTrip(t *testing.T) {
	p := ir.GateFailurePayload{
		Timestamp: "2026-08-07T00:00:00Z",
		ConcurrencyControl: ir.ConcurrencyControl{
			ExpectedParentCommitSHA: "abc123",
			StateVersionToken:       "v3.29-OCC",
		},
		Failures: []ir.Failure{{
			GateID:               "CRA-ANNEX-VII-RISK",
			Severity:             "high",
			Type:                 "POLICY_VIOLATION",
			SanitizedDescription: "missing",
			ASTCoordinates:       ir.ASTCoordinates{TargetFile: "risk_assessment.md"},
			Remediation:          ir.Remediation{ActionRequired: "fill", ExpectedState: "present"},
		}},
	}
	b, err := json.Marshal(p)
	if err != nil {
		t.Fatal(err)
	}
	var out ir.GateFailurePayload
	if err := json.Unmarshal(b, &out); err != nil {
		t.Fatal(err)
	}
	if out.Failures[0].GateID != "CRA-ANNEX-VII-RISK" {
		t.Fatal(out.Failures[0].GateID)
	}
	if out.ConcurrencyControl.StateVersionToken != "v3.29-OCC" {
		t.Fatal("OCC token drift")
	}
}
