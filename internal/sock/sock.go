package sock

import (
	"encoding/json"
	"fmt"
	"net"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/afelin/cyberready/internal/exportx"
	"github.com/afelin/cyberready/internal/ir"
	"github.com/afelin/cyberready/internal/packs"
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
	Graph    *GraphSummary          `json:"graph,omitempty"`
	Packet   json.RawMessage        `json:"explain_packet,omitempty"`
}

// GraphSummary is paths-only RKG summary for agents.
type GraphSummary struct {
	SchemaVersion string   `json:"schema_version"`
	Path          string   `json:"path,omitempty"`
	NodeCount     int      `json:"node_count"`
	EdgeCount     int      `json:"edge_count"`
	NodeTypes     []string `json:"node_types,omitempty"`
	Note          string   `json:"note"`
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

// Serve listens on a Unix domain socket and handles validate_delta / get_latest_failure / graph_summary / explain_packet.
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
	fmt.Fprintf(os.Stderr, "cyberready sock listening on %s mode=0600 (ops=validate_delta,get_latest_failure,graph_summary,explain_packet)\n", sockPath)
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
	switch op {
	case "validate_delta":
		_ = enc.Encode(ValidateDelta(repoRoot))
	case "get_latest_failure":
		_ = enc.Encode(GetLatestFailure(repoRoot))
	case "graph_summary":
		_ = enc.Encode(GraphSummaryOp(repoRoot))
	case "explain_packet":
		_ = enc.Encode(ExplainPacketOp(repoRoot))
	default:
		_ = enc.Encode(Response{OK: false, Reason: "unavailable", Detail: "unsupported op: " + op})
	}
}

// ValidateDelta runs Quiet validate and returns the sock Response shape.
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

// GetLatestFailure reads cache/latest_failure.json without re-running gates.
func GetLatestFailure(repoRoot string) Response {
	path := filepath.Join(repoRoot, ".github", "cyberready", "cache", "latest_failure.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: "no latest_failure.json — run check first"}
	}
	var p ir.GateFailurePayload
	if err := json.Unmarshal(data, &p); err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: "invalid latest_failure.json"}
	}
	return Response{
		OK:       len(p.Failures) == 0,
		Failures: p.Failures,
		Payload:  &p,
		Detail:   path,
	}
}

// GraphSummaryOp returns paths-only graph stats (builds graph if missing).
func GraphSummaryOp(repoRoot string) Response {
	path := filepath.Join(repoRoot, ".github", "cyberready", "graph", "policy-graph.json")
	if _, err := os.Stat(path); err != nil {
		if _, err := packs.ExportPolicyGraph(repoRoot, nil, path); err != nil {
			return Response{OK: false, Reason: "unavailable", Detail: err.Error()}
		}
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: err.Error()}
	}
	var g packs.PolicyGraph
	if err := json.Unmarshal(data, &g); err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: "invalid policy-graph.json"}
	}
	types := map[string]struct{}{}
	for _, n := range g.Nodes {
		types[n.Type] = struct{}{}
	}
	typeList := make([]string, 0, len(types))
	for t := range types {
		typeList = append(typeList, t)
	}
	sum := GraphSummary{
		SchemaVersion: g.SchemaVersion,
		Path:          filepath.ToSlash(filepath.Join(".github", "cyberready", "graph", "policy-graph.json")),
		NodeCount:     len(g.Nodes),
		EdgeCount:     len(g.Edges),
		NodeTypes:     typeList,
		Note:          "Paths only — no raw source. Local RKG for agents.",
	}
	return Response{OK: true, Graph: &sum, Detail: sum.Path}
}

// ExplainPacketOp writes/returns a sanitized explain-packet.
func ExplainPacketOp(repoRoot string) Response {
	path, err := exportx.WriteExplainPacket(repoRoot, nil, "")
	if err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: err.Error()}
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: err.Error()}
	}
	if err := exportx.PacketLooksAirlocked(data); err != nil {
		return Response{OK: false, Reason: "unavailable", Detail: err.Error()}
	}
	return Response{OK: true, Packet: data, Detail: filepath.ToSlash(filepath.Join(".github", "cyberready", "cache", "explain-packet.json"))}
}
