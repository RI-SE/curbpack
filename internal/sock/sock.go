package sock

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
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
	OK       bool                   `json:"ok"`
	Reason   string                 `json:"reason,omitempty"`
	Detail   string                 `json:"detail,omitempty"`
	Failures []ir.Failure           `json:"failures,omitempty"`
	Payload  *ir.GateFailurePayload `json:"payload,omitempty"`
}

// DefaultPath returns a private socket path.
// Order: CYBERREADY_SOCK → XDG_RUNTIME_DIR/cyberready/cyberready.sock →
// $TMPDIR/cyberready-$UID/cyberready.sock → .cyberready/cyberready.sock under cwd.
// Never defaults to a world-writable shared path like /tmp/cyberready.sock.
func DefaultPath() (string, error) {
	if p := strings.TrimSpace(os.Getenv("CYBERREADY_SOCK")); p != "" {
		return p, nil
	}
	if xdg := strings.TrimSpace(os.Getenv("XDG_RUNTIME_DIR")); xdg != "" {
		dir := filepath.Join(xdg, "cyberready")
		if err := ensurePrivateDir(dir); err != nil {
			return "", err
		}
		return filepath.Join(dir, "cyberready.sock"), nil
	}
	uid := os.Getuid()
	tmpBase := os.TempDir()
	dir := filepath.Join(tmpBase, fmt.Sprintf("cyberready-%d", uid))
	if err := ensurePrivateDir(dir); err != nil {
		// Fall back to repo-local .cyberready/
		cwd, err2 := os.Getwd()
		if err2 != nil {
			return "", fmt.Errorf("sock path: %w (and cwd: %v)", err, err2)
		}
		dir = filepath.Join(cwd, ".cyberready")
		if err := ensurePrivateDir(dir); err != nil {
			return "", err
		}
		return filepath.Join(dir, "cyberready.sock"), nil
	}
	return filepath.Join(dir, "cyberready.sock"), nil
}

func ensurePrivateDir(dir string) error {
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return err
	}
	info, err := os.Stat(dir)
	if err != nil {
		return err
	}
	mode := info.Mode().Perm()
	if mode&0o002 != 0 {
		return fmt.Errorf("refuse world-writable sock dir %s (mode %04o)", dir, mode)
	}
	// Tighten if group/other writable
	if mode&0o077 != 0 {
		if err := os.Chmod(dir, 0o700); err != nil {
			return fmt.Errorf("cannot tighten sock dir %s: %w", dir, err)
		}
	}
	return nil
}

// Serve listens on a Unix domain socket and handles validate_delta.
// Path defaults via DefaultPath(); socket file mode is 0600.
// Refuses parent directories that remain world-writable.
func Serve(sockPath, repoRoot string) error {
	var err error
	if sockPath == "" {
		sockPath, err = DefaultPath()
		if err != nil {
			return err
		}
	}
	parent := filepath.Dir(sockPath)
	if err := ensurePrivateDir(parent); err != nil {
		return err
	}
	_ = os.Remove(sockPath)
	ln, err := net.Listen("unix", sockPath)
	if err != nil {
		return err
	}
	if err := os.Chmod(sockPath, 0o600); err != nil {
		_ = ln.Close()
		return fmt.Errorf("chmod sock 0600: %w", err)
	}
	defer func() {
		_ = ln.Close()
		_ = os.Remove(sockPath)
	}()
	fmt.Fprintf(os.Stderr, "cyberready sock listening on %s mode=0600 (op=validate_delta)\n", sockPath)
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

	_ = enc.Encode(ValidateDelta(repoRoot))
}

// ValidateDelta runs Quiet validate and returns the sock Response shape.
// gate_id set must match check/validate --json (differential contract).
func ValidateDelta(repoRoot string) Response {
	res, err := validate.Run(validate.Options{RepoRoot: repoRoot, Quiet: true})
	if err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: err.Error()}
	}
	p := res.Payload
	return Response{
		OK:       res.Passed,
		Failures: p.Failures,
		Payload:  &p,
		Detail:   fmt.Sprintf("score=%d failures=%d", res.Score, len(p.Failures)),
	}
}
