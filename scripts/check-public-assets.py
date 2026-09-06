#!/usr/bin/env python3
"""Check public links, assets and explicit current-release statements.

INV-12 checks recorded release/advertisement events, not dates inferred from prose
or local tags. --verify-release independently compares that record with GitHub.
INV-13 checks declared HTML/CSS resources and module-loading syntax. It is a
static regression guard, not a proof that arbitrary JavaScript cannot network.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import struct
import sys
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []
FONT_STYLE_ALLOWLIST = {
    'fonts.googleapis.com': 'Google Fonts stylesheet delivery',
    'fonts.gstatic.com': 'Google Fonts font files',
}
RELEASE_SURFACES = ('docs/launch-status.md', 'docs/getting-started/pre-stranger-handoff.md')
RELEASE_START = '<!-- curbpack-release:start -->'
RELEASE_END = '<!-- curbpack-release:end -->'
# No module loader is needed by the static site. Refuse module syntax rather
# than trying to allowlist URLs in an incomplete JavaScript parser.
MODULE_RE = re.compile(r'\bimport\s*(?:\(|[\w*{\'"])|\bexport\s+[^;]*?\bfrom\s*[\'"]', re.S)
CSS_URL_RE = re.compile(r'''url\(\s*['"]?([^'"\s)]+)|@import\s+['"]([^'"]+)''', re.I)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in {'href', 'src'} and value)


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def load_release_record() -> dict:
    manifest = json.loads(read_text(ROOT / 'scripts/install-manifest.json'))
    gate = json.loads(read_text(ROOT / 'scripts/release-gate.json'))
    build = re.search(r'Version\s*=\s*"([^"]+)"', read_text(ROOT / 'internal/buildinfo/version.go'))
    version = gate.get('version', '')
    if (gate.get('schema') != 'curbpack-release-gate:1' or
            not re.fullmatch(r'v\d+\.\d+\.\d+', version) or
            manifest.get('default_version') != version or not build or
            build.group(1).lstrip('v') != version.lstrip('v')):
        raise ValueError('release-gate, manifest and buildinfo versions must agree')
    dates = []
    for key in ('published_at', 'advertised_at'):
        value = gate.get(key, '')
        if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
            raise ValueError(f'release-gate missing/invalid {key}')
        dates.append(datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ'))
    if dates[1] < dates[0]:
        raise ValueError('advertisement precedes publication')
    if gate.get('release_url') != f'https://github.com/RI-SE/curbpack/releases/tag/{version}':
        raise ValueError('release-gate missing/invalid release_url')
    if not re.fullmatch(r'https://github.com/RI-SE/curbpack/pull/[1-9]\d*', gate.get('advertise_pr', '')):
        raise ValueError('release-gate missing/invalid advertise_pr')
    if not re.fullmatch(r'[0-9a-f]{40}', gate.get('advertise_commit', '')):
        raise ValueError('release-gate missing/invalid advertise_commit')
    return gate


def release_statement(gate: dict) -> str:
    return (f"CLI release **{gate['version']}** published **{gate['published_at'][:10]}** "
            f"([release]({gate['release_url']})); advertised on `main` "
            f"**{gate['advertised_at'][:10]}** ([advertise PR]({gate['advertise_pr']})).")


def github_json(path: str) -> dict:
    # Paths are built here from validated version/PR values, never record URLs.
    request = Request('https://api.github.com/repos/RI-SE/curbpack/' + path,
                      headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'curbpack-public-assets'})
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if token:
        request.add_header('Authorization', 'Bearer ' + token)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def verify_release_record(gate: dict) -> None:
    release = github_json('releases/tags/' + gate['version'])
    pr = github_json('pulls/' + gate['advertise_pr'].rsplit('/', 1)[1])
    if (release.get('tag_name') != gate['version'] or release.get('draft') is not False or
            release.get('published_at') != gate['published_at'] or
            release.get('html_url') != gate['release_url']):
        raise ValueError('release-gate differs from GitHub release publication evidence')
    if (pr.get('merged') is not True or pr.get('merged_at') != gate['advertised_at'] or
            pr.get('merge_commit_sha') != gate['advertise_commit'] or
            pr.get('base', {}).get('ref') != 'main'):
        raise ValueError('release-gate differs from merged advertisement PR evidence')


def check_freshness(verify_remote: bool = False) -> None:
    try:
        gate = load_release_record()
        expected = release_statement(gate)
        for name in RELEASE_SURFACES:
            text = read_text(ROOT / name)
            if text.count(RELEASE_START) != 1 or text.count(RELEASE_END) != 1:
                raise ValueError(f'{name}: require exactly one current release block')
            actual = text.split(RELEASE_START, 1)[1].split(RELEASE_END, 1)[0].strip()
            if actual != expected:
                errors.append(f'{name}: current release statement differs from release-gate evidence')
        if verify_remote:
            verify_release_record(gate)
    except (OSError, ValueError, TypeError, KeyError) as error:
        errors.append(f'freshness: {error}')


def resource(path: Path, raw: str, kind: str) -> Path | None:
    # HTMLParser already decodes attribute entities. Normalize protocol-relative,
    # backslash and encoded forms conservatively before checking their origin.
    normalized = unquote(raw).strip().replace('\\', '/')
    normalized = ''.join(c for c in normalized if c not in '\r\n\t')
    url = urlparse(normalized)
    if url.scheme or url.netloc:
        hosts = {'stylesheet': {'fonts.googleapis.com'}, 'font': {'fonts.gstatic.com'},
                 'preconnect': set(FONT_STYLE_ALLOWLIST)}.get(kind, set())
        if (url.scheme == 'https' and url.hostname in hosts and not url.username and
                not url.password and url.port in (None, 443)):
            return None
        errors.append(f'{path.relative_to(ROOT)}: external {kind} resource refused: {raw}')
        return None
    if not url.path:
        errors.append(f'{path.relative_to(ROOT)}: empty {kind} resource')
        return None
    if url.path.startswith('/curbpack/'):
        target = ROOT / 'site' / url.path[len('/curbpack/'):]
    elif url.path.startswith('/'):
        errors.append(f'{path.relative_to(ROOT)}: {kind} must use /curbpack/ site root: {raw}')
        return None
    else:
        target = path.parent / url.path
    if not target.resolve().is_relative_to((ROOT / 'site').resolve()) or not target.is_file():
        errors.append(f'{path.relative_to(ROOT)}: missing/escaping local {kind} resource: {raw}')
        return None
    return target


def check_javascript(path: Path, text: str) -> None:
    if MODULE_RE.search(text):
        errors.append(f'{path.relative_to(ROOT)}: module loading is not allowed on the static site')


def check_css(path: Path, text: str) -> None:
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    # Decode CSS escapes before recognizing @import or url().
    def escape(match):
        value = match.group(1)
        stripped = value.strip()
        if re.fullmatch(r'[0-9a-fA-F]{1,6}', stripped):
            code = int(stripped, 16)
            return chr(code) if 0 < code <= 0x10ffff else '\ufffd'
        return value
    text = re.sub(r'\\([0-9a-fA-F]{1,6}\s?|.)', escape, text)
    for match in CSS_URL_RE.finditer(text):
        raw = match.group(1) or match.group(2)
        kind = 'stylesheet' if match.group(2) or re.search(r'@import\s*$', text[:match.start()], re.I) else 'font'
        resource(path, raw, kind)


class Resources(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.body = None
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if len({key for key, _ in attrs}) != len(attrs):
            errors.append(f'{self.path.relative_to(ROOT)}: duplicate HTML attributes refused')
        values = dict(attrs)
        if tag == 'script':
            kind = (values.get('type') or '').strip().lower()
            if kind in {'module', 'importmap'}:
                errors.append(f'{self.path.relative_to(ROOT)}: module/import map script refused')
            if 'src' in values:
                target = resource(self.path, values['src'] or '', 'script')
                if target:
                    check_javascript(target, read_text(target))
            self.body, self.chunks = 'script', []
        elif tag == 'style':
            self.body, self.chunks = 'style', []
        elif tag == 'link':
            rel = set((values.get('rel') or '').lower().split())
            kind = None
            if 'stylesheet' in rel:
                kind = 'stylesheet'
            elif 'modulepreload' in rel:
                errors.append(f'{self.path.relative_to(ROOT)}: module preload refused')
            elif rel & {'preload', 'prefetch'}:
                kind = (values.get('as') or '').lower()
                kind = 'stylesheet' if kind == 'style' else kind
            elif rel & {'preconnect', 'dns-prefetch'}:
                kind = 'preconnect'
            if kind is not None:
                resource(self.path, values.get('href') or '', kind)
        if values.get('style'):
            check_css(self.path, values['style'])
        for key, value in attrs:
            if key.startswith('on') and value:
                check_javascript(self.path, value)

    def handle_data(self, data):
        if self.body:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag != self.body:
            return
        text = ''.join(self.chunks)
        if tag == 'script':
            check_javascript(self.path, text)
        else:
            check_css(self.path, text)
        self.body, self.chunks = None, []


def check_resources() -> None:
    # Samples are served pages and receive exactly the same resource checks.
    for path in sorted((ROOT / 'site').rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.html', '.css', '.js', '.mjs'}:
            continue
        try:
            text = read_text(path)
            if path.suffix.lower() == '.html':
                parser = Resources(path)
                parser.feed(text)
                parser.close()
                if parser.body:
                    parser.handle_endtag(parser.body)
            elif path.suffix.lower() == '.css':
                check_css(path, text)
            else:
                check_javascript(path, text)
        except (OSError, ValueError) as error:
            errors.append(f'{path.relative_to(ROOT)}: {error}')


def check_links_and_card() -> None:
    for path in [ROOT / "README.md", *(ROOT / "docs").rglob("*.md"), *(ROOT / "site").rglob("*.html")]:
        rel = path.relative_to(ROOT)
        if rel.parts[:2] in {("docs", "internal"), ("docs", "gtm-oss")}:
            continue  # Historical/operator documents have a separate scope.
        try:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".md":
                urls = re.findall(r"\]\(([^ )]+)(?:\s+[^)]*)?\)", text)
            else:
                parser = Links()
                parser.feed(text)
                urls = parser.urls
            for raw in urls:
                url = urlparse(raw)
                if url.scheme or url.netloc or not url.path:
                    continue
                if url.path.startswith("/curbpack/"):
                    target = ROOT / "site" / unquote(url.path[len("/curbpack/") :])
                elif url.path.startswith("/"):
                    continue
                else:
                    target = path.parent / unquote(url.path)
                if not target.exists():
                    errors.append(f"{rel}: missing local target {raw}")
        except (OSError, UnicodeError, ValueError) as error:
            errors.append(f"{rel}: {error}")

    try:
        svg = ET.parse(ROOT / "site/assets/og-campaign.svg").getroot()
        assert svg.attrib["viewBox"] == "0 0 1200 630", "unexpected SVG viewBox"
        png = (ROOT / "site/assets/og-campaign.png").read_bytes()
        assert png[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
        assert png[12:16] == b"IHDR", "missing PNG dimensions"
        assert struct.unpack(">II", png[16:24]) == (1200, 630), "social card must be 1200 x 630"
    except (OSError, ET.ParseError, AssertionError, KeyError, struct.error) as error:
        errors.append(f"social card: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-release', action='store_true', help='compare recorded release events with GitHub (network required)')
    args = parser.parse_args()
    errors.clear()
    check_links_and_card()
    check_freshness(args.verify_release)
    check_resources()
    if errors:
        print('\n'.join(dict.fromkeys(errors)), file=sys.stderr)
        return 1
    print('Public links, social card, current release statements and declared resources: PASS')
    print('Release evidence: ' + ('GitHub verified' if args.verify_release else 'record checked locally; use --verify-release for GitHub verification'))
    print('Allowed external font resources: ' + ', '.join(sorted(FONT_STYLE_ALLOWLIST)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
