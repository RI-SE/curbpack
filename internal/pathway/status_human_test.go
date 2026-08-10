package pathway

import (
	"strings"
	"testing"
)

func TestFormatHumanStatus_NoPhasePath(t *testing.T) {
	t.Parallel()
	snap := Snapshot{
		Phase: PhaseAwaitSuggest,
		Path:  ParentStatePath(PhaseAwaitSuggest),
		Next: NextAction{
			Verb: "suggest packs",
			Cmd:  "cyberready pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes",
			Note: "enum seed only",
		},
	}
	out := FormatHumanStatus(snap)
	if strings.Contains(out, "phase:") || strings.Contains(out, "Root / Pathway") {
		t.Fatalf("human status must hide statechart, got:\n%s", out)
	}
	if !strings.Contains(out, "next ask:") || !strings.Contains(out, "run:") {
		t.Fatalf("want next ask + run:\n%s", out)
	}
	if !strings.Contains(out, ClaimFence) {
		t.Fatal("want claim fence")
	}
}
