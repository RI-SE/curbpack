"""Recorded Check facts for the Review technical-details dialog.

Reads the immutable run result and the embedded report objects. It does not
inspect Git, the working tree, or a hosting service.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from studio.common.presentation import NO_CRA_FIELD, NOT_A_LEGAL_CONCLUSION, worktree_sentence

_RUN_STAMP = re.compile(r"run-result_(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})Z\.json")


def render_technical_details(
    report: dict,
    *,
    door: dict | None = None,
    saved: bool = False,
    same_run_value: bool | None = None,
    unchecked: list[str] | None = None,
    verification: str = "",
) -> str:
    """Four sections: execution, loaded packs, recorded objects, raw result."""
    door = door or {}
    result = report.get("run_result") if isinstance(report.get("run_result"), dict) else {}
    claims = {
        claim["id"]: claim
        for claim in (report.get("claims") or [])
        if isinstance(claim, dict) and isinstance(claim.get("id"), str)
    }
    requirements = {
        requirement["id"]: requirement
        for requirement in (report.get("requirements") or [])
        if isinstance(requirement, dict) and isinstance(requirement.get("id"), str)
    }
    recorded = (
        "<h3>Recorded object details</h3>"
        + _claims_html(result.get("claims"), claims, requirements)
    )
    return (
        _execution(result, door, saved=saved, same_run_value=same_run_value, unchecked=unchecked)
        + _packs_section(result.get("packs"))
        + f"<section data-secondary>{recorded}{verification}</section>"
        + _raw_section(result)
    )


def _execution(
    result: dict,
    door: dict,
    *,
    saved: bool,
    same_run_value: bool | None,
    unchecked: list[str] | None,
) -> str:
    tool = _text(result.get("tool"))
    version = _text(result.get("tool_version"))
    if tool and version:
        curbcheck = f"{html.escape(tool)} {_code(version)}"
    elif tool or version:
        curbcheck = html.escape(tool or version)
    else:
        curbcheck = "unavailable"
    commit = _text(result.get("commit"))
    worktree = result.get("worktree") if result.get("worktree") in {"clean", "dirty"} else ""
    stamp = _check_time(door)
    filename = _result_name(door)
    rows = (
        _pair("Check time", html.escape(stamp) if stamp else "unavailable")
        + _pair("Curbcheck", curbcheck)
        + _pair("Commit", _code(commit) if commit else "unavailable", attr="data-commit", value=commit or "unavailable")
        + _pair(
            "Worktree",
            html.escape(worktree) if worktree else "unavailable",
            attr="data-worktree",
            value=worktree or "unavailable",
        )
        + _pair("Result", _code(filename) if filename else "unavailable")
    )
    note = ""
    sentence = worktree_sentence(result)
    if sentence:
        extra = ""
        if worktree == "dirty":
            extra = " The commit alone cannot reproduce the checked content."
        note = f"<p>{html.escape(sentence)}{extra}</p>"
    if same_run_value is True:
        same = '<p data-same-run="yes">same run: yes</p>'
    elif same_run_value is False:
        same = '<p data-same-run="no">same run: no. This saved report is an older run.</p>'
    else:
        same = ""
    missed = ""
    if unchecked:
        codes = ", ".join(f"<code>{html.escape(item)}</code>" for item in unchecked)
        missed = f"<p>These selected Requirements were not checked: {codes}</p>"
    saved_line = "" if saved else "<p>not saved</p>"
    limits = "".join(
        f"<li>{html.escape(item)}</li>" for item in (NOT_A_LEGAL_CONCLUSION, NO_CRA_FIELD)
    )
    return (
        '<section class="card" data-run-header>'
        "<h3>Execution</h3>"
        f"<dl>{rows}</dl>"
        f"{note}{same}{missed}{saved_line}"
        f'<ul class="muted">{limits}</ul>'
        "</section>"
    )


def _packs_section(packs: object) -> str:
    return (
        '<section class="card" data-packs>'
        "<h3>Loaded Packs</h3>"
        f"{_packs_html(packs)}"
        "</section>"
    )


def _packs_html(packs: object) -> str:
    if not isinstance(packs, list) or not packs:
        return "<p>No loaded packs.</p>"
    items = []
    for pack in packs:
        if not isinstance(pack, dict):
            continue
        name = _text(pack.get("id")) or "unavailable"
        version = _text(pack.get("version")) or "unavailable"
        digest = _text(pack.get("digest"))
        if digest:
            digest_html = (
                "<details><summary>Digest</summary>"
                f"<p>{_code(digest)}</p></details>"
            )
        else:
            digest_html = "<p>Digest unavailable.</p>"
        signed = pack.get("signed") if isinstance(pack.get("signed"), dict) else None
        signature = _signature_html({"signed": signed}) if signed else "<p>No recorded signature.</p>"
        items.append(f"<li>{_code(name)} {_code(version)}{digest_html}{signature}</li>")
    if not items:
        return "<p>No loaded packs.</p>"
    return "<ul>" + "".join(items) + "</ul>"


def _claims_html(rows: object, claims: dict, requirements: dict) -> str:
    if not isinstance(rows, list) or not rows:
        return "<p>No recorded claims.</p>"
    blocks = []
    for row in rows:
        if isinstance(row, dict):
            blocks.append(_claim_block(row, claims, requirements))
    if not blocks:
        return "<p>No recorded claims.</p>"
    return "".join(blocks)


def _claim_block(row: dict, claims: dict, requirements: dict) -> str:
    claim_id = _text(row.get("id")) or "unavailable"
    status = _text(row.get("status")) or "unavailable"
    identity = []
    for label, key in (
        ("Namespace", "namespace"),
        ("Pack", "pack_id"),
        ("Requirement", "requirement_id"),
        ("Binding", "binding"),
    ):
        value = _text(row.get(key))
        if value:
            identity.append(_pair(label, _code(value)))
    identity_html = f"<h4>Identity</h4><dl>{''.join(identity)}</dl>"
    if not identity:
        identity_html += "<p>Binding not recorded.</p>"
    digests = []
    for label, key in (
        ("Claim", "digest"),
        ("Requirement", "requirement_digest"),
        ("Resolved requirement", "actual_digest"),
    ):
        value = _text(row.get(key))
        if value:
            digests.append(_pair(label, _code(value)))
    digest_html = f"<h4>Digests</h4><dl>{''.join(digests)}</dl>"
    embedded = claims.get(claim_id) if claim_id != "unavailable" else None
    verification = "<h4>Verification</h4>" + _signature_html(embedded if isinstance(embedded, dict) else None)
    requirement_id = _text(row.get("requirement_id"))
    requirement = requirements.get(requirement_id) if requirement_id else None
    requirement_html = ""
    if isinstance(requirement, dict) and isinstance(requirement.get("signed"), dict):
        requirement_html = "<h4>Requirement signature</h4>" + _signature_html(requirement)
    body = identity_html + digest_html + _checks_html(row.get("checks")) + verification + requirement_html
    return f"<details><summary>{_code(claim_id)} {html.escape(status)}</summary>{body}</details>"


def _checks_html(checks: object) -> str:
    if not isinstance(checks, list) or not checks:
        return "<h4>Checks</h4><p>No recorded checks.</p>"
    items = []
    for check in checks:
        if not isinstance(check, dict):
            continue
        index = check.get("index")
        index_text = str(index) if isinstance(index, int) else "unavailable"
        name = _text(check.get("check")) or "unavailable"
        status = _text(check.get("status")) or "unavailable"
        detail = check.get("detail")
        detail_html = f"<p>{html.escape(detail)}</p>" if isinstance(detail, str) and detail else ""
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        args_html = (
            "<details><summary>Arguments</summary>"
            f"<pre>{html.escape(json.dumps(args, indent=2, ensure_ascii=False))}</pre></details>"
        )
        items.append(
            f"<li>{_code(index_text)} {_code(name)} {html.escape(status)}{detail_html}{args_html}</li>"
        )
    if not items:
        return "<h4>Checks</h4><p>No recorded checks.</p>"
    return "<h4>Checks</h4><ul>" + "".join(items) + "</ul>"


def _signature_html(obj: dict | None) -> str:
    signed = obj.get("signed") if isinstance(obj, dict) else None
    if not isinstance(signed, dict):
        return "<p>No recorded signature.</p>"
    name = _text(signed.get("name")) or "unavailable"
    when = _text(signed.get("at")) or "unavailable"
    body = f"<p>Signed by {_code(name)} at {_code(when)}.</p>"
    signature = signed.get("signature")
    if isinstance(signature, str) and signature:
        body += (
            "<details><summary>Signature</summary>"
            f"<pre>{html.escape(signature)}</pre></details>"
        )
    return body


def _raw_section(result: dict) -> str:
    text = html.escape(json.dumps(result, indent=2, ensure_ascii=False))
    return (
        '<section class="card" data-raw-result>'
        "<h3>Raw result</h3>"
        "<details><summary>Recorded JSON</summary>"
        f"<pre>{text}</pre></details>"
        "</section>"
    )


def _check_time(door: dict) -> str:
    for key in ("selected_result", "source_result"):
        name = Path(str(door.get(key) or "")).name
        match = _RUN_STAMP.fullmatch(name)
        if not match:
            continue
        year, month, day, hour, minute, second = match.groups()
        return f"{year}-{month}-{day} {hour}:{minute}:{second} UTC"
    return ""


def _result_name(door: dict) -> str:
    for key in ("selected_result", "source_result"):
        name = Path(str(door.get(key) or "")).name
        if name:
            return name
    return ""


def _pair(label: str, value_html: str, *, attr: str = "", value: str = "") -> str:
    extra = f' {attr}="{html.escape(value)}"' if attr else ""
    return f"<dt>{html.escape(label)}</dt><dd{extra}>{value_html}</dd>"


def _code(value: str) -> str:
    return f"<code>{html.escape(value)}</code>"


def _text(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""
