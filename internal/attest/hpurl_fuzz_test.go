package attest

import (
	"testing"
	"unicode/utf8"
)

func FuzzParseHPURLFragment(f *testing.F) {
	for _, s := range []string{
		"#?h=abc&p=def&s=ghi",
		"#?h=&p=&s=",
		"not-a-fragment",
		"#?h=deadbeef",
		"",
		"#?h=x&p=y&extra=1",
	} {
		f.Add(s)
	}
	f.Fuzz(func(t *testing.T, frag string) {
		if !utf8.ValidString(frag) || len(frag) > 4096 {
			return
		}
		parts, ok := ParseHPURLFragment(frag)
		if ok && parts.StateHash == "" {
			t.Fatal("ok with empty h")
		}
	})
}

func TestParseHPURLFragment(t *testing.T) {
	p, ok := ParseHPURLFragment("#?h=abc&p=def&s=sig")
	if !ok || p.StateHash != "abc" || p.Commit != "def" || p.SigHint != "sig" {
		t.Fatalf("%v %v", p, ok)
	}
	if _, ok := ParseHPURLFragment("#?p=only"); ok {
		t.Fatal("missing h must fail")
	}
	// Spec §3–4: first '?' in fragment starts the query (label before ? is ignored).
	p2, ok := ParseHPURLFragment("#capsule?h=deadbeef&p=c0ffee&s=unsigned")
	if !ok || p2.StateHash != "deadbeef" || p2.Commit != "c0ffee" || p2.SigHint != "unsigned" {
		t.Fatalf("first-? query: %#v ok=%v", p2, ok)
	}
	// Aliases
	p3, ok := ParseHPURLFragment("?hash=aa&commit=bb&sig=cc")
	if !ok || p3.StateHash != "aa" || p3.Commit != "bb" || p3.SigHint != "cc" {
		t.Fatalf("aliases: %#v ok=%v", p3, ok)
	}
}
