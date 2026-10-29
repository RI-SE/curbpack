"""Created-file values for product curbpack.json. Studio and the CLI share this."""

from __future__ import annotations

import copy

from common.validate import validate_curbpack_config

CREATED_SEARCH_HINTS = {
    "sources": [{"source": "documents"}, {"source": "git"}],
    "exclude_path_globs": [
        "**/node_modules/**",
        "**/.git/**",
        "**/dist/**",
        "**/build/**",
    ],
    "prefer_path_globs": ["**/docs/**", "**/SECURITY*", "**/README*"],
}


def created_curbpack(**overrides) -> dict:
    document = {
        "packs": [],
        "search_hints": copy.deepcopy(CREATED_SEARCH_HINTS),
        "packs_dir": "curbpack/packs",
        "claims_dir": "curbpack/claims",
        "results_dir": ".curbpack",
        "reports_dir": "curbpack/reports",
        "unsigned_requirements": "reject",
    }
    document.update(overrides)
    return validate_curbpack_config(document)
