"""Claims editor view-model. The URL stays on the old server."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from claims.bind import (
    build_claim,
    exist_args_for_path,
    law_passages,
    read_claim,
    read_claim_seal,
    rebind_from_fields,
    require_requirement_id,
    retire_claim,
    sign_claim,
    write_claim,
)
from common.canonical import version_digest
from common.errors import ModelError
from common.keystore import load_or_create_key, trust_store
from discovery.door import claim_file_relative, repo_claims_dir

if TYPE_CHECKING:
    from app.server import Workspace


def _claims_model(ws: Workspace, query: dict) -> dict:
    from app.server import _claims_lookup, _claims_repo, _door_chrome, _query_value

    door = _door_chrome(ws, query)
    lookup = _claims_lookup(ws, query)
    known_ids = list(lookup)
    trust = trust_store(ws.keys)
    repo = _claims_repo(ws, query)
    rows = []
    from common.store import load_claims

    config_path = repo / "curbpack.json"
    claims_dir = repo_claims_dir(repo) if config_path.is_file() else None
    claims = load_claims(claims_dir) if claims_dir is not None and claims_dir.is_dir() else []
    from claims.ui.coverage import load_run, retire_warning

    run_result = load_run(repo)
    if claims_dir is not None:
        for claim in claims:
            requirement_id = str(claim.get("requirement_id") or "")
            requirement = lookup.get(requirement_id)
            relative = claim_file_relative(repo, claims_dir, claim["id"])
            rows.append(
                {
                    "claim": claim,
                    "passages": law_passages(requirement) if requirement else [],
                    "reading": read_claim_seal(
                        claim,
                        trust,
                        repo=repo if claims_dir.is_dir() else None,
                        relative=relative,
                    ),
                    "retire_warning": retire_warning(claim, claims, run_result),
                }
            )
    prefill_requirement_id = (query.get("requirement_id") or [""])[0].strip()
    prefill_path = (query.get("path") or [""])[0].strip()
    prefill_passages: list[str] = []
    if prefill_requirement_id:
        # Validate query context when Discovery (or the user) named a Requirement.
        # Unknown ids must not fall back to a demo Requirement.
        if prefill_requirement_id not in lookup:
            raise ModelError(
                "claim",
                "requirement_id",
                f"an id in the selected Pack, not {prefill_requirement_id}",
            )
        prefill_passages = law_passages(lookup[prefill_requirement_id])
        if prefill_path:
            exist_args_for_path(prefill_path)
    prefill_source = ""
    if prefill_requirement_id and prefill_requirement_id in lookup:
        hints = lookup[prefill_requirement_id].get("discovery_hints") or {}
        sources = hints.get("sources") if isinstance(hints, dict) else None
        ids = [
            item.get("source")
            for item in sources or []
            if isinstance(item, dict) and isinstance(item.get("source"), str)
        ]
        if len(ids) == 1:
            prefill_source = ids[0]
    return {
        "claims": rows,
        "requirement_ids": known_ids,
        "prefill_requirement_id": prefill_requirement_id,
        "prefill_path": prefill_path,
        "prefill_source": prefill_source,
        "prefill_passages": prefill_passages,
        "repos": door.get("repos") or [],
        "repo_id": str(door.get("repo_id") or ""),
        "curbpack_file": door.get("curbpack_file") or "",
        "directory": door.get("directory") or "",
        "claims_dir": door.get("claims_dir") or "",
        "results_dir": door.get("results_dir") or "",
        "reports_dir": door.get("reports_dir") or "",
        "packs_dir_value": door.get("packs_dir_value") or "",
        "claims_dir_value": door.get("claims_dir_value") or "",
        "results_dir_value": door.get("results_dir_value") or "",
        "reports_dir_value": door.get("reports_dir_value") or "",
        "source_id": _query_value(query, "source_id"),
        "timestamp": _query_value(query, "timestamp"),
        "return_to": _query_value(query, "return_to"),
    }


def _create_claim(ws: Workspace, form: dict) -> str:
    from app.server import _claims_directory, _claims_lookup, _claims_redirect

    known = _claims_lookup(ws, form)
    requirement_id = require_requirement_id(
        (form.get("requirement_id") or [""])[0],
        list(known),
    )
    args = json.loads((form.get("args") or ["{}"])[0])
    checks = json.loads((form.get("checks") or ["[]"])[0])
    if not isinstance(args, dict):
        raise ModelError("claim", "args", "JSON object")
    if not isinstance(checks, list):
        raise ModelError("claim", "checks", "JSON list")
    claim = build_claim(
        claim_id=(form.get("id") or [""])[0].strip(),
        requirement=known[requirement_id],
        source=(form.get("source") or [""])[0].strip(),
        args=args,
        checks=checks,
        description=(form.get("description") or [""])[0].strip(),
        severity=(form.get("severity") or [""])[0].strip() or None,
    )
    claims_dir = _claims_directory(ws, form)
    destination = claims_dir / f"{claim['id']}.json"
    if destination.is_file():
        raise ModelError("claim", "id", "a new id; an existing Claim is edited explicitly")
    write_claim(claims_dir, claim)
    return _claims_redirect(form, f"saved=1&requirement_id={requirement_id}")


def _update_claim(ws: Workspace, claim_id: str, form: dict) -> str:
    from app.server import _claims_directory, _claims_redirect

    claim = read_claim(_claims_directory(ws, form) / f"{claim_id}.json")
    had_signed = isinstance(claim.get("signed"), dict)
    before = version_digest(claim)
    updated = rebind_from_fields(
        claim,
        source=(form.get("source") or [""])[0],
        args_json=(form.get("args") or ["{}"])[0],
        checks_json=(form.get("checks") or ["[]"])[0],
        severity=(form.get("severity") or [""])[0],
        description=(form.get("description") or [""])[0],
    )
    write_claim(_claims_directory(ws, form), updated)
    flag = "cleared=1" if had_signed and "signed" not in updated else "saved=1"
    return _claims_redirect(
        form,
        f"{flag}&requirement_id={updated.get('requirement_id', '')}",
        claim_changed=before != version_digest(updated),
    )


def _sign_claim(ws: Workspace, claim_id: str, form: dict) -> str:
    from app.server import _claims_directory, _claims_redirect, _now

    claim = read_claim(_claims_directory(ws, form) / f"{claim_id}.json")
    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    sealed = sign_claim(claim, name=name, private_key=private, at=_now())
    write_claim(_claims_directory(ws, form), sealed)
    return _claims_redirect(
        form,
        f"signed=1&requirement_id={claim.get('requirement_id', '')}",
        claim_changed=False,
    )


def _retire_claim(ws: Workspace, claim_id: str, form: dict) -> str:
    from app.server import _claims_directory, _claims_redirect

    retire_claim(_claims_directory(ws, form), claim_id)
    return _claims_redirect(form, "retired=1", claim_changed=False)
