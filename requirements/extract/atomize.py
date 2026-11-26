"""Extract operations.

The bodies live in ``studio.pack.impl.extract.atomize``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.atomize import (
    annotations,
    re,
    textwrap,
    PART_RE,
    INT_POINT_RE,
    SUB_POINT_RE,
    PAREN_POINT_RE,
    LETTER_RE,
    FOOTNOTE_LINE_RE,
    ExtractError,
    wrap_law,
    normalize_annex,
    strip_trailing_footnotes,
    split_parts,
    split_marker_blocks,
    looks_like_footnote_annex,
    split_top_points,
    expand_subpoints,
    split_lettered,
    build_law_text,
    locus_for,
    atomize,
)
