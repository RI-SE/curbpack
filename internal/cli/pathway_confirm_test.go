package cli

import (
	"strings"
	"testing"
)

func TestRequireHumanConfirm_failClosedWithoutFlag(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	err := requireHumanConfirm(nil)
	if err == nil {
		t.Fatal("expected refuse without --i-am-human or env")
	}
	if !strings.Contains(err.Error(), "--i-am-human") {
		t.Fatalf("want --i-am-human hint, got %v", err)
	}
}

func TestRequireHumanConfirm_flag(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	if err := requireHumanConfirm([]string{"--i-am-human"}); err != nil {
		t.Fatal(err)
	}
}

func TestRequireHumanConfirm_env(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "1")
	if err := requireHumanConfirm(nil); err != nil {
		t.Fatal(err)
	}
}

func TestRequireHumanConfirm_envNotOne(t *testing.T) {
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "true")
	if err := requireHumanConfirm(nil); err == nil {
		t.Fatal("only CURBPACK_ALLOW_CONFIRM=1 should allow")
	}
}

func TestRequireHumanConfirm_ignoresTTYAlone(t *testing.T) {
	// Document invariant: do not reopen TTY-alone path (agents often have a TTY).
	t.Setenv("CURBPACK_ALLOW_CONFIRM", "")
	t.Setenv("CYBERREADY_ALLOW_CONFIRM", "")
	if err := requireHumanConfirm([]string{}); err == nil {
		t.Fatal("TTY-alone must not authorize confirm")
	}
}
