package review

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"os"

	"github.com/afelin/curbpack/internal/ir"
	"github.com/afelin/curbpack/internal/pathjail"
)

// digestPaths hashes sorted relPaths under root with one streaming pass per file.
// On oversize: ("", true, skipped). If skipped > 0, callers must refuse (empty digest).
func digestPaths(root string, relPaths []string) (digest string, oversize bool, skipped int) {
	h := sha256.New()
	var streamed int64
	for _, rel := range relPaths {
		remaining := maxBundleDigestBytes - streamed
		if remaining <= 0 {
			return "", true, skipped
		}
		full, _, err := pathjail.Join(root, rel)
		if err != nil {
			skipped++
			continue
		}
		st, err := os.Lstat(full)
		if err != nil || st.Mode()&os.ModeSymlink != 0 || !st.Mode().IsRegular() {
			skipped++
			continue
		}
		if st.Size() > remaining {
			return "", true, skipped
		}
		fileHash, n, err := hashFileStreaming(full, remaining)
		if err != nil {
			skipped++
			continue
		}
		if n > remaining {
			return "", true, skipped
		}
		streamed += n
		ir.WriteLenPrefixed(h, rel)
		ir.WriteLenPrefixed(h, fileHash)
	}
	return fmt.Sprintf("%x", h.Sum(nil)), false, skipped
}

func computeClosureDigest(root string, closure *closureSet) (digest string, oversize bool, skipped int) {
	return digestPaths(root, closure.sorted())
}

func computeBundleDigest(root string, relPaths []string) (digest string, oversize bool, skipped int) {
	return digestPaths(root, relPaths)
}

func hashFileStreaming(path string, maxBytes int64) (hex string, n int64, err error) {
	if maxBytes <= 0 {
		return "", 0, fmt.Errorf("digest: no bytes remaining")
	}
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()
	h := sha256.New()
	n, err = io.CopyN(h, f, maxBytes+1)
	if err != nil && err != io.EOF {
		return "", n, err
	}
	return fmt.Sprintf("%x", h.Sum(nil)), n, nil
}

func computeRecordDigest(rep Report) string {
	cp := rep
	cp.RecordDigest = ""
	cp.BundleRoot = ""
	b, err := json.Marshal(cp)
	if err != nil {
		return ""
	}
	sum := sha256.Sum256(b)
	return fmt.Sprintf("%x", sum[:])
}
