"""Suggest overlapping Requirements and merge them only after confirmation.

The operations live in ``studio.pack.impl.consolidate``. Callers of this
module receive those same objects.
"""

from studio.pack.impl.consolidate import (
    _CONFLICT_KEYS,
    _freeze,
    _identifier,
    _locators,
    _passages,
    _shared_passages,
    apply_consolidation,
    preview_consolidation,
    suggest_consolidations,
)
