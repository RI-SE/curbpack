package exportx_test

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/exportx"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/packs"
	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/release/templates"
	"github.com/afelin/curbpack/internal/validate"
)

func TestWriteBuyerQuestions_HousePolicy(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)

	out := filepath.Join(dir, "buyer-questions.md")
	path, n, err := exportx.WriteBuyerQuestions(dir, []string{"house-policy"}, out)
	if err != nil {
		t.Fatal(err)
	}
	if n == 0 {
		t.Fatal("expected n>0 buyer questions for house-policy")
	}
	md, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	text := string(md)
	if !strings.Contains(text, "Not CE") || !strings.Contains(text, "not notified-body") {
		t.Fatal("markdown header must deny CE / notified-body")
	}
	if !strings.Contains(text, "structural_draft") {
		t.Fatal("every export must stamp structural_draft")
	}
	if !strings.Contains(text, "For human review:") {
		t.Fatal("questions must be prefixed For human review:")
	}
	if !strings.Contains(text, "Answer: Yes means the structural check passed") {
		t.Fatal("markdown must include claim-safe answer header")
	}
	deny := []string{"we are CE certified", "CE marking issued", "notified-body approved", "EU CRA Baseline"}
	lower := strings.ToLower(text)
	for _, d := range deny {
		if strings.Contains(lower, strings.ToLower(d)) {
			t.Fatalf("claim-unsafe phrase %q in buyer-questions", d)
		}
	}

	jsonPath := strings.TrimSuffix(path, ".md") + ".json"
	raw, err := os.ReadFile(jsonPath)
	if err != nil {
		t.Fatal(err)
	}
	var report exportx.BuyerQuestionsReport
	if err := json.Unmarshal(raw, &report); err != nil {
		t.Fatal(err)
	}
	if len(report.Questions) == 0 {
		t.Fatal("json questions empty")
	}
	for _, q := range report.Questions {
		if q.AssuranceClass != "structural_draft" {
			t.Fatalf("row %s assurance_class=%q", q.GateID, q.AssuranceClass)
		}
		if !strings.HasPrefix(q.HumanQuestion, "For human review:") {
			t.Fatalf("bad prefix: %q", q.HumanQuestion)
		}
	}
}

func TestPackPlainNames(t *testing.T) {
	got := exportx.PackPlainNames("house-policy,cra-baseline")
	if !strings.Contains(got, "House Policy") {
		t.Fatalf("want house policy plain name, got %q", got)
	}
	if !strings.Contains(got, "CRA Annex VII") {
		t.Fatalf("want CRA plain name, got %q", got)
	}
	if strings.Contains(strings.ToLower(got), "hpurl") {
		t.Fatal("pack labels must not use HPURL jargon")
	}
}

func TestAnsweredDerivedFromFailures(t *testing.T) {
	dir := t.TempDir()
	res := validate.Result{
		Payload: ir.GateFailurePayload{
			PackID: "house-policy",
			ConcurrencyControl: ir.ConcurrencyControl{
				ExpectedParentCommitSHA: "abc123commit",
			},
			Failures: []ir.Failure{{
				GateID: "HOUSE-SECURITY-MD",
				ASTCoordinates: ir.ASTCoordinates{
					TargetFile: "SECURITY.md",
				},
			}},
		},
	}
	qs, err := exportx.CollectBuyerQuestions(dir, []string{"house-policy"}, res)
	if err != nil {
		t.Fatal(err)
	}
	var mdQ, okQ *exportx.BuyerQuestion
	for i := range qs {
		switch qs[i].GateID {
		case "HOUSE-SECURITY-MD":
			mdQ = &qs[i]
		case "HOUSE-SECURITY-TXT":
			okQ = &qs[i]
		}
	}
	if mdQ == nil || okQ == nil {
		t.Fatalf("missing expected gates: %+v", qs)
	}
	if mdQ.Answered {
		t.Fatal("failed gate must not be answered")
	}
	if !okQ.Answered {
		t.Fatal("passing gate must be answered")
	}
	if okQ.Settlement != packs.SettlementSettles {
		t.Fatalf("house-policy settlement=%q want settles", okQ.Settlement)
	}
}

func TestSkippedRulesSuppressAnswers(t *testing.T) {
	dir := t.TempDir()
	res := validate.Result{
		SkippedRules: 2,
		Payload: ir.GateFailurePayload{
			PackID: "house-policy",
			ConcurrencyControl: ir.ConcurrencyControl{
				ExpectedParentCommitSHA: "abc123commit",
			},
		},
	}
	report, err := exportx.BuildBuyerQuestionsReportFromResult(dir, []string{"house-policy"}, res)
	if err != nil {
		t.Fatal(err)
	}
	if !report.AnswersSuppressed {
		t.Fatal("expected answers_suppressed")
	}
	if report.SkippedRules != 2 {
		t.Fatalf("skipped_rules=%d", report.SkippedRules)
	}
	for _, q := range report.Questions {
		if q.Answered {
			t.Fatalf("gate %s must not be answered when rules skipped", q.GateID)
		}
		if q.Evidence != "" || q.VerifiedAt != "" {
			t.Fatalf("gate %s must not emit evidence/verified_at when suppressed", q.GateID)
		}
	}
	md := exportx.FormatBuyerQuestionsMarkdown(report)
	if !strings.Contains(md, "Answers not emitted: 2 rules skipped") {
		t.Fatalf("missing refusal line: %s", md)
	}
	if strings.Contains(md, "| Yes |") {
		t.Fatal("must not emit Yes answers when suppressed")
	}
	if strings.Contains(md, "Present, not settled") {
		t.Fatal("must not emit Present answers when suppressed")
	}
}

func TestIndicativeNeverRendersYes(t *testing.T) {
	dir := t.TempDir()
	res := validate.Result{
		Payload: ir.GateFailurePayload{
			PackID: "cra-baseline",
			ConcurrencyControl: ir.ConcurrencyControl{
				ExpectedParentCommitSHA: "deadbeef",
			},
		},
	}
	qs, err := exportx.CollectBuyerQuestions(dir, []string{"cra-baseline"}, res)
	if err != nil {
		t.Fatal(err)
	}
	report := exportx.BuyerQuestionsReport{
		SchemaVersion:  "1",
		PackID:         "cra-baseline",
		AssuranceClass: "structural_draft",
		Questions:      qs,
	}
	md := exportx.FormatBuyerQuestionsMarkdown(report)
	var annexAnswered bool
	for _, q := range qs {
		if q.GateID == "CRA-ANNEX-VII-RISK" {
			annexAnswered = q.Answered
			if q.Settlement != packs.SettlementIndicative {
				t.Fatalf("settlement=%q", q.Settlement)
			}
			if !q.Answered {
				t.Fatal("CRA annex green path must keep Answered=true (pass/fail axis)")
			}
		}
	}
	if !annexAnswered {
		t.Fatal("expected CRA-ANNEX-VII-RISK answered")
	}
	if strings.Contains(md, "| Yes |") {
		// CRA-DEP may still Yes — that's OK; annex must not
		for _, line := range strings.Split(md, "\n") {
			if strings.Contains(line, "Annex VII risk") && strings.Contains(line, "| Yes |") {
				t.Fatalf("indicative annex must not render Yes: %s", line)
			}
		}
	}
	if !strings.Contains(md, "Present, not settled") {
		t.Fatal("CRA annex green must render Present, not settled")
	}
}

func TestHousePolicyYesStillWorks(t *testing.T) {
	dir := t.TempDir()
	res := validate.Result{
		Payload: ir.GateFailurePayload{
			PackID: "house-policy",
			ConcurrencyControl: ir.ConcurrencyControl{
				ExpectedParentCommitSHA: "abc",
			},
		},
	}
	report, err := exportx.BuildBuyerQuestionsReportFromResult(dir, []string{"house-policy"}, res)
	if err != nil {
		t.Fatal(err)
	}
	md := exportx.FormatBuyerQuestionsMarkdown(report)
	if !strings.Contains(md, "| Yes |") {
		t.Fatal("house-policy answered rows must still render Yes")
	}
	if strings.Contains(md, "| Present, not settled |") {
		t.Fatal("house-policy must not render Present, not settled")
	}
}

func TestEvidencePathPresentOnAnswered(t *testing.T) {
	dir := t.TempDir()
	res := validate.Result{
		Payload: ir.GateFailurePayload{
			PackID: "house-policy",
			ConcurrencyControl: ir.ConcurrencyControl{
				ExpectedParentCommitSHA: "commitsha",
			},
		},
	}
	qs, err := exportx.CollectBuyerQuestions(dir, []string{"house-policy"}, res)
	if err != nil {
		t.Fatal(err)
	}
	for _, q := range qs {
		if !q.Answered {
			continue
		}
		if strings.TrimSpace(q.ArtifactPath) == "" {
			continue
		}
		if strings.TrimSpace(q.Evidence) == "" {
			t.Fatalf("answered gate %s missing evidence path", q.GateID)
		}
	}
}

func TestVerifiedAtFromPayloadNotGit(t *testing.T) {
	dir := t.TempDir()
	want := "0000000000000000000000000000000000000000"
	res := validate.Result{
		Payload: ir.GateFailurePayload{
			PackID: "house-policy",
			ConcurrencyControl: ir.ConcurrencyControl{
				ExpectedParentCommitSHA: want,
			},
		},
	}
	qs, err := exportx.CollectBuyerQuestions(dir, []string{"house-policy"}, res)
	if err != nil {
		t.Fatal(err)
	}
	found := false
	for _, q := range qs {
		if q.Answered {
			found = true
			if q.VerifiedAt != want {
				t.Fatalf("VerifiedAt=%q want payload commit %q (not git HEAD)", q.VerifiedAt, want)
			}
		}
	}
	if !found {
		t.Fatal("expected at least one answered row")
	}
}

func TestExistingQuestionStringsUnchanged(t *testing.T) {
	dir := t.TempDir()
	res := validate.Result{
		Payload: ir.GateFailurePayload{
			PackID: "house-policy",
			Failures: []ir.Failure{{
				GateID: "HOUSE-SECURITY-MD",
			}},
		},
	}
	qs, err := exportx.CollectBuyerQuestions(dir, []string{"house-policy"}, res)
	if err != nil {
		t.Fatal(err)
	}
	for _, q := range qs {
		if q.GateID == "HOUSE-SECURITY-MD" {
			if !strings.Contains(q.HumanQuestion, "SECURITY.md") {
				t.Fatalf("human_question drift: %q", q.HumanQuestion)
			}
			if !strings.HasPrefix(q.HumanQuestion, "For human review:") {
				t.Fatalf("prefix drift: %q", q.HumanQuestion)
			}
			return
		}
	}
	t.Fatal("HOUSE-SECURITY-MD not found")
}

func TestOnePagerCoverSheetUnaffected(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)

	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	qs, err := exportx.CollectBuyerQuestions(dir, nil, res)
	if err != nil {
		t.Fatal(err)
	}
	if len(qs) == 0 {
		t.Fatal("no questions")
	}
	for i, q := range qs {
		if i >= 12 {
			break
		}
		if !strings.HasPrefix(q.HumanQuestion, "For human review:") {
			t.Fatalf("cover row %d bad question: %q", i, q.HumanQuestion)
		}
		if strings.TrimSpace(q.ArtifactPath) == "" && q.GateID != "HOUSE-DEP-AXIOS-PIN" {
			// dep gate may have empty path when no package.json dep hit
			continue
		}
		_ = templates.OnePagerCoverRow{Path: q.ArtifactPath, Question: q.HumanQuestion}
	}

	out := filepath.Join(dir, "review-pack")
	if err := release.Prepare(release.Options{
		RepoRoot: dir, PackIDs: []string{"house-policy"}, OutDir: out, AllowFailingGates: true, Result: &res,
	}); err != nil {
		t.Fatal(err)
	}
	htmlDoc, err := os.ReadFile(filepath.Join(out, "buyer-onepager.html"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(htmlDoc), qs[0].HumanQuestion) {
		t.Fatal("one-pager cover must still use HumanQuestion strings")
	}
}

func TestShareSingleValidateRun(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeGoodHouse(t, dir)
	mustWrite(t, filepath.Join(dir, ".curbpack.json"), `{"packs":["house-policy"]}`+"\n")

	runs := 0
	validate.RunInvocationHook = func() { runs++ }
	t.Cleanup(func() { validate.RunInvocationHook = nil })

	runGit(t, dir, "git", "add", "-A")
	runGit(t, dir, "git", "commit", "-m", "house", "-q")

	res, err := validate.Run(validate.Options{RepoRoot: dir, PackIDs: []string{"house-policy"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if runs != 1 {
		t.Fatalf("initial validate.Run: runs=%d want 1", runs)
	}
	before := runs
	if _, _, err := exportx.WriteBuyerQuestionsFromResult(dir, []string{"house-policy"}, "", res); err != nil {
		t.Fatal(err)
	}
	if runs != before {
		t.Fatalf("WriteBuyerQuestionsFromResult must not re-run validate: runs=%d", runs)
	}
	before = runs
	if err := release.Prepare(release.Options{
		RepoRoot: dir, PackIDs: []string{"house-policy"}, AllowFailingGates: true, Result: &res,
	}); err != nil {
		t.Fatal(err)
	}
	if runs != before {
		t.Fatalf("Prepare with Result must not re-run validate: runs=%d", runs)
	}
}

func runGit(t *testing.T, dir string, args ...string) {
	t.Helper()
	cmd := exec.Command(args[0], args[1:]...)
	cmd.Dir = dir
	cmd.Env = append(os.Environ(), "GIT_CONFIG_NOSYSTEM=1")
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("%v: %s", err, out)
	}
}
