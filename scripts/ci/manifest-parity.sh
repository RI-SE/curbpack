#!/usr/bin/env bash
# CI: manifest / release-gate / install parity
set -euo pipefail
cd "$(cd "$(dirname "$0")/../.." && pwd)"
python3 - <<'PY'
import json, pathlib
root = pathlib.Path(".")
man = json.loads((root/"scripts/install-manifest.json").read_text())
gate = json.loads((root/"scripts/release-gate.json").read_text())
assets = set(man["assets"])
assert "curbpack_windows_amd64.exe" in assets
assert man["default_version"].startswith("v")
assert gate.get("schema") == "curbpack-release-gate:1", gate
assert gate["version"] == man["default_version"]
for k in ("assets_verified", "checksums_verified", "install_smoke_verified", "scan_write_free_verified"):
    assert gate.get(k) is True, k
rel = (root/".github/workflows/release.yml").read_text()
assert "windows/amd64" in rel or "windows_amd64" in rel
sh = (root/"scripts/install.sh").read_text()
assert "cd /path/to/your/git/repo" in sh and "curbpack scan" in sh
assert "curbpack demo" in sh
ps1 = (root/"scripts/install.ps1").read_text()
assert "curbpack_windows_amd64.exe" in ps1
assert "cd /path/to/your/git/repo" in ps1 and "curbpack scan" in ps1
action = (root/"action.yml").read_text()
assert "Linux/macOS" in action and "not Windows runners" in action
PY
