package exportx

import (
	"strings"
	"testing"
)

func TestUsableHomeGuard(t *testing.T) {
	if usableHome("") || usableHome("/") || usableHome(`\`) {
		t.Fatal("empty or filesystem-root home must be unusable for scrub")
	}
	if !usableHome("/home/runner") || !usableHome("/Users/alice") {
		t.Fatal("normal homes should be usable")
	}
}

func TestScrubHomePrefixes_RootHomeWouldNotWipe(t *testing.T) {
	// Contract: even a path full of slashes must keep structure after scrub.
	// usableHome("/") is false, so a hypothetical HOME=/ cannot ReplaceAll("/", "~").
	in := "/corp/shared/apps/myapp/SECURITY.md"
	out := scrubHomePrefixes(in)
	if strings.Count(out, "/") < 3 {
		t.Fatalf("slashes wiped under home scrub: %q -> %q", in, out)
	}
	if !strings.Contains(out, "SECURITY.md") {
		t.Fatalf("basename lost: %q", out)
	}
}

func TestRepoRelativePrefer(t *testing.T) {
	rel, ok := repoRelative("/home/runner/work/r/r/SECURITY.md", "/home/runner/work/r/r")
	if !ok || rel != "SECURITY.md" {
		t.Fatalf("got rel=%q ok=%v", rel, ok)
	}
	if _, ok := repoRelative("/etc/passwd", "/home/runner/work/r/r"); ok {
		t.Fatal("outside repo must not relativize")
	}
}
