"""Render a saved review report without reading mutable product files.

The renderer lives in ``studio.compile.impl.pdf``. ``compile-pdf.py`` still
imports this module.
"""

from studio.compile.impl.pdf import compile_pdf

__all__ = ["compile_pdf"]
