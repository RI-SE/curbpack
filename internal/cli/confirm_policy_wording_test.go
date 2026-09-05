package cli

import (
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"testing"
)

// MUST-70 honesty: public/agent-facing prose must not treat a TTY as sufficient
// confirmation. Logic stays in requireHumanConfirm; this only locks wording.
func TestConfirmPolicyWording_NoTTYAloneAuth(t *testing.T) {
	_, thisFile, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("runtime.Caller failed")
	}
	root := filepath.Clean(filepath.Join(filepath.Dir(thisFile), "..", ".."))

	// Patterns that historically implied TTY alone (or TTY as a peer auth path).
	bad := []*regexp.Regexp{
		regexp.MustCompile(`(?i)on a TTY,\s*with\s*\x60?--i-am-human`),
		regexp.MustCompile(`(?i)confirm-packs\s*\(TTY\s*/`),
		regexp.MustCompile(`(?i)Confirms?\s+(?:need|require|via)\s+a\s+TTY\b`),
	}

	files := []string{
		"papers/curbpack-whitepaper.md",
		"AGENTS.md",
		"CLAUDE.md",
		"README.md",
		"docs/assistant-loop.md",
		"docs/getting-started/pathway.md",
		"internal/skilldata/SKILL.md",
	}
	var hits []string
	for _, rel := range files {
		b, err := os.ReadFile(filepath.Join(root, rel))
		if err != nil {
			t.Fatalf("read %s: %v", rel, err)
		}
		body := string(b)
		for _, re := range bad {
			if re.FindStringIndex(body) != nil {
				hits = append(hits, rel+": "+re.String())
			}
		}
		// Positive: when confirms are discussed with TTY, require the refuse phrase.
		if strings.Contains(body, "TTY") && (strings.Contains(body, "confirm") || strings.Contains(body, "Confirm")) {
			if !strings.Contains(body, "TTY alone is not enough") && !strings.Contains(body, "TTY alone is not sufficient") {
				// Allow files that mention TTY only for init/non-confirm contexts.
				lower := strings.ToLower(body)
				if strings.Contains(lower, "confirm") && strings.Contains(lower, "tty") &&
					(strings.Contains(lower, "i-am-human") || strings.Contains(lower, "allow_confirm")) {
					hits = append(hits, rel+": mentions TTY+confirm without refuse phrase")
				}
			}
		}
	}
	if len(hits) > 0 {
		t.Fatalf("MUST-70 wording regressions:\n  %s", strings.Join(hits, "\n  "))
	}
}
