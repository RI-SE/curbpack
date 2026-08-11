package research

import (
	"crypto/sha256"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

const (
	fetchTimeout   = 10 * time.Second
	fetchMaxBytes  = 64 * 1024 // 64 KiB cap
	fetchExcerptMax = 1200
)

// HTTPDoer is injectable for tests.
type HTTPDoer interface {
	Do(req *http.Request) (*http.Response, error)
}

// DefaultHTTPClient is the allowlisted GET client (timeout + redirects limited).
func DefaultHTTPClient() *http.Client {
	return &http.Client{
		Timeout: fetchTimeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			if len(via) >= 3 {
				return fmt.Errorf("too many redirects")
			}
			if err := ValidateSourceURL(req.URL.String()); err != nil {
				return err
			}
			return nil
		},
	}
}

// FetchSources fills excerpt/sha256/retrieved_at or fetch_error per URL (fail-open).
func FetchSources(sources []Source, retrievedAt string) {
	FetchSourcesWith(sources, retrievedAt, DefaultHTTPClient())
}

// FetchSourcesWith is the injectable variant.
func FetchSourcesWith(sources []Source, retrievedAt string, client HTTPDoer) {
	if client == nil {
		client = DefaultHTTPClient()
	}
	for i := range sources {
		s := &sources[i]
		if err := ValidateSourceURL(s.URL); err != nil {
			s.FetchError = err.Error()
			continue
		}
		excerpt, digest, err := fetchOne(client, s.URL)
		s.RetrievedAt = retrievedAt
		if err != nil {
			s.FetchError = err.Error()
			continue
		}
		s.Excerpt = excerpt
		s.ContentSHA256 = digest
		s.FetchError = ""
	}
}

func fetchOne(client HTTPDoer, rawURL string) (excerpt, digest string, err error) {
	req, err := http.NewRequest(http.MethodGet, rawURL, nil)
	if err != nil {
		return "", "", err
	}
	req.Header.Set("User-Agent", "curbpack-research/1 (+local allowlisted fetch; not a crawler)")
	req.Header.Set("Accept", "text/html,text/plain,application/xhtml+xml;q=0.9,*/*;q=0.1")

	resp, err := client.Do(req)
	if err != nil {
		return "", "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", "", fmt.Errorf("http %d", resp.StatusCode)
	}
	limited := io.LimitReader(resp.Body, fetchMaxBytes+1)
	body, err := io.ReadAll(limited)
	if err != nil {
		return "", "", err
	}
	if len(body) > fetchMaxBytes {
		body = body[:fetchMaxBytes]
	}
	sum := sha256.Sum256(body)
	digest = fmt.Sprintf("%x", sum)
	excerpt = stripToExcerpt(string(body), fetchExcerptMax)
	return excerpt, digest, nil
}

func stripToExcerpt(s string, max int) string {
	// Cheap HTML/tag strip for human brief — not a full parser.
	var b strings.Builder
	inTag := false
	for _, r := range s {
		switch {
		case r == '<':
			inTag = true
		case r == '>':
			inTag = false
		case inTag:
			continue
		default:
			if r == '\r' {
				continue
			}
			b.WriteRune(r)
		}
	}
	text := strings.Join(strings.Fields(b.String()), " ")
	if max > 0 && len(text) > max {
		return text[:max] + "…"
	}
	return text
}
