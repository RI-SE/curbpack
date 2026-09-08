package validate_test

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/validate"
)

func TestEvaluationBindsChangedInputsAndRules(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	mustRealGitValidate(t, root)
	packdir := t.TempDir()
	t.Setenv("CURBPACK_PACKS_DIR", packdir)
	pack := `{"id":"audit","name":"Audit","version":"1.0.0","rules":[{"id":"ONE","check":"text_forbid","paths":["input.txt"],"pattern":"deny","severity":"high","type":"POLICY_VIOLATION","description":"Audit","remediation":"Remove deny"}]}`
	mustWriteFresh(t, packdir, "audit/pack.json", pack)
	mustWriteFresh(t, root, "input.txt", "deny")
	run := func() []byte {
		t.Helper()
		if _, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: []string{"audit"}, Quiet: true}); err != nil {
			t.Fatal(err)
		}
		b, err := os.ReadFile(filepath.Join(root, ".github", "curbpack", "cache", "latest_evaluation.json"))
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	first := run()
	mustWriteFresh(t, root, "input.txt", "deny; different bytes, same finding")
	second := run()
	if bytes.Equal(first, second) {
		t.Error("changed evaluated bytes did not change canonical evaluation")
	}
	mustWriteFresh(t, packdir, "audit/pack.json", string(bytes.ReplaceAll([]byte(pack), []byte(`"pattern":"deny"`), []byte(`"pattern":"deny|newly-forbidden"`))))
	third := run()
	if bytes.Equal(second, third) {
		t.Error("changed rule bytes did not change canonical evaluation")
	}
	if !bytes.Contains(third, []byte(`"as_of"`)) {
		t.Error("canonical evaluation lacks explicit as_of")
	}
}
