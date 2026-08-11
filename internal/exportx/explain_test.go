package exportx_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/afelin/cyberready/internal/exportx"
	"github.com/afelin/cyberready/internal/ir"
)

func TestWriteExplainPacket_NoAbsHome(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)

	// Inject absolute home paths into a synthetic failure description path via Assemble.
	pkt := exportx.AssembleExplainPacket(ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			Severity:             "high",
			SanitizedDescription: "missing file under /Users/alice/secret/repo/SECURITY.md",
			ASTCoordinates: ir.ASTCoordinates{
				TargetFile: "/Users/alice/secret/repo/SECURITY.md",
			},
			Remediation: ir.Remediation{
				ActionRequired: "create /Users/alice/secret/repo/SECURITY.md",
				ExpectedState:  "file exists at /home/bob/project/SECURITY.md",
			},
		}},
	}, nil, nil, false, "")

	raw, err := json.Marshal(pkt)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(raw); err != nil {
		t.Fatal(err)
	}
	s := string(raw)
	if strings.Contains(s, "/Users/") || strings.Contains(s, "/home/") {
		t.Fatalf("absolute home paths leaked: %s", s)
	}
	home, _ := os.UserHomeDir()
	if home != "" && home != "/" && strings.Contains(s, home) {
		t.Fatalf("$HOME leaked: %s", home)
	}

	// End-to-end write also airlocked.
	path, err := exportx.WriteExplainPacket(dir, []string{"house-policy"}, filepath.Join(dir, "explain.json"))
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(data); err != nil {
		t.Fatal(err)
	}
}

func TestWriteExplainPacket_NoPEM(t *testing.T) {
	pem := "-----BEGIN RSA PRIVATE KEY-----\n" +
		"MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF6PZGFw7N+EXAMPLEKEYMATERIAL12\n" +
		"34567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ012345\n" +
		"-----END RSA PRIVATE KEY-----"
	pkt := exportx.AssembleExplainPacket(ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			Severity:             "high",
			SanitizedDescription: "leak: " + pem,
			Remediation: ir.Remediation{
				ActionRequired: "rotate key that looked like " + pem,
			},
		}},
	}, nil, nil, false, "")

	raw, err := json.Marshal(pkt)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(raw); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(raw), "BEGIN RSA PRIVATE KEY") {
		t.Fatal("PEM blob must be stripped from explain-packet")
	}
	if !strings.Contains(string(raw), "[REDACTED_PEM]") {
		t.Fatal("expected REDACTED_PEM marker")
	}
}

func TestWriteExplainPacket_UntrustedWrapper(t *testing.T) {
	dir := t.TempDir()
	mustRealGit(t, dir)
	writeMinimalHouseFail(t, dir)
	path, err := exportx.WriteExplainPacket(dir, []string{"house-policy"}, filepath.Join(dir, "pkt.json"))
	if err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var pkt exportx.ExplainPacket
	if err := json.Unmarshal(data, &pkt); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(pkt.Untrusted, "<untrusted_metadata>") || !strings.Contains(pkt.Untrusted, "</untrusted_metadata>") {
		t.Fatalf("agent-facing body missing untrusted_metadata wrapper: %q", pkt.Untrusted)
	}
	if !strings.Contains(string(data), "<untrusted_metadata>") {
		t.Fatal("serialized packet missing literal untrusted_metadata tags")
	}
}

func TestAirlock_GHARunnerPath(t *testing.T) {
	repo := "/home/runner/work/cyberready/cyberready"
	pkt := exportx.AssembleExplainPacket(ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			SanitizedDescription: "missing " + repo + "/SECURITY.md",
			ASTCoordinates: ir.ASTCoordinates{
				TargetFile: repo + "/SECURITY.md",
			},
			Remediation: ir.Remediation{
				ActionRequired: "create " + repo + "/SECURITY.md",
			},
		}},
	}, nil, nil, false, repo)

	raw, err := json.Marshal(pkt)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(raw); err != nil {
		t.Fatal(err)
	}
	s := string(raw)
	if strings.Contains(s, "/home/runner") {
		t.Fatalf("GHA runner path leaked: %s", s)
	}
	if !strings.Contains(s, "SECURITY.md") {
		t.Fatalf("expected relative SECURITY.md retained: %s", s)
	}
}

func TestAirlock_RootHomePath(t *testing.T) {
	pkt := exportx.AssembleExplainPacket(ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			SanitizedDescription: "missing /root/project/SECURITY.md",
			ASTCoordinates: ir.ASTCoordinates{
				TargetFile: "/root/project/SECURITY.md",
			},
		}},
	}, nil, nil, false, "/root/project")

	raw, err := json.Marshal(pkt)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(raw); err != nil {
		t.Fatal(err)
	}
	s := string(raw)
	if strings.Contains(s, "/root/") {
		t.Fatalf("/root path leaked: %s", s)
	}
}

func TestAirlock_WSLPath(t *testing.T) {
	pkt := exportx.AssembleExplainPacket(ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			SanitizedDescription: "missing /mnt/c/Users/alice/project/SECURITY.md",
			ASTCoordinates: ir.ASTCoordinates{
				TargetFile: "/mnt/c/Users/alice/project/SECURITY.md",
			},
		}},
	}, nil, nil, false, "")

	raw, err := json.Marshal(pkt)
	if err != nil {
		t.Fatal(err)
	}
	if err := exportx.PacketLooksAirlocked(raw); err != nil {
		t.Fatal(err)
	}
	s := string(raw)
	if strings.Contains(s, "/mnt/c/Users/") || strings.Contains(s, "/Users/alice") {
		t.Fatalf("WSL home path leaked: %s", s)
	}
}

func TestAirlock_HomeIsRootDoesNotWipeSlashes(t *testing.T) {
	pkt := exportx.AssembleExplainPacket(ir.GateFailurePayload{
		PackID: "house-policy",
		Failures: []ir.Failure{{
			GateID:               "HOUSE-SECURITY-MD",
			SanitizedDescription: "corp path /corp/shared/apps/myapp/SECURITY.md still readable",
			ASTCoordinates: ir.ASTCoordinates{
				TargetFile: "/corp/shared/apps/myapp/SECURITY.md",
			},
		}},
	}, nil, nil, false, "/corp/shared/apps/myapp")

	raw, err := json.Marshal(pkt)
	if err != nil {
		t.Fatal(err)
	}
	s := string(raw)
	if strings.Contains(s, "/corp/") {
		t.Fatalf("repo-absolute corp path should be relativized: %s", s)
	}
	if !strings.Contains(s, "SECURITY.md") {
		t.Fatalf("basename/relative should survive: %s", s)
	}
	if strings.Count(s, "~") > 0 && !strings.Contains(s, "/") && !strings.Contains(s, "SECURITY") {
		t.Fatalf("path structure wiped: %s", s)
	}
	if err := exportx.PacketLooksAirlocked(raw); err != nil {
		t.Fatal(err)
	}
}
