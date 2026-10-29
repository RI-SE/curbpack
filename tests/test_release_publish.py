"""The release tag and the refusal to publish a CI run that has not passed."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release" / "publish.py"
spec = importlib.util.spec_from_file_location("release_publish", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleasePublishTest(unittest.TestCase):
    def test_blank_tag_uses_the_run_date(self):
        self.assertEqual(
            module.choose_tag("", "2026-10-28T12:09:00Z", lambda _name: False),
            "v2026.10.28",
        )

    def test_blank_tag_steps_past_a_tag_that_exists(self):
        taken = {"v2026.10.28", "v2026.10.28.2"}
        self.assertEqual(
            module.choose_tag("", "2026-10-28T12:09:00Z", taken.__contains__),
            "v2026.10.28.3",
        )

    def test_typed_tag_is_kept(self):
        self.assertEqual(
            module.choose_tag("test-1", "2026-10-28T12:09:00Z", lambda _name: True),
            "test-1",
        )

    def test_typed_tag_rejects_spaces(self):
        with self.assertRaises(ValueError):
            module.choose_tag("test 1", "2026-10-28T12:09:00Z", lambda _name: False)

    def test_binary_notes_check_the_download_and_say_how_to_allow_it(self):
        mac = "a" * 64
        win = "b" * 64
        texts = [
            f"{mac}  curbpack-studio-macos-arm64\n{mac}  curbcheck-macos-arm64\n",
            f"{win}  curbpack-studio-windows-x64.exe\n",
        ]
        notes = module.binary_notes(texts, "RI-SE/curbpack", "2026-10-28a-test-release")
        base = "https://github.com/RI-SE/curbpack/releases/download/2026-10-28a-test-release"
        self.assertNotIn("did not rebuild", notes)
        self.assertNotIn("SHA256SUMS", notes)
        self.assertIn(f"curl -fsSL -O {base}/curbpack-studio-macos-arm64", notes)
        self.assertIn(f"shasum -a 256 -c <<'EOF'\n{mac}  curbpack-studio-macos-arm64\n", notes)
        self.assertIn(
            "Get-FileHash -Algorithm SHA256 -LiteralPath $name).Hash.ToLowerInvariant()",
            notes,
        )
        self.assertIn(f"'{win}  curbpack-studio-windows-x64.exe'", notes)
        self.assertIn("To download and run:", notes)
        self.assertIn("To check the hash:", notes)
        self.assertNotIn("To compare the hash:", notes)

    def test_binary_notes_match_the_release_page(self):
        notes = module.binary_notes(
            [
                "12ef3b913034a0006af99430c50537cec2ef5ec5060c90d4dd7ef4ed08ab94e2  curbpack-studio-macos-arm64\n"
                "bccbbdabb2901a1e4cc62f3932a51bf8c982da6ddbff2e6bb9a4d9c7c7bbbae3  curbcheck-macos-arm64\n",
                "27ff88e7e6e8bd52f83df4eb240cb0da8ad626dd67cd3c9a4654f99f80626142  curbpack-studio-windows-x64.exe\n"
                "a4b5f2159620db31a0fd44123eee96ea7184486fdb4b5330c561c0e08aa39bab  curbcheck-windows-x64.exe\n",
            ],
            "RI-SE/curbpack",
            "2026-10-28a-test-release",
        )
        self.assertEqual(
            notes,
            """\
macOS

To download and run:

```sh
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/2026-10-28a-test-release/curbpack-studio-macos-arm64
curl -fsSL -O https://github.com/RI-SE/curbpack/releases/download/2026-10-28a-test-release/curbcheck-macos-arm64
chmod +x curbpack-studio-macos-arm64 curbcheck-macos-arm64
./curbpack-studio-macos-arm64
```

To check the hash:

```sh
shasum -a 256 -c <<'EOF'
12ef3b913034a0006af99430c50537cec2ef5ec5060c90d4dd7ef4ed08ab94e2  curbpack-studio-macos-arm64
bccbbdabb2901a1e4cc62f3932a51bf8c982da6ddbff2e6bb9a4d9c7c7bbbae3  curbcheck-macos-arm64
EOF
```

Windows

To download and run:

```powershell
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/2026-10-28a-test-release/curbpack-studio-windows-x64.exe
curl.exe -fsSL -O https://github.com/RI-SE/curbpack/releases/download/2026-10-28a-test-release/curbcheck-windows-x64.exe
.\\curbpack-studio-windows-x64.exe
```

To check the hash:

```powershell
@(
  '27ff88e7e6e8bd52f83df4eb240cb0da8ad626dd67cd3c9a4654f99f80626142  curbpack-studio-windows-x64.exe',
  'a4b5f2159620db31a0fd44123eee96ea7184486fdb4b5330c561c0e08aa39bab  curbcheck-windows-x64.exe'
) | ForEach-Object {
  $digest, $name = $_ -split '  ', 2
  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $name).Hash.ToLowerInvariant()
  if ($actual -eq $digest) { "${name}: OK" } else { "${name}: FAILED" }
}
```

The process prints a local URL. Open it. The usual one is http://127.0.0.1:8770.
""",
        )

    def test_binary_notes_refuse_a_sums_line_that_is_not_a_command(self):
        with self.assertRaises(ValueError):
            module.binary_notes(["not-a-sum\n"], "RI-SE/curbpack", "v1")

    def test_a_green_run_is_publishable(self):
        self.assertIsNone(module.latest_run_refusal({"conclusion": "success", "databaseId": 7}))

    def test_a_run_that_has_not_passed_is_refused(self):
        message = module.latest_run_refusal(
            {
                "databaseId": 7,
                "status": "in_progress",
                "conclusion": None,
                "url": "https://example.test/run/7",
            }
        )
        self.assertIn("7", message)
        self.assertIn("in_progress", message)
        self.assertIn("https://example.test/run/7", message)
