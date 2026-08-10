package research

import (
	"fmt"
	"net/url"
	"strings"
)

// AllowedHosts are the only hosts research may cite or fetch (PR to extend).
// Separate from pack-id freeze — citation host discipline only.
var AllowedHosts = map[string]struct{}{
	"eur-lex.europa.eu": {},
	"www.iso.org":       {},
	"iso.org":           {},
	"www.iec.ch":        {},
	"iec.ch":            {},
	"data.europa.eu":    {},
}

// HostAllowed reports whether host (lowercase, no port) is on the allowlist.
func HostAllowed(host string) bool {
	h := strings.ToLower(strings.TrimSpace(host))
	if h == "" {
		return false
	}
	if _, ok := AllowedHosts[h]; ok {
		return true
	}
	return false
}

// ValidateSourceURL refuses non-https and non-allowlisted hosts.
func ValidateSourceURL(raw string) error {
	raw = strings.TrimSpace(raw)
	if raw == "" {
		return fmt.Errorf("empty url")
	}
	u, err := url.Parse(raw)
	if err != nil {
		return fmt.Errorf("parse url: %w", err)
	}
	if !strings.EqualFold(u.Scheme, "https") {
		return fmt.Errorf("refuse non-https url: %s", raw)
	}
	host := strings.ToLower(u.Hostname())
	if !HostAllowed(host) {
		return fmt.Errorf("host not on research allowlist: %s", host)
	}
	return nil
}
