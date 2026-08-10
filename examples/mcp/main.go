// Command cyberready-mcp is a thin MCP stdio server that shells out to PATH `cyberready`.
// Optional CYBERREADY_SOCK enables sock-backed tools; no new sock ops.
// Claim-safe: tools never certify conformity.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

const serverName = "cyberready-mcp"
const serverVersion = "0.1.0"

type rpcReq struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id,omitempty"`
	Method  string          `json:"method"`
	Params  json.RawMessage `json:"params,omitempty"`
}

type rpcResp struct {
	JSONRPC string          `json:"jsonrpc"`
	ID      json.RawMessage `json:"id,omitempty"`
	Result  any             `json:"result,omitempty"`
	Error   *rpcErr         `json:"error,omitempty"`
}

type rpcErr struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
}

type toolCallParams struct {
	Name      string         `json:"name"`
	Arguments map[string]any `json:"arguments"`
}

func main() {
	if err := serve(os.Stdin, os.Stdout); err != nil {
		fmt.Fprintf(os.Stderr, "%s: %v\n", serverName, err)
		os.Exit(1)
	}
}

func serve(in io.Reader, out io.Writer) error {
	br := bufio.NewReader(in)
	enc := json.NewEncoder(out)
	for {
		line, err := br.ReadBytes('\n')
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return err
		}
		line = bytes.TrimSpace(line)
		if len(line) == 0 {
			continue
		}
		var req rpcReq
		if err := json.Unmarshal(line, &req); err != nil {
			_ = enc.Encode(rpcResp{JSONRPC: "2.0", Error: &rpcErr{Code: -32700, Message: "parse error"}})
			continue
		}
		resp := handle(req)
		if resp == nil {
			continue // notification
		}
		if err := enc.Encode(resp); err != nil {
			return err
		}
	}
}

func handle(req rpcReq) *rpcResp {
	switch req.Method {
	case "initialize":
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"protocolVersion": "2024-11-05",
			"capabilities":    map[string]any{"tools": map[string]any{}},
			"serverInfo":      map[string]any{"name": serverName, "version": serverVersion},
			"instructions":    "CyberReady MCP wraps the local cyberready CLI. Exit codes and IR are authoritative. Never claim certification or conformity assessment.",
		}}
	case "notifications/initialized", "initialized":
		return nil
	case "tools/list":
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{"tools": toolDefs()}}
	case "tools/call":
		var p toolCallParams
		_ = json.Unmarshal(req.Params, &p)
		text, isErr := callTool(p.Name, p.Arguments)
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{
			"content": []map[string]any{{"type": "text", "text": text}},
			"isError": isErr,
		}}
	case "ping":
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Result: map[string]any{}}
	default:
		if len(req.ID) == 0 || string(req.ID) == "null" {
			return nil
		}
		return &rpcResp{JSONRPC: "2.0", ID: req.ID, Error: &rpcErr{Code: -32601, Message: "method not found: " + req.Method}}
	}
}

func toolDefs() []map[string]any {
	claim := "Structural evidence only — not a conformity assessment or certification."
	return []map[string]any{
		tool("cyberready_check", "Run cyberready check (exit code authoritative). "+claim, map[string]any{
			"type": "object",
			"properties": map[string]any{
				"packs": map[string]any{"type": "string", "description": "Optional comma-separated pack ids"},
				"heal":  map[string]any{"type": "boolean", "description": "If true, pass --heal (missing stubs only; never attest)"},
			},
		}),
		tool("cyberready_context_pack", "Run cyberready export --context-pack and return the washed ContextPack path/summary. "+claim, map[string]any{
			"type":       "object",
			"properties": map[string]any{"packs": map[string]any{"type": "string"}},
		}),
		tool("cyberready_ask_propose", "Run cyberready ask … --propose on latest_failure.json (propose-only). "+claim, map[string]any{
			"type":       "object",
			"properties": map[string]any{"path": map[string]any{"type": "string", "description": "Optional GateFailure JSON path"}},
		}),
		tool("cyberready_explain_packet", "Export explain-packet (CLI) or sock explain_packet when CYBERREADY_SOCK is set. "+claim, map[string]any{
			"type":       "object",
			"properties": map[string]any{"packs": map[string]any{"type": "string"}},
		}),
		tool("cyberready_validate_delta", "Sock validate_delta when CYBERREADY_SOCK is set; else cyberready validate --json. "+claim, map[string]any{
			"type":       "object",
			"properties": map[string]any{"packs": map[string]any{"type": "string"}},
		}),
	}
}

func tool(name, desc string, schema map[string]any) map[string]any {
	return map[string]any{
		"name":        name,
		"description": desc,
		"inputSchema": schema,
	}
}

func callTool(name string, args map[string]any) (string, bool) {
	bin, err := lookCyberready()
	if err != nil {
		return "cyberready not found on PATH — install from https://github.com/afelin/cyberready (fail-open; not blocking promote). " + err.Error(), true
	}
	root, _ := os.Getwd()
	packs := strArg(args, "packs")
	switch name {
	case "cyberready_check":
		argv := []string{"check"}
		if packs != "" {
			argv = append(argv, "--packs", packs)
		}
		if boolArg(args, "heal") {
			argv = append(argv, "--heal")
		}
		return runCLI(bin, argv)
	case "cyberready_context_pack":
		argv := []string{"export", "--context-pack"}
		if packs != "" {
			argv = append(argv, "--packs", packs)
		}
		out, isErr := runCLI(bin, argv)
		path := filepath.Join(root, ".github", "cyberready", "cache", "context-pack.json")
		if b, rerr := os.ReadFile(path); rerr == nil {
			return out + "\n\n" + string(b), isErr
		}
		return out, isErr
	case "cyberready_ask_propose":
		path := strArg(args, "path")
		if path == "" {
			path = filepath.Join(root, ".github", "cyberready", "cache", "latest_failure.json")
		}
		return runCLI(bin, []string{"ask", path, "--propose"})
	case "cyberready_explain_packet":
		if sock := strings.TrimSpace(os.Getenv("CYBERREADY_SOCK")); sock != "" {
			if body, serr := sockOp(sock, "explain_packet", nil); serr == nil {
				return body, false
			}
		}
		argv := []string{"export", "--explain-packet"}
		if packs != "" {
			argv = append(argv, "--packs", packs)
		}
		return runCLI(bin, argv)
	case "cyberready_validate_delta":
		if sock := strings.TrimSpace(os.Getenv("CYBERREADY_SOCK")); sock != "" {
			if body, serr := sockOp(sock, "validate_delta", nil); serr == nil {
				return body, false
			}
		}
		argv := []string{"validate", "--json"}
		if packs != "" {
			argv = append(argv, "--packs", packs)
		}
		return runCLI(bin, argv)
	default:
		return "unknown tool: " + name, true
	}
}

func lookCyberready() (string, error) {
	if p := strings.TrimSpace(os.Getenv("CYBERREADY_BIN")); p != "" {
		return p, nil
	}
	return exec.LookPath("cyberready")
}

func runCLI(bin string, argv []string) (string, bool) {
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Minute)
	defer cancel()
	cmd := exec.CommandContext(ctx, bin, argv...)
	var buf bytes.Buffer
	cmd.Stdout = &buf
	cmd.Stderr = &buf
	err := cmd.Run()
	out := buf.String()
	if len(out) > 64*1024 {
		out = out[:64*1024] + "\n…(truncated)"
	}
	disclaimer := "\n\n[cyberready-mcp] Structural evidence for human review — not a conformity assessment. Exit code authoritative; never invent certification."
	if err != nil {
		return out + "\n" + err.Error() + disclaimer, true
	}
	return out + disclaimer, false
}

func sockOp(sockPath, op string, payload any) (string, error) {
	conn, err := net.DialTimeout("unix", sockPath, 2*time.Second)
	if err != nil {
		return "", err
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(60 * time.Second))
	req := map[string]any{"op": op}
	if payload != nil {
		req["payload"] = payload
	}
	b, _ := json.Marshal(req)
	if _, err := conn.Write(append(b, '\n')); err != nil {
		return "", err
	}
	resp, err := bufio.NewReader(conn).ReadBytes('\n')
	if err != nil && err != io.EOF {
		return "", err
	}
	return string(bytes.TrimSpace(resp)), nil
}

func strArg(args map[string]any, k string) string {
	if args == nil {
		return ""
	}
	v, ok := args[k]
	if !ok || v == nil {
		return ""
	}
	switch t := v.(type) {
	case string:
		return t
	default:
		return fmt.Sprint(t)
	}
}

func boolArg(args map[string]any, k string) bool {
	if args == nil {
		return false
	}
	v, ok := args[k]
	if !ok || v == nil {
		return false
	}
	switch t := v.(type) {
	case bool:
		return t
	case string:
		return t == "1" || strings.EqualFold(t, "true")
	default:
		return false
	}
}
