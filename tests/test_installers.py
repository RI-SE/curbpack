"""SYS-05: Studio installs both programs; checker-only installation stays independent."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        spec = importlib.util.spec_from_file_location('package_installers', ROOT / 'scripts/build/package_installers.py')
        self.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.builder)
        self.builder.build(self.root / 'installers')
        self.release = self.root / 'release'
        self.release.mkdir()
        self.destination = self.root / 'installed programs'
        self.destination.mkdir()
        (self.destination / 'curbpack-studio').write_bytes(b'old studio')
        (self.destination / 'curbcheck').write_bytes(b'old checker')
        lines = []
        for host in ('macos-arm64', 'linux-x64'):
            for name in ('curbpack-studio', 'curbcheck'):
                asset = f'{name}-{host}'
                data = f'new {asset}'.encode()
                (self.release / asset).write_bytes(data)
                lines.append(f'{hashlib.sha256(data).hexdigest()}  {asset}')
        (self.release / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')
        commands = self.root / 'commands'
        commands.mkdir()
        fixtures = {
            'uname': '#!/bin/sh\ncase "$1" in -s) echo "$TEST_OS";; -m) echo "$TEST_ARCH";; esac\n',
            'getconf': '#!/bin/sh\nprintf "%s\\n" "$TEST_LIBC"\n',
            'curl': '#!/bin/sh\nset -eu\nprintf "%s\\n" "$2" >> "$CURL_LOG"\ncase "$2" in */releases/latest) printf "https://github.com/RI-SE/curbpack/releases/tag/test-release";; *) cp "$RELEASE_FIXTURE/${2##*/}" "$4";; esac\n',
        }
        for name, script in fixtures.items():
            path = commands / name
            path.write_bytes(script.encode())
            path.chmod(0o755)
        self.env = dict(os.environ, PATH=str(commands) + os.pathsep + os.environ['PATH'],
                        RELEASE_FIXTURE=self.release.as_posix(), TEST_OS='Linux', TEST_ARCH='x86_64', TEST_LIBC='glibc 2.35',
                        CURBPACK_VERSION='test-release', CURBPACK_INSTALL_DIR=self.destination.as_posix(),
                        CURL_LOG=(self.root / 'downloads.log').as_posix())

    def run_installer(self, product='studio'):
        script = self.root / 'installers' / f'install-{product}.sh'
        return subprocess.run(['sh', script.as_posix()], env=self.env, capture_output=True, text=True)

    def test_studio_installs_both_programs_with_stable_names_on_each_unix_host(self):
        for system, machine, host in [('Linux', 'x86_64', 'linux-x64'), ('Darwin', 'arm64', 'macos-arm64')]:
            with self.subTest(system=system):
                self.env.update(TEST_OS=system, TEST_ARCH=machine)
                result = self.run_installer()
                self.assertEqual(result.returncode, 0, result.stderr)
                for name in ('curbpack-studio', 'curbcheck'):
                    self.assertEqual((self.destination / name).read_bytes(), f'new {name}-{host}'.encode())
                    if os.name != 'nt':
                        self.assertTrue(os.access(self.destination / name, os.X_OK))

    def test_checker_only_installer_preserves_existing_studio(self):
        result = self.run_installer('curbcheck')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / 'curbpack-studio').read_bytes(), b'old studio')
        self.assertEqual((self.destination / 'curbcheck').read_bytes(), b'new curbcheck-linux-x64')

    def test_bad_second_download_preserves_both_existing_programs(self):
        (self.release / 'curbcheck-linux-x64').write_bytes(b'tampered')
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.destination / 'curbpack-studio').read_bytes(), b'old studio')
        self.assertEqual((self.destination / 'curbcheck').read_bytes(), b'old checker')

    def test_missing_asset_preserves_existing_programs(self):
        (self.release / 'curbcheck-linux-x64').unlink()
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual((self.destination / 'curbpack-studio').read_bytes(), b'old studio')

    def test_missing_checksum_preserves_existing_programs(self):
        (self.release / 'SHA256SUMS').write_text('')
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual((self.destination / 'curbcheck').read_bytes(), b'old checker')

    def test_unsupported_architecture_is_rejected(self):
        self.env['TEST_ARCH'] = 'aarch64'
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertEqual((self.destination / 'curbcheck').read_bytes(), b'old checker')

    def test_latest_is_resolved_to_one_specific_tag(self):
        self.env['CURBPACK_VERSION'] = 'latest'
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('test-release', result.stdout)

    def test_installer_package_contains_four_standalone_scripts_and_checksums(self):
        folder = self.root / 'installers'
        names = {'install-studio.sh', 'install-studio.ps1', 'install-curbcheck.sh', 'install-curbcheck.ps1'}
        self.assertEqual({p.name for p in folder.iterdir()}, names | {'SHA256SUMS'})
        for line in (folder / 'SHA256SUMS').read_text().splitlines():
            digest, name = line.split('  ')
            self.assertEqual(hashlib.sha256((folder / name).read_bytes()).hexdigest(), digest)

    def test_pinned_version_is_used_for_every_download(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        urls = (self.root / 'downloads.log').read_text().splitlines()
        self.assertEqual(len(urls), 3)
        self.assertTrue(all('/releases/download/test-release/' in url for url in urls))

    def test_reinstall_updates_selected_programs_and_removes_staging_files(self):
        self.assertEqual(self.run_installer().returncode, 0)
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({p.name for p in self.destination.iterdir()}, {'curbpack-studio', 'curbcheck'})
        self.assertEqual((self.destination / 'curbcheck').read_bytes(), b'new curbcheck-linux-x64')

    def test_existing_command_on_path_needs_no_path_instruction(self):
        self.env['PATH'] = str(self.destination) + os.pathsep + self.env['PATH']
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('Add this directory', result.stdout)

    def test_default_unix_destination_without_writing_to_the_real_home(self):
        self.env.pop('CURBPACK_INSTALL_DIR')
        # Stop before the first installation write; record the real default argument.
        mkdir = self.root / 'commands' / 'mkdir'
        mkdir.write_bytes(b'#!/bin/sh\nprintf "%s\\n" "$2" > "$DESTINATION_LOG"\nexit 1\n')
        mkdir.chmod(0o755)
        self.env['DESTINATION_LOG'] = (self.root / 'destination.log').as_posix()
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        actual = (self.root / 'destination.log').read_text().strip()
        shell_home = subprocess.check_output(['sh', '-c', 'printf "%s" "$HOME"'], env=self.env, text=True)
        self.assertEqual(actual, shell_home + '/.local/bin')

    def test_invalid_tag_is_rejected_before_any_download(self):
        self.env['CURBPACK_VERSION'] = '../invalid'
        self.assertNotEqual(self.run_installer().returncode, 0)
        self.assertFalse((self.root / 'downloads.log').exists())

    def test_directory_in_place_of_a_program_is_not_overwritten(self):
        (self.destination / 'curbcheck').unlink()
        (self.destination / 'curbcheck').mkdir()
        result = self.run_installer()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.destination / 'curbpack-studio').read_bytes(), b'old studio')
        self.assertTrue((self.destination / 'curbcheck').is_dir())

    def test_unsupported_linux_libc_stops_before_downloading_or_replacing_programs(self):
        for libc in ('musl 1.2.5', 'glibc 2.31', ''):
            with self.subTest(libc=libc):
                self.env['TEST_LIBC'] = libc
                result = self.run_installer()
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('glibc 2.35 or newer', result.stderr)
                self.assertFalse((self.root / 'downloads.log').exists())
                self.assertEqual((self.destination / 'curbpack-studio').read_bytes(), b'old studio')
                self.assertEqual((self.destination / 'curbcheck').read_bytes(), b'old checker')
