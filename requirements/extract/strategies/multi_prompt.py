"""Extract operations.

The bodies live in ``studio.pack.impl.extract.strategies.multi_prompt``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.strategies.multi_prompt import (
    annotations,
    CompleteFn,
    _one_call,
    run_multi_prompt,
)
