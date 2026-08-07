package sock

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/validate"
)

// Request is the Coreward bridge IPC envelope.
type Request struct {
	Op      string          `json:"op"`
	Payload json.RawMessage `json:"payload,omitempty"`
}

// Response is GateFailure-shaped (or ok) for Coreward's cyberreadyValidateDelta.
type Response struct {
	OK       bool                  `json:"ok"`
	Reason   string                `json:"reason,omitempty"`
	Detail   string                `json:"detail,omitempty"`
	Failures []ir.Failure          `json:"failures,omitempty"`
	Payload  *ir.GateFailurePayload `json:"payload,omitempty"`
}

// Serve listens on a Unix domain socket and handles validate_delta.
// Path defaults to CYBERREADY_SOCK or /tmp/cyberready.sock.
func Serve(sockPath, repoRoot string) error {
	if sockPath == "" {
		sockPath = strings.TrimSpace(os.Getenv("CYBERREADY_SOCK"))
	}
	if sockPath == "" {
		sockPath = "/tmp/cyberready.sock"
	}
	_ = os.Remove(sockPath)
	ln, err := net.Listen("unix", sockPath)
	if err != nil {
		return err
	}
	defer ln.Close()
	fmt.Fprintf(os.Stderr, "cyberready sock listening on %s (op=validate_delta)\n", sockPath)
	for {
		conn, err := ln.Accept()
		if err != nil {
			return err
		}
		go handle(conn, repoRoot)
	}
}

func handle(conn net.Conn, repoRoot string) {
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(30 * time.Second))
	dec := json.NewDecoder(conn)
	enc := json.NewEncoder(conn)

	var req Request
	if err := dec.Decode(&req); err != nil {
		_ = enc.Encode(Response{OK: false, Reason: "unavailable", Detail: "invalid json: " + err.Error()})
		return
	}
	op := strings.TrimSpace(req.Op)
	if op == "" {
		op = "validate_delta"
	}
	if op != "validate_delta" {
		_ = enc.Encode(Response{OK: false, Reason: "unavailable", Detail: "unsupported op: " + op})
		return
	}

	res, err := validate.Run(validate.Options{RepoRoot: repoRoot, Quiet: true})
	if err != nil {
		_ = enc.Encode(Response{OK: false, Reason: "unavailable", Detail: err.Error()})
		return
	}
	p := res.Payload
	_ = enc.Encode(Response{
		OK:       res.Passed,
		Failures: p.Failures,
		Payload:  &p,
		Detail:   fmt.Sprintf("score=%d failures=%d", res.Score, len(p.Failures)),
	})
}
