package contract_test

import (
	"os"
	"regexp"
	"testing"
)

func TestActionHealDefaultFalse(t *testing.T) {
	b, err := os.ReadFile("../../action.yml")
	if err != nil {
		t.Fatal(err)
	}
	// Fail-closed: heal must default false (opt-in stubs only).
	re := regexp.MustCompile(`(?m)^  heal:\n(?:.*\n){0,4}    default: 'false'`)
	if !re.Match(b) {
		t.Fatal("action.yml heal default must be 'false'")
	}
	if regexp.MustCompile(`(?m)^  heal:\n(?:.*\n){0,4}    default: 'true'`).Match(b) {
		t.Fatal("action.yml heal must not default to 'true'")
	}
}

func TestActionRefusesWindowsRunners(t *testing.T) {
	b, err := os.ReadFile("../../action.yml")
	if err != nil {
		t.Fatal(err)
	}
	if !regexp.MustCompile(`mingw\*\|msys\*\|cygwin\*\|windows\*`).Match(b) {
		t.Fatal("action.yml must refuse Windows/MINGW/CYGWIN runners early")
	}
	if !regexp.MustCompile(`curbpack-REMEDIATION-REVIEW`).Match(b) {
		t.Fatal("action.yml must upload REMEDIATION REVIEW artifact on red, not quiet buyer-onepager success")
	}
}
