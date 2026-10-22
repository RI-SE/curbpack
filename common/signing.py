"""Local Ed25519 seals.

`packs2.md` verifies a signature with the trusted certificate for `name` and
does not fetch that certificate. PoC2 has no X.509 store. A name maps to a
local Ed25519 public key the operator already has. Verification uses that key
and nothing else.

If the key is missing, the reading says the certificate is not available.
This module never writes a placeholder signature.
"""

from __future__ import annotations

import base64
import copy
from typing import Optional

from common.canonical import version_digest
from common.errors import ModelError, SigningUnavailable

try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
except ImportError:  # pragma: no cover - exercised only without the dependency
    serialization = None
    Ed25519PrivateKey = None
    Ed25519PublicKey = None


def signing_available() -> bool:
    return Ed25519PrivateKey is not None


def generate_keypair() -> tuple[bytes, bytes]:
    """Return raw (private, public) key bytes."""
    if Ed25519PrivateKey is None or serialization is None:
        raise SigningUnavailable("Ed25519 signing is unavailable because cryptography is not installed")
    key = Ed25519PrivateKey.generate()
    private = key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return private, public


def signature_message(digest: str, name: str, at: str) -> bytes:
    """Version digest, plus name, plus at. The signature bytes are not in this."""
    return f"{digest}\n{name}\n{at}".encode("utf-8")


def _require_signer(name: str, at: str) -> None:
    if Ed25519PrivateKey is None:
        raise SigningUnavailable("Ed25519 signing is unavailable because cryptography is not installed")
    if not isinstance(name, str) or not name.strip():
        raise ModelError("signed", "name", "non-empty string")
    if not isinstance(at, str) or not at.strip():
        raise ModelError("signed", "at", "non-empty UTC timestamp")


def signed_block(digest: str, *, name: str, private_key: bytes, at: str) -> dict:
    _require_signer(name, at)
    signature = Ed25519PrivateKey.from_private_bytes(private_key).sign(
        signature_message(digest, name, at)
    )
    return {
        "at": at,
        "name": name,
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def sign_object(obj: dict, *, name: str, private_key: bytes, at: str) -> dict:
    """Seal a requirement, claim, or review report. The digest is the object without `signed`."""
    out = copy.deepcopy(obj)
    out.pop("signed", None)
    out["signed"] = signed_block(version_digest(out), name=name, private_key=private_key, at=at)
    return out


def read_signature(obj: dict, trust: dict[str, bytes], *, what: str) -> dict:
    """The five facts from packs2.md §2.6. `trust` maps a display name to a raw public key."""
    return read_digest(version_digest(obj), obj.get("signed"), trust, what=what)


def read_digest(digest: str, signed: object, trust: dict[str, bytes], *, what: str) -> dict:
    if not isinstance(signed, dict):
        return {
            "what": what,
            "who": None,
            "when": None,
            "version": digest,
            "verifiable": False,
            "reason": "No signed block and no signed Git commit. The object is unsigned.",
        }
    name = signed.get("name")
    at = signed.get("at")
    reading = {
        "what": what,
        "who": name if isinstance(name, str) else None,
        "when": at if isinstance(at, str) else None,
        "version": digest,
        "verifiable": False,
    }
    if not isinstance(name, str) or not name.strip() or not isinstance(at, str):
        reading["reason"] = "The certificate does not verify the signature, or name is not the identity on that certificate."
        return reading
    public = trust.get(name)
    if public is None or Ed25519PublicKey is None:
        reading["reason"] = "The certificate for name is not available. Verification does not fetch it."
        return reading
    raw = _decode_signature(signed.get("signature"))
    if raw is None:
        reading["reason"] = "The certificate does not verify the signature, or name is not the identity on that certificate."
        return reading
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(
            raw, signature_message(digest, name, at)
        )
    except Exception:
        reading["reason"] = (
            "The current bytes are not the digest that was signed, "
            "or the certificate does not verify the signature."
        )
        return reading
    reading["verifiable"] = True
    return reading


def _decode_signature(value: object) -> Optional[bytes]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return base64.b64decode(value, validate=True)
    except Exception:
        return None
