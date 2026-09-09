package ask

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/redact"
)

// Run explains a GateFailure payload from stdin or path. Propose-only — never writes.
func Run(path string, propose bool) error {
	var data []byte
	var err error
	if path == "" || path == "-" {
		data, err = io.ReadAll(os.Stdin)
	} else {
		data, err = os.ReadFile(path)
	}
	if err != nil {
		return err
	}
	data = []byte(strings.TrimSpace(string(data)))
	if len(data) == 0 {
		return fmt.Errorf("empty input — pipe GateFailure JSON or pass a file path")
	}

	var payload ir.GateFailurePayload
	if err := json.Unmarshal(data, &payload); err != nil {
		return fmt.Errorf("parse GateFailure JSON: %w", err)
	}

	if len(payload.Failures) == 0 {
		fmt.Println("No findings in this report. No edits proposed.")
		if payload.SkippedRules > 0 {
			fmt.Println("Some checks were skipped. Run curbpack check for a full result.")
		}
		return nil
	}
	home, _ := os.UserHomeDir()
	clean := func(s string) string {
		return redact.String(s, redact.Context{Mode: redact.Plain, Home: home, Secrets: true})
	}
	fmt.Println("# Findings to address")
	for _, f := range payload.Failures {
		fmt.Printf("\n## %s (%s)\nFile: %s\nFinding: %s\nNext action: %s\nExpected result: %s\n", clean(f.GateID), clean(f.Severity), clean(f.ASTCoordinates.TargetFile), clean(f.SanitizedDescription), clean(f.Remediation.ActionRequired), clean(f.Remediation.ExpectedState))
	}
	fmt.Println("---")
	failed := payload.FailedRules
	if failed == 0 {
		failed = ir.UniqueFailedGates(payload.Failures)
	}
	evaluated := fmt.Sprint(payload.EvaluatedRules)
	if payload.EvaluatedRules == 0 && payload.EvaluationDigest == "" {
		evaluated = "unknown"
	}
	fmt.Printf("failed=%d evaluated=%s skipped=%d · findings: %d\n", failed, evaluated, payload.SkippedRules, len(payload.Failures))

	if propose {
		fmt.Println("These are proposed edits only; nothing was applied.")
	}
	fmt.Println("After editing, run curbpack check again.")
	return nil
}
