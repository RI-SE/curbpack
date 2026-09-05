#!/usr/bin/env python3
"""Validate public links, SVG syntax, and the advertised social-card dimensions."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
import re
import struct
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
errors = []

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in {'href', 'src'} and value)

for path in [ROOT / 'README.md', *(ROOT / 'docs').rglob('*.md'), *(ROOT / 'site').rglob('*.html')]:
    rel = path.relative_to(ROOT)
    if rel.parts[:2] in {('docs', 'internal'), ('docs', 'gtm-oss')}:
        continue  # Historical/operator documents have a separate scope.
    try:
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.md':
            urls = re.findall(r'\]\(([^ )]+)(?:\s+[^)]*)?\)', text)
        else:
            parser = Links()
            parser.feed(text)
            urls = parser.urls
        for raw in urls:
            url = urlparse(raw)
            if url.scheme or url.netloc or not url.path:
                continue
            if url.path.startswith('/curbpack/'):
                target = ROOT / 'site' / unquote(url.path[len('/curbpack/'):])
            elif url.path.startswith('/'):
                continue
            else:
                target = path.parent / unquote(url.path)
            if not target.exists():
                errors.append(f'{rel}: missing local target {raw}')
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(f'{rel}: {error}')

try:
    svg = ET.parse(ROOT / 'site/assets/og-campaign.svg').getroot()
    assert svg.attrib['viewBox'] == '0 0 1200 630', 'unexpected SVG viewBox'
    png = (ROOT / 'site/assets/og-campaign.png').read_bytes()
    assert png[:8] == b'\x89PNG\r\n\x1a\n', 'not a PNG'
    assert png[12:16] == b'IHDR', 'missing PNG dimensions'
    assert struct.unpack('>II', png[16:24]) == (1200, 630), 'social card must be 1200 x 630'
except (OSError, ET.ParseError, AssertionError, KeyError, struct.error) as error:
    errors.append(f'social card: {error}')

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
print('public local links, SVG syntax, and social-card dimensions: PASS')
