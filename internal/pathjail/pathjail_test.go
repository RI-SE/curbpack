package pathjail_test

import (
	"testing"

	"github.com/afelin/curbpack/internal/pathjail"
)

func TestUnderGitCaseInsensitive(t *testing.T) {
	for _, p := range []string{".git/config", ".Git/hooks/pre-commit", ".GIT/HEAD"} {
		if !pathjail.UnderGit(p) {
			t.Fatalf("expected .git jail for %q", p)
		}
		if err := pathjail.ValidateRel(p); err == nil {
			t.Fatalf("ValidateRel must refuse %q", p)
		}
	}
}

func TestAllowedRelMatchesValidate(t *testing.T) {
	cases := []string{"docs/a.md", "../x", ".git/x", "/abs", "", "ok\x00bad"}
	for _, c := range cases {
		err := pathjail.ValidateRel(c)
		allowed := pathjail.AllowedRel(c)
		if allowed && err != nil {
			t.Fatalf("AllowedRel true but ValidateRel err for %q: %v", c, err)
		}
		if !allowed && err == nil {
			t.Fatalf("AllowedRel false but ValidateRel ok for %q", c)
		}
	}
}
