// Package redact consolidates home-path and PEM scrubbing for crossing surfaces.
// Emit paths use an explicit Context (never invent a home via os.UserHomeDir).
// Verify paths keep custom-home leak detection via Context.Home or UserHomeDir.
package redact

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// Mode selects replacement tokens. Plain is human-facing; Embedded is machine JSON.
type Mode int

const (
	// Plain replaces homes with "~" and PEM with "[REDACTED_PEM]".
	Plain Mode = iota
	// Embedded replaces homes with "<redacted:home-path>" and PEM with "<redacted:pem>".
	Embedded
)

const (
	plainHome     = "~"
	plainPEM      = "[REDACTED_PEM]"
	embeddedHome  = "<redacted:home-path>"
	embeddedPEM   = "<redacted:pem>"
	plainSecretRe = `(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+`
)

var (
	homePathRE = regexp.MustCompile(`(?i)(/Users/[^/\s"'<>]+|/home/[^/\s"'<>]+|/mnt/[a-z]/Users/[^/\s"'<>]+|C:\\Users\\[^\\\s"'<>]+)`)
	pemBlobRE  = regexp.MustCompile(`-----BEGIN [A-Z0-9 ]+-----[\s\S]{20,}?-----END [A-Z0-9 ]+-----`)
	secretRE   = regexp.MustCompile(plainSecretRe)
)

// Context is the explicit redaction/verify contract. Emit must not call
// os.UserHomeDir when Home is empty — pattern scrub only. Verify may resolve
// Home from UserHomeDir when empty so custom-home leaks still fail closed.
type Context struct {
	Mode     Mode
	Home     string // absolute home to scrub/verify; empty = emit pattern-only
	RepoRoot string // optional; absolute paths under this tree become repo-relative
	Secrets  bool   // Plain explain-path also scrubs api_key= style secrets
}

// Emit returns a Context for scrubbing outbound bytes. Home is never filled from
// the environment — callers that need home substitution must set Home explicitly.
func Emit(mode Mode) Context {
	return Context{Mode: mode}
}

// Verify returns a Context for leak detection. When Home is empty it uses
// os.UserHomeDir when usable so verify-side custom-home protection remains.
func Verify(mode Mode) Context {
	ctx := Context{Mode: mode}
	if home, err := os.UserHomeDir(); err == nil && usableHome(home) {
		ctx.Home = strings.TrimSpace(home)
	}
	return ctx
}

// HomeToken is the replacement used for home paths under Mode.
func (c Context) HomeToken() string {
	if c.Mode == Embedded {
		return embeddedHome
	}
	return plainHome
}

// PEMToken is the replacement used for PEM blobs under Mode.
func (c Context) PEMToken() string {
	if c.Mode == Embedded {
		return embeddedPEM
	}
	return plainPEM
}

// String scrubs s according to Context. Emit with empty Home never calls UserHomeDir.
func String(s string, ctx Context) string {
	s = pemBlobRE.ReplaceAllString(s, ctx.PEMToken())
	if ctx.Secrets {
		s = secretRE.ReplaceAllString(s, "$1=[REDACTED]")
	}
	s = scrubRepoRoot(s, ctx.RepoRoot)
	if home := strings.TrimSpace(ctx.Home); usableHome(home) {
		s = strings.ReplaceAll(s, home, ctx.HomeToken())
		if slash := filepath.ToSlash(home); slash != home {
			s = strings.ReplaceAll(s, slash, ctx.HomeToken())
		}
	}
	s = homePathRE.ReplaceAllString(s, ctx.HomeToken())
	return s
}

// LooksClean reports whether data avoids absolute homes / PEM (and explicit Home).
// Empty Home still consults UserHomeDir when usable — verify-side custom-home protection.
func LooksClean(data []byte, ctx Context) error {
	if pemBlobRE.Match(data) {
		return fmt.Errorf("packet contains PEM-looking blob")
	}
	if homePathRE.Match(data) {
		return fmt.Errorf("packet contains absolute home path")
	}
	homes := explicitHomes(ctx)
	for _, home := range homes {
		if bytes.Contains(data, []byte(home)) {
			return fmt.Errorf("packet contains user home directory path")
		}
		if slash := filepath.ToSlash(home); slash != home && bytes.Contains(data, []byte(slash)) {
			return fmt.Errorf("packet contains user home directory path")
		}
	}
	return nil
}

func explicitHomes(ctx Context) []string {
	var out []string
	home := strings.TrimSpace(ctx.Home)
	if usableHome(home) {
		out = append(out, home)
		return out
	}
	// Verify-side fallback: process home when Context did not pin one.
	if home, err := os.UserHomeDir(); err == nil && usableHome(home) {
		out = append(out, strings.TrimSpace(home))
	}
	return out
}

func usableHome(home string) bool {
	home = strings.TrimSpace(home)
	if home == "" || home == "/" || home == `\` || home == `C:\` || home == `C:/` {
		return false
	}
	return true
}

func scrubRepoRoot(s, repoRoot string) string {
	if strings.TrimSpace(repoRoot) == "" {
		return s
	}
	abs, err := filepath.Abs(repoRoot)
	if err != nil {
		return s
	}
	abs = filepath.Clean(abs)
	if abs == "" || abs == "/" || abs == `.` {
		return s
	}
	for _, root := range []string{filepath.ToSlash(abs), abs} {
		s = strings.ReplaceAll(s, root+"/", "")
		s = strings.ReplaceAll(s, root+`\`, "")
		// A bare root ends at a text delimiter. Do not rewrite a sibling such as
		// /repo-copy merely because the configured root is /repo.
		re := regexp.MustCompile(regexp.QuoteMeta(root) + `($|[\s"'<>),;])`)
		s = re.ReplaceAllString(s, ".${1}")
	}
	return s
}

// RelativizePath rewrites abs paths under RepoRoot to slash-relative form;
// otherwise applies home/pattern scrub and basename fallback for abs leftovers.
func RelativizePath(p string, ctx Context) string {
	p = strings.TrimSpace(p)
	if p == "" {
		return ""
	}
	if rel, ok := repoRelative(p, ctx.RepoRoot); ok {
		return filepath.ToSlash(rel)
	}
	p = String(p, ctx)
	p = filepath.ToSlash(p)
	if strings.HasPrefix(p, "/") || strings.Contains(p, ":/") {
		p = filepath.Base(p)
	}
	return p
}

func repoRelative(p, repoRoot string) (string, bool) {
	if strings.TrimSpace(repoRoot) == "" || !filepath.IsAbs(p) {
		return "", false
	}
	absRoot, err := filepath.Abs(repoRoot)
	if err != nil {
		return "", false
	}
	absRoot = filepath.Clean(absRoot)
	absPath := filepath.Clean(p)
	rel, err := filepath.Rel(absRoot, absPath)
	if err != nil {
		return "", false
	}
	if rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) {
		return "", false
	}
	return rel, true
}
