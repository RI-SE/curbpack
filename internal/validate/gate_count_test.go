package validate_test

import (
	"github.com/afelin/curbpack/internal/validate"
	"os"
	"path/filepath"
	"testing"
)

func TestMultipleFindingsCountOneFailedGate(t *testing.T) {
	root := t.TempDir()
	mustRealGitValidate(t, root)
	packs := t.TempDir()
	mustWriteFresh(t, packs, "audit/pack.json", `{"id":"audit","name":"Audit","version":"1.0.0","rules":[{"id":"ONE","check":"text_forbid","paths":["a.txt","b.txt"],"pattern":"deny","severity":"high","type":"POLICY_VIOLATION","description":"Audit","remediation":"Remove deny"}]}`)
	t.Setenv("CURBPACK_PACKS_DIR", packs)
	for _, name := range []string{"a.txt", "b.txt"} {
		if err := os.WriteFile(filepath.Join(root, name), []byte("deny"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: []string{"audit"}, Quiet: true})
	if err != nil {
		t.Fatal(err)
	}
	if len(res.Payload.Failures) != 2 {
		t.Fatalf("fixture produced %d findings", len(res.Payload.Failures))
	}
	if res.FailedRules != 1 || res.EvaluatedRules != 1 || res.Payload.FailedRules != 1 {
		t.Fatalf("one failed gate reported as %d/%d (%d in payload)", res.FailedRules, res.EvaluatedRules, res.Payload.FailedRules)
	}
}
