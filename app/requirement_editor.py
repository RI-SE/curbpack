"""Requirement editor view-model, save, and sign POST. Renders nothing.

The URLs stay on the old server.
"""

from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING

from common.canonical import version_digest
from common.errors import ModelError
from common.keystore import load_or_create_key, trust_store
from common.signing import read_signature
from discovery.repos import load_repos
from discovery.try_run import load_try_result, read_try_job
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
    from app.server import _open_requirement, _pack_query

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
        "try_assess_limit": 5,
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
        "list_href": (
            "/requirements/copy?" + _pack_query(query)
            if _pack_query(query)
            else "/requirements/copy"
        ),
    }


def _editor_message(query: dict) -> str:
    if (query.get("saved") or [""])[0]:
        return "Saved."
    if (query.get("signed") or [""])[0]:
        return "Signed with the local Ed25519 key."
    return ""


def _save_requirement_form(ws: Workspace, requirement_id: str, form: dict) -> None:
    from app.server import _open_requirement

    directory, _pack, requirement = _open_requirement(ws, requirement_id, form)
    if directory is None or requirement is None:
        raise ModelError("requirement", "id", "a requirement in the selected working copy")
    edited = apply_edits(requirement, _edits_from_form(requirement, form))
    save_working_requirement(
        directory,
        edited,
        expected_digest=(form.get("expected_digest") or [""])[0],
    )


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
