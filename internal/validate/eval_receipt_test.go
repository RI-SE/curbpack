package validate_test

import (
	"bytes"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/afelin/curbpack/internal/clock"
	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/validate"
)

// W2: with SOURCE_DATE_EPOCH unset, two evaluations of the same inputs must
// produce identical canonical evaluation bytes (wall-clock lives only on receipt).
func TestCanonicalEvaluationStableWithoutEpoch(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "")
	_ = os.Unsetenv("SOURCE_DATE_EPOCH")

	dir := t.TempDir()
	mustRealGitValidate(t, dir)
	writeGoodHouse(t, dir)

	run := func() []byte {
		t.Helper()
		res, err := validate.Run(validate.Options{
			RepoRoot: dir,
			PackIDs:  []string{"house-policy"},
			Quiet:    true,
		})
		if err != nil {
			t.Fatalf("validate.Run: %v", err)
		}
		if res.Payload.Outcome == "" {
			t.Fatal("expected outcome on payload")
		}
		path := filepath.Join(dir, ".github", "curbpack", "cache", "latest_evaluation.json")
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("read latest_evaluation.json: %v", err)
		}
		var eval ir.Evaluation
		if err := json.Unmarshal(raw, &eval); err != nil {
			t.Fatalf("evaluation json: %v\n%s", err, raw)
		}
		if eval.SchemaVersion != ir.EvaluationSchemaVersion {
			t.Fatalf("schema = %q", eval.SchemaVersion)
		}
		// Guard: canonical file must not smuggle a wall-clock timestamp field.
		var probe map[string]any
		if err := json.Unmarshal(raw, &probe); err != nil {
			t.Fatal(err)
		}
		if _, ok := probe["timestamp"]; ok {
			t.Fatalf("canonical evaluation must omit timestamp, got %v", probe["timestamp"])
		}
		if _, ok := probe["agent_identity"]; ok {
			t.Fatalf("canonical evaluation must omit agent_identity")
		}
		return raw
	}

	first := run()
	time.Sleep(1100 * time.Millisecond) // cross a wall-clock second if timestamp leaked
	second := run()
	if !bytes.Equal(first, second) {
		t.Fatalf("canonical evaluation drifted across wall-clock second without SOURCE_DATE_EPOCH:\nfirst:\n%s\nsecond:\n%s", first, second)
	}

	receiptPath := filepath.Join(dir, ".github", "curbpack", "cache", "latest_receipt.json")
	rawReceipt, err := os.ReadFile(receiptPath)
	if err != nil {
		t.Fatalf("read latest_receipt.json: %v", err)
	}
	var receipt ir.RunReceipt
	if err := json.Unmarshal(rawReceipt, &receipt); err != nil {
		t.Fatalf("receipt json: %v\n%s", err, rawReceipt)
	}
	if receipt.SchemaVersion != ir.RunReceiptSchemaVersion {
		t.Fatalf("receipt schema = %q", receipt.SchemaVersion)
	}
	if receipt.EvaluationDigest == "" || receipt.Timestamp == "" {
		t.Fatalf("receipt incomplete: %#v", receipt)
	}

	// Legacy aliases remain readable GateFailurePayload for existing consumers.
	legacyPath := filepath.Join(dir, ".github", "curbpack", "cache", "latest_failure.json")
	legacyRaw, err := os.ReadFile(legacyPath)
	if err != nil {
		t.Fatal(err)
	}
	var legacy ir.GateFailurePayload
	if err := json.Unmarshal(legacyRaw, &legacy); err != nil {
		t.Fatalf("legacy json: %v", err)
	}
	if legacy.Timestamp == "" {
		t.Fatal("legacy adapter must still expose timestamp for readers")
	}
}

func TestValidateRejectsInvalidSourceDateEpoch(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "not-a-unix-second")
	dir := t.TempDir()
	mustRealGitValidate(t, dir)
	writeGoodHouse(t, dir)
	_, err := validate.Run(validate.Options{
		RepoRoot: dir,
		PackIDs:  []string{"house-policy"},
		Quiet:    true,
	})
	if err == nil {
		t.Fatal("validate.Run must reject invalid SOURCE_DATE_EPOCH")
	}
	if !errors.Is(err, clock.ErrInvalidSourceDateEpoch) {
		t.Fatalf("err = %v, want ErrInvalidSourceDateEpoch", err)
	}
}

// W2: same inputs, SOURCE_DATE_EPOCH unset, vary HOME → stable canonical evaluation.
func TestCanonicalEvaluationStableAcrossHOME(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "")
	_ = os.Unsetenv("SOURCE_DATE_EPOCH")

	dir := t.TempDir()
	mustRealGitValidate(t, dir)
	writeGoodHouse(t, dir)

	runUnderHOME := func(home string) (digest string, evalRaw []byte) {
		t.Helper()
		t.Setenv("HOME", home)
		res, err := validate.Run(validate.Options{
			RepoRoot: dir,
			PackIDs:  []string{"house-policy"},
			Quiet:    true,
		})
		if err != nil {
			t.Fatalf("validate.Run under HOME=%s: %v", home, err)
		}
		path := filepath.Join(dir, ".github", "curbpack", "cache", "latest_evaluation.json")
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("read evaluation: %v", err)
		}
		var eval ir.Evaluation
		if err := json.Unmarshal(raw, &eval); err != nil {
			t.Fatalf("evaluation json: %v", err)
		}
		d, err := ir.ComputeEvaluationDigest(eval)
		if err != nil {
			t.Fatal(err)
		}
		_ = res
		return d, raw
	}

	homeA := filepath.Join(t.TempDir(), "home-a")
	homeB := filepath.Join(t.TempDir(), "home-b")
	if err := os.MkdirAll(homeA, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(homeB, 0o755); err != nil {
		t.Fatal(err)
	}

	digestA, rawA := runUnderHOME(homeA)
	legacyDigestA := ir.ComputeResultDigest(mustLegacyPayload(t, dir))
	digestB, rawB := runUnderHOME(homeB)
	legacyDigestB := ir.ComputeResultDigest(mustLegacyPayload(t, dir))
	if digestA != digestB {
		t.Fatalf("evaluation digest drifted across HOME:\nA=%s\nB=%s", digestA, digestB)
	}
	if !bytes.Equal(rawA, rawB) {
		t.Fatalf("canonical evaluation bytes drifted across HOME:\nA:\n%s\nB:\n%s", rawA, rawB)
	}
	if legacyDigestA != legacyDigestB {
		t.Fatalf("legacy result digest drifted across HOME: %s vs %s", legacyDigestA, legacyDigestB)
	}
}

func mustLegacyPayload(t *testing.T, dir string) ir.GateFailurePayload {
	t.Helper()
	raw, err := os.ReadFile(filepath.Join(dir, ".github", "curbpack", "cache", "latest_failure.json"))
	if err != nil {
		t.Fatal(err)
	}
	var p ir.GateFailurePayload
	if err := json.Unmarshal(raw, &p); err != nil {
		t.Fatal(err)
	}
	return p
}
