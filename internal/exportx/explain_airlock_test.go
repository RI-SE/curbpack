package exportx

import (
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/redact"
)

func TestUsableHomeGuardViaEmit(t *testing.T) {
	in := "/corp/shared/apps/myapp/SECURITY.md"
	out := redact.String(in, redact.Context{Mode: redact.Plain, Home: "/"})
	if strings.Count(out, "/") < 3 {
		t.Fatalf("slashes wiped under home scrub: %q -> %q", in, out)
	}
	if !strings.Contains(out, "SECURITY.md") {
		t.Fatalf("basename lost: %q", out)
	}
}

func TestRepoRelativePrefer(t *testing.T) {
	root := "/home/runner/work/r/r"
	inside := "/home/runner/work/r/r/SECURITY.md"
	outside := "/etc/passwd"
	if runtime.GOOS == "windows" {
		root = `C:\Users\runner\work\r\r`
		inside = `C:\Users\runner\work\r\r\SECURITY.md`
		outside = `C:\Windows\System32\drivers\etc\hosts`
	}
	ctx := redact.Emit(redact.Plain)
	ctx.RepoRoot = root
	got := redact.RelativizePath(inside, ctx)
	if got != "SECURITY.md" {
		t.Fatalf("got rel=%q", got)
	}
	out := redact.RelativizePath(outside, ctx)
	if out == "" {
		t.Fatal("outside must still return basename-ish")
	}
	_ = filepath.Base(outside)
}
