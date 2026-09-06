package clock

import (
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"
)

// ErrInvalidSourceDateEpoch is returned when SOURCE_DATE_EPOCH is set but is
// not a non-negative Unix second. Callers must not fall back to wall clock.
var ErrInvalidSourceDateEpoch = errors.New("invalid SOURCE_DATE_EPOCH")

// ParseSourceDateEpoch reports the pinned epoch when SOURCE_DATE_EPOCH is set.
// Unset/empty → (zero, false, nil). Invalid → (_, false, ErrInvalidSourceDateEpoch).
// A value that is only whitespace is invalid (the variable is set but unusable).
func ParseSourceDateEpoch() (time.Time, bool, error) {
	raw, set := os.LookupEnv("SOURCE_DATE_EPOCH")
	if !set {
		return time.Time{}, false, nil
	}
	v := stringsTrim(raw)
	if v == "" {
		return time.Time{}, false, fmt.Errorf("%w: %q (want non-negative Unix seconds)", ErrInvalidSourceDateEpoch, raw)
	}
	sec, err := strconv.ParseInt(v, 10, 64)
	if err != nil || sec < 0 {
		return time.Time{}, false, fmt.Errorf("%w: %q (want non-negative Unix seconds)", ErrInvalidSourceDateEpoch, v)
	}
	return time.Unix(sec, 0).UTC(), true, nil
}

// CheckSourceDateEpoch returns nil when unset or valid; otherwise wraps ErrInvalidSourceDateEpoch.
func CheckSourceDateEpoch() error {
	_, _, err := ParseSourceDateEpoch()
	return err
}

// NowUTC returns UTC time for operational timestamps (receipts, display).
// Tests and reproducible builds may pin via SOURCE_DATE_EPOCH (Unix seconds).
// Invalid SOURCE_DATE_EPOCH is rejected — there is no silent wall-clock fallback.
func NowUTC() (time.Time, error) {
	if t, set, err := ParseSourceDateEpoch(); err != nil {
		return time.Time{}, err
	} else if set {
		return t, nil
	}
	return time.Now().UTC(), nil
}

// RFC3339 returns a UTC RFC3339 timestamp using NowUTC.
func RFC3339() (string, error) {
	t, err := NowUTC()
	if err != nil {
		return "", err
	}
	return t.Format(time.RFC3339), nil
}

// EvidenceEpoch is the fixed synthetic UTC timestamp used for digest-bound
// evidence fields when SOURCE_DATE_EPOCH is unset.
const EvidenceEpoch = "1970-01-01T00:00:00Z"

// RFC3339ForEvidence returns a stable UTC RFC3339 timestamp for digest-bound
// evidence (SBOM metadata.timestamp / VEX timestamp). Honors SOURCE_DATE_EPOCH
// when set; otherwise uses EvidenceEpoch so re-attest on the same inputs is
// idempotent without encoding hash entropy into the clock field.
// Invalid SOURCE_DATE_EPOCH is rejected (no silent wall-clock fallback).
func RFC3339ForEvidence() (string, error) {
	if _, set, err := ParseSourceDateEpoch(); err != nil {
		return "", err
	} else if !set {
		return EvidenceEpoch, nil
	}
	return RFC3339()
}

// Art14ReportingStart is the CRA Art 14 reporting clock start (UTC date).
// EC reporting date — see https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R2847
var Art14ReportingStart = time.Date(2026, 9, 11, 0, 0, 0, 0, time.UTC)

// DaysUntilUTC returns whole calendar days from NowUTC (date-truncated) until deadline.
// Negative when the deadline has passed.
func DaysUntilUTC(deadline time.Time) (int, error) {
	now, err := NowUTC()
	if err != nil {
		return 0, err
	}
	now = now.Truncate(24 * time.Hour)
	d := deadline.UTC().Truncate(24 * time.Hour)
	return int(d.Sub(now).Hours() / 24), nil
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
