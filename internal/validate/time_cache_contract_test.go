package validate_test

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/validate"
)

func TestAsOfControlsFreshnessAndCanonicalIdentity(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704153600")
	t.Setenv("GIT_AUTHOR_DATE", "2024-01-01T00:00:00Z")
	t.Setenv("GIT_COMMITTER_DATE", "2024-01-01T00:00:00Z")
	root := t.TempDir()
	mustRealGitValidate(t, root)
	packs := t.TempDir()
	t.Setenv("CURBPACK_PACKS_DIR", packs)
	mustWriteFresh(t, packs, "audit/pack.json", `{"id":"audit","name":"Audit","version":"1.0.0","rules":[{"id":"FRESH","check":"fresh","path":"policy.md","min_bytes":1,"max_age_days":7,"severity":"high","type":"POLICY_VIOLATION","description":"Recent policy","remediation":"Review it"}]}`)
	mustWriteFresh(t, root, "policy.md", "Reviewed policy")
	runGitFresh(t, root, "add", "policy.md")
	runGitFresh(t, root, "commit", "-qm", "policy")
	opts := validate.Options{RepoRoot: root, PackIDs: []string{"audit"}, Quiet: true, AsOf: "2024-01-02"}
	first, err := validate.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	if !first.Passed {
		t.Fatalf("fresh at explicit as_of: %v", first.Payload.Failures)
	}
	opts.AsOf = "2024-01-20T00:00:00Z"
	second, err := validate.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	if second.Passed || first.Receipt.EvaluationDigest == second.Receipt.EvaluationDigest {
		t.Fatal("as_of failed to change freshness and identity")
	}
	if first.Evaluation.ComparisonKey == second.Evaluation.ComparisonKey {
		t.Fatal("different time bases must not trend")
	}
	opts.AsOf = "yesterday"
	if _, err := validate.Run(opts); err == nil {
		t.Fatal("invalid as_of accepted")
	}
}

func TestImmutableCacheVerifiesObjectsAndPreservesPointerOnFailure(t *testing.T) {
	root := t.TempDir()
	mustRealGitValidate(t, root)
	writeGoodHouse(t, root)
	opts := validate.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, Quiet: true, AsOf: "2024-01-02"}
	first, err := validate.Run(opts)
	if err != nil {
		t.Fatal(err)
	}
	e, r, err := validate.LoadLatest(root)
	if err != nil {
		t.Fatal(err)
	}
	if r.EvaluationDigest != first.Receipt.EvaluationDigest || e.AsOf != first.Evaluation.AsOf {
		t.Fatal("cache loaded another evaluation")
	}
	cache := filepath.Join(root, ".github", "curbpack", "cache")
	pointer, err := os.ReadFile(filepath.Join(cache, "latest.json"))
	if err != nil {
		t.Fatal(err)
	}
	// Mutable historical aliases cannot influence current cache readers.
	if err := os.WriteFile(filepath.Join(cache, "latest_failure.json"), []byte(`{"outcome":"pass"}`), 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := validate.LoadLatest(root); err != nil {
		t.Fatal(err)
	}
	// A blocked alias prevents advancing the authoritative pointer.
	if err := os.Remove(filepath.Join(cache, "latest_receipt.json")); err != nil {
		t.Fatal(err)
	}
	if err := os.Mkdir(filepath.Join(cache, "latest_receipt.json"), 0700); err != nil {
		t.Fatal(err)
	}
	opts.AsOf = "2024-01-03"
	if _, err := validate.Run(opts); err == nil {
		t.Fatal("blocked publication reported success")
	}
	after, err := os.ReadFile(filepath.Join(cache, "latest.json"))
	if err != nil || !bytes.Equal(pointer, after) {
		t.Fatal("failed publication advanced pointer")
	}
	// Integrity is recomputed, not inferred from a digest-shaped filename.
	object := filepath.Join(cache, "evaluations", r.EvaluationDigest+".json")
	b, err := os.ReadFile(object)
	if err != nil {
		t.Fatal(err)
	}
	b = bytes.Replace(b, []byte(`"tool_version":`), []byte(`"extra":true,"tool_version":`), 1)
	if err := os.WriteFile(object, b, 0600); err != nil {
		t.Fatal(err)
	}
	if _, _, err := validate.LoadLatest(root); err == nil {
		t.Fatal("altered immutable object accepted")
	}
}

func TestOperationalStateIsExcludedAndUnboundFieldsAreRejected(t *testing.T) {
	root := t.TempDir()
	mustRealGitValidate(t, root)
	writeGoodHouse(t, root)
	res, err := validate.Run(validate.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, Quiet: true, ReadOnly: true, AsOf: "2024-01-02"})
	if err != nil {
		t.Fatal(err)
	}
	first, err := ir.MarshalCanonical(res.Evaluation)
	if err != nil {
		t.Fatal(err)
	}
	res.Evaluation.StatechartContext.ActiveParentStatePath = []string{"different operator workflow"}
	res.Evaluation.ConcurrencyControl.StateVersionToken = "different lease"
	second, err := ir.MarshalCanonical(res.Evaluation)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(first, second) {
		t.Fatal("operational state changed canonical evaluation")
	}
	if strings.Contains(string(first), "statechart_context") || strings.Contains(string(first), "agent_identity") {
		t.Fatal("operational state leaked into canonical bytes")
	}
	var fields map[string]any
	if err := json.Unmarshal(first, &fields); err != nil {
		t.Fatal(err)
	}
	fields["timestamp"] = "2024-01-02T00:00:00Z"
	altered, _ := json.MarshalIndent(fields, "", "  ")
	if _, err := ir.ParseCanonical(append(altered, '\n')); err == nil {
		t.Fatal("unbound field accepted")
	}
}

func TestFreshEmissionStableAcrossRelocationAndEnvironment(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "")
	if err := os.Unsetenv("SOURCE_DATE_EPOCH"); err != nil {
		t.Fatal(err)
	}
	root := t.TempDir()
	mustRealGitValidate(t, root)
	packs := t.TempDir()
	t.Setenv("CURBPACK_PACKS_DIR", packs)
	mustWriteFresh(t, packs, "audit/pack.json", `{"id":"audit","name":"Audit","version":"1.0.0","rules":[{"id":"ONE","check":"text_forbid","paths":["input.txt"],"pattern":"deny","severity":"high","type":"POLICY_VIOLATION","description":"Audit","remediation":"Remove deny"}]}`)
	mustWriteFresh(t, root, "input.txt", "deny")
	relocated := filepath.Join(t.TempDir(), "relocated repository")
	if err := os.Mkdir(relocated, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.CopyFS(relocated, os.DirFS(root)); err != nil {
		t.Fatal(err)
	}
	var canonical []byte
	for n, location := range []string{root, relocated} {
		home := filepath.Join(t.TempDir(), "staff", "custom-home")
		if err := os.MkdirAll(home, 0700); err != nil {
			t.Fatal(err)
		}
		t.Setenv("HOME", home)
		t.Setenv("USERPROFILE", home)
		tmp := t.TempDir()
		t.Setenv("TMPDIR", tmp)
		t.Setenv("TMP", tmp)
		t.Setenv("TEMP", tmp)
		locale := "C"
		if n == 1 {
			locale = "en_US.UTF-8"
		}
		t.Setenv("LC_ALL", locale)
		res, err := validate.Run(validate.Options{RepoRoot: location, PackIDs: []string{"audit"}, Quiet: true, AsOf: "2024-01-02"})
		if err != nil {
			t.Fatal(err)
		}
		b, err := ir.MarshalCanonical(res.Evaluation)
		if err != nil {
			t.Fatal(err)
		}
		if n == 0 {
			canonical = b
		} else if !bytes.Equal(canonical, b) {
			t.Fatal("relocation/HOME/TMPDIR/locale changed canonical bytes")
		}
		// Subsequent reading is separately checked against the stored immutable pair.
		e, r, err := validate.LoadLatest(location)
		if err != nil {
			t.Fatal(err)
		}
		got, err := ir.MarshalCanonical(e)
		if err != nil || !bytes.Equal(got, b) || r.EvaluationDigest != res.Receipt.EvaluationDigest {
			t.Fatal("subsequent read differs from fresh emission")
		}
	}
}
