package ask

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/validate"
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

	fmt.Println(validate.SemanticMarkdown(payload))
	fmt.Println("---")
	fmt.Printf("Readiness score: %d%% · findings: %d\n", payload.ReadinessScore, len(payload.Failures))

	if propose {
		fmt.Println()
		fmt.Println("## Proposed markdown edits (propose-only — not applied)")
		fmt.Println()
		for _, f := range payload.Failures {
			fmt.Printf("### %s\n", f.GateID)
			fmt.Printf("- File hint: `%s`\n", f.ASTCoordinates.TargetFile)
			fmt.Printf("- Proposed change: %s\n", f.Remediation.ActionRequired)
			fmt.Printf("- Expected state: %s\n\n", f.Remediation.ExpectedState)
		}
		fmt.Println("Re-run `cyberready validate` after editing. CyberReady will not apply diffs automatically.")
	}
	return nil
}
