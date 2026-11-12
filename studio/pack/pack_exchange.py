"""ZIP exchange of one Pack directory. The directory export is unchanged."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

from common.errors import ModelError
from common.store import load_pack_directory
from studio.pack.pack_export import _signature_rows


def export_pack_zip(directory: Path, trust: dict) -> tuple[bytes, list[dict]]:
    """Archive the Pack directory as it stands and report VR-00 for each object."""
    files = _regular_files(directory)
    pack, requirements = load_pack_directory(directory)
    rows = _signature_rows(directory, pack, requirements, trust)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path in files:
            archive.writestr(path.relative_to(directory).as_posix(), path.read_bytes())
    return buffer.getvalue(), rows


def _regular_files(directory: Path) -> list[Path]:
    found = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ModelError("export", "path", "a regular file")
        if path.is_file():
            found.append(path)
    return found
