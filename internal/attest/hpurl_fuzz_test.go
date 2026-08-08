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
}
