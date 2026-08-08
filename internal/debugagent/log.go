// Package debugagent writes NDJSON debug session logs (temporary instrumentation).
package debugagent

import (
	"encoding/json"
	"os"
	"time"
)

const (
	sessionID = "561228"
	logPath   = "/Users/afelin/.cursor/CyberReady+/.cursor/debug-561228.log"
)

// Log appends one NDJSON line for hypothesis evaluation. Fail-open.
func Log(hypothesisID, location, message string, data map[string]any) {
	// #region agent log
	payload := map[string]any{
		"sessionId":    sessionID,
		"hypothesisId": hypothesisID,
		"location":     location,
		"message":      message,
		"data":         data,
		"timestamp":    time.Now().UnixMilli(),
		"runId":        os.Getenv("CYBERREADY_DEBUG_RUN"),
	}
	b, err := json.Marshal(payload)
	if err != nil {
		return
	}
	f, err := os.OpenFile(logPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	_, _ = f.Write(append(b, '\n'))
	_ = f.Close()
	// #endregion
}
