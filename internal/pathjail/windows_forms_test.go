package pathjail_test

import (
	"strings"
	"testing"

	"github.com/afelin/curbpack/internal/pathjail"
)

func TestWindowsPathFormsRefused(t *testing.T) {
	cases := []struct {
		rel string
		sub string
	}{
		{`C:\Windows\system32`, "absolute"},
		{`D:/escape`, "absolute"},
		{`C:escape`, "drive-relative"},
		{`docs/file.md:stream`, "alternate stream"},
		{`.git::$INDEX_ALLOCATION`, "alternate stream"},
		{`\\server\share\file`, "absolute"},
		{`//server/share/file`, "absolute"},
		{`docs\.git\config`, ".git"},
		{`.git.`, ".git"},
		{`.git `, ".git"},
		{`foo/.git./bar`, ".git"},
		{`CON`, "reserved"},
		{`com1`, "reserved"},
		{`aux.txt`, "reserved"},
		{`prn`, "reserved"},
		{`nul`, "reserved"},
		{`lpt9`, "reserved"},
		{`docs\ok.md`, ""}, // alt separator allowed after normalize
	}
	for _, tc := range cases {
		err := pathjail.ValidateRel(tc.rel)
		allowed := pathjail.AllowedRel(tc.rel)
		if tc.sub == "" {
			if err != nil || !allowed {
				t.Fatalf("%q should be allowed, err=%v allowed=%v", tc.rel, err, allowed)
			}
			continue
		}
		if err == nil || allowed {
			t.Fatalf("%q must refuse (%s), err=%v allowed=%v", tc.rel, tc.sub, err, allowed)
		}
		if !strings.Contains(strings.ToLower(err.Error()), strings.ToLower(tc.sub)) &&
			!(tc.sub == "absolute" && strings.Contains(err.Error(), "absolute")) &&
			!(tc.sub == "reserved" && strings.Contains(err.Error(), "reserved")) &&
			!(tc.sub == ".git" && strings.Contains(err.Error(), ".git")) {
			t.Fatalf("%q: want error mentioning %q, got %v", tc.rel, tc.sub, err)
		}
	}
}

func TestIsWindowsAbs(t *testing.T) {
	if !pathjail.IsWindowsAbs(`C:\x`) || !pathjail.IsWindowsAbs(`\\srv\share`) {
		t.Fatal("expected windows abs detection")
	}
	if pathjail.IsWindowsAbs(`docs/a.md`) {
		t.Fatal("relative path must not be windows abs")
	}
}
