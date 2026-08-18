package contract_test

import (
	"os"
	"regexp"
	"strings"
	"testing"
)

func TestActionHealDefaultFalse(t *testing.T) {
	b, err := os.ReadFile("../../action.yml")
	if err != nil {
		t.Fatal(err)
	}
	// CRLF-tolerant: Windows checkouts may retain \r\n; allow optional CR in the regex.
	text := strings.ReplaceAll(string(b), "\r\n", "\n")
	text = strings.ReplaceAll(text, "\r", "\n")
	// Fail-closed: heal must default false (opt-in stubs only).
	re := regexp.MustCompile(`(?m)^  heal:\r?\n(?:.*\r?\n){0,4}    default: 'false'`)
	if !re.MatchString(text) {
		t.Fatal("action.yml heal default must be 'false'")
	}
	if regexp.MustCompile(`(?m)^  heal:\r?\n(?:.*\r?\n){0,4}    default: 'true'`).MatchString(text) {
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
