"""Extract operations.

The bodies live in ``studio.pack.impl.extract.formex.text``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.formex.text import (
    annotations,
    re,
    ET,
    _SKIP_TAGS,
    local_tag,
    collapse_ws,
    element_text,
    _collect,
)
