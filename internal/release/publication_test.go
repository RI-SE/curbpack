package release_test

import (
	"encoding/json"
	"github.com/afelin/curbpack/internal/ir"
	"os"
	"path/filepath"
	"testing"

	"github.com/afelin/curbpack/internal/release"
	"github.com/afelin/curbpack/internal/review"
)

func TestPreparePreflightsWholePackBeforeReplacingArtifacts(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	initPassingHouse(t, root)
	out := filepath.Join(root, "review-pack")
	if err := os.MkdirAll(filepath.Join(out, "proof-index.html"), 0755); err != nil {
		t.Fatal(err)
	}
	previous := []byte("previous complete artifact")
	if err := os.WriteFile(filepath.Join(out, "01-gate-failures.json"), previous, 0600); err != nil {
		t.Fatal(err)
	}
	if err := release.Prepare(release.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, AllowFailingGates: true}); err == nil {
		t.Fatal("blocked final artifact accepted")
	}
	got, err := os.ReadFile(filepath.Join(out, "01-gate-failures.json"))
	if err != nil || string(got) != string(previous) {
		t.Fatalf("pack changed before all destinations were checked: %s (%v)", got, err)
	}
}

func TestPreparePublishesEvaluationReceiptAndCompletionManifest(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	initPassingHouse(t, root)
	if err := release.Prepare(release.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"evaluation.json", "run-receipt.json", "pack-manifest.json"} {
		if _, err := os.ReadFile(filepath.Join(root, "review-pack", name)); err != nil {
			t.Errorf("missing published contract %s: %v", name, err)
		}
	}
}

func TestReviewRejectsChangedManifestArtifact(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	initPassingHouse(t, root)
	if err := release.Prepare(release.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(root, "review-pack")
	path := filepath.Join(out, "04-sbom-summary.json")
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, append(raw, ' '), 0600); err != nil {
		t.Fatal(err)
	}
	rep, err := review.Run(review.Options{BundleRoot: out, JSONOut: true})
	if err != nil {
		t.Fatal(err)
	}
	if !review.HasContradictions(rep) {
		t.Fatal("changed manifest artifact accepted as consistent")
	}
}

func TestOfflinePackAuditDimensionsAndAlterations(t *testing.T) {
	t.Setenv("SOURCE_DATE_EPOCH", "1704067200")
	root := t.TempDir()
	initPassingHouse(t, root)
	if err := release.Prepare(release.Options{RepoRoot: root, PackIDs: []string{"house-policy"}, AllowFailingGates: true}); err != nil {
		t.Fatal(err)
	}
	original := map[string][]byte{}
	names, err := os.ReadDir(filepath.Join(root, "review-pack"))
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range names {
		raw, err := os.ReadFile(filepath.Join(root, "review-pack", name.Name()))
		if err != nil {
			t.Fatal(err)
		}
		original[name.Name()] = raw
	}
	for _, kind := range []string{"unchanged", "altered", "missing", "no-manifest", "invalid-evaluation", "invalid-receipt", "unlisted", "symlink"} {
		t.Run(kind, func(t *testing.T) {
			// The received directory has no Git checkout and may use an unrelated HOME,
			// locale and invalid epoch: review verifies evidence without re-evaluation.
			t.Setenv("HOME", filepath.Join(t.TempDir(), "custom-home"))
			t.Setenv("TMPDIR", t.TempDir())
			t.Setenv("LANG", "C")
			t.Setenv("SOURCE_DATE_EPOCH", "invalid")
			out := t.TempDir()
			files := map[string][]byte{}
			for name, raw := range original {
				files[name] = append([]byte(nil), raw...)
			}
			switch kind {
			case "altered":
				files["04-sbom-summary.json"] = append(files["04-sbom-summary.json"], ' ')
			case "missing":
				delete(files, "05-vex-draft.json")
			case "no-manifest":
				delete(files, ir.PackManifestFile)
			case "invalid-evaluation", "invalid-receipt":
				name := "evaluation.json"
				if kind == "invalid-receipt" {
					name = "run-receipt.json"
				}
				var obj map[string]any
				if err := json.Unmarshal(files[name], &obj); err != nil {
					t.Fatal(err)
				}
				obj["unknown_unbound_field"] = true
				files[name], err = json.MarshalIndent(obj, "", "  ")
				if err != nil {
					t.Fatal(err)
				}
				files[name] = append(files[name], '\n')
				delete(files, ir.PackManifestFile)
				m, err := ir.NewPackManifest(files)
				if err != nil {
					t.Fatal(err)
				}
				files[ir.PackManifestFile], err = ir.MarshalPackManifest(m)
				if err != nil {
					t.Fatal(err)
				}
			case "unlisted":
				files["unlisted.txt"] = []byte("outside declared scope")
			}
			for name, raw := range files {
				if err := os.WriteFile(filepath.Join(out, name), raw, 0600); err != nil {
					t.Fatal(err)
				}
			}
			if kind == "symlink" {
				name := filepath.Join(out, "05-vex-draft.json")
				if err := os.Remove(name); err != nil {
					t.Fatal(err)
				}
				target := filepath.Join(t.TempDir(), "outside.json")
				if err := os.WriteFile(target, original["05-vex-draft.json"], 0600); err != nil {
					t.Fatal(err)
				}
				if err := os.Symlink(target, name); err != nil {
					t.Skip(err)
				}
			}
			rep, err := review.Run(review.Options{BundleRoot: out, JSONOut: true})
			if err != nil {
				t.Fatal(err)
			}
			if rep.Audit == nil {
				t.Fatal("missing separate audit dimensions")
			}
			if rep.Audit.Authenticity.Status != "unverified" || rep.Audit.Applicability.Status != "not_assessed" || rep.Audit.SubjectCommitStatus != "claimed" {
				t.Fatalf("overstated trust: %+v", rep.Audit)
			}
			if kind == "unchanged" || kind == "unlisted" {
				if rep.Audit.Integrity.Status != "verified" || review.HasContradictions(rep) {
					t.Fatalf("clean declared set rejected: %+v %+v", rep.Audit, rep.Findings)
				}
				want := "verified"
				if kind == "unlisted" {
					want = "unverified"
				}
				if rep.Audit.Completeness.Status != want {
					t.Fatalf("completeness: %+v", rep.Audit)
				}
			} else if !review.HasContradictions(rep) || rep.Audit.Integrity.Status != "failed" {
				t.Fatalf("%s accepted: %+v", kind, rep.Audit)
			}
		})
	}
}
