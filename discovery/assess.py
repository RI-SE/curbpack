"""Discovery operation.

The body lives in ``studio.claim.impl.assess``. Callers of this module receive those same objects.
"""

from studio.claim.impl.assess import (
    MAX_CHARS,
    DEFAULT_MODEL,
    DEFAULT_ENDPOINT,
    DEFAULT_ASSESS_LIMIT,
    RANKS,
    SCORE_PROMPT,
    CompleteFn,
    assess_candidates,
    _law_text,
    _truncate,
    _sha,
    _copy_assessment,
    shows_support,
    _judgment,
)
