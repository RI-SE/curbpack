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
