"""Discovery operation.

The body lives in ``studio.claim.impl.feedback``. Callers of this module receive those same objects.
"""

from studio.claim.impl.feedback import (
    feedback_path,
    load_feedback,
    save_vote,
    save_check,
    dismiss_why,
    add_finding,
    _empty,
    _checked,
    _entry,
    _write,
)
