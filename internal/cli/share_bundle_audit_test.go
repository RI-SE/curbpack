package cli_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/cli"
	"github.com/afelin/curbpack/internal/review"
)

func TestShareBundleIsInCompletedManifest(t *testing.T) {
	dir := t.TempDir()
	initScanGit(t, dir)
	old, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	if err := os.Chdir(dir); err != nil {
		t.Fatal(err)
	}
	defer os.Chdir(old)
	capture(t, func() {
		err := cli.Run([]string{"share", "--bundle", "--as-of", "2026-09-08"})
		if err != nil && cli.ExitCode(err) != cli.ExitGates {
			t.Fatal(err)
		}
	})
	pack := filepath.Join(dir, "review-pack")
	rep, err := review.Run(review.Options{BundleRoot: pack, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Audit == nil || rep.Audit.Integrity.Status != "verified" || rep.Audit.Completeness.Status != "verified" {
		t.Fatalf("fresh share bundle is not fully covered: %+v", rep.Audit)
	}
	bundle := filepath.Join(pack, "evidence-bundle.html")
	raw, err := os.ReadFile(bundle)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(bundle, append(raw, []byte("tampered")...), 0600); err != nil {
		t.Fatal(err)
	}
	rep, err = review.Run(review.Options{BundleRoot: pack, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if rep.Audit.Integrity.Status != "failed" || !review.HasContradictions(rep) {
		t.Fatalf("changed bundle escaped integrity check: %+v", rep.Audit)
	}
}
