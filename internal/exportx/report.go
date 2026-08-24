package exportx

import (
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/ir"
)

type Report struct {
	PackID   string
	Failures []ReportFinding
}

type ReportFinding struct {
	GateID      string
	Severity    string
	Description string
	TargetFile  string
}

func ReportFromPayload(payload ir.GateFailurePayload) Report {
	out := Report{PackID: payload.PackID}
	for _, f := range payload.Failures {
		out.Failures = append(out.Failures, ReportFinding{
			GateID: f.GateID, Severity: f.Severity,
			Description: f.SanitizedDescription,
			TargetFile: strings.TrimSpace(f.ASTCoordinates.TargetFile),
		})
	}
	sort.Slice(out.Failures, func(i, j int) bool { return out.Failures[i].GateID < out.Failures[j].GateID })
	return out
}

// FromGateFailures maps GateFailure IR to SARIF (ruleId == gate_id).
// Text and path fields reuse the same exportx sanitize helpers as explain-packet.
// repoRoot enables repo-relative path rewrite when non-empty.
func RenderSARIF(rep Report, repoRoot string) SARIFDocument {
	rulesByID := map[string]SARIFRule{}
	results := make([]SARIFResult, 0, len(rep.Failures))
	for _, f := range rep.Failures {
		sev := strings.ToLower(f.Severity)
		level := "warning"
		if sev == "high" || sev == "critical" {
			level = "error"
		}
		desc := sanitizeText(f.Description, repoRoot)
		if _, ok := rulesByID[f.GateID]; !ok {
			r := SARIFRule{ID: f.GateID}
			r.ShortDescription.Text = desc
			rulesByID[f.GateID] = r
		}
		res := SARIFResult{
			RuleID:  f.GateID,
			Level:   level,
			Message: SARIFMessage{Text: desc},
			Properties: map[string]any{
				"assurance_class":       "structural_draft",
				"certification_claimed": false,
				"instrument_panel":      true,
				"note":                  "Structural evidence for human review — not a conformity assessment.",
			},
		}
		file := strings.TrimSpace(f.TargetFile)
		if file != "" {
			var loc SARIFLocation
			loc.PhysicalLocation.ArtifactLocation.URI = relativizePath(file, repoRoot)
			loc.PhysicalLocation.Region.StartLine = 1
			res.Locations = []SARIFLocation{loc}
		}
		results = append(results, res)
	}
	ruleIDs := make([]string, 0, len(rulesByID))
	for id := range rulesByID {
		ruleIDs = append(ruleIDs, id)
	}
	sort.Strings(ruleIDs)
	rules := make([]SARIFRule, 0, len(ruleIDs))
	for _, id := range ruleIDs {
		rules = append(rules, rulesByID[id])
	}
	return SARIFDocument{
		Schema:  "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
		Version: "2.1.0",
		Runs: []SARIFRun{{
			Tool: SARIFTool{Driver: SARIFDriver{
				Name:           "curbpack",
				InformationURI: "https://github.com/RI-SE/curbpack",
				Rules:          rules,
			}},
			Results: results,
			Invocations: []SARIFInvocation{{
				ExecutionSuccessful: true,
				Properties: map[string]any{
					"assurance_class":       "structural_draft",
					"certification_claimed": false,
					"instrument_panel":      true,
					"note":                  "Structural evidence for human review — not a conformity assessment.",
				},
			}},
		}},
	}
}


func FromGateFailures(payload ir.GateFailurePayload, repoRoot string) SARIFDocument {
	return RenderSARIF(ReportFromPayload(payload), repoRoot)
}
