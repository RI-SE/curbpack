package invariants_test

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// TestMDRQuoteFragmentsVerbatim guards Annex IV(8) and Annex VII §1.2.3(c)
// against paraphrase-as-quote regressions (W1a).
func TestMDRQuoteFragmentsVerbatim(t *testing.T) {
	_, thisFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	root := filepath.Clean(filepath.Join(filepath.Dir(thisFile), "..", ".."))
	path := filepath.Join(root, "docs", "shared-frame-annexes.md")
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	text := string(b)
	want := []string{
		`a description of the conformity assessment procedure performed and identification of the certificate or certificates issued`,
		`engage in any activity that may conflict with their independence of judgement or integrity in relation to conformity assessment activities for which they are designated`,
	}
	for _, frag := range want {
		if !strings.Contains(text, frag) {
			t.Fatalf("missing verbatim MDR fragment in %s: %q", path, frag)
		}
	}
	if strings.Contains(text, "a description of the conformity assessment procedure performed…") ||
		strings.Contains(text, "a description of the conformity assessment procedure performed...") {
		t.Fatal("Annex IV(8) must not use ellipsis inside the operative quote fragment")
	}
}
