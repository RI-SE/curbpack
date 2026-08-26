package review_test

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/review"
)

func TestRecordDeterminism(t *testing.T) {
	dir := writeMinimalConsistent(t)
	var a, b bytes.Buffer
	ra, err := review.Run(review.Options{BundleRoot: dir, Writer: &a, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	rb, err := review.Run(review.Options{BundleRoot: dir, Writer: &b, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if ra.RecordDigest == "" || ra.BundleDigest == "" {
		t.Fatalf("digests empty: record=%q bundle=%q", ra.RecordDigest, ra.BundleDigest)
	}
	if ra.RecordDigest != rb.RecordDigest {
		t.Fatalf("record_digest drift: %s vs %s", ra.RecordDigest, rb.RecordDigest)
	}
	if ra.BundleDigest != rb.BundleDigest {
		t.Fatalf("bundle_digest drift: %s vs %s", ra.BundleDigest, rb.BundleDigest)
	}
}

func TestRecordDigestPathIndependent(t *testing.T) {
	src := writeMinimalConsistent(t)
	dst := filepath.Join(t.TempDir(), "elsewhere-pack")
	if err := copyDir(src, dst); err != nil {
		t.Fatal(err)
	}
	ra, err := review.Run(review.Options{BundleRoot: src, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	rb, err := review.Run(review.Options{BundleRoot: dst, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	if ra.RecordDigest != rb.RecordDigest {
		t.Fatalf("record_digest must exclude bundle_root name: %s vs %s (roots %q %q)",
			ra.RecordDigest, rb.RecordDigest, ra.BundleRoot, rb.BundleRoot)
	}
	if ra.BundleRoot == rb.BundleRoot {
		t.Fatal("test setup: directory basenames must differ")
	}
}

func TestRecordDigestExcludesItself(t *testing.T) {
	dir := writeMinimalConsistent(t)
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	cp := rep
	cp.RecordDigest = ""
	cp.BundleRoot = ""
	b, err := json.Marshal(cp)
	if err != nil {
		t.Fatal(err)
	}
	// Recompute same way as package (sha256 of marshaled JSON with blanks).
	sum := sha256SumHex(b)
	if sum != rep.RecordDigest {
		t.Fatalf("recomputed record_digest %s ≠ emitted %s", sum, rep.RecordDigest)
	}
}

func TestBundleDigestChangesOnContentChange(t *testing.T) {
	dir := writeMinimalConsistent(t)
	r1, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	mustWrite(t, filepath.Join(dir, "02-action-report.md"), []byte("ok\nchanged\n"))
	r2, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	if r1.BundleDigest == r2.BundleDigest {
		t.Fatal("bundle_digest must change when file content changes")
	}
}

func TestBundleDigestLargeFileNotTruncated(t *testing.T) {
	// Per-file parse cap is 8 MiB; content past that must still affect bundle_digest
	// when the whole bundle still fits under the 64 MiB digest ceiling.
	dir := writeMinimalConsistent(t)
	bigA := append(bytes.Repeat([]byte("a"), 9<<20), []byte("TAIL-A")...)
	mustWrite(t, filepath.Join(dir, "big.bin"), bigA)
	r1, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	bigB := append(bytes.Repeat([]byte("a"), 9<<20), []byte("TAIL-B")...)
	mustWrite(t, filepath.Join(dir, "big.bin"), bigB)
	r2, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	if r1.BundleDigest == "" || r2.BundleDigest == "" {
		t.Fatalf("digests empty under ceiling: %q %q", r1.BundleDigest, r2.BundleDigest)
	}
	if r1.BundleDigest == r2.BundleDigest {
		t.Fatal("bundle_digest must hash past per-file parse cap (no truncate)")
	}
}

func TestBundleDigestRefusesOversizeBundle(t *testing.T) {
	dir := writeMinimalConsistent(t)
	// Two files that together exceed 64 MiB digest ceiling.
	chunk := bytes.Repeat([]byte("z"), 33<<20)
	mustWrite(t, filepath.Join(dir, "huge-a.bin"), chunk)
	mustWrite(t, filepath.Join(dir, "huge-b.bin"), chunk)
	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}, Full: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.BundleDigest != "" {
		t.Fatalf("oversize must leave bundle_digest empty, got %q", rep.BundleDigest)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "structure:bundle-size-cap" && f.State == review.StateContradicted && f.Cause == review.CauseSelfDisagree {
			found = true
		}
	}
	if !found {
		t.Fatalf("want structure:bundle-size-cap contradicted, got %+v", rep.Findings)
	}
	if !review.HasContradictions(rep) {
		t.Fatal("oversize refuse must contradict")
	}
}

func TestMarkdownGoldenUnchangedExceptRecordLines(t *testing.T) {
	root := repoRoot(t)
	pack := filepath.Join(root, "testdata", "sample-review-pack")
	for _, full := range []bool{false, true} {
		name := "terse"
		goldenRel := "testdata/markdown_terse_pre_w3.txt"
		if full {
			name = "full"
			goldenRel = "testdata/markdown_full_pre_w3.txt"
		}
		t.Run(name, func(t *testing.T) {
			var buf bytes.Buffer
			_, err := review.Run(review.Options{BundleRoot: pack, Writer: &buf, Full: full})
			if err != nil {
				t.Fatal(err)
			}
			got := buf.String()
			lines := strings.Split(strings.TrimSuffix(got, "\n"), "\n")
			if len(lines) < 2 {
				t.Fatalf("too short: %q", got)
			}
			footer := lines[len(lines)-2:]
			if !strings.HasPrefix(footer[0], "record_digest ") || !strings.Contains(footer[0], "method "+review.MethodVersion) {
				t.Fatalf("missing record_digest footer line: %q", footer[0])
			}
			if footer[1] != "Record of an offline structural check. Not a conformity assessment." {
				t.Fatalf("missing claim-safe record line: %q", footer[1])
			}
			body := strings.Join(lines[:len(lines)-2], "\n") + "\n"
			want, err := os.ReadFile(filepath.Join(root, "internal", "review", goldenRel))
			if err != nil {
				t.Fatal(err)
			}
			if body != string(want) {
				t.Fatalf("%s markdown drifted beyond the two record lines\n--- got body ---\n%s\n--- want ---\n%s", name, body, want)
			}
		})
	}
}

func repoRoot(t *testing.T) string {
	t.Helper()
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	// internal/review → repo root
	return filepath.Clean(filepath.Join(wd, "..", ".."))
}

func copyDir(src, dst string) error {
	if err := os.MkdirAll(dst, 0o755); err != nil {
		return err
	}
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(target, data, 0o644)
	})
}

func sha256SumHex(b []byte) string {
	sum := sha256.Sum256(b)
	return fmt.Sprintf("%x", sum[:])
}

func TestDigestIncompleteOnUnreadablePath(t *testing.T) {
	dir := writeMinimalConsistent(t)
	secret := filepath.Join(dir, "secret.dat")
	mustWrite(t, secret, []byte("x"))
	if err := os.Chmod(secret, 0o000); err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chmod(secret, 0o644) })

	rep, err := review.Run(review.Options{BundleRoot: dir, Writer: ioDiscard{}})
	if err != nil {
		t.Fatal(err)
	}
	if rep.BundleDigest != "" {
		t.Fatalf("unreadable path must refuse bundle_digest, got %q", rep.BundleDigest)
	}
	found := false
	for _, f := range rep.Findings {
		if f.ID == "structure:digest-incomplete" && f.State == review.StateContradicted {
			found = true
		}
	}
	if !found {
		t.Fatalf("want structure:digest-incomplete, findings=%+v", rep.Findings)
	}
}
