"""Discovery operation.

The body lives in ``studio.claim.impl.try_run``. Callers of this module receive those same objects.
"""

from studio.claim.impl.try_run import (
    _LOCK,
    _SAFE,
    result_path,
    load_try_result,
    start_try_job,
    read_try_job,
    candidate_for_path,
    read_try_file,
    _run,
    _finish,
    _fail,
    _advance,
    _save,
    _slug,
)
