"""Discovery operation.

The body lives in ``studio.claim.impl.jobs``. Callers of this module receive those same objects.
"""

from studio.claim.impl.jobs import (
    _LOCK,
    CURBPACK_COPY,
    SearchFn,
    AssessFn,
    start_discover_job,
    read_job,
    request_abort,
    reviewable_targets,
    latest_job,
    _run,
    _prior_candidates,
    _endpoint_failure,
    _candidate,
    _locator,
    _fail,
    _advance,
    _save,
    _job_path,
)
