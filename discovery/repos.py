"""Discovery operation.

The body lives in ``studio.claim.impl.repos``. Callers of this module receive those same objects.
"""

from studio.claim.impl.repos import (
    REPOS_NAME,
    repos_path,
    load_repos,
    save_repos,
    resolve_repo_path,
    add_repo,
    find_repo,
    set_repo_status,
    _repo_id,
)
