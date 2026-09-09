package exportx_test

import (
	"github.com/afelin/curbpack/internal/exportx"
	"strings"
	"testing"
)

func TestPrebetaBuyerStatusDoesNotAnswerNegativeQuestionYes(t *testing.T) {
	r := exportx.BuyerQuestionsReport{Questions: []exportx.BuyerQuestion{{GateID: "EXAMPLE", HumanQuestion: "Is SECURITY.md missing?", Answered: true}}}
	s := exportx.FormatBuyerQuestionsMarkdown(r)
	if strings.Contains(s, "| Yes |") || !strings.Contains(s, "Passed") {
		t.Fatalf("misleading status: %s", s)
	}
	r.AnswersSuppressed = true
	r.SkippedRules = 1
	s = exportx.FormatBuyerQuestionsMarkdown(r)
	if !strings.Contains(s, "Not evaluated") {
		t.Fatalf("missing skipped explanation: %s", s)
	}
}
