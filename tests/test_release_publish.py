"""The release tag and the refusal to publish a CI run that has not passed."""

from __future__ import annotations

import hashlib
import importlib.util
import subprocess
from unittest.mock import patch
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

    def test_linux_release_has_download_run_and_checksum_instructions(self):
        digest = "c" * 64
        notes = module.binary_notes(
            [f"{digest}  curbpack-studio-linux-x64\n{digest}  curbcheck-linux-x64\n"],
            "RI-SE/curbpack",
            "test-linux",
        )
        base = "https://github.com/RI-SE/curbpack/releases/download/test-linux"
        self.assertIn("Linux x64", notes)
        self.assertIn(f"curl -fsSL -O {base}/curbcheck-linux-x64", notes)
        self.assertIn(f"curl -fsSL -O {base}/curbpack-studio-linux-x64", notes)
        self.assertIn("chmod +x curbpack-studio-linux-x64 curbcheck-linux-x64", notes)
        self.assertIn("./curbpack-studio-linux-x64", notes)
        self.assertIn(f"sha256sum -c <<'EOF'\n{digest}  curbpack-studio-linux-x64\n", notes)
        self.assertIn(f"{digest}  curbcheck-linux-x64\nEOF", notes)

    def test_checker_only_release_does_not_require_studio(self):
        for host in ("macos-arm64", "windows-x64.exe", "linux-x64"):
            with self.subTest(host=host):
                name = f"curbcheck-{host}"
                notes = module.binary_notes([f"{'d' * 64}  {name}\n"], "RI-SE/curbpack", "test")
                self.assertIn(f"/{name}", notes)
                self.assertIn(f"{name} --help", notes)
                self.assertNotIn("curbpack-studio", notes)
                self.assertNotIn("local URL", notes)

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


class IndependentReleaseTest(unittest.TestCase):
    def test_publish_uses_the_packages_present_in_the_successful_run(self):
        for filename in ("curbcheck-linux-x64", "curbpack-studio-macos-arm64"):
            with self.subTest(filename=filename):
                record = {
                    "workflowName": "CI", "headSha": "a" * 40,
                    "conclusion": "success", "jobs": [{"name": "tests", "conclusion": "success"}],
                }
                calls = []
                def gh(args, **kwargs):
                    calls.append(args)
                    if args[0] == "api":
                        return subprocess.CompletedProcess(args, 0, stdout=filename + "\nother-artifact\n")
                    if args[:2] == ["run", "download"]:
                        self.assertEqual(args[args.index("-n") + 1], filename)
                        dest = Path(args[args.index("-D") + 1])
                        (dest / filename).write_bytes(b"tested binary")
                        digest = hashlib.sha256(b"tested binary").hexdigest()
                        (dest / "SHA256SUMS").write_text(f"{digest}  {filename}\n")
                    if args[:2] == ["release", "create"]:
                        sums = Path(args[-1])
                        self.assertEqual(sums.name, "SHA256SUMS")
                        self.assertIn(filename, sums.read_text())
                        self.assertEqual(Path(args[-2]).name, filename)
                    return subprocess.CompletedProcess(args, 0, stdout="")

                with patch.object(module, "_run_record", return_value=record), patch.object(
                    module, "_repository", return_value="RI-SE/curbpack"
                ), patch.object(module, "_tag_exists", return_value=False), patch.object(
                    module, "_gh", side_effect=gh
                ):
                    self.assertEqual(module.main(["--run-id", "7", "--tag", "test"]), 0)
                self.assertEqual(sum(args[:2] == ["run", "download"] for args in calls), 1)
                self.assertEqual(sum(args[:2] == ["release", "create"] for args in calls), 1)

    def test_release_includes_the_tested_installers_and_their_checksums(self):
        import runpy
        build = runpy.run_path(str(SCRIPT.parents[1] / 'build' / 'package_installers.py'))['build']
        record = {
            'workflowName': 'CI', 'headSha': 'a' * 40, 'conclusion': 'success',
            'jobs': [{'name': 'tests', 'conclusion': 'success'}],
        }
        uploaded = []

        def gh(args, **kwargs):
            if args[0] == 'api':
                return subprocess.CompletedProcess(args, 0, stdout='curbcheck-linux-x64\ncurbpack-installers\n')
            if args[:2] == ['run', 'download']:
                destination = Path(args[args.index('-D') + 1])
                if args[args.index('-n') + 1] == 'curbpack-installers':
                    build(destination)
                else:
                    name = 'curbcheck-linux-x64'
                    (destination / name).write_bytes(b'tested checker')
                    digest = hashlib.sha256(b'tested checker').hexdigest()
                    (destination / 'SHA256SUMS').write_text(f'{digest}  {name}\n')
            if args[:2] == ['release', 'create']:
                files = {Path(item).name: Path(item) for item in args[args.index('--notes') + 2:]}
                for name in ('install-studio.sh', 'install-studio.ps1', 'install-curbcheck.sh', 'install-curbcheck.ps1'):
                    self.assertIn(name, files)
                for line in files['SHA256SUMS'].read_text().splitlines():
                    digest, name = line.split('  ')
                    self.assertEqual(hashlib.sha256(files[name].read_bytes()).hexdigest(), digest)
                uploaded.append(files.keys())
            return subprocess.CompletedProcess(args, 0, stdout='')

        with patch.object(module, '_run_record', return_value=record), patch.object(
            module, '_repository', return_value='RI-SE/curbpack'
        ), patch.object(module, '_tag_exists', return_value=False), patch.object(module, '_gh', side_effect=gh):
            self.assertEqual(module.main(['--run-id', '7', '--tag', 'test']), 0)
        self.assertEqual(len(uploaded), 1)
