package clock

import (
	"os"
	"strconv"
	"time"
)

// NowUTC returns UTC time for artifact timestamps.
// Tests and reproducible builds may pin via SOURCE_DATE_EPOCH (Unix seconds).
func NowUTC() time.Time {
	if v := stringsTrim(os.Getenv("SOURCE_DATE_EPOCH")); v != "" {
		if sec, err := strconv.ParseInt(v, 10, 64); err == nil && sec >= 0 {
			return time.Unix(sec, 0).UTC()
		}
	}
	return time.Now().UTC()
}

// RFC3339 returns a UTC RFC3339 timestamp using NowUTC.
func RFC3339() string {
	return NowUTC().Format(time.RFC3339)
}

// EvidenceEpoch is the fixed synthetic UTC timestamp used for digest-bound
// evidence fields when SOURCE_DATE_EPOCH is unset.
const EvidenceEpoch = "1970-01-01T00:00:00Z"

// RFC3339ForEvidence returns a stable UTC RFC3339 timestamp for digest-bound
// evidence (SBOM metadata.timestamp / VEX timestamp). Honors SOURCE_DATE_EPOCH
// when set; otherwise uses EvidenceEpoch so re-attest on the same inputs is
// idempotent without encoding hash entropy into the clock field.
func RFC3339ForEvidence() string {
	if v := stringsTrim(os.Getenv("SOURCE_DATE_EPOCH")); v != "" {
		return RFC3339()
	}
	return EvidenceEpoch
}

// Art14ReportingStart is the CRA Art 14 reporting clock start (UTC date).
// EC reporting date — see https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847
var Art14ReportingStart = time.Date(2026, 9, 11, 0, 0, 0, 0, time.UTC)

// DaysUntilUTC returns whole calendar days from NowUTC (date-truncated) until deadline.
// Negative when the deadline has passed.
func DaysUntilUTC(deadline time.Time) int {
	now := NowUTC().Truncate(24 * time.Hour)
	d := deadline.UTC().Truncate(24 * time.Hour)
	return int(d.Sub(now).Hours() / 24)
}

// FormatArt14Countdown formats days until Art14ReportingStart for site HTML.
// Matches site/index.html client-side formatCountdown (progressive enhancement).
func FormatArt14Countdown(days int) string {
	if days > 0 {
		s := "s"
		if days == 1 {
			s = ""
		}
		return "Article 14 reporting starts in " + strconv.Itoa(days) + " day" + s + " (11 September 2026)"
	}
	if days == 0 {
		return "Article 14 reporting starts today (11 September 2026)"
	}
	return "Article 14 reporting has applied since 11 September 2026"
}

func stringsTrim(s string) string {
	i := 0
	j := len(s)
	for i < j && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r') {
		i++
	}
	for j > i && (s[j-1] == ' ' || s[j-1] == '\t' || s[j-1] == '\n' || s[j-1] == '\r') {
		j--
	}
	return s[i:j]
}
