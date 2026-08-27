package research

import "github.com/afelin/curbpack/internal/sourceurl"

// AllowedHosts re-exports the citation host allowlist.
var AllowedHosts = sourceurl.AllowedHosts

// HostAllowed reports whether host is on the research allowlist.
func HostAllowed(host string) bool { return sourceurl.HostAllowed(host) }

// ValidateSourceURL refuses non-https and non-allowlisted hosts.
func ValidateSourceURL(raw string) error { return sourceurl.Validate(raw) }
