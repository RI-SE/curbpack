"""Requirement editor view-model, save, sign POST, and try-discovery POST.

Renders nothing. The URLs stay on the old server.
"""

from __future__ import annotations

import copy
import json
import secrets
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from common.canonical import version_digest
from common.errors import ModelError
from common.jsonio import read_json
from common.keystore import load_or_create_key, trust_store
from common.signing import read_signature
from discovery.door import repo_pack_requirements
from discovery.repos import find_repo, load_repos, resolve_repo_path
from discovery.assess import DEFAULT_ASSESS_LIMIT
from discovery.try_run import load_try_result, read_try_job, start_try_job
from requirements.editing import (
    apply_edits,
    approve_working_copy,
    assign_reference_numbers,
    publish_requirement,
    read_pack_seal,
    save_working_requirement,
)

if TYPE_CHECKING:
    from app.server import Workspace


def _editor_model(ws: Workspace, requirement_id: str, query: dict) -> dict:
    from app.server import _open_requirement

    directory, pack, requirement = _open_requirement(ws, requirement_id, query)
    if requirement is None or directory is None or pack is None:
        return {"requirement": None}
    trust = trust_store(ws.keys)
    try_repo = (query.get("try_repo") or [""])[0].strip()
    try_job_id = (query.get("try_job") or [""])[0].strip()
    try_open = bool((query.get("try_open") or [""])[0])
    try_job = None
    if try_job_id:
        try:
            try_job = read_try_job(ws.root / "jobs", try_job_id)
        except ModelError:
            try_job = None
        if try_job and try_job.get("status") == "done":
            try_repo = try_repo or str(try_job.get("repo_id") or "")
            try_open = True
            try_job = None
    try_document = load_try_result(ws.root / "jobs", requirement_id, try_repo) if try_repo else None
    return {
        "requirement": requirement,
        "expected_digest": version_digest(requirement),
        "reading": read_signature(requirement, trust, what="requirement"),
        "seal": read_pack_seal(directory, trust),
        "pack_version": pack.get("version"),
        "pack_id": pack.get("id"),
        "copy_timestamp": directory.name,
        "message": _editor_message(query),
        "repos": load_repos(ws.root).get("repos") or [],
        "try_repo_id": try_repo,
        "try_open": try_open or bool(try_document and not try_job),
        "try_ran": bool(try_document),
        "try_candidates": list((try_document or {}).get("candidates") or []),
        "try_assess_limit": DEFAULT_ASSESS_LIMIT,
        "try_error": (query.get("try_error") or [""])[0],
        "try_job": try_job,
        "workspace_root": str(ws.root.resolve()),
        "error": (query.get("error") or [""])[0],
        "invalid_fields": [
            name.strip()
            for name in (query.get("invalid") or [])
            if str(name).strip()
        ],
        "repo_id": (query.get("repo") or [""])[0].strip(),
        "bound_pack": (query.get("pack") or [""])[0].strip(),
        "proposal": (query.get("proposal") or [""])[0].strip(),
        "destination": (query.get("destination") or [""])[0].strip(),
        "section": (query.get("section") or [""])[0].strip(),
        "affected_claims": _affected_claims(ws, query, requirement),
        "ownership_claims": _ownership_claims(ws, query, requirement),
        "claims_repo_id": (query.get("repo") or [""])[0].strip() or (_open_repo(ws) or ""),
        "list_href": _list_href(query),
    }


def _list_href(query: dict) -> str:
    from urllib.parse import quote

    from app.server import _pack_query
    from studio.pack.compare_form import copy_list_target

    section = (query.get("section") or [""])[0].strip()
    if (query.get("proposal") or [""])[0].strip():
        return copy_list_target(query)
    packed = _pack_query(query)
    if packed:
        if section:
            return f"/requirements/copy?{packed}&section={quote(section, safe='')}"
        return "/requirements/copy?" + packed
    return "/requirements/copy"


def _open_repo(ws: Workspace) -> str:
    from discovery.door import open_repo_id

    return open_repo_id(ws.root) or ""


def _open_claims(ws: Workspace, query: dict) -> list[dict]:
    from common.validate import validate_claim
    from discovery.door import repo_claims_dir
    from discovery.repos import find_repo, load_repos, resolve_repo_path

    repo_id = (query.get("repo") or [""])[0].strip() or _open_repo(ws)
    if not repo_id:
        return []
    row = find_repo(load_repos(ws.root), repo_id)
    if row is None:
        return []
    try:
        repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
        folder = repo_claims_dir(repo)
    except (ModelError, OSError, ValueError):
        return []
    claims = []
    if folder.is_dir():
        for path in sorted(folder.glob("*.json")):
            try:
                claims.append(validate_claim(read_json(path)))
            except (ModelError, OSError, ValueError):
                continue
    return claims


def _affected_claims(ws: Workspace, query: dict, requirement: dict) -> list[dict]:
    from claims.impact import claims_unresolved_for_requirement

    return claims_unresolved_for_requirement(_open_claims(ws, query), requirement)


def _ownership_claims(ws: Workspace, query: dict, requirement: dict) -> dict:
    from claims.impact import claims_after_ownership

    return claims_after_ownership(_open_claims(ws, query), requirement)


def _editor_message(query: dict) -> str:
    if (query.get("saved") or [""])[0]:
        return "Saved."
    if (query.get("signed") or [""])[0]:
        return "Signed with the local Ed25519 key."
    return ""


def _save_requirement_form(ws: Workspace, requirement_id: str, form: dict) -> str | bytes:
    from urllib.parse import quote

    from app.server import _open_copy_query, _open_requirement, _pack_query
    from requirements.ownership import in_target_namespace, take_ownership
    from requirements.workspace import mark_selected
    from studio.pack.pages import ownership_confirmation_page

    directory, pack, requirement = _open_requirement(ws, requirement_id, form)
    if directory is None or requirement is None or pack is None:
        raise ModelError("requirement", "id", "a requirement in the selected working copy")
    namespace_base, packs = _namespace_base_for_edit(ws, form)
    if not in_target_namespace(pack, namespace_base):
        if (form.get("take_ownership") or [""])[0] != "1":
            query = _pack_query(form) or _open_copy_query(form)
            cancel = f"/requirements/requirement/{quote(requirement_id, safe='')}"
            if query:
                cancel = f"{cancel}?{query}"
            return ownership_confirmation_page(requirement_id, form, cancel)
        expected = (form.get("expected_digest") or [""])[0]
        if version_digest(requirement) != expected:
            raise ModelError(
                f"requirement {requirement_id}",
                "version",
                "the digest read before this save",
            )
        copied = take_ownership(
            directory,
            ws.root,
            namespace_base=namespace_base,
            requirement_id=requirement_id,
            edits=_edits_from_form(requirement, form),
            also_search=(packs,),
        )
        try:
            mark_selected(ws.root, str(pack["id"]), copied.name)
        except Exception:
            shutil.rmtree(copied, ignore_errors=True)
            raise
        return f"/requirements/requirement/{quote(requirement_id, safe='')}?saved=1"
    edited = apply_edits(requirement, _edits_from_form(requirement, form))
    save_working_requirement(
        directory,
        edited,
        expected_digest=(form.get("expected_digest") or [""])[0],
    )
    extra = _pack_query(form) or _open_copy_query(form)
    kept = []
    for key in ("proposal", "destination", "section"):
        value = (form.get(key) or [""])[0].strip()
        if value:
            kept.append(f"{key}={quote(value, safe='')}")
    if kept:
        extra = f"{extra}&{'&'.join(kept)}" if extra else "&".join(kept)
    suffix = f"?{extra}&saved=1" if extra else "?saved=1"
    return f"/requirements/requirement/{requirement_id}{suffix}"


def _namespace_base_for_edit(ws: Workspace, form: dict) -> tuple[str, Path]:
    """Publisher base and that repository's packs directory. A missing file is an error."""
    from app.server import _registered_repo_path
    from curbcheck.api import packs_dir
    from common.validate import validate_curbpack_config
    from discovery.door import open_repo_id

    repo_id = (form.get("repo") or [""])[0].strip() or (open_repo_id(ws.root) or "")
    if not repo_id:
        raise ModelError("curbpack.json", "namespace_base", "the open repository")
    repo = _registered_repo_path(ws, repo_id)
    path = repo / "curbpack.json"
    if not path.is_file():
        raise ModelError("curbpack.json", "namespace_base", "a curbpack.json in the repository")
    config = validate_curbpack_config(read_json(path))
    return str(config["namespace_base"]), packs_dir(repo, config)


def _edits_from_form(requirement: dict, form: dict) -> dict:
    from app.server import _lines

    present = set(form.get("present") or [])
    edits: dict = {}
    for field in (
        "remediation_hint",
        "note",
        "strength",
        "responsible",
        "applicability",
        "exceptions",
        "scope",
    ):
        if field in present:
            edits[field] = (form.get(field) or [""])[0].strip()
    source_fields = ("framework", "instrument", "identifier", "edition", "language", "url")
    if any(field in present for field in source_fields):
        source = dict(requirement.get("source") or {})
        for field in source_fields:
            if field not in present:
                continue
            value = (form.get(field) or [""])[0].strip()
            if value:
                source[field] = value
            else:
                source.pop(field, None)
        edits["source"] = source
    hint_names = ("concepts", "path_hints", "expected_evidence")
    if any(field in present for field in hint_names) or "sources" in present:
        hints = copy.deepcopy(requirement.get("discovery_hints") or {})
        for field in hint_names:
            if field not in present:
                continue
            values = _lines((form.get(field) or [""])[0])
            if values:
                hints[field] = values
            else:
                hints.pop(field, None)
        if "sources" in present:
            raw = (form.get("sources") or [""])[0].strip()
            if not raw:
                hints.pop("sources", None)
            else:
                parsed = json.loads(raw)
                if not isinstance(parsed, list):
                    raise ModelError("requirement", "discovery_hints.sources", "a JSON list")
                hints["sources"] = parsed
        edits["discovery_hints"] = hints
    if "references" in present:
        locators = form.get("ref_locator") or []
        texts = form.get("ref_law_text") or []
        if len(locators) != len(texts):
            raise ModelError("requirement", "references", "a locator and law text for each row")
        edits["references"] = assign_reference_numbers(
            [
                {"locator": locator.strip(), "law_text": text}
                for locator, text in zip(locators, texts)
            ]
        )
    return edits


def _sign_requirement(ws: Workspace, requirement_id: str, form: dict) -> str:
    from app.server import _now, _open_requirement, _pack_query

    directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
    if directory is None or requirement is None:
        raise ModelError("requirement", "id", "a requirement in the selected working copy")
    name = (form.get("name") or [""])[0].strip()
    private, _public = load_or_create_key(ws.keys, name)
    if "origin" in requirement:
        signed = approve_working_copy(requirement, name=name, private_key=private, at=_now())
    else:
        signed = publish_requirement(requirement, name=name, private_key=private, at=_now())
    save_working_requirement(
        directory,
        signed,
        expected_digest=(form.get("expected_digest") or [""])[0],
    )
    extra = _pack_query(form)
    suffix = f"?{extra}&signed=1" if extra else "?signed=1"
    return f"/requirements/requirement/{requirement_id}{suffix}"


def _pack_id_for_requirement(repo: Path, requirement_id: str) -> str:
    """Pack in curbpack.json that contains this requirement, or empty."""
    if not requirement_id:
        return ""
    path = repo / "curbpack.json"
    if not path.is_file():
        return ""
    from common.validate import validate_curbpack_config

    try:
        config = validate_curbpack_config(read_json(path))
    except ModelError:
        return ""
    for pack_id in config["packs"]:
        try:
            requirements = repo_pack_requirements(repo, pack_id)
        except ModelError:
            continue
        if any(isinstance(item, dict) and item.get("id") == requirement_id for item in requirements):
            return pack_id
    return ""


def _run_try_discovery(ws: Workspace, requirement_id: str, form: dict) -> str:
    from app.server import _open_requirement, _pack_query

    directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
    if requirement is None or directory is None:
        raise ModelError("try discovery", "requirement", "a requirement in the selected working copy")
    repo_id = (form.get("repo_id") or [""])[0].strip()
    data = load_repos(ws.root)
    row = find_repo(data, repo_id)
    if row is None:
        raise ModelError("try discovery", "repo_id", f"a registered repository, not {repo_id}")
    raw_limit = (form.get("assess_limit") or [str(DEFAULT_ASSESS_LIMIT)])[0].strip() or str(DEFAULT_ASSESS_LIMIT)
    if not raw_limit.isdigit():
        raise ModelError("try discovery", "assess_limit", "an integer from 0 to 20")
    assess_limit = int(raw_limit)
    if assess_limit > 20:
        raise ModelError("try discovery", "assess_limit", "an integer from 0 to 20")
    repo = resolve_repo_path(ws.root, str(row.get("path") or ""))
    config_path = repo / "curbpack.json"
    config = read_json(config_path) if config_path.is_file() else {}
    if not isinstance(config, dict):
        config = {}
    hunt = {"search_hints": config.get("search_hints") or {}}
    # The editor's pack field is the pack being edited. Product Discover only
    # accepts a pack named in this repo's curbpack.json.
    pack_id = _pack_id_for_requirement(repo, str(requirement.get("id") or ""))
    editor_query = _pack_query(form)
    job_id = f"try-{secrets.token_hex(4)}"
    start_try_job(
        ws.root / "jobs",
        job_id=job_id,
        repo=repo,
        repo_id=repo_id,
        requirement=requirement,
        hunt=hunt,
        assess_limit=assess_limit,
        pack_id=pack_id,
        editor_query=editor_query,
        complete=getattr(ws, "discover_complete", None),
    )
    extra = _pack_query(form)
    suffix = f"?{extra}&try_job={job_id}" if extra else f"?try_job={job_id}"
    return f"/requirements/requirement/{requirement_id}{suffix}"
