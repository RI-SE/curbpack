#!/usr/bin/env python3
"""Receipt v0 — assemble / structurally validate a thin index over local artefacts.

Not a conformity assessment. Digests only when files are locally available.

profile.digest identifies resolved pack/profile bytes (packs/<id>/pack.json or
internal/packs/data/<id>/pack.json). NEVER a ContextPack / run-export hash —
those belong only under artefacts[].
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "curbpack-receipt:0"
CLAIM = "Prepares evidence for human review — not a conformity assessment."
DIGEST_UNAVAILABLE = "unavailable"
REQUIRED = (
    "schema",
    "claim",
    "request_id",
    "profile",
    "repository",
    "artefacts",
    "assertions",
    "exceptions",
    "limitations",
    "evaluator",
    "generated_at",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def pack_json_candidates(root: Path, pack_id: str) -> list[Path]:
    """Deterministic locations for resolved pack bytes (never ContextPack)."""
    pid = pack_id.strip()
    out: list[Path] = []
    override = (
        os.environ.get("CURBPACK_PACKS_DIR") or os.environ.get("CYBERREADY_PACKS_DIR") or ""
    ).strip()
    if override:
        out.append(Path(override) / pid / "pack.json")
    out.append(root / "packs" / pid / "pack.json")
    out.append(root / "internal" / "packs" / "data" / pid / "pack.json")
    return out


def resolve_pack_digest(root: Path, pack_id: str) -> tuple[str | None, Path | None]:
    """Hash first available pack.json. Returns (sha256:hex, path) or (None, None)."""
    for p in pack_json_candidates(root, pack_id):
        if p.is_file():
            return f"sha256:{sha256_file(p)}", p
    return None, None


def profile_block(
    pack_id: str,
    pack_digest: str | None,
    *,
    resolve_from: Path | None,
) -> dict[str, Any]:
    """Build profile with pack digest or explicit unavailable status.

    If pack_digest is None and resolve_from is set, resolve from pack bytes.
    Empty string with resolve_from=None forces unavailable (no invent from exports).
    Never invent a digest from run-export artefacts.
    """
    digest = (pack_digest or "").strip() or None
    source: Path | None = None
    if digest is None and resolve_from is not None:
        digest, source = resolve_pack_digest(resolve_from, pack_id)

    profile: dict[str, Any] = {"pack_id": pack_id}
    if digest:
        profile["digest"] = digest
        if source is not None:
            try:
                rel = source.resolve().relative_to(resolve_from.resolve())  # type: ignore[union-attr]
                profile["digest_source"] = str(rel).replace("\\", "/")
            except (ValueError, AttributeError):
                profile["digest_source"] = str(source)
    else:
        profile["digest"] = None
        profile["digest_status"] = DIGEST_UNAVAILABLE
    return profile


def assemble(
    *,
    root: Path,
    request_path: Path,
    out_path: Path,
    artefact_paths: list[str],
    evaluator_version: str,
    pack_id: str,
    pack_digest: str | None,
    commit: str,
    check_passed: bool,
    readiness_score: int | None,
    exceptions: list[dict[str, Any]] | None = None,
    resolve_pack: bool = True,
) -> dict[str, Any]:
    req = load_json(request_path)
    request_id = req.get("request_id")
    if not request_id:
        raise SystemExit("receipt-assemble: request JSON missing request_id")

    artefacts: list[dict[str, str]] = []
    for rel in artefact_paths:
        p = root / rel
        if not p.is_file():
            raise SystemExit(f"receipt-assemble: artefact missing: {rel}")
        artefacts.append({"path": rel.replace("\\", "/"), "sha256": sha256_file(p)})

    assertions: list[dict[str, str]] = [
        {
            "label": "local_check_passed" if check_passed else "local_check_failed",
            "status": "observed",
            "evidence": f"curbpack check passed={'true' if check_passed else 'false'}"
            + (f" score={readiness_score}" if readiness_score is not None else ""),
        },
        {
            "label": "artefacts_fingerprinted",
            "status": "observed",
            "evidence": f"{len(artefacts)} local file(s)",
        },
    ]

    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "claim": CLAIM,
        "certification_claimed": False,
        "request_id": request_id,
        "profile": profile_block(
            pack_id,
            pack_digest,
            resolve_from=root if resolve_pack else None,
        ),
        "repository": {"commit": commit},
        "artefacts": artefacts,
        "assertions": assertions,
        "exceptions": exceptions or [],
        "limitations": [
            "Structural index over local artefacts only",
            "Cannot verify remote repositories or unavailable profiles",
            "Not conformity assessment / CE / certification",
            "profile.digest is pack/profile bytes only — ContextPack hashes live under artefacts[]",
        ],
        "evaluator": {
            "id": "curbpack-native",
            "version": evaluator_version,
            "method": "deterministic",
        },
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=False)
        f.write("\n")
    return receipt


def validate(
    *,
    receipt_path: Path,
    root: Path | None,
    request_path: Path | None,
    recompute_digests: bool,
) -> None:
    errors: list[str] = []
    try:
        receipt = load_json(receipt_path)
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"receipt-validate: cannot read {receipt_path}: {e}") from e

    if not isinstance(receipt, dict):
        raise SystemExit("receipt-validate: root must be a JSON object")

    if receipt.get("schema") != SCHEMA:
        errors.append(f"schema want {SCHEMA!r} got {receipt.get('schema')!r}")

    for key in REQUIRED:
        if key not in receipt:
            errors.append(f"missing required field: {key}")

    evaluator = receipt.get("evaluator")
    if isinstance(evaluator, dict):
        if evaluator.get("id") != "curbpack-native":
            errors.append("evaluator.id must be curbpack-native for Receipt v0")
        if evaluator.get("method") != "deterministic":
            errors.append("evaluator.method must be deterministic")
        if not evaluator.get("version"):
            errors.append("evaluator.version required")
    else:
        errors.append("evaluator must be an object")

    profile = receipt.get("profile")
    if not isinstance(profile, dict) or not profile.get("pack_id"):
        errors.append("profile.pack_id required")
    elif isinstance(profile, dict):
        status = profile.get("digest_status")
        digest = profile.get("digest")
        if status == DIGEST_UNAVAILABLE:
            if digest not in (None, ""):
                errors.append(
                    "profile.digest must be null when digest_status is unavailable "
                    "(do not substitute ContextPack / run-export hashes)"
                )
            # Pack digest not required when unavailable.
        else:
            if not digest or not isinstance(digest, str):
                errors.append(
                    "profile.digest required unless digest_status is "
                    f"{DIGEST_UNAVAILABLE!r}"
                )
            elif recompute_digests and root is not None:
                want = str(digest).removeprefix("sha256:")
                got_digest, src = resolve_pack_digest(root, str(profile["pack_id"]))
                if got_digest is None:
                    errors.append(
                        "profile.digest present but pack.json not locally available "
                        "to recompute (set digest null + digest_status unavailable "
                        "instead of using a run-export hash)"
                    )
                else:
                    got = got_digest.removeprefix("sha256:")
                    if got != want:
                        where = str(src) if src else "pack.json"
                        errors.append(
                            f"profile.digest mismatch vs {where}: got {got} want {want}"
                        )

    repo = receipt.get("repository")
    if not isinstance(repo, dict) or not repo.get("commit"):
        errors.append("repository.commit required")

    artefacts = receipt.get("artefacts")
    if not isinstance(artefacts, list):
        errors.append("artefacts must be a list")
    else:
        for i, art in enumerate(artefacts):
            if not isinstance(art, dict):
                errors.append(f"artefacts[{i}] must be object")
                continue
            if not art.get("path") or not art.get("sha256"):
                errors.append(f"artefacts[{i}] needs path and sha256")
                continue
            if recompute_digests and root is not None:
                p = root / str(art["path"])
                if p.is_file():
                    got = sha256_file(p)
                    want = str(art["sha256"]).removeprefix("sha256:")
                    if got != want:
                        errors.append(
                            f"artefacts[{i}] digest mismatch for {art['path']}: "
                            f"got {got} want {want}"
                        )
                # skip if not locally available — narrow structural verify

    if request_path is not None and request_path.is_file():
        req = load_json(request_path)
        rid = req.get("request_id")
        if rid and receipt.get("request_id") != rid:
            errors.append(
                f"request_id mismatch: receipt={receipt.get('request_id')!r} request={rid!r}"
            )

    claim = str(receipt.get("claim") or "")
    if "conformity assessment" not in claim.lower() and "not a conformity" not in claim.lower():
        if "not" not in claim.lower():
            errors.append("claim must include claim-safe boundary language")

    if receipt.get("certification_claimed") is True:
        errors.append("certification_claimed must not be true")

    if errors:
        for e in errors:
            print(f"receipt-validate FAIL: {e}", file=sys.stderr)
        raise SystemExit(1)
    print(f"receipt-validate OK: {receipt_path}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Receipt v0 assemble / validate")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("assemble", help="Write receipt.json from local artefacts")
    a.add_argument("--root", type=Path, required=True)
    a.add_argument("--request", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    a.add_argument("--artefact", action="append", default=[], dest="artefacts")
    a.add_argument("--evaluator-version", required=True)
    a.add_argument("--pack-id", default="house-policy")
    a.add_argument(
        "--pack-digest",
        default=None,
        help="sha256:… of pack.json bytes; omit to resolve from packs/ or internal/packs/data/",
    )
    a.add_argument(
        "--pack-digest-unavailable",
        action="store_true",
        help="Force profile.digest=null and digest_status=unavailable (never invent from ContextPack)",
    )
    a.add_argument("--commit", required=True)
    a.add_argument("--check-passed", choices=("true", "false"), required=True)
    a.add_argument("--readiness-score", type=int, default=None)

    v = sub.add_parser("validate", help="Structurally validate receipt.json")
    v.add_argument("receipt", type=Path)
    v.add_argument("--root", type=Path, default=None)
    v.add_argument("--request", type=Path, default=None)
    v.add_argument("--recompute-digests", action="store_true")

    r = sub.add_parser(
        "resolve-pack-digest",
        help="Print pack digest JSON for a pack_id (pack bytes only; never ContextPack)",
    )
    r.add_argument("--root", type=Path, required=True)
    r.add_argument("--pack-id", required=True)

    args = ap.parse_args(argv)
    if args.cmd == "assemble":
        if not args.artefacts:
            raise SystemExit("receipt-assemble: pass at least one --artefact PATH")
        assemble(
            root=args.root.resolve(),
            request_path=args.request.resolve(),
            out_path=args.out.resolve(),
            artefact_paths=args.artefacts,
            evaluator_version=args.evaluator_version,
            pack_id=args.pack_id,
            pack_digest=None if args.pack_digest_unavailable else args.pack_digest,
            commit=args.commit,
            check_passed=(args.check_passed == "true"),
            readiness_score=args.readiness_score,
            resolve_pack=not args.pack_digest_unavailable,
        )
        print(f"receipt-assemble OK: {args.out}")
        return 0
    if args.cmd == "validate":
        validate(
            receipt_path=args.receipt.resolve(),
            root=args.root.resolve() if args.root else None,
            request_path=args.request.resolve() if args.request else None,
            recompute_digests=bool(args.recompute_digests),
        )
        return 0
    if args.cmd == "resolve-pack-digest":
        digest, src = resolve_pack_digest(args.root.resolve(), args.pack_id)
        if digest is None:
            print(json.dumps({"digest": None, "digest_status": DIGEST_UNAVAILABLE}))
        else:
            payload: dict[str, Any] = {"digest": digest, "digest_status": None}
            if src is not None:
                try:
                    payload["path"] = str(
                        src.resolve().relative_to(args.root.resolve())
                    ).replace("\\", "/")
                except ValueError:
                    payload["path"] = str(src)
            print(json.dumps(payload))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
