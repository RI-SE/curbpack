package exportx

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/review"
	"github.com/afelin/curbpack/internal/validate"
)

// HoldingReportPaths resolves review-pack/holding-report paths.
func HoldingReportPaths(root, outPath string) (mdPath, jsonPath string) {
	if outPath == "" {
		base := filepath.Join(root, "review-pack", "holding-report")
		return base + ".md", base + ".json"
	}
	return buyerQuestionsStemPaths(outPath)
}

// WriteHoldingReport writes the scheduled holding report (answered-first retention artifact).
// Requires --since prior review JSON. Refuses section 1 when answers_suppressed.
// Never renders Yes on indicative settlement rows.
func WriteHoldingReport(root string, packIDs []string, sincePath, outPath string) (string, error) {
	if strings.TrimSpace(sincePath) == "" {
		return "", fmt.Errorf("export --holding-report requires --since <prior-report.json>")
	}
	priorRaw, err := os.ReadFile(sincePath)
	if err != nil {
		return "", fmt.Errorf("holding-report --since: %w", err)
	}
	var prior review.Report
	if err := json.Unmarshal(priorRaw, &prior); err != nil {
		return "", fmt.Errorf("holding-report --since: invalid JSON: %w", err)
	}

	buyer, err := BuildBuyerQuestionsReportReadOnly(root, packIDs)
	if err != nil {
		return "", err
	}
	if buyer.AnswersSuppressed {
		return "", fmt.Errorf("holding-report refuses section 1: answers_suppressed (run a full check, not diff mode)")
	}

	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, Quiet: true, ReadOnly: true})
	if err != nil {
		return "", err
	}
	_ = res

	// Current review record for delta (repo mode, references-only surfaces from packs).
	surfaces := holdingSurfaces(packIDs)
	cur, err := review.Run(review.Options{
		BundleRoot:     root,
		Writer:         ioDiscard{},
		JSONOut:        true,
		ReferencesOnly: true,
		TriageSurfaces: surfaces,
		Prior:          &prior,
	})
	if err != nil {
		return "", fmt.Errorf("holding-report review: %w", err)
	}

	md := FormatHoldingReportMarkdown(buyer, prior, cur)
	mdPath, jsonPath := HoldingReportPaths(root, outPath)
	if err := os.MkdirAll(filepath.Dir(mdPath), 0o755); err != nil {
		return "", err
	}
	if err := os.WriteFile(mdPath, []byte(md), 0o644); err != nil {
		return "", err
	}
	payload := map[string]any{
		"schema_version":       "1",
		"note":                 "Holding report — what still holds / what changed / what needs a person. Not conformity assessment.",
		"parent_record_digest": cur.ParentRecordDigest,
		"record_digest":        cur.RecordDigest,
		"answers_suppressed":   buyer.AnswersSuppressed,
		"buyer_questions":      buyer,
		"classifier_version":   cur.ClassifierVersion,
		"method_version":       cur.MethodVersion,
	}
	b, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return "", err
	}
	if err := os.WriteFile(jsonPath, append(b, '\n'), 0o644); err != nil {
		return "", err
	}
	return mdPath, nil
}

type ioDiscard struct{}

func (ioDiscard) Write(p []byte) (int, error) { return len(p), nil }

func holdingSurfaces(packIDs []string) []string {
	if len(packIDs) == 0 {
		packIDs = []string{"house-policy"}
	}
	composed, _, err := packs.Compose(packIDs)
	if err != nil {
		return nil
	}
	seen := map[string]struct{}{}
	var out []string
	for _, r := range composed.Rules {
		for _, p := range append([]string{r.Path}, r.Paths...) {
			p = strings.TrimSpace(p)
			if p == "" {
				continue
			}
			if _, ok := seen[p]; ok {
				continue
			}
			seen[p] = struct{}{}
			out = append(out, p)
		}
	}
	sort.Strings(out)
	return out
}

// FormatHoldingReportMarkdown renders the three-section holding report.
func FormatHoldingReportMarkdown(buyer BuyerQuestionsReport, prior, cur review.Report) string {
	var b strings.Builder
	b.WriteString("# Holding report\n\n")
	b.WriteString("> Local pack gates. Humans review. Not conformity assessment.\n")
	b.WriteString("> Not CE / not notified-body. No wall-clock in this body.\n\n")
	fmt.Fprintf(&b, "- **Packs:** %s\n", buyer.PackID)
	fmt.Fprintf(&b, "- **Parent record digest:** `%s`\n", cur.ParentRecordDigest)
	fmt.Fprintf(&b, "- **Record digest:** `%s`\n\n", cur.RecordDigest)

	b.WriteString("## 1. What still holds\n\n")
	b.WriteString("| Question | Answer | Evidence |\n|---|---|---|\n")
	answeredRows := 0
	for _, q := range buyer.Questions {
		if !q.Answered {
			continue
		}
		answeredRows++
		label := "Yes"
		if q.Settlement == packs.SettlementIndicative {
			label = "Present, not settled"
		}
		fmt.Fprintf(&b, "| %s | %s | %s |\n", mdCell(q.HumanQuestion), mdCell(label), mdCell(q.Evidence))
	}
	if answeredRows == 0 {
		b.WriteString("| _(none answered)_ | — | — |\n")
	}
	b.WriteString("\n")

	b.WriteString("## 2. What changed\n\n")
	b.WriteString(review.FormatDelta(prior, cur))
	b.WriteString("\n")

	b.WriteString("## 3. What needs a person\n\n")
	b.WriteString("| gate_id | why |\n|---|---|\n")
	needPerson := 0
	for _, q := range buyer.Questions {
		if q.Settlement == packs.SettlementIndicative {
			fmt.Fprintf(&b, "| %s | indicative settlement — positive content not settled by structural check |\n", mdCell(q.GateID))
			needPerson++
		} else if !q.Answered {
			fmt.Fprintf(&b, "| %s | unanswered structural check |\n", mdCell(q.GateID))
			needPerson++
		}
	}
	for _, f := range cur.Findings {
		if f.Category == "reference" && f.State != review.StateConfirmed {
			fmt.Fprintf(&b, "| %s | unresolved reference (%s) |\n", mdCell(f.ID), mdCell(string(f.State)))
			needPerson++
		}
	}
	if needPerson == 0 {
		b.WriteString("| _(none)_ | — |\n")
	}
	b.WriteString("\n")
	return b.String()
}
