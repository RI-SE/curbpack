package redact_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/redact"
)

func TestPlainVsEmbeddedTokensDiffer(t *testing.T) {
	in := `/Users/alice/proj/secret.txt`
	plain := redact.String(in, redact.Emit(redact.Plain))
	emb := redact.String(in, redact.Emit(redact.Embedded))
	if plain == emb {
		t.Fatalf("Plain and Embedded must differ on home scrub: both %q", plain)
	}
	if !strings.Contains(plain, "~") {
		t.Fatalf("Plain want ~ token, got %q", plain)
	}
	if !strings.Contains(emb, "<redacted:home-path>") {
		t.Fatalf("Embedded want <redacted:home-path>, got %q", emb)
	}
}

func TestEmitDoesNotInventHome(t *testing.T) {
	// Pattern-only: non-standard home shape still matched by regex; empty Context.Home.
	ctx := redact.Emit(redact.Embedded)
	if ctx.Home != "" {
		t.Fatalf("Emit must leave Home empty, got %q", ctx.Home)
	}
	out := redact.String(`/opt/build/x`, ctx)
	if out != `/opt/build/x` {
		t.Fatalf("non-standard home without Context.Home must stay unchanged, got %q", out)
	}
}

func TestLooksCleanVerifyCustomHome(t *testing.T) {
	ctx := redact.Verify(redact.Plain)
	if ctx.Home == "" {
		t.Skip("no usable UserHomeDir in this environment")
	}
	leak := []byte("path=" + ctx.Home + "/secret")
	if err := redact.LooksClean(leak, ctx); err == nil {
		t.Fatal("want custom-home leak detected on verify side")
	}
}

func TestRepositoryPrefixDoesNotRewriteSibling(t *testing.T) {
	ctx := redact.Context{RepoRoot: "/opt/audit/repo", Mode: redact.Plain}
	got := redact.String("/opt/audit/repo-copy/file /opt/audit/repo/file (/opt/audit/repo)", ctx)
	if got != "/opt/audit/repo-copy/file file (.)" {
		t.Fatalf("path prefix corrupted: %q", got)
	}
}
