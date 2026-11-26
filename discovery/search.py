"""Discovery operation.

The body lives in ``studio.claim.impl.search``. Callers of this module receive those same objects.
"""

from studio.claim.impl.search import (
    glob_hit,
    excluded,
    iter_markdown,
    _excerpt,
    read_source_text,
    verify_excerpt,
    highlight_verified,
    _read_text,
    discover_candidates,
)
