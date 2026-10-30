#!/usr/bin/env python3
"""Package four standalone installers from the shared Unix and Windows sources."""
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def build(destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    sums = []
    for product, programs in (('studio', ['curbpack-studio', 'curbcheck']), ('curbcheck', ['curbcheck'])):
        for extension, source in (('sh', 'unix.sh'), ('ps1', 'windows.ps1')):
            body = (ROOT / 'scripts' / 'install' / source).read_text(encoding='utf-8')
            if extension == 'sh':
                call = 'install_programs ' + ' '.join(programs)
            else:
                call = 'Install-Programs @(' + ', '.join(repr(program) for program in programs) + ')'
            data = (body + '\n' + call + '\n').encode('utf-8')
            name = f'install-{product}.{extension}'
            (destination / name).write_bytes(data)
            sums.append(f'{hashlib.sha256(data).hexdigest()}  {name}')
    (destination / 'SHA256SUMS').write_bytes(('\n'.join(sums) + '\n').encode('utf-8'))


if __name__ == '__main__':
    build(ROOT / 'dist' / 'installers')
