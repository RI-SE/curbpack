// Package githook owns exact pre-commit hook bodies shipped by Curbpack.
// Install replaces only known Curbpack bodies; custom hooks are refused.
package githook

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
)

// CurrentPreCommit is the non-healing hook body written by current installs.
// LF-only ASCII: never write CRLF; avoid non-ASCII so CI grep -F is never
// locale/"binary file" sensitive on the fail-closed assertion string.
const CurrentPreCommit = "#!/bin/sh\n" +
	"# Curbpack - fail commit on high/critical gate findings\n" +
	"# Remediation is explicit; a commit hook must not create or edit tracked files.\n" +
	"# Hooks enabled => missing binary is fail-closed (no silent skip).\n" +
	"if command -v curbpack >/dev/null 2>&1; then\n" +
	"  exec curbpack check\n" +
	"elif [ -x ./bin/curbpack ]; then\n" +
	"  exec ./bin/curbpack check\n" +
	"elif [ -x ./curbpack ]; then\n" +
	"  exec ./curbpack check\n" +
	"else\n" +
	"  echo \"curbpack not on PATH - refusing commit (hooks enabled)\" >&2\n" +
	"  exit 1\n" +
	"fi\n"

// LegacyHealPreCommitV052to054 is the exact body shipped by v0.5.2–v0.5.4
// (identical across those tags). Byte-identical match only.
const LegacyHealPreCommitV052to054 = "#!/bin/sh\n" +
	"# Curbpack — fail commit on high/critical gate findings\n" +
	"# --heal: create missing stubs only (never overwrite filled docs; never attest)\n" +
	"# Hooks enabled ⇒ missing binary is fail-closed (no silent skip).\n" +
	"if command -v curbpack >/dev/null 2>&1; then\n" +
	"  exec curbpack check --heal\n" +
	"elif [ -x ./bin/curbpack ]; then\n" +
	"  exec ./bin/curbpack check --heal\n" +
	"elif [ -x ./curbpack ]; then\n" +
	"  exec ./curbpack check --heal\n" +
	"else\n" +
	"  echo \"curbpack not on PATH — refusing commit (hooks enabled)\" >&2\n" +
	"  exit 1\n" +
	"fi\n"

// Kind classifies an on-disk pre-commit hook relative to known Curbpack bodies.
type Kind int

const (
	KindMissing Kind = iota
	KindCurrent
	KindLegacyHeal
	KindCustom
)

// Classify returns the kind of the hook body.
func Classify(body []byte) Kind {
	if bytes.Equal(body, []byte(CurrentPreCommit)) {
		return KindCurrent
	}
	if bytes.Equal(body, []byte(LegacyHealPreCommitV052to054)) {
		return KindLegacyHeal
	}
	return KindCustom
}

// IsKnownLegacy reports whether body is an exact shipped healing hook.
func IsKnownLegacy(body []byte) bool {
	return Classify(body) == KindLegacyHeal
}

// ContainsHeal reports whether the hook invokes curbpack check --heal.
func ContainsHeal(body []byte) bool {
	return bytes.Contains(body, []byte("--heal"))
}

// Path returns .git/hooks/pre-commit under root.
func Path(root string) string {
	return filepath.Join(root, ".git", "hooks", "pre-commit")
}

// InstallResult describes what Install did.
type InstallResult struct {
	ReplacedLegacy bool
	AlreadyCurrent bool
	WroteNew       bool
}

// Install writes the current non-healing hook when missing, already current, or
// an exact known legacy heal body. Custom or composed hooks are refused.
func Install(root string) (InstallResult, error) {
	var result InstallResult
	hookDir := filepath.Join(root, ".git", "hooks")
	if err := os.MkdirAll(hookDir, 0o755); err != nil {
		return result, err
	}
	path := Path(root)
	current := []byte(CurrentPreCommit)
	if bytes.Contains(current, []byte("\r")) {
		return result, fmt.Errorf("internal: hook script must be LF-only")
	}

	existing, err := os.ReadFile(path)
	if err != nil {
		if !os.IsNotExist(err) {
			return result, err
		}
		if err := os.WriteFile(path, current, 0o755); err != nil {
			return result, err
		}
		result.WroteNew = true
		return result, nil
	}

	switch Classify(existing) {
	case KindCurrent:
		result.AlreadyCurrent = true
		return result, nil
	case KindLegacyHeal:
		bak := path + ".curbpack-legacy.bak"
		if err := os.WriteFile(bak, existing, 0o755); err != nil {
			return result, fmt.Errorf("backup legacy hook: %w", err)
		}
		if err := os.WriteFile(path, current, 0o755); err != nil {
			return result, err
		}
		result.ReplacedLegacy = true
		return result, nil
	default:
		return result, fmt.Errorf(
			"refusing to overwrite custom pre-commit hook at %s\n"+
				"Curbpack replaces only an exact known legacy body (v0.5.2–v0.5.4 heal hook) or installs when missing.\n"+
				"Manual options:\n"+
				"  1) Keep your hook; remove --heal from any curbpack check invocation so commits never mutate tracked files.\n"+
				"  2) Diff against a known body, then replace only if you intend to adopt CurrentPreCommit.\n"+
				"Do not blindly re-run init --hooks over a composed hook.",
			path,
		)
	}
}
