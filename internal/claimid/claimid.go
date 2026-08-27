// Package claimid is the single definition site for pack claim-id matching
// used by review and research extractors (not skilldata / check output alphabet).
package claimid

import (
	"regexp"
	"strings"
)

// DropUnknownNamespace labels claim-shaped tokens that miss the claim namespace.
const DropUnknownNamespace = "unknown-claim-namespace"

// Pattern is the provisional claim-id shape (ClassifierVersion refclass:2).
// Deny-list tokens matching the shape are never claims.
const Pattern = `[A-Z][A-Z0-9]{1,15}-[A-Z0-9-]+`

var (
	reClaim = regexp.MustCompile(`\b` + Pattern + `\b`)
	// Exact full-string match for ClassifyReference.
	reClaimExact = regexp.MustCompile(`^` + Pattern + `$`)
)

// denyExact are full-token denials (common standards/license/hash labels).
var denyExact = map[string]struct{}{
	"SPDX-License-Identifier": {},
	"RFC-2119":                {},
	"SHA-256":                 {},
	"SHA-1":                   {},
	"SHA-512":                 {},
	"ISO-8601":                {},
	"UTF-8":                   {},
}

// denyPrefixes catches SPDX-* and similar without listing every license id.
var denyPrefixes = []string{
	"SPDX-",
	"RFC-",
	"SHA-",
}

// FindAll returns claim-shaped tokens in text (may include denied tokens).
func FindAll(text string) []string {
	return reClaim.FindAllString(text, -1)
}

// MatchFull reports whether s is exactly one claim-shaped token.
func MatchFull(s string) bool {
	return reClaimExact.MatchString(strings.TrimSpace(s))
}

// Denied reports deny-list tokens that must never become claims.
func Denied(s string) bool {
	s = strings.TrimSpace(s)
	if _, ok := denyExact[s]; ok {
		return true
	}
	for _, p := range denyPrefixes {
		if strings.HasPrefix(s, p) {
			return true
		}
	}
	return false
}

// IsClaim reports whether s is an accepted claim id (shaped and not denied).
func IsClaim(s string) bool {
	s = strings.TrimSpace(s)
	if !MatchFull(s) {
		return false
	}
	return !Denied(s)
}

// FormatDrop formats a dropped claim-shaped token with reason.
func FormatDrop(token, reason string) string {
	token = strings.TrimSpace(token)
	reason = strings.TrimSpace(reason)
	if reason == "" {
		return token
	}
	return token + " [" + reason + "]"
}
