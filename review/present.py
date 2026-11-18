"""Group a raw run result by the current Requirement. No HTML.

The read model lives in ``studio.review.impl.present``.
"""

from studio.review.impl.present import (
    BYTES_CHANGED,
    CERT_IDENTITY,
    CERT_UNAVAILABLE,
    CHANGED,
    INVALID_SEAL,
    NEW_RUN,
    NO_SIGNED,
    PREVIOUS_UNKNOWN,
    RELATIONSHIP_CHANGED,
    UNCHANGED,
    UNRESOLVED,
    UNSIGNED,
    UNTRUSTED_SIGNER,
    VERIFICATION_UNAVAILABLE,
    path_adapter,
    path_state,
    present_compiled_report,
    present_raw_run,
    seal_forces_open,
    seal_label,
)

__all__ = [
    "BYTES_CHANGED",
    "CERT_IDENTITY",
    "CERT_UNAVAILABLE",
    "CHANGED",
    "INVALID_SEAL",
    "NEW_RUN",
    "NO_SIGNED",
    "PREVIOUS_UNKNOWN",
    "RELATIONSHIP_CHANGED",
    "UNCHANGED",
    "UNRESOLVED",
    "UNSIGNED",
    "UNTRUSTED_SIGNER",
    "VERIFICATION_UNAVAILABLE",
    "path_adapter",
    "path_state",
    "present_compiled_report",
    "present_raw_run",
    "seal_forces_open",
    "seal_label",
]
