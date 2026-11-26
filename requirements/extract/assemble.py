"""Extract operations.

The bodies live in ``studio.pack.impl.extract.assemble``. Callers of this module receive those same objects.
"""

from studio.pack.impl.extract.assemble import (
    annotations,
    ModelError,
    validate_requirement,
    _INTERPRET_FIELDS,
    _HINTS_FIELDS,
    _ALLOWED_FIELDS,
    _COPY_FIELDS,
    validate_interpret_proposal,
    validate_hints_proposal,
    assemble_requirements,
    _provision_loci,
    _reject_duplicate_kind,
    _is_interpret,
    _is_hints,
    _merge_proposals,
    _build_requirement,
    _namespace_for_adapter,
    _omit_unusable_expected_evidence,
    _check_hints_shape,
    _reject_unexpected,
    _required_locus,
)
