"""Command-line entry point for the Compile PDF component."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description='Render a saved review-report JSON as a monochrome PDF.')
    parser.add_argument('--report', type=Path, required=True, help='Existing review-report JSON.')
    parser.add_argument('--out', type=Path, required=True, help='New PDF path; the parent directory must exist.')
    args = parser.parse_args(argv)
    try:
        from compile.pdf import compile_pdf
        out = compile_pdf(args.report, args.out)
    except ImportError as exc:
        print(f'PDF dependency unavailable: {exc}. Install requirements.txt.', file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f'Cannot render {args.report} to {args.out}: {exc}', file=sys.stderr)
        return 1
    print(f'wrote {out}')
    return 0
