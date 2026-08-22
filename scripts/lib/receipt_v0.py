#!/usr/bin/env python3
"""Receipt v0 — assemble / structurally validate a thin index over local artefacts.

Not a conformity assessment. Digests only when files are locally available.
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


def assemble(
    *,
    root: Path,
    request_path: Path,
    out_path: Path,
    artefact_paths: list[str],
    evaluator_version: str,
    pack_id: str,
    pack_digest: str,
    commit: str,
    check_passed: bool,
    readiness_score: int | None,
    exceptions: list[dict[str, Any]] | None = None,
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
        "profile": {"pack_id": pack_id, "digest": pack_digest},
        "repository": {"commit": commit},
        "artefacts": artefacts,
        "assertions": assertions,
        "exceptions": exceptions or [],
        "limitations": [
            "Structural index over local artefacts only",
            "Cannot verify remote repositories or unavailable profiles",
            "Not conformity assessment / CE / certification",
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
        # Prefer explicit claim-safe sentence; soft-check for boundary language.
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
    a.add_argument("--pack-digest", default="")
    a.add_argument("--commit", required=True)
    a.add_argument("--check-passed", choices=("true", "false"), required=True)
    a.add_argument("--readiness-score", type=int, default=None)

    v = sub.add_parser("validate", help="Structurally validate receipt.json")
    v.add_argument("receipt", type=Path)
    v.add_argument("--root", type=Path, default=None)
    v.add_argument("--request", type=Path, default=None)
    v.add_argument("--recompute-digests", action="store_true")

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
            pack_digest=args.pack_digest,
            commit=args.commit,
            check_passed=(args.check_passed == "true"),
            readiness_score=args.readiness_score,
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
    return 2


if __name__ == "__main__":
    sys.exit(main())
