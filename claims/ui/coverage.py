"""Presentation-only coverage mark.

The operations live in ``studio.claim.impl.coverage``. Callers of this
module receive those same objects.
"""

from studio.claim.impl.coverage import (
    COVERED_LABEL,
    NO_REPLACEMENT,
    REPLACEMENT_UNCHECKED,
    _checks_this_evidence,
    _repo_relative,
    _row,
    _source_path,
    claim_passed,
    covered_paths,
    load_run,
    retire_warning,
)
