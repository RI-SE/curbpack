// Package airlock checks emitted bytes for absolute homes / PEM blobs without heavier deps.
package airlock

import (
	"fmt"
	"strings"

	"github.com/afelin/curbpack/internal/redact"
)

// PacketLooksAirlocked reports whether packet bytes avoid absolute homes / PEM blobs.
// Verify-side: custom home from the process environment is still checked.
func PacketLooksAirlocked(data []byte) error {
	if err := redact.LooksClean(data, redact.Verify(redact.Plain)); err != nil {
		msg := err.Error()
		if strings.HasPrefix(msg, "packet ") {
			msg = "explain-packet " + strings.TrimPrefix(msg, "packet ")
		}
		return fmt.Errorf("%s", msg)
	}
	return nil
}
