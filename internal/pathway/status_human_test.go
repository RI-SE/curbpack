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
			Cmd:  "curbpack pathway suggest --product=hygiene --eu-docs=no --medtech=no --sector=none --house-first=yes",
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
	if strings.Contains(out, "fence:") {
		t.Fatal("human status must not use opaque fence: label")
	}
	for _, bad := range []string{"HPURL", "RKG", "OCC"} {
		if strings.Contains(out, bad) {
			t.Fatalf("human status must not contain %s:\n%s", bad, out)
		}
	}
}

func TestFormatHumanStatus_DoneProofPage(t *testing.T) {
	t.Parallel()
	snap := Snapshot{
		Phase: PhaseAwaitHPURLVerify,
		Path:  ParentStatePath(PhaseAwaitHPURLVerify),
		Next: NextAction{
			Verb: "verify HPURL (human)",
			Cmd:  "open proof/index.html",
			Note: "paste state_hash from evidence pointer; HPURL compare",
		},
	}
	out := FormatHumanStatus(snap)
	if !strings.Contains(out, "Done — open the local proof page to compare the bound hash") {
		t.Fatalf("want Done proof-page ask:\n%s", out)
	}
	for _, bad := range []string{"HPURL", "RKG", "OCC", "fence:"} {
		if strings.Contains(out, bad) {
			t.Fatalf("human status must not contain %q:\n%s", bad, out)
		}
	}
}
