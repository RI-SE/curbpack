package review_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/ir"
)

// fixtureShape selects default tree layout for writeFixture.
type fixtureShape string

const (
	shapeBundle fixtureShape = "bundle" // curbpack-native review-pack layers (default)
	shapeRepo   fixtureShape = "repo"   // bare tree; only Files / Refs / Dirs
)

// fixtureRefs embeds extractable references into one surface document.
type fixtureRefs struct {
	Paths  []string // backtick-wrapped path tokens
	Claims []string // HOUSE|CRA|MEDTECH-… claim ids
	URLs   []string // https://… URLs
	Raw    string   // appended verbatim after structured refs
}

// fixtureSpec builds a temp directory for review tests.
// Empty Shape defaults to shapeBundle (same bytes as the historical writeMinimalConsistent).
type fixtureSpec struct {
	Shape fixtureShape

	// Files maps slash-relative paths to contents. Overrides defaults for the same path.
	Files map[string]string

	// SizePads appends N zero bytes after the file content (oversize / refuse tests).
	SizePads map[string]int

	// Dirs creates empty directories (repo ignore / walk tests).
	Dirs []string

	// Surface is the slash-relative path that receives Refs (bundle default: 02-action-report.md).
	Surface string
	Refs    fixtureRefs

	// PackID overrides the default house-policy pack id in the gate payload / one-pager.
	PackID string
}

// writeFixture materializes spec under a fresh temp directory and returns its path.
func writeFixture(t *testing.T, spec fixtureSpec) string {
	t.Helper()
	dir := t.TempDir()
	shape := spec.Shape
	if shape == "" {
		shape = shapeBundle
	}

	for _, d := range spec.Dirs {
		d = filepath.FromSlash(strings.TrimSpace(d))
		if d == "" {
			continue
		}
		if err := os.MkdirAll(filepath.Join(dir, d), 0o755); err != nil {
			t.Fatal(err)
		}
	}

	files := map[string]string{}
	if shape == shapeBundle {
		packID := strings.TrimSpace(spec.PackID)
		if packID == "" {
			packID = "house-policy"
		}
		payload := ir.GateFailurePayload{SchemaVersion: "1", PackID: packID, ReadinessScore: 80}
		raw, err := json.MarshalIndent(payload, "", "  ")
		if err != nil {
			t.Fatal(err)
		}
		files["01-gate-failures.json"] = string(append(raw, '\n'))
		files["02-action-report.md"] = "ok\n"
		files["03-executive-summary.md"] = "ok\n"
		digest := ir.ComputeResultDigest(payload)
		files["buyer-onepager.html"] = `<!-- curbpack-onepager-fp:aaaaaaaaaaaaaaaa -->
<dl class="prov"><dt>Rule packs</dt><dd>` + packID + `</dd>
<dt>result_digest</dt><dd>` + digest[:12] + `…</dd></dl>`
	}
	for k, v := range spec.Files {
		k = filepath.ToSlash(strings.TrimSpace(k))
		if k == "" {
			continue
		}
		files[k] = v
	}

	surface := filepath.ToSlash(strings.TrimSpace(spec.Surface))
	if surface == "" && shape == shapeBundle {
		surface = "02-action-report.md"
	}
	if surface != "" && hasFixtureRefs(spec.Refs) {
		var b strings.Builder
		if existing, ok := files[surface]; ok {
			b.WriteString(existing)
			if !strings.HasSuffix(existing, "\n") {
				b.WriteByte('\n')
			}
		}
		for _, p := range spec.Refs.Paths {
			p = strings.TrimSpace(p)
			if p == "" {
				continue
			}
			b.WriteString("`")
			b.WriteString(p)
			b.WriteString("`\n")
		}
		for _, c := range spec.Refs.Claims {
			c = strings.TrimSpace(c)
			if c == "" {
				continue
			}
			b.WriteString(c)
			b.WriteByte('\n')
		}
		for _, u := range spec.Refs.URLs {
			u = strings.TrimSpace(u)
			if u == "" {
				continue
			}
			b.WriteString(u)
			b.WriteByte('\n')
		}
		if raw := spec.Refs.Raw; raw != "" {
			b.WriteString(raw)
			if !strings.HasSuffix(raw, "\n") {
				b.WriteByte('\n')
			}
		}
		files[surface] = b.String()
	}

	for rel, body := range files {
		pad := 0
		if spec.SizePads != nil {
			pad = spec.SizePads[rel]
		}
		writeFixtureFile(t, dir, rel, body, pad)
	}
	// SizePads for paths not otherwise listed (pure padding files).
	for rel, pad := range spec.SizePads {
		rel = filepath.ToSlash(strings.TrimSpace(rel))
		if rel == "" {
			continue
		}
		if _, ok := files[rel]; ok {
			continue
		}
		writeFixtureFile(t, dir, rel, "", pad)
	}
	return dir
}

func hasFixtureRefs(r fixtureRefs) bool {
	return len(r.Paths) > 0 || len(r.Claims) > 0 || len(r.URLs) > 0 || strings.TrimSpace(r.Raw) != ""
}

func writeFixtureFile(t *testing.T, root, rel, body string, pad int) {
	t.Helper()
	rel = filepath.FromSlash(rel)
	full := filepath.Join(root, rel)
	if err := os.MkdirAll(filepath.Dir(full), 0o755); err != nil {
		t.Fatal(err)
	}
	data := []byte(body)
	if pad > 0 {
		data = append(data, make([]byte, pad)...)
	}
	mustWrite(t, full, data)
}

// writeMinimalConsistent returns a minimal consistent review-pack (bundle shape).
// Prefer writeFixture with an explicit fixtureSpec for new tests.
func writeMinimalConsistent(t *testing.T) string {
	t.Helper()
	return writeFixture(t, fixtureSpec{})
}

func TestFixtureBuilderBundleDefaults(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{})
	for _, name := range []string{
		"01-gate-failures.json", "02-action-report.md",
		"03-executive-summary.md", "buyer-onepager.html",
	} {
		st, err := os.Stat(filepath.Join(dir, name))
		if err != nil || st.Size() == 0 {
			t.Fatalf("default bundle missing %s: %v", name, err)
		}
	}
}

func TestFixtureBuilderRepoShapeAndRefs(t *testing.T) {
	dir := writeFixture(t, fixtureSpec{
		Shape:   shapeRepo,
		Surface: "docs/note.md",
		Files: map[string]string{
			"docs/note.md":     "# note\n",
			"SECURITY.md":      "# security\n",
			"docs/present.txt": "here\n",
		},
		Dirs: []string{".git/objects", "node_modules/left-pad"},
		Refs: fixtureRefs{
			Paths:  []string{"SECURITY.md", "docs/missing.md"},
			Claims: []string{"HOUSE-SECURITY-MD"},
			URLs:   []string{"https://example.com/docs"},
		},
	})
	if _, err := os.Stat(filepath.Join(dir, "01-gate-failures.json")); !os.IsNotExist(err) {
		t.Fatal("repo shape must not invent pack layers")
	}
	body, err := os.ReadFile(filepath.Join(dir, "docs/note.md"))
	if err != nil {
		t.Fatal(err)
	}
	s := string(body)
	for _, want := range []string{"`SECURITY.md`", "HOUSE-SECURITY-MD", "https://example.com/docs"} {
		if !strings.Contains(s, want) {
			t.Fatalf("surface missing %q in %q", want, s)
		}
	}
	if st, err := os.Stat(filepath.Join(dir, ".git/objects")); err != nil || !st.IsDir() {
		t.Fatalf(".git/objects: %v", err)
	}
}
