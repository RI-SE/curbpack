#!/usr/bin/env python3
"""Validate public links, SVG syntax, social-card dimensions, and surface freshness (INV-12/13)."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse
import json
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
errors: list[str] = []

# INV-13: stylesheet/font hosts allowed with stated why (scripts/module imports never allowlisted).
FONT_STYLE_ALLOWLIST = {
    "fonts.googleapis.com": "Google Fonts CSS delivery for Fraunces / IBM Plex (no script execution)",
    "fonts.gstatic.com": "Google Fonts font-file CDN paired with fonts.googleapis.com CSS",
}

EXCLUDE_PREFIXES = (
    ("site", "samples"),
    ("testdata",),
)
EXCLUDE_NAMES = {"CHANGELOG.md"}

VERSION_RE = re.compile(r"\bv?(\d+\.\d+\.\d+)\b", re.I)
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
# live/published/shipped/advertised (and post-vX.Y.Z advertise) near a version + date
CLAIM_VERBS = re.compile(
    r"\b(live|published|shipped|advertised|advertise)\b",
    re.I,
)
POST_ADVERTISE_RE = re.compile(
    r"post-v?(\d+\.\d+\.\d+)\s+advertise",
    re.I,
)
EXTERNAL_SCRIPT_SRC_RE = re.compile(
    r"""<script\b[^>]*\bsrc\s*=\s*["'](https?://[^"']+)["']""",
    re.I,
)
ESM_IMPORT_RE = re.compile(
    r"""(?:import\s+[^;]*?\s+from\s+|import\s*\(\s*)["'](https?://[^"']+)["']""",
    re.I,
)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        self.urls.extend(value for key, value in attrs if key in {"href", "src"} and value)


def is_excluded(rel: Path) -> bool:
    parts = rel.parts
    for prefix in EXCLUDE_PREFIXES:
        if parts[: len(prefix)] == prefix:
            return True
    if rel.name in EXCLUDE_NAMES:
        return True
    return False


def git_tag_date(version: str) -> str | None:
    """Return annotated-tagger date (YYYY-MM-DD) for vX.Y.Z, else None."""
    tag = version if version.startswith("v") else f"v{version}"
    try:
        out = subprocess.run(
            [
                "git",
                "for-each-ref",
                f"refs/tags/{tag}",
                "--format=%(taggerdate:short)%0a%(creatordate:short)",
            ],
            cwd=ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None
    for line in out.splitlines():
        line = line.strip()
        if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", line):
            return line
    return None


def load_manifest_version() -> str:
    data = json.loads((ROOT / "scripts/install-manifest.json").read_text(encoding="utf-8"))
    ver = data.get("default_version")
    if not isinstance(ver, str) or not ver:
        raise ValueError("install-manifest.json missing default_version")
    return ver.lstrip("v")


def load_buildinfo_version() -> str:
    text = (ROOT / "internal/buildinfo/version.go").read_text(encoding="utf-8")
    match = re.search(r'Version\s*=\s*"([^"]+)"', text)
    if not match:
        raise ValueError("internal/buildinfo/version.go: Version string not found")
    return match.group(1).lstrip("v")


def iter_public_text_files() -> list[Path]:
    paths: list[Path] = []
    for base in (ROOT / "docs", ROOT / "site", ROOT / "README.md"):
        if base.is_file():
            paths.append(base)
            continue
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() in {".md", ".html", ".txt"} and path.is_file():
                paths.append(path)
    return paths


def check_freshness() -> None:
    """INV-12 date/version truth + INV-13 zero external scripts/module imports."""
    try:
        manifest_ver = load_manifest_version()
        build_ver = load_buildinfo_version()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"freshness: cannot load version sources: {error}")
        return

    if manifest_ver != build_ver:
        errors.append(
            f"scripts/install-manifest.json vs internal/buildinfo/version.go: "
            f"advertised {manifest_ver} != buildinfo {build_ver}"
        )

    # Current advertised install/live pin (not historical checklist rows; Action @v0.5.2 exempt).
    current_advertise_re = re.compile(
        r"(?:"
        r"live on [`']?main[`']?|"
        r"installer supplies|"
        r"(?<![Aa]ction )[Ii]nstall pin|"
        r"downloads?\s+\*{0,2}v?"
        r")[^\n]{0,60}?\bv?(\d+\.\d+\.\d+)\b"
        r"|"
        r"\bv?(\d+\.\d+\.\d+)\b[^\n]{0,40}\blive on [`']?main[`']?",
        re.I,
    )

    # Pass 1: collect version+date claims keyed by file.
    file_bad_dates: dict[Path, set[str]] = {}

    for path in iter_public_text_files():
        rel = path.relative_to(ROOT)
        if is_excluded(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{rel}: {error}")
            continue
        lines = text.splitlines()

        for idx, line in enumerate(lines, start=1):
            dates = DATE_RE.findall(line)
            if not dates:
                continue
            versions: list[str] = []
            for m in POST_ADVERTISE_RE.finditer(line):
                versions.append(m.group(1))
            if CLAIM_VERBS.search(line):
                versions.extend(VERSION_RE.findall(line))
            # de-dupe preserve order
            seen: set[str] = set()
            uniq_versions: list[str] = []
            for v in versions:
                key = v.lstrip("v").lower()
                if key not in seen:
                    seen.add(key)
                    uniq_versions.append(key)

            for version in uniq_versions:
                tag_date = git_tag_date(version)
                if tag_date is None:
                    continue
                for claimed in dates:
                    if claimed != tag_date:
                        errors.append(
                            f"FAIL {rel}:{idx}   asserts v{version} "
                            f"{'advertise' if POST_ADVERTISE_RE.search(line) else 'live/published/shipped'} "
                            f"{claimed}; tag dated {tag_date}"
                        )
                        file_bad_dates.setdefault(path, set()).add(claimed)

        # Advertised-version agreement on public install surfaces.
        if rel.as_posix() in {
            "docs/getting-started/pre-stranger-handoff.md",
            "docs/launch-status.md",
            "site/index.html",
            "site/for-builders/index.html",
            "site/art14/index.html",
            "README.md",
        }:
            for idx, line in enumerate(lines, start=1):
                if "Action pin" in line or "@v0.5.2" in line:
                    continue
                for m in current_advertise_re.finditer(line):
                    found = (m.group(1) or m.group(2) or "").lstrip("v")
                    if found and found != manifest_ver:
                        errors.append(
                            f"FAIL {rel}:{idx}   advertised version v{found}; "
                            f"manifest/buildinfo v{manifest_ver}"
                        )

    # Pass 2: copy-paste dates — same wrong date in a file that already has a mismatched claim.
    for path, bad_dates in file_bad_dates.items():
        rel = path.relative_to(ROOT)
        lines = path.read_text(encoding="utf-8").splitlines()
        for idx, line in enumerate(lines, start=1):
            for claimed in DATE_RE.findall(line):
                if claimed not in bad_dates:
                    continue
                # Skip lines already reported as version claims, and lines whose version matches claimed date.
                versions = VERSION_RE.findall(line)
                if versions:
                    if all(git_tag_date(v) == claimed for v in versions):
                        continue
                    if any(CLAIM_VERBS.search(line) or POST_ADVERTISE_RE.search(line) for _ in [0]):
                        continue  # already FAIL'd in pass 1
                # Flag operational lines that reused the wrong stamp without a matching version tag.
                if not versions or any(git_tag_date(v) != claimed for v in versions):
                    # Avoid duplicate for pass-1 lines
                    marker = f"FAIL {rel}:{idx}   "
                    if any(e.startswith(marker) for e in errors):
                        continue
                    if CLAIM_VERBS.search(line) or POST_ADVERTISE_RE.search(line):
                        continue
                    errors.append(
                        f"FAIL {rel}:{idx}   asserts action {claimed} alongside mismatched version advertise"
                    )

    # INV-13: external script src + ESM https imports (both quote styles).
    for path in (ROOT / "site").rglob("*.html"):
        rel = path.relative_to(ROOT)
        if is_excluded(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{rel}: {error}")
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            for m in EXTERNAL_SCRIPT_SRC_RE.finditer(line):
                errors.append(f"FAIL {rel}:{idx}   external script {m.group(1)}")
            for m in ESM_IMPORT_RE.finditer(line):
                errors.append(f"FAIL {rel}:{idx}   external module import {m.group(1)}")


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


check_links_and_card()
check_freshness()

if errors:
    # De-dupe while preserving order
    unique = list(dict.fromkeys(errors))
    print("\n".join(unique), file=sys.stderr)
    sys.exit(1)
print(
    "public local links, SVG syntax, social-card dimensions, and freshness (INV-12/13): PASS"
)
print(
    "INV-13 note: fonts/stylesheets allowlisted — "
    + "; ".join(f"{h} ({why})" for h, why in sorted(FONT_STYLE_ALLOWLIST.items()))
)
