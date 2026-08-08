package skilldata

import (
	_ "embed"
	"os"
	"path/filepath"
)

//go:embed SKILL.md
var skillMD []byte

// Install copies the embedded Cursor skill into .cursor/skills/cyberready/SKILL.md.
func Install(repoRoot string) (string, error) {
	dest := filepath.Join(repoRoot, ".cursor", "skills", "cyberready", "SKILL.md")
	if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
		return "", err
	}
	if err := os.WriteFile(dest, skillMD, 0o644); err != nil {
		return "", err
	}
	return dest, nil
}

// WriteIDETasks writes .vscode/tasks.json for F1 → CyberReady: Check.
// If the file already exists, returns dest without overwriting (ok, nil).
func WriteIDETasks(repoRoot string) (string, error) {
	dest := filepath.Join(repoRoot, ".vscode", "tasks.json")
	if err := os.MkdirAll(filepath.Dir(dest), 0o755); err != nil {
		return "", err
	}
	if _, err := os.Stat(dest); err == nil {
		return dest, nil
	}
	const body = `{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "CyberReady: Check",
      "type": "shell",
      "command": "cyberready check",
      "problemMatcher": [
        {
          "owner": "cyberready",
          "fileLocation": ["relative", "${workspaceFolder}"],
          "pattern": {
            "regexp": "^(HOUSE|CRA|MD|CR)-[A-Z0-9-]+:\\s*(.+)$",
            "file": 1,
            "message": 2
          }
        }
      ],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      },
      "group": {
        "kind": "test",
        "isDefault": false
      }
    },
    {
      "label": "CyberReady: Export SARIF",
      "type": "shell",
      "command": "cyberready export --sarif",
      "problemMatcher": {
        "owner": "cyberready-sarif",
        "fileLocation": ["relative", "${workspaceFolder}"],
        "pattern": {
          "regexp": "\"ruleId\"\\s*:\\s*\"([^\"]+)\".*\"text\"\\s*:\\s*\"([^\"]*)\"",
          "file": 1,
          "message": 2
        }
      },
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "CyberReady: Doctor",
      "type": "shell",
      "command": "cyberready doctor",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    },
    {
      "label": "CyberReady: Demo (sandbox)",
      "type": "shell",
      "command": "cyberready demo --keep",
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "shared"
      }
    }
  ]
}
`
	if err := os.WriteFile(dest, []byte(body), 0o644); err != nil {
		return "", err
	}
	return dest, nil
}
