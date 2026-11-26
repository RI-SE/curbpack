"""Discovery operation.

The body lives in ``studio.claim.impl.present``. Callers of this module receive those same objects.
"""

from studio.claim.impl.present import (
    overview_rows,
    merge_findings,
    claim_links,
    _locator,
    signing_label,
    _signing,
)
