"""Extract operations.

The bodies live in ``studio.pack.impl.extract.strategies.single_call``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.strategies.single_call import (
    annotations,
    CompleteFn,
    _one_call,
    run_single_call,
)
