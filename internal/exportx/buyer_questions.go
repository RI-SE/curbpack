package exportx

import (
	"encoding/json"
	"fmt"
	"path/filepath"
	"strings"

	"github.com/afelin/curbpack/internal/attest"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/validate"
)

const buyerQuestionsAssuranceClass = "structural_draft"

// BuyerQuestion is one human-review checklist row for buyers/auditors.
type BuyerQuestion struct {
	GateID          string `json:"gate_id"`
	Severity        string `json:"severity"`
	HumanQuestion   string `json:"human_question"`
	ArtifactPath    string `json:"artifact_path"`
	AssuranceClass  string `json:"assurance_class"`
	RemediationHint string `json:"remediation_hint"`
	Answered        bool   `json:"answered"`
	// Settlement is packs.SettlementSettles or packs.SettlementIndicative (render axis; Answered stays pass/fail).
	Settlement string `json:"settlement,omitempty"`
	Evidence   string `json:"evidence,omitempty"`
	VerifiedAt string `json:"verified_at,omitempty"`
}

// BuyerQuestionsReport is Markdown+JSON checklist export (claim-safe).
type BuyerQuestionsReport struct {
	SchemaVersion     string          `json:"schema_version"`
	Note              string          `json:"note"`
	PackID            string          `json:"pack_id"`
	AssuranceClass    string          `json:"assurance_class"`
	AttestationStatus string          `json:"attestation_status"`
	Questions         []BuyerQuestion `json:"questions"`
	SkippedRules      int             `json:"skipped_rules,omitempty"`
	AnswersSuppressed bool            `json:"answers_suppressed,omitempty"`
}

// CollectBuyerQuestions builds the same checklist rows WriteBuyerQuestions writes,
// without touching the filesystem. Used by prepare-release one-pager cover sheet.
func CollectBuyerQuestions(root string, packIDs []string, res validate.Result) ([]BuyerQuestion, error) {
	ids := packIDs
	if len(ids) == 0 {
		ids = nonzeroPacks(strings.Split(res.Payload.PackID, ","))
	}
	composed, _, err := packs.Compose(ids)
	if err != nil {
		return nil, err
	}
	failRem := map[string]string{}
	failPath := map[string]string{}
	failed := map[string]struct{}{}
	for _, f := range res.Payload.Failures {
		failed[f.GateID] = struct{}{}
		failRem[f.GateID] = f.Remediation.ActionRequired
		if p := strings.TrimSpace(f.ASTCoordinates.TargetFile); p != "" {
			failPath[f.GateID] = p
		}
	}
	suppressAnswers := res.SkippedRules > 0
	verifiedAt := strings.TrimSpace(res.Payload.ConcurrencyControl.ExpectedParentCommitSHA)
	assurance := strings.TrimSpace(composed.AssuranceClass)
	if assurance == "" {
		assurance = buyerQuestionsAssuranceClass
	}
	questions := make([]BuyerQuestion, 0, len(composed.Rules))
	for _, r := range composed.Rules {
		path := strings.TrimSpace(r.Path)
		if path == "" && r.Check == "manifest_dep_ban" {
			path = "package.json"
		}
		if path == "" && len(r.Paths) > 0 {
			path = strings.Join(r.Paths, ", ")
		}
		if fp, ok := failPath[r.ID]; ok {
			path = fp
		}
		hint := strings.TrimSpace(r.Remediation)
		if h, ok := failRem[r.ID]; ok && strings.TrimSpace(h) != "" {
			hint = h
		}
		q := BuyerQuestion{
			GateID:          r.ID,
			Severity:        r.Severity,
			HumanQuestion:   humanQuestionForRule(r),
			ArtifactPath:    path,
			AssuranceClass:  assurance,
			RemediationHint: hint,
			Settlement:      packs.EffectiveSettlement(r),
		}
		if !suppressAnswers {
			if _, isFailed := failed[r.ID]; !isFailed {
				q.Answered = true
				q.Evidence = path
				q.VerifiedAt = verifiedAt
			}
		}
		questions = append(questions, q)
	}
	return questions, nil
}

// PackPlainNames returns human pack names for a CSV of pack ids (fallback: the id).
func PackPlainNames(packIDCSV string) string {
	var names []string
	for _, id := range strings.Split(packIDCSV, ",") {
		id = strings.TrimSpace(id)
		if id == "" {
			continue
		}
		p, err := packs.LoadPack(id)
		if err != nil || strings.TrimSpace(p.Name) == "" {
			names = append(names, id)
			continue
		}
		names = append(names, strings.TrimSpace(p.Name))
	}
	return strings.Join(names, "; ")
}

// BuildBuyerQuestionsReport runs pack gates and assembles the checklist report (no filesystem writes).
func BuildBuyerQuestionsReport(root string, packIDs []string) (BuyerQuestionsReport, error) {
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, Quiet: true})
	if err != nil {
		return BuyerQuestionsReport{}, err
	}
	return BuildBuyerQuestionsReportFromResult(root, packIDs, res)
}

// BuildBuyerQuestionsReportReadOnly is like BuildBuyerQuestionsReport but does not write cache under .github/.
func BuildBuyerQuestionsReportReadOnly(root string, packIDs []string) (BuyerQuestionsReport, error) {
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: packIDs, Quiet: true, ReadOnly: true})
	if err != nil {
		return BuyerQuestionsReport{}, err
	}
	return BuildBuyerQuestionsReportFromResult(root, packIDs, res)
}

// BuildBuyerQuestionsReportFromResult assembles the checklist from a pre-built validate.Result.
func BuildBuyerQuestionsReportFromResult(root string, packIDs []string, res validate.Result) (BuyerQuestionsReport, error) {
	questions, err := CollectBuyerQuestions(root, packIDs, res)
	if err != nil {
		return BuyerQuestionsReport{}, err
	}
	ids := packIDs
	if len(ids) == 0 {
		ids = nonzeroPacks(strings.Split(res.Payload.PackID, ","))
	}
	composed, _, err := packs.Compose(ids)
	if err != nil {
		return BuyerQuestionsReport{}, err
	}
	assurance := strings.TrimSpace(composed.AssuranceClass)
	if assurance == "" {
		assurance = buyerQuestionsAssuranceClass
	}
	report := BuyerQuestionsReport{
		SchemaVersion:     "1",
		Note:              "Local pack gates prepare evidence for human review. Not CE / not notified-body. Not a conformity assessment.",
		PackID:            composed.ID,
		AssuranceClass:    assurance,
		AttestationStatus: attestationStatus(root),
		Questions:         questions,
	}
	if res.SkippedRules > 0 {
		report.SkippedRules = res.SkippedRules
		report.AnswersSuppressed = true
	}
	return report, nil
}

// WriteBuyerQuestions emits buyer-questions.md + .json under cache (or outPath stem).
func WriteBuyerQuestions(root string, packIDs []string, outPath string) (string, int, error) {
	report, err := BuildBuyerQuestionsReport(root, packIDs)
	if err != nil {
		return "", 0, err
	}
	return writeBuyerQuestionsReport(root, packIDs, outPath, report)
}

// WriteBuyerQuestionsFromResult writes buyer-questions from a pre-built validate.Result.
func WriteBuyerQuestionsFromResult(root string, packIDs []string, outPath string, res validate.Result) (string, int, error) {
	report, err := BuildBuyerQuestionsReportFromResult(root, packIDs, res)
	if err != nil {
		return "", 0, err
	}
	return writeBuyerQuestionsReport(root, packIDs, outPath, report)
}

func writeBuyerQuestionsReport(root string, packIDs []string, outPath string, report BuyerQuestionsReport) (string, int, error) {
	mdPath, jsonPath := buyerQuestionsPaths(root, outPath)
	if err := writeBuyerQuestionsFiles(root, report, mdPath, jsonPath); err != nil {
		return "", 0, err
	}
	return mdPath, len(report.Questions), nil
}

// SupplierQuestionsPaths resolves review-pack/supplier-checklist paths (or --out stem).
func SupplierQuestionsPaths(root, outPath string) (mdPath, jsonPath string) {
	if outPath == "" {
		base := filepath.Join(root, "review-pack", "supplier-checklist")
		return base + ".md", base + ".json"
	}
	if !filepath.IsAbs(outPath) {
		outPath = filepath.Join(root, outPath)
	}
	return buyerQuestionsStemPaths(outPath)
}

// WriteSupplierChecklist writes supplier-checklist.md + .json under review-pack/ (or outPath stem).
func WriteSupplierChecklist(root string, packIDs []string, outPath string) (string, int, error) {
	report, err := BuildBuyerQuestionsReportReadOnly(root, packIDs)
	if err != nil {
		return "", 0, err
	}
	return WriteSupplierChecklistReport(root, report, outPath)
}

// WriteSupplierChecklistReport writes a pre-built report to review-pack/ (or outPath stem).
func WriteSupplierChecklistReport(root string, report BuyerQuestionsReport, outPath string) (string, int, error) {
	mdPath, jsonPath := SupplierQuestionsPaths(root, outPath)
	if err := writeBuyerQuestionsFiles(root, report, mdPath, jsonPath); err != nil {
		return "", 0, err
	}
	return mdPath, len(report.Questions), nil
}

func writeBuyerQuestionsFiles(root string, report BuyerQuestionsReport, mdPath, jsonPath string) error {
	md := FormatBuyerQuestionsMarkdown(report)
	b, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	if err := writeContainedAt(root, mdPath, []byte(md)); err != nil {
		return err
	}
	return writeContainedAt(root, jsonPath, append(b, '\n'))
}

func buyerQuestionsPaths(root, outPath string) (mdPath, jsonPath string) {
	if outPath == "" {
		base := filepath.Join(root, ".github", "curbpack", "cache", "buyer-questions")
		return base + ".md", base + ".json"
	}
	return buyerQuestionsStemPaths(outPath)
}

func buyerQuestionsStemPaths(outPath string) (mdPath, jsonPath string) {
	ext := strings.ToLower(filepath.Ext(outPath))
	stem := strings.TrimSuffix(outPath, ext)
	switch ext {
	case ".md", ".markdown":
		return outPath, stem + ".json"
	case ".json":
		return stem + ".md", outPath
	default:
		return outPath + ".md", outPath + ".json"
	}
}

func humanQuestionForRule(r packs.Rule) string {
	body := strings.TrimSpace(r.Expected)
	if body == "" {
		body = "Evidence for " + r.ID
	}
	return "For human review: " + strings.TrimRight(body, ".?") + "."
}

// BuyerResultLabel describes the mechanical result, never a human answer.
func BuyerResultLabel(q BuyerQuestion, suppressed bool) string {
	if suppressed {
		return "Not evaluated — run a full check"
	}
	if !q.Answered {
		return "Finding — action needed"
	}
	if q.Settlement == packs.SettlementIndicative {
		return "Passed — content needs human review"
	}
	return "Passed"
}

// FormatBuyerQuestionsMarkdown renders the human-review checklist as Markdown.
func FormatBuyerQuestionsMarkdown(report BuyerQuestionsReport) string {
	var b strings.Builder
	b.WriteString("# Buyer questions (human review checklist)\n\n")
	b.WriteString("> Local pack gates. Humans review. Not conformity assessment.\n")
	b.WriteString("> Not CE / not notified-body.\n\n")
	fmt.Fprintf(&b, "- **Packs:** %s\n", report.PackID)
	fmt.Fprintf(&b, "- **Assurance class:** `%s`\n", report.AssuranceClass)
	fmt.Fprintf(&b, "- **Attestation status:** `%s`\n\n", report.AttestationStatus)

	if report.AnswersSuppressed {
		b.WriteString("Not evaluated — this partial run cannot supply complete results.\n\n")
		writeChecklistTable(&b, report.Questions)
		fmt.Fprintf(&b, "\nAnswers not emitted: %d rules skipped (diff mode). Run a full check to produce answers.\n\n", report.SkippedRules)
		return b.String()
	}

	b.WriteString("> Result describes a mechanical check, not a human answer or product approval.\n")
	b.WriteString("> Passed — content needs human review means the structure passed; the substance remains for the reviewer.\n\n")

	var answered, unanswered []BuyerQuestion
	for _, q := range report.Questions {
		if q.Answered {
			answered = append(answered, q)
		} else {
			unanswered = append(unanswered, q)
		}
	}

	if len(answered) > 0 {
		b.WriteString("## Checks passed — review the evidence\n\n")
		b.WriteString("| Review task | Check result | Referenced evidence | Claimed commit |\n")
		b.WriteString("|---|---|---|---|\n")
		for _, q := range answered {
			fmt.Fprintf(&b, "| %s | %s | %s | %s |\n",
				mdCell(q.HumanQuestion),
				mdCell(BuyerResultLabel(q, false)),
				mdCell(q.Evidence),
				mdCell(q.VerifiedAt),
			)
		}
		b.WriteString("\n")
	}

	if len(unanswered) > 0 {
		b.WriteString("## Findings — action needed\n\n")
		writeChecklistTable(&b, unanswered)
		b.WriteString("\n")
	}
	b.WriteString("Referenced product files are not included automatically. Request them from the producer through an approved channel. Keep private content out of public reports.\n")
	return b.String()
}

func writeChecklistTable(b *strings.Builder, questions []BuyerQuestion) {
	b.WriteString("| Check | Priority | Review task | Referenced evidence | Scope | Next action |\n")
	b.WriteString("|---|---|---|---|---|---|\n")
	for _, q := range questions {
		fmt.Fprintf(b, "| %s | %s | %s | %s | %s | %s |\n",
			mdCell(q.GateID),
			mdCell(q.Severity),
			mdCell(q.HumanQuestion),
			mdCell(q.ArtifactPath),
			mdCell(q.AssuranceClass),
			mdCell(q.RemediationHint),
		)
	}
}

// FormatSupplierEmailTemplate returns a claim-safe copy-paste email for suppliers.
func FormatSupplierEmailTemplate(report BuyerQuestionsReport) string {
	packLabel := strings.TrimSpace(report.PackID)
	if packLabel == "" {
		packLabel = "our product"
	}
	var b strings.Builder
	b.WriteString("Subject: Supplier evidence checklist — human review (not certification)\n\n")
	b.WriteString("Hi,\n\n")
	fmt.Fprintf(&b, "We are preparing structural evidence for %s under local pack gates. ", packLabel)
	b.WriteString("This is not a conformity assessment and does not claim CE marking or notified-body approval.\n\n")
	b.WriteString("Please review the checklist below (or the attached supplier-checklist.md) and confirm the artifact paths listed, or share your equivalent documentation.\n\n")
	b.WriteString("Thanks,\n")
	b.WriteString("[Your name]\n")
	return b.String()
}

func mdCell(s string) string {
	s = strings.ReplaceAll(s, "|", "\\|")
	s = strings.ReplaceAll(s, "\n", " ")
	return s
}

// attestationStatus returns none | ssh-agent via LatestBind (not HEAD-only).
func attestationStatus(root string) string {
	bind, _ := attest.LatestBind(root)
	if !bind.Found {
		return "none"
	}
	if bind.UserTouch == "ssh-agent-signed" && bind.StateHash != "" {
		return "ssh-agent"
	}
	return "none"
}
