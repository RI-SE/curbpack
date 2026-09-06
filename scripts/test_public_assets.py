#!/usr/bin/env python3
"""Behavioral mutations of the public-assets command, without Git or network."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
SURFACES = ('docs/launch-status.md', 'docs/getting-started/pre-stranger-handoff.md')


class PublicAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('scripts/check-public-assets.py', 'scripts/install-manifest.json',
                     'internal/buildinfo/version.go', 'site/assets/og-campaign.svg',
                     'site/assets/og-campaign.png'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.record = {
            'schema': 'curbpack-release-gate:1', 'version': 'v0.5.5',
            'published_at': '2026-09-05T21:01:18Z',
            'release_url': 'https://github.com/RI-SE/curbpack/releases/tag/v0.5.5',
            'advertised_at': '2026-09-05T21:47:35Z',
            'advertise_pr': 'https://github.com/RI-SE/curbpack/pull/51',
            'advertise_commit': '17a18ed5395d635758424873113c7ef106409e17',
        }
        self.write('README.md', '')
        self.write('site/index.html', '<!doctype html><title>Fixture</title>')
        self.save_record()

    def write(self, name, text):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def save_record(self):
        self.write('scripts/release-gate.json', json.dumps(self.record))
        r = self.record
        statement = (f"CLI release **{r['version']}** published **{r['published_at'][:10]}** "
                     f"([release]({r['release_url']})); advertised on `main` "
                     f"**{r['advertised_at'][:10]}** ([advertise PR]({r['advertise_pr']})).")
        for name in SURFACES:
            self.write(name, '<!-- curbpack-release:start -->\n' + statement
                       + '\n<!-- curbpack-release:end -->\n')

    def check(self, success):
        result = subprocess.run([sys.executable, 'scripts/check-public-assets.py'],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if success else 1,
                         result.stdout + result.stderr)

    def test_complete_record_works_without_git_tags(self):
        self.check(True)

    def test_later_advertisement_is_valid(self):
        self.record['advertised_at'] = '2026-09-06T08:00:00Z'
        self.save_record()
        self.check(True)

    def test_required_release_evidence_cannot_be_missing(self):
        for key in ('published_at', 'advertised_at', 'release_url', 'advertise_pr', 'advertise_commit'):
            with self.subTest(key=key):
                bad = dict(self.record)
                del bad[key]
                self.write('scripts/release-gate.json', json.dumps(bad))
                self.check(False)

    def test_invalid_evidence_is_refused(self):
        for key, value in (('published_at', '2026-02-30T00:00:00Z'),
                           ('advertised_at', '2020-01-01T00:00:00Z'),
                           ('release_url', 'https://example.invalid/release'),
                           ('advertise_commit', 'short'), ('version', 'v0.5.4')):
            with self.subTest(key=key):
                bad = dict(self.record, **{key: value})
                self.write('scripts/release-gate.json', json.dumps(bad))
                self.check(False)

    def test_wrong_public_date_is_refused(self):
        target = self.root / SURFACES[0]
        target.write_text(target.read_text().replace('2026-09-05', '2020-01-01', 1))
        self.check(False)

    def test_missing_public_release_block_is_refused(self):
        self.write(SURFACES[0], 'No current release evidence.')
        self.check(False)

    def test_historical_operational_date_is_not_rewritten_as_release_date(self):
        with (self.root / SURFACES[1]).open('a') as f:
            f.write('\nHistorical: API DELETE 2026-08-25.\n')
        self.check(True)

    def test_external_executable_and_style_forms_are_refused(self):
        cases = [
            '<script src="https://example.invalid/x.js"></script>',
            '<script src="//example.invalid/x.js"></script>',
            '<script\n src="https://example.invalid/x.js"></script>',
            '<script src=https://example.invalid/x.js></script>',
            '<script src="&#47;&#47;example.invalid/x.js"></script>',
            '<script src="\\\\example.invalid/x.js"></script>',
            '<script src="data:text/javascript,alert(1)"></script>',
            '<script type="module">import "https://example.invalid/x.js";</script>',
            '<script>import("//example.invalid/x.js")</script>',
            '<script>import(\n"https://example.invalid/x.js")</script>',
            '<link rel=stylesheet href=https://example.invalid/x.css>',
            '<link rel=stylesheet href="//fonts.googleapis.com/css2">',
            '<link rel=stylesheet href="https://fonts.googleapis.com.evil.invalid/x.css">',
            '<link rel=stylesheet href="https://fonts.googleapis.com@evil.invalid/x.css">',
            '<link rel=modulepreload href="//example.invalid/x.js">',
            '<link rel=preload as=script href="//example.invalid/x.js">',
            '<style>@import "https://example.invalid/x.css";</style>',
        ]
        for html in cases:
            with self.subTest(html=html):
                self.write('site/index.html', html)
                self.check(False)

    def test_served_samples_are_included(self):
        self.write('site/samples/demo.html', '<script src="//example.invalid/x.js"></script>')
        self.check(False)

    def test_local_module_source_is_checked(self):
        self.write('site/assets/demo.js', 'export {x} from "https://example.invalid/x.js";')
        self.check(False)

    def test_local_script_with_non_js_extension_is_checked(self):
        self.write('site/index.html', '<script src="/curbpack/assets/demo.txt"></script>')
        self.write('site/assets/demo.txt', 'import("https://example.invalid/x.js");')
        self.check(False)

    def test_local_css_imports_and_urls_are_checked(self):
        for css in ('@import "https://example.invalid/x.css";',
                    '@import url(//example.invalid/x.css);',
                    '@font-face {src:url(https://example.invalid/x.woff2)}',
                    r'@\69mport "https://example.invalid/x.css";'):
            with self.subTest(css=css):
                self.write('site/assets/demo.css', css)
                self.check(False)

    def test_allowed_font_hosts_and_local_classic_scripts(self):
        self.write('site/index.html', '''<link rel=stylesheet href="https://fonts.googleapis.com/css2?family=Fraunces">
            <link rel=preconnect href="https://fonts.gstatic.com" crossorigin>
            <script src="/curbpack/assets/demo.js"></script>''')
        self.write('site/assets/demo.js', 'document.title = "local";')
        self.write('site/assets/demo.css', '@font-face {src:url(https://fonts.gstatic.com/demo.woff2)}')
        self.check(True)


if __name__ == '__main__':
    unittest.main()
