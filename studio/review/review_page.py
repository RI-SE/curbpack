"""Review page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from app.pages import _flash, _reading, page, repo_config_panel
from checks.labels import check_caption, check_remediation, check_short_label
from studio.claim.researcher import check_editor_dialog, check_form_script, _check_editor_values
from review.present import UNCHANGED
from studio.compile.impl.report import assessment_identity
from studio.review.technical_details import render_technical_details


def review_page(
    report: dict | None,
    reading: dict | None,
    message: str = "",
    error: str = "",
    discovery: dict | None = None,
    *,
    saved: bool = False,
    report_exists: bool = False,
    same_run_value: bool | None = None,
    unchecked: list[str] | None = None,
    door: dict | None = None,
) -> bytes:
    dialogs = ""
    decision = ""
    signed_report = isinstance(report, dict) and isinstance(report.get("signed"), dict)
    if report is None:
        body_report = _unchosen_run(door or {})
    else:
        decision = report.get("decision") or ""
        result = report.get("run_result") if isinstance(report.get("run_result"), dict) else {}
        claims_by_id = {
            claim["id"]: claim
            for claim in (report.get("claims") or [])
            if isinstance(claim, dict) and isinstance(claim.get("id"), str)
        }
        claims_href = _claims_href(discovery or {})
        ready = _discovery_ready(discovery or {})
        discover_href = "" if ready else _discover_home(door or {})
        rows = []
        dialog_parts = []
        review_return = _review_return_url(door or {})
        for row in result.get("claims") or []:
            if not isinstance(row, dict):
                continue
            claim = claims_by_id.get(row.get("id")) or {}
            rows.append(_review_claim_row(row, claim, claims_href, discover_href))
            if not ready:
                continue
            dialog = _review_discover_dialog(row, claim, discovery or {}, return_to=review_return)
            if dialog:
                dialog_parts.append(dialog)
        if ready and door and isinstance(door.get("presentation"), dict) and not dialog_parts:
            for group in door["presentation"].get("groups") or []:
                if not isinstance(group, dict):
                    continue
                group_id = str(group.get("id") or "")
                for item in group.get("claims") or []:
                    if not isinstance(item, dict):
                        continue
                    requirement_id = str(item.get("requirement_id") or "")
                    if group_id and group_id != "Unresolved Claims":
                        requirement_id = group_id
                    dialog = _review_discover_dialog(
                        {"id": item.get("id"), "status": item.get("status")},
                        {"requirement_id": requirement_id},
                        discovery or {},
                        return_to=review_return,
                    )
                    if dialog:
                        dialog_parts.append(dialog)
        appendix = []
        for item in report.get("appendix") or []:
            appendix.append(
                f"<li><code>{html.escape(item.get('id', ''))}</code> "
                f"requirement <code>{html.escape(item.get('requirement_id', ''))}</code> "
                f"{html.escape(item.get('reason', ''))}</li>"
            )
        if not saved:
            appendix_html = ""
        elif appendix:
            appendix_html = "<h2>Signature appendix</h2><ul>" + "".join(appendix) + "</ul>"
        else:
            appendix_html = (
                "<h2>Signature appendix</h2>"
                '<p class="muted">No unsigned or unverifiable Claims in this run.</p>'
            )
        dialogs = "".join(dialog_parts) + _review_discover_script(bool(dialog_parts))
        if door and door.get("presentation"):
            queue = _review_queue(
                door["presentation"],
                door,
                _assessment_index(report),
                not signed_report,
            )
            queue_html = queue + appendix_html
        else:
            queue_html = f"<h2>Check results</h2><ul>{''.join(rows)}</ul>{appendix_html}"
        file_dialog = _review_file_dialog(door or {})
        body_report = file_dialog + queue_html
    door = door or {}
    panel = repo_config_panel(
        door,
        action="/review",
        show=("config", "packs", "claims", "results", "reports"),
    )
    repo_id = str(door.get("repo_id") or "")
    report_value = str((door or {}).get("report_path") or "")
    hidden = ""
    if repo_id:
        hidden += f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
    if report_value:
        hidden += f'<input type="hidden" name="report" value="{html.escape(report_value)}">'
    signed = signed_report
    pending = [str(item) for item in (door.get("retirement_pending") or []) if str(item)]
    removal = isinstance(report, dict) and report.get("remove_retired_checks") is True
    retry = bool(removal and signed and pending)
    sign_warning = ""
    if retry:
        sign_warning = (
            f'<p class="err">These Claims were not updated: {html.escape(", ".join(pending))}. '
            "Signing again retries those Claims and does not sign the report again.</p>"
        )
    elif removal and saved and not signed:
        sign_warning = "<p>Signing will modify or delete Claim files.</p>"
    sign_button = "Try retirement again" if retry else "review-sign"
    sign_form = f"""
<form method="post" action="/review/sign" data-include-assessments>
{hidden}
{sign_warning}
<label>Signer name</label>
<input type="text" name="name" placeholder="External Reviewer">
<button type="submit">{sign_button}</button>
</form>
"""
    if saved and signed and not pending:
        decision_forms = f"""
<p data-decision>{html.escape(decision)}</p>
"""
    elif saved and signed:
        decision_forms = f"""
<p data-decision>{html.escape(decision)}</p>
{sign_form}
"""
    elif saved:
        decision_forms = f"""
<form method="post" action="/review" data-include-assessments>
{hidden}
<label>Decision</label>
<textarea name="decision">{html.escape(decision)}</textarea>
<button type="submit">Save decision</button>
</form>
{sign_form}
"""
    else:
        decision_forms = (
            '<p class="muted">Save decision and review-sign need a report file.</p>'
        )
    if not repo_id and report is None:
        body_report = "<p>No repository is chosen.</p>"
        decision_forms = ""
    if report is None:
        decision_forms = ""
        shown = f"<div class=\"card\">{body_report}</div>"
        detail = ""
    else:
        shown = body_report
        presentation = door.get("presentation") if isinstance(door.get("presentation"), dict) else None
        detail = _run_detail_dialog(
            door,
            report,
            saved,
            body=render_technical_details(
                report,
                door=door,
                saved=saved,
                same_run_value=same_run_value,
                unchecked=unchecked,
                verification=_current_verification(presentation, reading, saved),
            ),
        )
    body = f"""
<div class="review-board">
<div class="brand">curbpack-review</div>
<div class="header">
<div>
<h1>Review</h1>
{_review_intro(door, report)}
</div>
</div>
{_current_run_card(door, report, saved)}
{_review_empty(door)}
{_flash(message, error)}
{detail}
{shown}
{decision_forms}
{_review_actions(door, report, saved, repo_id)}
{_retire_dialog()}
{_resume_dialog(door or {})}
{dialogs}
</div>
"""
    return page("Review", body, banner=panel)


def _review_queue(
    presentation: dict,
    door: dict,
    assessments: dict,
    editable: bool,
) -> str:
    """Review queue. Every recorded Check is a row, including a passing Check."""
    repo = quote(str(door.get("repo_id") or ""), safe="")
    selected_result = quote(str(door.get("selected_result") or ""), safe="")
    selected_report = quote(str(door.get("selected_report") or ""), safe="")
    document = f"report={selected_report}" if selected_report else f"result={selected_result}"
    open_ids = [
        str(group.get("id") or "")
        for group in presentation.get("groups") or []
        if isinstance(group, dict) and group.get("open")
    ]
    body_rows: list[str] = []
    dialogs: list[str] = []
    notes: list[str] = []
    claim_count = 0
    deviation_count = 0
    changed = 0

    def remember(text: str) -> None:
        if text and text != UNCHANGED and text not in notes:
            notes.append(text)

    for group in presentation.get("groups") or []:
        if not isinstance(group, dict):
            continue
        queued = []
        for claim in group.get("claims") or []:
            if not isinstance(claim, dict):
                continue
            deviations = _claim_deviations(claim)
            if not deviations:
                if _claim_changed(claim):
                    changed += 1
                    for line in claim.get("sentences") or []:
                        remember(str(line))
                for check in claim.get("checks") or []:
                    if not isinstance(check, dict):
                        continue
                    for entry in check.get("paths") or []:
                        if isinstance(entry, dict) and entry.get("state") == "missing":
                            remember(
                                f"Path {entry.get('path')} is missing in the working tree now."
                            )
            if deviations or _passing_checks(claim):
                queued.append((claim, deviations))
        if not queued:
            continue
        requirement_span = sum(
            _claim_row_count(claim, deviations) for claim, deviations in queued
        )
        requirement_written = False
        requirement_id = str(group.get("id") or "")
        group_rows: list[str] = []
        for claim, deviations in queued:
            claim_count += 1
            deviation_count += len(deviations)
            passes = _passing_checks(claim)
            requirement_tip = _requirement_remedy(claim)
            claim_rows: list[tuple[str, object]] = []
            for check in passes:
                claim_rows.append(("pass", check))
            claim_rows.extend(("deviation", deviation) for deviation in deviations)
            if requirement_tip:
                claim_rows.append(("requirement", requirement_tip))
            claim_span = len(claim_rows)
            dialog_id, update_dialog = _failed_check_dialog(
                claim, repo, document, open_ids, requirement_id
            )
            if update_dialog:
                dialogs.append(update_dialog)
            for index, (kind, payload) in enumerate(claim_rows):
                cells = []
                if not requirement_written:
                    cells.append(
                        f'<td rowspan="{requirement_span}">'
                        f"{_requirement_link(claim, requirement_id, repo)}</td>"
                    )
                    requirement_written = True
                if index == 0:
                    cells.append(
                        f'<td rowspan="{claim_span}" data-claim="{html.escape(str(claim.get("id") or ""))}">'
                        f"{_file_cell(claim, open_ids, repo, document)}</td>"
                    )
                if kind == "pass":
                    check = payload if isinstance(payload, dict) else {}
                    identity = {
                        "kind": "check",
                        "claim_id": claim.get("id"),
                        "claim_digest": claim.get("digest"),
                        "index": check.get("index"),
                    }
                    comment_id = _comment_id(identity)
                    verdict, comment, comment_dialog = _verdict_controls(
                        identity,
                        claim,
                        assessments,
                        editable,
                        comment_id,
                        choices=(("", "Passed"), ("retire", "Retire")),
                        check_label=f"{check_short_label(check)} · check {check.get('index')}",
                    )
                    dialogs.append(comment_dialog)
                    cells.append("<td>" + _check_span(claim, check, dialog_id) + "</td>")
                    cells.extend(("<td></td>", f"<td>{verdict}</td>", f"<td>{comment}</td>"))
                elif kind == "requirement":
                    cells.append(f"<td></td><td>{payload}</td><td></td><td></td>")
                else:
                    deviation = payload if isinstance(payload, dict) else {}
                    if deviation.get("kind") == "binding":
                        dialogs.append(
                            _binding_dialog(
                                claim,
                                str(door.get("repo_id") or ""),
                                f"/review?repo={repo}&{document}"
                                f"&expanded={quote(','.join(open_ids), safe='')}",
                            )
                        )
                    cells.append("<td>" + _deviation_checks(claim, deviation, dialog_id) + "</td>")
                    remedy, verdict, comment, dialog = _deviation_cells(
                        claim, deviation, assessments, editable
                    )
                    dialogs.append(dialog)
                    cells.extend((f"<td>{remedy}</td>", f"<td>{verdict}</td>", f"<td>{comment}</td>"))
                group_rows.append("<tr>" + "".join(cells) + "</tr>")
        body_rows.append(
            f'<tbody data-requirement="{html.escape(requirement_id)}">'
            + "".join(group_rows)
            + "</tbody>"
        )
    when = _reviewed_when(door)
    def _plural(count: int, word: str) -> str:
        return f"{count} {word}" + ("" if count == 1 else "s")

    count = (
        f"{_plural(claim_count, 'claim')} · {_plural(deviation_count, 'deviation')}"
        if claim_count
        else "No claims need attention"
    )
    meta = f'<p class="review-meta">{html.escape(when + " · " if when else "")}{html.escape(count)}</p>'
    if not body_rows:
        table = "<p>No claims need attention.</p>"
    else:
        table = (
            '<table class="review-queue"><thead><tr>'
            "<th>Requirement</th><th>File</th><th>Checks</th>"
            '<th class="tips" title="Wrench: suggestion from the Check. '
            'Scroll: suggestion from the Requirement.">Remedy suggestions</th>'
            "<th>Verdict</th><th>Comment</th>"
            "</tr></thead>"
            + "".join(body_rows)
            + "</table>"
        )
    note_lines = []
    if changed:
        note_lines.append(
            f"{changed} {'claim' if changed == 1 else 'claims'} changed since this run."
        )
    note_lines.extend(notes)
    changed_note = "".join(f'<p class="muted">{html.escape(line)}</p>' for line in note_lines)
    script = _comment_script()
    if any("check-form" in item for item in dialogs):
        script += "<script>\n" + check_form_script() + "\n</script>"
    return meta + table + changed_note + "".join(dialogs) + script


def _claim_deviations(claim: dict) -> list[dict]:
    found = []
    for check in claim.get("checks") or []:
        if isinstance(check, dict) and str(check.get("status") or "") in {"fail", "skipped"}:
            found.append({"kind": "check", "check": check})
    if str(claim.get("binding") or "") in {"stale", "missing"}:
        found.append({"kind": "binding"})
    return found


def _claim_changed(claim: dict) -> bool:
    if claim.get("changed"):
        return True
    return any(
        "relationship changed" in str(line).lower()
        for line in claim.get("sentences") or []
    )


def _requirement_link(claim: dict, requirement_id: str, repo: str) -> str:
    label = html.escape(requirement_id or "Unresolved")
    inspect_id = str(claim.get("inspect_requirement_id") or "")
    if not inspect_id or not repo or requirement_id == "Unresolved Claims":
        return f"<code>{label}</code>"
    pack = quote(str(claim.get("pack_id") or ""), safe="")
    href = f"/requirements/requirement/{quote(inspect_id, safe='')}?repo={repo}"
    if pack:
        href += f"&pack={pack}"
    return f'<a data-leave="1" href="{html.escape(href)}"><code>{label}</code></a>'


def _file_cell(claim: dict, open_ids: list[str], repo: str, document: str) -> str:
    claim_id = str(claim.get("id") or "")
    links = []
    seen = set()
    for check in claim.get("checks") or []:
        if not isinstance(check, dict):
            continue
        visible, _bits = _review_path_cell(check, open_ids, repo, document)
        if visible and visible not in seen:
            seen.add(visible)
            links.append(visible)
    if not links:
        links.append(f"<code>{html.escape(claim_id)}</code>")
    extras = []
    unsafe = False
    for check in claim.get("checks") or []:
        if not isinstance(check, dict):
            continue
        if str(check.get("edit") or "") == "unsafe":
            unsafe = True
    if unsafe:
        extras.append(
            '<span data-edit-unsafe="1">The current Check cannot be matched safely.</span>'
        )
    extra = f'<div class="file-actions">{"".join(extras)}</div>' if extras else ""
    return "".join(links) + extra


def _passing_checks(claim: dict) -> list[dict]:
    return [
        check
        for check in claim.get("checks") or []
        if isinstance(check, dict) and str(check.get("status") or "") == "pass"
    ]


def _claim_row_count(claim: dict, deviations: list[dict]) -> int:
    return (
        len(deviations)
        + len(_passing_checks(claim))
        + (1 if _requirement_remedy(claim) else 0)
    )


def _comment_id(identity: dict) -> str:
    dialog_id = "comment-" + "-".join(
        str(part or "")
        for part in (
            identity.get("kind"),
            identity.get("claim_id"),
            identity.get("index"),
            identity.get("binding"),
        )
    )
    return re.sub(r"[^A-Za-z0-9_-]", "-", dialog_id)


def _deviation_checks(claim: dict, deviation: dict, dialog_id: str) -> str:
    """The check or binding pill for one deviation row."""
    pills = []
    if deviation.get("kind") == "check":
        check = deviation.get("check")
        if isinstance(check, dict):
            pills.append(_check_span(claim, check, dialog_id))
    else:
        binding = str(claim.get("binding") or "")
        if binding in {"stale", "missing"}:
            bind_id = _binding_dialog_id(claim)
            name = "Requirement Binding" if binding == "stale" else f"Binding {binding}"
            label = f'{_status_mark("fail", f"Binding {binding}")}{html.escape(name)}'
            if bind_id:
                pills.append(
                    f'<button type="button" class="check fail" data-binding="{html.escape(binding)}" '
                    f'data-binding-dialog="{html.escape(bind_id)}">{label}</button>'
                )
            else:
                pills.append(
                    f'<span class="check fail" data-binding="{html.escape(binding)}">{label}</span>'
                )
    return " ".join(pills)


def _binding_dialog_id(claim: dict) -> str:
    claim_id = str(claim.get("id") or "")
    if not claim_id:
        return ""
    return "binding-" + re.sub(r"[^A-Za-z0-9_-]", "-", claim_id)


def _binding_dialog(claim: dict, repo_id: str, return_to: str) -> str:
    """Explain a stale or missing binding. Sign confirms the Claim still applies."""
    dialog_id = _binding_dialog_id(claim)
    if not dialog_id:
        return ""
    binding = str(claim.get("binding") or "")
    if binding == "missing":
        text = "<p>The Requirement this Claim names was not loaded for this run.</p>"
    else:
        text = (
            "<p>The Requirement has changed since this Claim was bound to it.</p>"
            "<p>Have you checked the Requirement and confirmed this Claim still applies?</p>"
        )
    claim_id = str(claim.get("id") or "")
    namespace = str(claim.get("namespace") or "")
    pack_id = str(claim.get("pack_id") or "")
    requirement_id = str(claim.get("recorded_requirement_id") or "")
    if claim_id and repo_id and namespace and pack_id and requirement_id:
        actions = (
            f'<form method="post" action="/claims/{html.escape(claim_id)}/rebind">'
            f'<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">'
            f'<input type="hidden" name="namespace" value="{html.escape(namespace)}">'
            f'<input type="hidden" name="pack_id" value="{html.escape(pack_id)}">'
            f'<input type="hidden" name="requirement_id" value="{html.escape(requirement_id)}">'
            f'<input type="hidden" name="return_to" value="{html.escape(return_to)}">'
            '<p class="actions"><button type="submit">Sign</button> '
            '<button type="button" class="secondary" data-close-binding>Cancel</button></p>'
            "</form>"
        )
    else:
        actions = '<p><button type="button" class="secondary" data-close-binding>Cancel</button></p>'
    return f'<dialog id="{html.escape(dialog_id)}" class="binding-note">{text}{actions}</dialog>'


def _check_span(claim: dict, check: dict, dialog_id: str) -> str:
    status = str(check.get("status") or "")
    name = str(check.get("check") or "")
    opener = _check_opener(claim, check, dialog_id) if status == "fail" else ""
    return (
        f'<span data-check="{html.escape(name)}" data-status="{html.escape(status)}">'
        f"{_check_pill(check, status, opener)}{_unlinked_args(check)}</span>"
    )


def _unlinked_args(check: dict) -> str:
    """Show path arguments for a Check that has no file link. Do not invent a link."""
    if check.get("paths") or check.get("dep_ban"):
        return ""
    args = check.get("args") if isinstance(check.get("args"), dict) else {}
    names: list[str] = []
    path = args.get("path")
    if isinstance(path, str) and path:
        names.append(path)
    paths = args.get("paths")
    if isinstance(paths, list):
        names.extend(item for item in paths if isinstance(item, str) and item and item not in names)
    if not names:
        return ""
    return " " + " ".join(f"<code>{html.escape(name)}</code>" for name in names)


def _current_verification(presentation: dict | None, reading: dict | None, saved: bool) -> str:
    """Live seal readings. They are not the recorded Check."""
    parts = []
    if isinstance(presentation, dict):
        label = str(presentation.get("report_seal_label") or "")
        if label:
            parts.append(f'<p data-report-seal="{html.escape(label)}">{html.escape(label)}</p>')
        parts.append(_secondary_details(presentation))
    if saved:
        parts.append(_reading(reading))
    body = "".join(part for part in parts if part)
    if not body:
        return ""
    return (
        "<details><summary>Current verification</summary>"
        '<p class="muted">Read from the repository now. This is not the recorded Check.</p>'
        f"{body}</details>"
    )


def _secondary_details(presentation: dict) -> str:
    """Seal readings stay out of the queue. Check arguments are recorded separately."""
    seals = []
    for group in presentation.get("groups") or []:
        if not isinstance(group, dict):
            continue
        label = str(group.get("seal_label") or "")
        seal = group.get("seal") if isinstance(group.get("seal"), dict) else None
        if label or seal:
            line = _seal_line(seal) if seal else ""
            seals.append(
                f'<p data-seal-label="{html.escape(label)}">{html.escape(label)}{line}</p>'
            )
        for claim in group.get("claims") or []:
            if not isinstance(claim, dict):
                continue
            chain = _chain_html(claim)
            if chain:
                seals.append(f'<div class="muted">{chain}</div>')
            claim_label = str(claim.get("seal_label") or "")
            claim_seal = claim.get("seal") if isinstance(claim.get("seal"), dict) else None
            if claim_label or claim_seal:
                line = _seal_line(claim_seal) if claim_seal else ""
                seals.append(
                    f'<p data-claim-seal="{html.escape(claim_label)}">'
                    f"{html.escape(str(claim.get('id') or ''))}{line}</p>"
                )
    return "".join(seals)


def _only_absent(detail: str) -> bool:
    """True when every clause only says a path is absent."""
    parts = [part.strip() for part in detail.split(";") if part.strip()]
    return bool(parts) and all(part.endswith(" is absent") for part in parts)


def _default_check_remedy(check: dict, detail: str, hint: str) -> str:
    """A check-kind tip. A hint recorded on the result is shown instead."""
    if hint or str(check.get("status") or "") != "fail":
        return ""
    text = check_remediation(check, detail)
    if not text:
        return ""
    return (
        f'<p data-check-remediation>{_remedy_icon("wrench", "Check remediation")} '
        f"{html.escape(text)}</p>"
    )


def _deviation_cells(
    claim: dict, deviation: dict, assessments: dict, editable: bool
) -> tuple[str, str, str, str]:
    if deviation["kind"] == "check":
        check = deviation["check"]
        identity = {
            "kind": "check",
            "claim_id": claim.get("id"),
            "claim_digest": claim.get("digest"),
            "index": check.get("index"),
        }
        detail = str(check.get("detail") or "")
        hint = str(check.get("remediation_hint") or "")
        remedy = ""
        if detail and not _only_absent(detail):
            remedy = f'<p data-detail>{html.escape(detail)}</p>'
        remedy += _default_check_remedy(check, detail, hint)
        if hint:
            remedy += (
                f'<p data-check-remediation>{_remedy_icon("wrench", "Check remediation")} '
                f"{html.escape(hint)}</p>"
            )
    else:
        identity = {
            "kind": "binding",
            "claim_id": claim.get("id"),
            "claim_digest": claim.get("digest"),
            "namespace": claim.get("namespace"),
            "pack_id": claim.get("pack_id"),
            "requirement_id": claim.get("recorded_requirement_id"),
            "requirement_digest": claim.get("requirement_digest"),
            "binding": claim.get("binding"),
        }
        remedy = _binding_remedy(str(claim.get("binding") or ""))
    dialog_id = "comment-" + "-".join(
        str(part or "")
        for part in (
            identity.get("kind"),
            identity.get("claim_id"),
            identity.get("index"),
            identity.get("binding"),
        )
    )
    dialog_id = re.sub(r"[^A-Za-z0-9_-]", "-", dialog_id)
    check_label = ""
    if deviation["kind"] == "check":
        check_label = f"{check_short_label(check)} · check {check.get('index')}"
    verdict, comment, dialog = _verdict_controls(
        identity, claim, assessments, editable, dialog_id, check_label=check_label
    )
    return remedy, verdict, comment, dialog


def _binding_remedy(binding: str) -> str:
    if binding == "stale":
        text = (
            "The Requirement has changed since this Claim was bound to it. "
            "Click the check to rebind this Claim."
        )
    elif binding == "missing":
        text = "The Requirement this Claim names was not loaded for this run."
    else:
        text = ""
    return (
        f'<p data-binding="{html.escape(binding)}">{html.escape(text)}</p>'
    )


def _requirement_remedy(claim: dict) -> str:
    hint_from = str(claim.get("requirement_hint_from") or "")
    hint = str(claim.get("requirement_hint") or "")
    if not hint or hint_from == "unresolved":
        return ""
    return (
        f'<p data-requirement-remediation data-hint-from="{html.escape(hint_from)}">'
        f'{_remedy_icon("scroll", "Requirement remediation")} {html.escape(hint)}</p>'
    )


def _icon_svg(body: str, *, label: str = "", css: str, size: int = 16) -> str:
    named = (
        f' role="img" aria-label="{html.escape(label)}" title="{html.escape(label)}"'
        if label
        else ' aria-hidden="true"'
    )
    return (
        f'<svg class="{css}" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
        f"{named}>{body}</svg>"
    )


def _status_mark(status: str, label: str = "") -> str:
    """A check before a passing check, a cross before a failed one."""
    if status == "pass":
        body = '<path d="M20 6 9 17l-5-5"/>'
    elif status == "fail":
        body = '<path d="M18 6 6 18"/><path d="M6 6l12 12"/>'
    else:
        return ""
    return _icon_svg(body, label=label or status, css="mark", size=14)


def _remedy_icon(kind: str, label: str) -> str:
    bodies = {
        "wrench": (
            '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105'
            "c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3"
            'l7.91-7.91a6 6 0 0 1 7.057-8.259c.438.12.54.662.219.984z"/>'
        ),
        "scroll": (
            '<path d="M15 12h-5"/>'
            '<path d="M15 8h-5"/>'
            '<path d="M19 17V5a2 2 0 0 0-2-2H4"/>'
            '<path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"/>'
        ),
    }
    return _icon_svg(bodies[kind], label=label, css="remedy-icon")


def _document_icon() -> str:
    return _icon_svg(
        '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" x2="8" y1="13" y2="13"/>'
        '<line x1="16" x2="8" y1="17" y2="17"/>',
        css="doc-icon",
    )


def _verdict_controls(
    identity: dict,
    claim: dict,
    assessments: dict,
    editable: bool,
    dialog_id: str,
    *,
    choices: tuple[tuple[str, str], ...] | None = None,
    check_label: str = "",
) -> tuple[str, str, str]:
    saved = assessments.get(assessment_identity(identity))
    disposition = str(saved.get("disposition") or "") if isinstance(saved, dict) else ""
    text = str(saved.get("text") or "") if isinstance(saved, dict) else ""
    hidden = _assessment_hidden(identity, claim)
    if choices is None:
        if identity.get("kind") == "binding":
            choices = (("", "Not assessed"), ("accept", "Accept"), ("must_fix", "Must be fixed"))
        else:
            choices = (
                ("", "Not assessed"),
                ("accept", "Accept"),
                ("must_fix", "Must be fixed"),
                ("retire", "Retire"),
            )
    marker = (
        f' data-claim-id="{html.escape(str(identity.get("claim_id") or ""))}"'
        f' data-check-label="{html.escape(check_label)}"'
    )
    if not editable:
        label = dict(choices).get(disposition, "Not assessed")
        carried = hidden + (
            f'<input type="hidden" name="assess_disposition" form="review-compile" data-assessment-field'
            f'{marker} value="{html.escape(disposition)}">'
            f'<input type="hidden" name="assess_text" form="review-compile" data-assessment-field '
            f'value="{html.escape(text)}">'
        )
        verdict = (
            f'{carried}<span data-disposition="{html.escape(disposition or "not_assessed")}">'
            f"{html.escape(label)}</span>"
        )
    else:
        options = "".join(
            f'<option value="{html.escape(value)}"'
            f'{" selected" if disposition == value else ""}>{html.escape(caption)}</option>'
            for value, caption in choices
        )
        verdict = f"""
{hidden}
<select class="verdict" name="assess_disposition" form="review-compile" data-assessment data-assessment-field{marker} data-comment-dialog="{html.escape(dialog_id)}">
{options}
</select>
"""
    mark = " has-comment" if text.strip() else ""
    glyph = _document_icon() if text.strip() else ""
    comment = (
        f'<button type="button" class="comment-mark{mark}" data-comment-for="{html.escape(dialog_id)}" '
        f'aria-label="Comment">{glyph}</button>'
    )
    if editable:
        editor = (
            f'<textarea name="assess_text" form="review-compile" data-assessment data-assessment-field>'
            f"{html.escape(text)}</textarea>"
        )
    else:
        editor = f"<p>{html.escape(text or 'No comment.')}</p>"
    dialog = (
        f'<dialog id="{html.escape(dialog_id)}" class="comment-editor">'
        "<p>Comment</p>"
        "<p data-comment-demand hidden>This verdict needs a comment. "
        "Close without one and the previous verdict returns.</p>"
        f"{editor}"
        '<p><button type="button" class="secondary" data-close-comment>Close</button></p>'
        "</dialog>"
    )
    return verdict, comment, dialog


def _reviewed_when(door: dict) -> str:
    for key in ("selected_result", "source_result", "selected_report"):
        name = Path(str(door.get(key) or "")).name
        stamp = name
        for prefix in ("run-result_", "review-report_"):
            if stamp.startswith(prefix):
                stamp = stamp.removeprefix(prefix)
        stamp = stamp.removesuffix(".json")
        if (
            len(stamp) == 16
            and stamp.endswith("Z")
            and stamp[8] == "T"
            and stamp[:8].isdigit()
            and stamp[9:15].isdigit()
        ):
            return (
                f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]} "
                f"{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]} UTC"
            )
    return ""


def _comment_script() -> str:
    icon = json.dumps(_document_icon())
    return f"""
<script>
(function() {{
  var doc = {icon};
  function refresh(button) {{
    var dialog = document.getElementById(button.getAttribute("data-comment-for"));
    if (!dialog) return;
    var field = dialog.querySelector("textarea");
    if (!field) return;
    var has = field.value.trim() !== "";
    button.classList.toggle("has-comment", has);
    button.innerHTML = has ? doc : "";
  }}
  var needsComment = {{accept: true, must_fix: true, retire: true}};
  function commentDialog(id) {{
    return id ? document.getElementById(id) : null;
  }}
  function commentText(dialog) {{
    var field = dialog && dialog.querySelector("textarea");
    return field ? field.value.trim() : "";
  }}
  function showDemand(dialog, on) {{
    var note = dialog && dialog.querySelector("[data-comment-demand]");
    if (note) note.hidden = !on;
  }}
  function openComment(dialog, demand) {{
    if (!dialog || !dialog.showModal || dialog.open) return;
    showDemand(dialog, demand);
    dialog.showModal();
    var field = dialog.querySelector("textarea");
    if (field) field.focus();
  }}
  document.querySelectorAll("button[data-comment-for]").forEach(function(button) {{
    button.addEventListener("click", function() {{
      var dialog = commentDialog(button.getAttribute("data-comment-for"));
      var verdict = document.querySelector('select[data-comment-dialog="' + (dialog ? dialog.id : "") + '"]');
      var demand = verdict && needsComment[verdict.value] && commentText(dialog) === "";
      openComment(dialog, demand);
    }});
  }});
  document.querySelectorAll("select[data-comment-dialog]").forEach(function(field) {{
    field.setAttribute("data-kept", field.value);
    field.addEventListener("change", function() {{
      var dialog = commentDialog(field.getAttribute("data-comment-dialog"));
      if (!needsComment[field.value] || commentText(dialog) !== "") {{
        field.setAttribute("data-kept", field.value);
        return;
      }}
      openComment(dialog, true);
    }});
  }});
  document.querySelectorAll("dialog.comment-editor").forEach(function(dialog) {{
    dialog.addEventListener("close", function() {{
      var field = document.querySelector('select[data-comment-dialog="' + dialog.id + '"]');
      if (field && needsComment[field.value] && commentText(dialog) === "") {{
        field.value = field.getAttribute("data-kept") || "";
      }} else if (field) {{
        field.setAttribute("data-kept", field.value);
      }}
      showDemand(dialog, false);
      var opener = document.querySelector('button[data-comment-for="' + dialog.id + '"]');
      if (opener) refresh(opener);
    }});
  }});
  document.querySelectorAll("[data-close-comment]").forEach(function(button) {{
    button.addEventListener("click", function() {{
      var dialog = button.closest("dialog");
      if (dialog) dialog.close();
    }});
  }});
  document.querySelectorAll("[data-binding-dialog]").forEach(function(button) {{
    button.addEventListener("click", function() {{
      var dialog = document.getElementById(button.getAttribute("data-binding-dialog"));
      if (dialog && dialog.showModal) dialog.showModal();
    }});
  }});
  document.querySelectorAll("[data-close-binding]").forEach(function(button) {{
    button.addEventListener("click", function() {{
      var dialog = button.closest("dialog");
      if (dialog) dialog.close();
    }});
  }});
}})();
</script>
"""


def _review_requirement_card(
    group: dict,
    open_ids: list[str],
    repo: str,
    document: str,
    discover_href: str = "",
    assessments: dict | None = None,
    editable: bool = False,
) -> str:
    group_id = str(group.get("id") or "")
    if group.get("open"):
        nxt = [item for item in open_ids if item != group_id]
    else:
        nxt = sorted(set(open_ids) | {group_id})
    href = f"/review?repo={repo}&{document}&expanded={quote(','.join(nxt), safe='')}"
    open_attr = " open" if group.get("open") else ""
    label = str(group.get("seal_label") or "")
    label_html = ""
    if label:
        bad = ' style="background:#fee2e2;color:#991b1b"' if label == "Invalid seal" else ""
        label_html = (
            f'<span class="pill" data-seal-label="{html.escape(label)}"{bad}>'
            f"{html.escape(label)}</span>"
        )
    seal = _seal_line(group.get("seal")) if isinstance(group.get("seal"), dict) else ""
    counts = _review_check_counts(group)
    skipped_bit = f" · {counts['skipped']} skipped" if counts["skipped"] else ""
    count_pill = (
        f'<span class="pill">{counts["fail"]} fail · {counts["pass"]} pass'
        f"{skipped_bit}</span>"
    )
    result_summary = str(group.get("result_summary") or "")
    claim_header = []
    claims_html = []
    for claim in group.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("id") or "")
        claim_label = str(claim.get("seal_label") or "")
        claim_label_html = (
            f' <span class="pill" data-claim-seal="{html.escape(claim_label)}">'
            f"{html.escape(claim_label)}</span>"
            if claim_label
            else ""
        )
        claim_facts = _seal_line(claim.get("seal")) if isinstance(claim.get("seal"), dict) else ""
        binding_html = _binding_html(str(claim.get("binding") or ""))
        claim_header.append(
            f" claim {html.escape(claim_id)}{claim_label_html}{binding_html}{claim_facts}"
        )
        claims_html.append(
            _review_claim_card(
                claim, open_ids, repo, document, discover_href, assessments or {}, editable
            )
        )
    note = _review_attention_note(group)
    note_html = f'<p class="note">{html.escape(note)}</p>' if note else ""
    passages = _passage_html(group.get("passages") or [])
    summary = (
        f'<a href="{html.escape(href)}">'
        f'<div class="header" style="margin-bottom:.35rem">'
        f"<div><h3><code>{html.escape(group_id)}</code></h3></div>"
        f'<div style="display:flex;gap:.5rem;align-items:center;flex-wrap:wrap">'
        f"{label_html}{count_pill}"
        f'<span class="pill">{html.escape(result_summary)}</span>'
        f"</div></div>"
        f'<span class="seal-facts">{seal}{"".join(claim_header)}</span>'
        f"</a>"
    )
    return (
        f'<details class="requirement card" data-requirement="{html.escape(group_id)}"{open_attr}>'
        f"<summary>{summary}</summary>"
        f"{passages}{note_html}{''.join(claims_html)}</details>"
    )


def _review_claim_card(
    claim: dict,
    open_ids: list[str],
    repo: str,
    document: str,
    discover_href: str = "",
    assessments: dict | None = None,
    editable: bool = False,
) -> str:
    claim_id = str(claim.get("id") or "")
    status = str(claim.get("status") or "")
    klass = ' class="pill-bad"' if status == "fail" else ""
    binding_html = _binding_html(str(claim.get("binding") or ""))
    requirement_id = str(claim.get("requirement_id") or "")
    requirement_html = (
        f'<p class="muted">Unresolved requirement <code>{html.escape(requirement_id)}</code></p>'
        if requirement_id
        else ""
    )
    attention_sentences = [
        str(line)
        for line in claim.get("sentences") or []
        if str(line) and str(line) != "The Claim is unchanged since the Check run."
    ]
    sentences = "".join(f'<p class="note">{html.escape(line)}</p>' for line in attention_sentences)
    unchanged = "The Claim is unchanged since the Check run." in [
        str(line) for line in claim.get("sentences") or []
    ]
    # Keep the unchanged sentence in the DOM for scenario tests, but do not lead with it
    # when the Claim already has a fail/skipped result or another attention note.
    if unchanged and status not in {"fail", "skipped"} and not attention_sentences:
        unchanged_html = "<p>The Claim is unchanged since the Check run.</p>"
    elif unchanged:
        unchanged_html = '<p class="muted" hidden>The Claim is unchanged since the Check run.</p>'
    else:
        unchanged_html = ""
    path_rows, check_items, actions, tech_parts = _review_claim_checks(
        claim, open_ids, repo, document, discover_href
    )
    chain = _chain_html(claim)
    if chain:
        tech_parts.append(chain)
    table = (
        '<table class="path-checks"><thead><tr><th>Path</th><th>Checks</th></tr></thead>'
        f"<tbody>{''.join(path_rows)}</tbody></table>"
        if path_rows
        else ""
    )
    tech_block = ""
    if tech_parts:
        tech_block = (
            '<details class="technical"><summary>Technical details</summary>'
            + "".join(tech_parts)
            + "</details>"
        )
    description = str(claim.get("description") or "")
    description_html = (
        f'<p data-claim-description="{html.escape(description)}">{html.escape(description)}</p>'
        if description
        else ""
    )
    return (
        f'<div class="card claim-card" data-claim="{html.escape(claim_id)}">'
        f'<div class="header" style="margin-bottom:.35rem">'
        f"<div><h3>Claim <code>{html.escape(claim_id)}</code></h3></div>"
        f'<div><span class="fact">Check <span data-status="{html.escape(status)}"{klass}>'
        f"{html.escape(status)}</span></span>{binding_html}</div>"
        f"</div>"
        f"{description_html}{requirement_html}{sentences}{unchanged_html}"
        f"{_deviation_html(claim, assessments or {}, editable)}"
        f"{table}"
        f"{tech_block}"
        f'<ul class="review-check-list" aria-hidden="true">{"".join(check_items)}</ul>'
        f'<div class="actions">{"".join(actions)}</div>'
        f"</div>"
    )


def _chain_html(claim: dict) -> str:
    rows = []
    for attr, key, label in (
        ("data-requirement-location", "requirement_location", "Requirement location"),
        ("data-requirement-commit", "requirement_commit", "Requirement commit"),
        ("data-recorded-digest", "recorded_digest", "Recorded requirement digest"),
        ("data-current-digest", "current_digest", "Current requirement digest"),
        ("data-signature-method", "signature_method", "Requirement signature method"),
        ("data-signature-status", "signature_status", "Requirement signature status"),
        ("data-claim-location", "claim_location", "Claim location"),
        ("data-claim-commit", "claim_commit", "Claim commit"),
        ("data-claim-recorded-digest", "claim_recorded_digest", "Recorded claim digest"),
        ("data-claim-recovered-digest", "claim_recovered_digest", "Recovered claim digest"),
        ("data-claim-current-digest", "claim_current_digest", "Current claim digest"),
        ("data-claim-signature-method", "claim_signature_method", "Claim signature method"),
        ("data-claim-signature-status", "claim_signature_status", "Claim signature status"),
        ("data-chain-binding", "chain_binding", "Binding"),
    ):
        value = str(claim.get(key) or "")
        if not value:
            continue
        text = html.escape(value)
        rows.append(f"<dt>{html.escape(label)}</dt><dd><span {attr}=\"{text}\">{text}</span></dd>")
    differences = []
    for item in claim.get("differences") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name:
            continue
        historical = html.escape(str(item.get("historical") or ""))
        current = html.escape(str(item.get("current") or ""))
        differences.append(
            f'<p><span data-difference="{html.escape(name)}">{html.escape(name)} {historical} {current}</span></p>'
        )
    if not rows and not differences:
        return ""
    listed = f"<dl>{''.join(rows)}</dl>" if rows else ""
    return listed + "".join(differences)


def _review_claim_checks(
    claim: dict,
    open_ids: list[str],
    repo: str,
    document: str,
    discover_href: str = "",
) -> tuple[list[str], list[str], list[str], list[str]]:
    path_rows: list[str] = []
    check_items: list[str] = []
    actions: list[str] = []
    tech_parts: list[str] = []
    claim_id = str(claim.get("id") or "")
    status = str(claim.get("status") or "")
    action_edit_added = False
    for check in claim.get("checks") or []:
        if not isinstance(check, dict):
            continue
        detail = str(check.get("detail") or "")
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        check_status = str(check.get("status") or "")
        check_name = str(check.get("check") or "")
        check_class = ' class="pill-bad"' if check_status == "fail" else ""
        pill = _check_pill(check, check_status)
        path_cell, path_bits = _review_path_cell(check, open_ids, repo, document)
        path_mark = ' <span class="path-mark">✗</span>' if check_status == "fail" else ""
        path_rows.append(f"<tr><td>{path_cell}{path_mark}</td><td>{pill}</td></tr>")
        edit = str(check.get("edit") or "none")
        edit_html = ""
        if edit == "ok":
            return_to = (
                f"/review?repo={repo}&{document}"
                f"&expanded={quote(','.join(open_ids), safe='')}"
            )
            edit_href = (
                f"/claims?repo_id={repo}&return_to={quote(return_to, safe='')}"
                f"#claim-{quote(claim_id, safe='')}"
            )
            edit_html = (
                f'<a class="edit-review" data-leave="1" data-edit-check="{html.escape(str(check.get("index")))}" '
                f'href="{html.escape(edit_href)}">Edit</a>'
            )
            if not action_edit_added:
                actions.append(
                    f'<a class="btn primary edit-review" data-leave="1" data-edit-check="{html.escape(str(check.get("index")))}" '
                    f'href="{html.escape(edit_href)}">Edit <code>{html.escape(claim_id)}</code></a>'
                )
                action_edit_added = True
        elif edit == "unsafe":
            edit_html = (
                '<span data-edit-unsafe="1">The current Check cannot be matched safely.</span>'
            )
            actions.append(edit_html)
        tech_inner = (
            f"<p>{html.escape(str(check.get('index')))}: {html.escape(check_name)} "
            f"{html.escape(check_status)}"
            f"{(' — ' + html.escape(detail)) if detail else ''}</p>"
            f"<code>{html.escape(json.dumps(args, ensure_ascii=False))}</code>"
        )
        tech_parts.append(tech_inner)
        # Contract list keeps args/paths for scenario tests; not shown in the primary card.
        check_items.append(
            "<li "
            f'data-check="{html.escape(check_name)}" '
            f'data-status="{html.escape(check_status)}"{check_class}>'
            f"{pill}"
            f"{(' ' + ' '.join(path_bits)) if path_bits else ''}"
            f"{(' ' + edit_html) if edit_html else ''}"
            f'<details class="technical"><summary>Technical details</summary>{tech_inner}</details>'
            f"</li>"
        )
    inspect_id = str(claim.get("inspect_requirement_id") or "")
    if inspect_id and repo:
        pack = quote(str(claim.get("pack_id") or ""), safe="")
        inspect_href = f"/requirements/requirement/{quote(inspect_id, safe='')}?repo={repo}"
        if pack:
            inspect_href += f"&pack={pack}"
        actions.append(
            f'<a class="btn" data-leave="1" href="{html.escape(inspect_href)}">Inspect Requirement</a>'
        )
    if str(claim.get("binding") or "") in {"stale", "missing"} and claim_id and repo:
        return_to = (
            f"/review?repo={repo}&{document}&expanded={quote(','.join(open_ids), safe='')}"
        )
        rebind_href = (
            f"/claims?repo_id={repo}&return_to={quote(return_to, safe='')}"
            f"#claim-{quote(claim_id, safe='')}"
        )
        actions.append(
            f'<a class="btn" data-leave="1" href="{html.escape(rebind_href)}">Rebind</a>'
        )
    if status in {"fail", "skipped"} and claim_id:
        if discover_href:
            actions.append(
                f'<a class="btn discover-again" data-leave="1" href="{html.escape(discover_href)}">Re-Discover</a>'
            )
        else:
            actions.append(
                f'<button type="button" class="btn discover-again" '
                f'data-dialog="{html.escape(_dialog_id(claim_id))}">'
                f"Re-Discover</button>"
            )
    return path_rows, check_items, actions, tech_parts


def _review_path_cell(
    check: dict, open_ids: list[str], repo: str, document: str
) -> tuple[str, list[str]]:
    path_bits: list[str] = []
    visible: list[str] = []
    for entry in check.get("paths") or []:
        if not isinstance(entry, dict):
            continue
        rel = str(entry.get("path") or "")
        state = str(entry.get("state") or "")
        if state == "present":
            file_href = (
                f"/review?repo={repo}&{document}"
                f"&expanded={quote(','.join(open_ids), safe='')}"
                f"&file={quote(rel, safe='')}"
            )
            link = (
                f'<a class="file-link" data-path="{html.escape(rel)}" data-path-state="present" '
                f'href="{html.escape(file_href)}"><code>{html.escape(rel)}</code></a>'
            )
            path_bits.append(
                f'<a data-path="{html.escape(rel)}" data-path-state="present" '
                f'href="{html.escape(file_href)}">{html.escape(rel)}</a>'
            )
            visible.append(link)
        else:
            text = (
                f'<span data-path="{html.escape(rel)}" '
                f'data-path-state="{html.escape(state)}">'
                f"<code>{html.escape(rel)}</code> ({html.escape(state)})</span>"
            )
            path_bits.append(
                f'<span data-path="{html.escape(rel)}" '
                f'data-path-state="{html.escape(state)}">{html.escape(rel)} ({html.escape(state)})</span>'
            )
            visible.append(text)
    dep = check.get("dep_ban") if isinstance(check.get("dep_ban"), dict) else None
    if dep is not None:
        banned = ", ".join(html.escape(str(item)) for item in (dep.get("banned_versions") or []))
        package = html.escape(str(dep.get("package") or ""))
        dep_html = (
            f'<span data-dep-ban="{package}">package {package} banned_versions {banned}</span>'
        )
        path_bits.append(dep_html)
        visible.append(dep_html)
    if not visible:
        # Unknown checks: show a neutral placeholder; args stay in Technical details / li.
        visible.append('<span class="muted">—</span>')
    return " ".join(visible), path_bits


def _check_pill(check: dict, status: str, opener: str = "") -> str:
    kind = status if status in {"pass", "fail", "skipped"} else "fail"
    entry = check if isinstance(check, dict) else {"check": str(check or "")}
    name = html.escape(check_short_label(entry))
    mark = _status_mark(status)
    label = f"{mark}{name}" if mark else f"{name} · {html.escape(status)}"
    title = html.escape(check_caption(entry))
    if opener:
        return (
            f'<button type="button" class="check {html.escape(kind)}" title="{title}" {opener}>'
            f"{label}</button>"
        )
    return (
        f'<span class="check {html.escape(kind)}" title="{title}">'
        f"{label}</span>"
    )


def _check_opener(claim: dict, check: dict, dialog_id: str) -> str:
    if not dialog_id or str(check.get("edit") or "") != "ok":
        return ""
    index = check.get("index")
    if not isinstance(index, int):
        return ""
    path = _check_file(check)
    values = json.dumps(_check_editor_values(check, path))
    return (
        f'data-check-dialog="{html.escape(dialog_id)}" data-index="{index}" '
        f'data-path="{html.escape(path)}" data-values="{html.escape(values)}"'
    )


def _check_file(check: dict) -> str:
    args = check.get("args") if isinstance(check.get("args"), dict) else {}
    single = args.get("path")
    if isinstance(single, str) and single.strip():
        return single.strip()
    listed = args.get("paths")
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, str) and item.strip():
                return item.strip()
    for entry in check.get("paths") or []:
        if isinstance(entry, dict) and str(entry.get("path") or "").strip():
            return str(entry["path"]).strip()
    return ""


def _failed_check_dialog(
    claim: dict, repo: str, document: str, open_ids: list[str], requirement_id: str
) -> tuple[str, str]:
    claim_id = str(claim.get("id") or "")
    pack_id = str(claim.get("pack_id") or "")
    requirement = str(claim.get("recorded_requirement_id") or requirement_id or "")
    if not claim_id or not repo or not pack_id or not requirement or requirement == "Unresolved Claims":
        return "", ""
    editable = [
        check
        for check in claim.get("checks") or []
        if isinstance(check, dict)
        and str(check.get("status") or "") == "fail"
        and str(check.get("edit") or "") == "ok"
        and isinstance(check.get("index"), int)
    ]
    if not editable:
        return "", ""
    dialog_id = "check-update-" + re.sub(r"[^A-Za-z0-9_-]", "-", claim_id)
    path = _check_file(editable[0])
    return_to = (
        f"/review?repo={repo}&{document}&expanded={quote(','.join(open_ids), safe='')}"
    )
    hidden = (
        f'<input type="hidden" name="repo_id" value="{html.escape(repo)}">'
        f'<input type="hidden" name="pack" value="{html.escape(pack_id)}">'
        f'<input type="hidden" name="requirement_id" value="{html.escape(requirement)}">'
        f'<input type="hidden" name="claim_id" value="{html.escape(claim_id)}">'
        '<input type="hidden" name="edit_index" value="">'
        f'<input type="hidden" name="return_to" value="{html.escape(return_to)}">'
    )
    dialog = check_editor_dialog(
        path=path,
        hidden=hidden,
        submit_label="Update",
        cancel_label="Cancel",
        dialog_id=dialog_id,
    )
    return dialog_id, dialog


def _review_check_counts(group: dict) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "skipped": 0}
    for claim in group.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            status = str(check.get("status") or "")
            if status in counts:
                counts[status] += 1
    return counts


def _review_attention_note(group: dict) -> str:
    notes: list[str] = []
    if str(group.get("seal_label") or "") == "Invalid seal":
        notes.append("Invalid seal on this Requirement.")
    for claim in group.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        for line in claim.get("sentences") or []:
            text = str(line)
            if text and text != "The Claim is unchanged since the Check run.":
                notes.append(text)
        if str(claim.get("seal_label") or "") == "Invalid seal":
            notes.append(f"Invalid seal on claim {claim.get('id')}.")
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            detail = str(check.get("detail") or "")
            status = str(check.get("status") or "")
            if status == "fail":
                notes.append(detail or f"Check {check.get('check')} failed.")
            elif status == "skipped":
                notes.append(detail or f"Check {check.get('check')} was skipped.")
            for path in check.get("paths") or []:
                if isinstance(path, dict) and path.get("state") == "missing":
                    notes.append(
                        f"Path {path.get('path')} is missing in the working tree now."
                    )
    seen: set[str] = set()
    ordered: list[str] = []
    for note in notes:
        if note in seen:
            continue
        seen.add(note)
        ordered.append(note)
    return " ".join(ordered[:3])


def _seal_line(reading: dict) -> str:
    who = reading.get("who") or "—"
    when = reading.get("when") or "—"
    verified = "yes" if reading.get("verifiable") else "no"
    reason = str(reading.get("reason") or "")
    reason_html = f" {html.escape(reason)}" if reason else ""
    return (
        f" {html.escape(str(reading.get('what') or ''))}"
        f" who {html.escape(str(who))}"
        f" when {html.escape(str(when))}"
        f" verifiable {verified}"
        f" version {html.escape(str(reading.get('version') or ''))}"
        f"{reason_html}"
    )


def _review_file_dialog(door: dict) -> str:
    view = door.get("file_view")
    if not isinstance(view, dict):
        return ""
    rel = str(view.get("path") or "")
    state = str(view.get("state") or "")
    repo = quote(str(door.get("repo_id") or ""), safe="")
    selected_result = quote(str(door.get("selected_result") or ""), safe="")
    selected_report = quote(str(door.get("selected_report") or ""), safe="")
    document = f"report={selected_report}" if selected_report else f"result={selected_result}"
    groups = door.get("presentation", {}).get("groups") if isinstance(door.get("presentation"), dict) else []
    open_ids = [
        str(group.get("id") or "")
        for group in (groups or [])
        if isinstance(group, dict) and group.get("open")
    ]
    close_href = (
        f"/review?repo={repo}&{document}&expanded={quote(','.join(open_ids), safe='')}"
    )
    if state != "present":
        return (
            f'<div class="card" data-file-dialog="{html.escape(rel)}" '
            f'data-file-state="{html.escape(state)}">'
            f"<p>Path {html.escape(rel)} is {html.escape(state)}.</p>"
            f'<p><a href="{html.escape(close_href)}">Close file</a></p></div>'
        )
    return (
        f'<div class="card" data-file-dialog="{html.escape(rel)}" data-file-state="present">'
        f"<p>{html.escape(rel)}</p>"
        f"<p class=\"muted\">This is the file in the working tree now.</p>"
        f"<pre>{html.escape(str(view.get('text') or ''))}</pre>"
        f'<p><a href="{html.escape(close_href)}">Close file</a></p></div>'
    )


def _review_actions(door: dict, report: dict | None, saved: bool, repo_id: str) -> str:
    if not repo_id or report is None:
        return ""
    rerun = f"""
<form method="post" action="/check">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="action" value="check">
<input type="hidden" name="return_to" value="/review">
<p class="actions"><button type="submit" data-leave="1">Re-run Checks</button></p>
</form>
"""
    back = (
        f'<p><a class="btn" data-leave="1" href="/claims?repo_id={quote(repo_id, safe="")}">'
        "Back to Claims</a></p>"
    )
    return (
        f'<div class="review-actions">{rerun}{_compile_form(door, report, saved, repo_id)}{back}</div>'
        f"{_leave_dialog()}{_unsaved_script()}"
    )


def _assessment_index(report: dict | None) -> dict:
    found = {}
    if not isinstance(report, dict):
        return found
    for item in report.get("assessments") or []:
        if isinstance(item, dict):
            found[assessment_identity(item)] = item
    return found


def _deviation_html(claim: dict, assessments: dict, editable: bool) -> str:
    blocks = []
    hint_from = str(claim.get("requirement_hint_from") or "")
    hint = str(claim.get("requirement_hint") or "")
    if hint_from == "unresolved":
        requirement_hint = (
            f"{_requirement_remedy({'requirement_hint_from': 'unresolved'})}"
        )
    elif hint:
        requirement_hint = (
            f"{_requirement_remedy({'requirement_hint_from': hint_from, 'requirement_hint': hint})}"
        )
    else:
        requirement_hint = ""
    for check in claim.get("checks") or []:
        if not isinstance(check, dict) or str(check.get("status") or "") not in {"fail", "skipped"}:
            continue
        detail = str(check.get("detail") or "")
        check_hint = str(check.get("remediation_hint") or "")
        check_hint_html = (
            f'<p data-check-remediation>{_remedy_icon("wrench", "Check remediation")} {html.escape(check_hint)}</p>'
            if check_hint
            else ""
        )
        identity = {
            "kind": "check",
            "claim_id": claim.get("id"),
            "claim_digest": claim.get("digest"),
            "index": check.get("index"),
        }
        blocks.append(
            "<section class=\"deviation\" "
            f'data-deviation="check" data-claim="{html.escape(str(claim.get("id") or ""))}" '
            f'data-index="{html.escape(str(check.get("index")))}">'
            f"<p>Check <code>{html.escape(str(check.get('check') or ''))}</code> "
            f"is {html.escape(str(check.get('status') or ''))}.</p>"
            f"<p data-detail>{html.escape(detail)}</p>"
            f"{check_hint_html}{requirement_hint}"
            f"{_assessment_controls(identity, claim, assessments, editable)}"
            "</section>"
        )
    if str(claim.get("binding") or "") in {"stale", "missing"}:
        identity = {
            "kind": "binding",
            "claim_id": claim.get("id"),
            "claim_digest": claim.get("digest"),
            "namespace": claim.get("namespace"),
            "pack_id": claim.get("pack_id"),
            "requirement_id": claim.get("recorded_requirement_id"),
            "requirement_digest": claim.get("requirement_digest"),
            "binding": claim.get("binding"),
        }
        blocks.append(
            "<section class=\"deviation\" "
            f'data-deviation="binding" data-claim="{html.escape(str(claim.get("id") or ""))}" '
            f'data-binding="{html.escape(str(claim.get("binding") or ""))}">'
            f"{_binding_remedy(str(claim.get('binding') or ''))}"
            f"{requirement_hint}"
            f"{_assessment_controls(identity, claim, assessments, editable)}"
            "</section>"
        )
    if not blocks:
        return ""
    paths = any(
        isinstance(check, dict) and check.get("paths")
        for check in claim.get("checks") or []
    )
    working_tree = (
        '<p class="muted">Evidence paths are the working tree now. They are not a recorded Check result.</p>'
        if paths
        else ""
    )
    return f'<div class="deviations">{working_tree}{"".join(blocks)}</div>'


def _assessment_controls(identity: dict, claim: dict, assessments: dict, editable: bool) -> str:
    saved = assessments.get(assessment_identity(identity))
    disposition = str(saved.get("disposition") or "") if isinstance(saved, dict) else ""
    text = str(saved.get("text") or "") if isinstance(saved, dict) else ""
    if not editable:
        if disposition == "accept":
            label = f"Accept deviation. {text}"
        elif disposition == "must_fix":
            label = f"Must be fixed. {text}"
        else:
            label = "Not assessed"
        carried = _assessment_hidden(identity, claim) + (
            f'<input type="hidden" name="assess_disposition" form="review-compile" data-assessment-field '
            f'value="{html.escape(disposition)}">'
            f'<input type="hidden" name="assess_text" form="review-compile" data-assessment-field '
            f'value="{html.escape(text)}">'
        )
        return (
            f'{carried}<p data-disposition="{html.escape(disposition or "not_assessed")}">'
            f"{html.escape(label)}</p>"
        )
    selected = {
        "": " selected" if disposition == "" else "",
        "accept": " selected" if disposition == "accept" else "",
        "must_fix": " selected" if disposition == "must_fix" else "",
    }
    fields = _assessment_hidden(identity, claim)
    return f"""
{fields}
<label>Assessment
<select name="assess_disposition" form="review-compile" data-assessment data-assessment-field>
<option value=""{selected[""]}>Not assessed</option>
<option value="accept"{selected["accept"]}>Accept deviation</option>
<option value="must_fix"{selected["must_fix"]}>Must be fixed</option>
</select>
</label>
<label>Justification or required correction
<textarea name="assess_text" form="review-compile" data-assessment data-assessment-field>{html.escape(text)}</textarea>
</label>
"""


def _assessment_hidden(identity: dict, claim: dict) -> str:
    kind = str(identity.get("kind") or "")
    values = {
        "assess_kind": kind,
        "assess_claim_id": str(identity.get("claim_id") or ""),
        "assess_claim_digest": str(identity.get("claim_digest") or claim.get("digest") or ""),
        "assess_index": "" if kind != "check" else str(identity.get("index")),
        "assess_namespace": str(identity.get("namespace") or ""),
        "assess_pack_id": str(identity.get("pack_id") or ""),
        "assess_requirement_id": str(identity.get("requirement_id") or ""),
        "assess_requirement_digest": str(identity.get("requirement_digest") or ""),
        "assess_binding": str(identity.get("binding") or ""),
    }
    return "".join(
        f'<input type="hidden" name="{name}" form="review-compile" data-assessment-field '
        f'value="{html.escape(value)}">'
        for name, value in values.items()
    )


def _unsaved_script() -> str:
    return """
<script>
(function() {
  function dirty() {
    return Array.prototype.some.call(document.querySelectorAll("[data-assessment]"), function(field) {
      return field.value !== (field.getAttribute("data-initial") || "");
    });
  }
  document.querySelectorAll("[data-assessment]").forEach(function(field) {
    field.setAttribute("data-initial", field.value);
  });
  var pendingHref = "";
  var pendingForm = null;
  var leaving = false;
  document.addEventListener("click", function(event) {
    if (!dirty() || leaving) return;
    var link = event.target.closest("a[href]");
    if (!link || link.getAttribute("data-resume") === "1") return;
    var href = link.getAttribute("href") || "";
    if (!href || href.charAt(0) === "#") return;
    event.preventDefault();
    event.stopPropagation();
    pendingHref = href;
    pendingForm = null;
    var dialog = document.getElementById("review-leave");
    if (dialog && dialog.showModal && !dialog.open) dialog.showModal();
  }, true);
  document.addEventListener("submit", function(event) {
    var form = event.target;
    if (!form || form.id === "review-compile" || form.hasAttribute("data-include-assessments")) return;
    if (!dirty() || leaving) return;
    event.preventDefault();
    pendingHref = "";
    pendingForm = form;
    var dialog = document.getElementById("review-leave");
    if (dialog && dialog.showModal && !dialog.open) dialog.showModal();
  }, true);
  window.addEventListener("beforeunload", function(event) {
    if (!dirty() || leaving) return;
    event.preventDefault();
    event.returnValue = "";
  });
  document.querySelectorAll("form[data-include-assessments]").forEach(function(form) {
    form.addEventListener("submit", function() {
      document.querySelectorAll("[data-assessment-field]").forEach(function(field) {
        var hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = field.name;
        hidden.value = field.value;
        form.appendChild(hidden);
      });
    });
  });
  document.addEventListener("DOMContentLoaded", function() {
  var compile = document.getElementById("review-compile");
  var retireDialog = document.getElementById("retire-confirm");
  if (compile && retireDialog) {
    compile.addEventListener("submit", function(event) {
      compile.removeAttribute("data-held");
      if (compile.getAttribute("data-retire-confirmed") === "1") return;
      var needsComment = {accept: true, must_fix: true, retire: true};
      var missing = null;
      document.querySelectorAll("select[name=assess_disposition]").forEach(function(field) {
        if (missing || !needsComment[field.value]) return;
        var dialog = document.getElementById(field.getAttribute("data-comment-dialog") || "");
        var text = dialog && dialog.querySelector("textarea");
        if (dialog && text && text.value.trim() === "") missing = dialog;
      });
      if (missing) {
        event.preventDefault();
        compile.setAttribute("data-held", "1");
        var note = missing.querySelector("[data-comment-demand]");
        if (note) note.hidden = false;
        if (missing.showModal && !missing.open) missing.showModal();
        var area = missing.querySelector("textarea");
        if (area) area.focus();
        return;
      }
      var byClaim = {};
      document.querySelectorAll("[name=assess_disposition]").forEach(function(field) {
        if (field.value !== "retire") return;
        var claim = field.getAttribute("data-claim-id") || "";
        var label = field.getAttribute("data-check-label") || "Check";
        if (!byClaim[claim]) byClaim[claim] = [];
        byClaim[claim].push(label);
      });
      var claims = Object.keys(byClaim);
      if (!claims.length) return;
      event.preventDefault();
      compile.setAttribute("data-held", "1");
      var list = document.getElementById("retire-list");
      list.replaceChildren();
      claims.forEach(function(claim) {
        var title = document.createElement("p");
        var code = document.createElement("code");
        code.textContent = claim;
        title.appendChild(code);
        var items = document.createElement("ul");
        byClaim[claim].forEach(function(label) {
          var line = document.createElement("li");
          line.textContent = label;
          items.appendChild(line);
        });
        list.appendChild(title);
        list.appendChild(items);
      });
      retireDialog.showModal();
    });
    document.getElementById("retire-cancel").addEventListener("click", function() {
      retireDialog.close();
    });
    document.getElementById("retire-continue").addEventListener("click", function() {
      var choice = document.createElement("input");
      choice.type = "hidden";
      choice.name = "remove_retired_checks";
      choice.value = document.getElementById("retire-remove").checked ? "true" : "false";
      compile.appendChild(choice);
      compile.setAttribute("data-retire-confirmed", "1");
      retireDialog.close();
      compile.requestSubmit();
    });
  }
  var leaveDialog = document.getElementById("review-leave");
  if (leaveDialog) {
    document.getElementById("review-leave-save").addEventListener("click", function() {
      var next = document.getElementById("review-next");
      if (next) next.value = pendingHref;
      leaving = true;
      if (compile) compile.requestSubmit();
      if (!compile || compile.getAttribute("data-held") === "1") {
        leaving = false;
        if (leaveDialog.open) leaveDialog.close();
      }
    });
    document.getElementById("review-leave-discard").addEventListener("click", function() {
      leaving = true;
      leaveDialog.close();
      if (pendingForm) pendingForm.submit();
      else if (pendingHref) window.location.href = pendingHref;
    });
    document.getElementById("review-leave-cancel").addEventListener("click", function() {
      pendingHref = "";
      pendingForm = null;
      leaveDialog.close();
    });
  }
  });
})();
</script>
"""


def _leave_dialog() -> str:
    return """
<dialog id="review-leave" class="review-choice">
<p>Save this review before leaving?</p>
<p>The Check result stays unchanged. Save writes an unsigned report.</p>
<p>
<button type="button" id="review-leave-save">Save</button>
<button type="button" id="review-leave-discard">Don't save</button>
<button type="button" id="review-leave-cancel">Cancel</button>
</p>
</dialog>
"""


def _started_review(door: dict) -> dict | None:
    """The newest report for this run, when that report is still unsigned."""
    if door.get("review_fresh") or str(door.get("selected_report") or ""):
        return None
    if not str(door.get("selected_result") or ""):
        return None
    rows = door.get("run_reports") or []
    if not rows or not isinstance(rows[0], dict) or rows[0].get("signed"):
        return None
    if not str(rows[0].get("path") or ""):
        return None
    return rows[0]


def _resume_dialog(door: dict) -> str:
    started = _started_review(door)
    if not started:
        return ""
    repo = quote(str(door.get("repo_id") or ""), safe="")
    result = quote(str(door.get("selected_result") or ""), safe="")
    report = quote(str(started.get("path") or ""), safe="")
    continue_href = f"/review?repo={repo}&report={report}"
    fresh_href = f"/review?repo={repo}&result={result}&fresh=1"
    cancel_href = f"/review?repo={repo}"
    return (
        '<dialog id="resume-review" class="review-choice">'
        "<p>A review of this Check run is already started.</p>"
        "<p>The Check result is unchanged. Continue the unsigned report, start over, or go back.</p>"
        "<p>"
        f'<a class="btn primary" data-resume="1" href="{html.escape(continue_href)}">Continue</a>'
        f'<a class="btn" data-resume="1" href="{html.escape(fresh_href)}">Start over</a>'
        f'<a class="btn" data-resume="1" href="{html.escape(cancel_href)}">Cancel</a>'
        "</p></dialog>"
        "<script>document.addEventListener('DOMContentLoaded',function(){"
        "var dialog=document.getElementById('resume-review');"
        "if(dialog&&dialog.showModal)dialog.showModal();"
        "});</script>"
    )


def _retire_dialog() -> str:
    return """
<dialog id="retire-confirm">
<p>These Checks will be retired.</p>
<div id="retire-list"></div>
<p>Their original results and retirement justifications will remain in the report.</p>
<p>Claim files will only be changed after the report is signed.</p>
<label><input id="retire-remove" type="checkbox"> Remove retired Checks from Claims when signing the report.</label>
<p>
<button type="button" id="retire-cancel">Cancel</button>
<button type="button" id="retire-continue">Continue</button>
</p>
</dialog>
"""


def _compile_form(door: dict, report: dict | None, saved: bool, repo_id: str) -> str:
    if not repo_id:
        return ""
    signed = bool(report) and isinstance(report.get("signed"), dict)
    result_path = str(door.get("selected_result") or "") or str(door.get("source_result") or "")
    preview = report is not None and not saved and not str(door.get("selected_report") or "")
    if not result_path and not preview:
        return ""
    note = ""
    if saved and signed:
        note = (
            "<p class=\"muted\">This writes a new unsigned report from the same Check run. "
            "The signed report stays unchanged.</p>"
        )
    report_input = ""
    report_value = str(door.get("report_path") or "")
    if report_value and not signed:
        report_input = f'<input type="hidden" name="report" value="{html.escape(report_value)}">'
    return f"""
<form id="review-compile" method="post" action="/review/compile">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
<input type="hidden" name="result" value="{html.escape(result_path)}">
<input type="hidden" name="next" id="review-next" value="">
{report_input}
{note}
<p class="actions"><button type="submit">Create New Report</button></p>
</form>
"""


def _unchosen_run(door: dict) -> str:
    latest = str(door.get("latest_result") or "")
    repo = str(door.get("repo_id") or "")
    check = '<a href="/check">Check</a>'
    if not latest or not repo:
        return (
            "<p>No previous Check result has been chosen. "
            f"To start a review, go to the {check} tab and select a result to review.</p>"
        )
    name = Path(latest).name
    href = f"/review?repo={quote(repo, safe='')}&result={quote(latest, safe='')}"
    return (
        "<p>No previous Check result has been chosen. "
        f"To start a review, go to the {check} tab and select a result to review, "
        f'or <a href="{html.escape(href)}">review the latest Check result '
        f"<code>{html.escape(name)}</code></a>.</p>"
    )


def _review_intro(door: dict, report: dict | None) -> str:
    return ""


def _run_file_name(door: dict, saved: bool) -> str:
    path = str(door.get("source_result") or "") if saved else str(door.get("selected_result") or "")
    return Path(path).name if path else ""


def _current_run_card(door: dict, report: dict | None, saved: bool, summary: str = "") -> str:
    if report is None:
        return ""
    return (
        '<p data-selected="run"><button type="button" class="link" id="run-detail-open">'
        "Technical details</button></p>"
        f"{summary}"
    )


def _run_detail_dialog(
    door: dict,
    report: dict | None,
    saved: bool,
    *,
    body: str,
) -> str:
    if report is None:
        return ""
    name = _run_file_name(door, saved)
    title = f"Check run <code>{html.escape(name)}</code>" if name else "Check run"
    return f"""
<dialog id="run-detail" class="run-detail">
  <div class="head">
    <h2>{title}</h2>
    <button type="button" class="secondary" data-close>Close</button>
  </div>
  <div class="body">
    {body}
  </div>
</dialog>
<script>
(function() {{
  var open = document.getElementById("run-detail-open");
  var dialog = document.getElementById("run-detail");
  if (!open || !dialog) return;
  open.addEventListener("click", function() {{ dialog.showModal(); }});
  dialog.querySelectorAll("[data-close]").forEach(function(button) {{
    button.addEventListener("click", function() {{ dialog.close(); }});
  }});
}})();
</script>
"""


def _review_empty(door: dict) -> str:
    if str(door.get("selected_result") or "") or str(door.get("selected_report") or ""):
        return ""
    notice = str(door.get("results_notice") or "")
    if not notice:
        return ""
    return f"<p>{html.escape(notice)}</p>"


def _passage_html(passages: list) -> str:
    parts = []
    for passage in passages:
        if not isinstance(passage, dict):
            continue
        text = str(passage.get("law_text") or "")
        if not text:
            continue
        locator = str(passage.get("locator") or "")
        label = f"{html.escape(locator)} " if locator else ""
        parts.append(
            f'<p class="requirement-text" data-law-text="{html.escape(text)}">'
            f"{label}{html.escape(text)}</p>"
        )
    return "".join(parts)


def _binding_html(binding: str) -> str:
    if binding not in {"match", "stale", "missing"}:
        return ""
    gloss = {
        "match": "The Requirement is the version the Claim recorded.",
        "stale": "The Requirement changed after the Claim was bound.",
        "missing": "The Requirement named by the Claim was not loaded for this run.",
    }[binding]
    return (
        f' <span class="fact">Requirement binding '
        f'<span data-binding="{html.escape(binding)}">{html.escape(binding)}</span></span>'
        f' <span class="muted">{html.escape(gloss)}</span>'
    )


def _discovery_ready(discovery: dict) -> bool:
    return all(str(discovery.get(key) or "") for key in ("repo_id", "source_id", "timestamp"))


def _discover_home(door: dict) -> str:
    repo = quote(str(door.get("repo_id") or ""), safe="")
    if repo:
        return f"/discover?repo={repo}"
    return "/discover"


def _claims_href(discovery: dict) -> str:
    parts = []
    for key in ("repo_id", "source_id", "timestamp"):
        value = str(discovery.get(key) or "")
        if value:
            parts.append(f"{key}={quote(value)}")
    if not parts:
        return "/claims"
    return "/claims?" + "&".join(parts)


def _review_claim_row(row: dict, claim: dict, claims_href: str, discover_href: str = "") -> str:
    claim_id = str(row.get("id") or "")
    status = str(row.get("status") or "")
    checks = _review_checks(row)
    if status not in {"fail", "skipped"} or not claim:
        return (
            f'<li data-claim="{html.escape(claim_id)}" data-status="{html.escape(status)}">'
            f"<code>{html.escape(claim_id)}</code> {html.escape(status)} "
            f"<ul>{checks}</ul>"
            f'<p><a href="{html.escape(claims_href)}">Open the Claim</a></p></li>'
        )
    requirement_id = str(claim.get("requirement_id") or "")
    args = claim.get("args") if isinstance(claim.get("args"), dict) else {}
    source_path = str(args.get("path") or "")
    button = ""
    if requirement_id and discover_href:
        button = f'<a class="discover-again" href="{html.escape(discover_href)}">Re-Discover</a>'
    elif requirement_id:
        button = (
            f'<button type="button" class="discover-again" data-dialog="{html.escape(_dialog_id(claim_id))}">'
            "Re-Discover</button>"
        )
    return (
        f'<li class="review-failed" data-claim="{html.escape(claim_id)}" '
        f'data-status="{html.escape(status)}" data-requirement="{html.escape(requirement_id)}">'
        f"<code>{html.escape(claim_id)}</code> {html.escape(status)}"
        f"<p>Requirement <code>{html.escape(requirement_id)}</code></p>"
        f"<p>Source path <code>{html.escape(source_path)}</code></p>"
        f"<p class=\"muted\">Source args <code>{html.escape(json.dumps(args, ensure_ascii=False))}</code></p>"
        f"<ul>{checks}</ul>"
        f"{button}"
        f'<p><a href="{html.escape(claims_href)}">Open the Claim</a></p></li>'
    )


def _review_checks(row: dict) -> str:
    parts = []
    for item in row.get("checks") or []:
        if not isinstance(item, dict):
            continue
        detail = str(item.get("detail") or "")
        detail_html = f" — {html.escape(detail)}" if detail else ""
        args = item.get("args") if isinstance(item.get("args"), dict) else {}
        parts.append(
            "<li "
            f'data-check="{html.escape(str(item.get("check") or ""))}" '
            f'data-status="{html.escape(str(item.get("status") or ""))}">'
            f"{html.escape(str(item.get('index')))}: {html.escape(check_caption(item))} "
            f"{html.escape(str(item.get('status') or ''))}{detail_html} "
            f"<code>{html.escape(json.dumps(args, ensure_ascii=False))}</code></li>"
        )
    return "".join(parts)


def _review_discover_dialog(row: dict, claim: dict, discovery: dict, *, return_to: str = "") -> str:
    if str(row.get("status") or "") not in {"fail", "skipped"}:
        return ""
    requirement_id = str(claim.get("requirement_id") or "")
    if not requirement_id:
        return ""
    claim_id = str(row.get("id") or "")
    repo_id = str(discovery.get("repo_id") or "")
    source_id = str(discovery.get("source_id") or "")
    timestamp = str(discovery.get("timestamp") or "")
    if repo_id and source_id and timestamp:
        src = (
            f"/discover/claims/{quote(requirement_id)}"
            f"?repo={quote(repo_id)}&source={quote(source_id)}&timestamp={quote(timestamp)}&from=review"
        )
        if return_to:
            src += f"&return_to={quote(return_to, safe='')}"
        frame = (
            f'<iframe title="Discovery for {html.escape(requirement_id)}" src="{html.escape(src)}"></iframe>'
        )
    else:
        frame = (
            "<p class=\"muted\">Choose the repository, source, and working copy on Discover "
            "before this popup can open that Requirement.</p>"
        )
    return f"""
<dialog id="{html.escape(_dialog_id(claim_id))}" class="review-discover" data-requirement="{html.escape(requirement_id)}">
  <div class="head">
    <h2>Re-Discover — <code>{html.escape(requirement_id)}</code></h2>
    <button type="button" class="secondary" data-close>Close</button>
  </div>
  <div class="body">
    <p>Find equivalent evidence for this Requirement and configure suitable Checks. Closing this leaves the failed Claim and its Checks unchanged.</p>
    {frame}
  </div>
</dialog>
"""


def _review_discover_script(enabled: bool) -> str:
    if not enabled:
        return ""
    return """
<script>
document.querySelectorAll("button.discover-again").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = document.getElementById(button.dataset.dialog);
    if (dialog && dialog.showModal) dialog.showModal();
  });
});
document.querySelectorAll("dialog.review-discover [data-close]").forEach((button) => {
  button.addEventListener("click", () => {
    const dialog = button.closest("dialog");
    if (dialog) dialog.close();
  });
});
</script>
"""


def _review_return_url(door: dict) -> str:
    repo = quote(str(door.get("repo_id") or ""), safe="")
    selected_result = quote(str(door.get("selected_result") or ""), safe="")
    selected_report = quote(str(door.get("selected_report") or ""), safe="")
    if not repo or (not selected_result and not selected_report):
        return ""
    document = f"report={selected_report}" if selected_report else f"result={selected_result}"
    groups = door.get("presentation", {}).get("groups") if isinstance(door.get("presentation"), dict) else []
    open_ids = [
        str(group.get("id") or "")
        for group in (groups or [])
        if isinstance(group, dict) and group.get("open")
    ]
    return f"/review?repo={repo}&{document}&expanded={quote(','.join(open_ids), safe='')}"


def _dialog_id(claim_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", claim_id).strip("-") or "claim"
    return f"review-discover-{slug}"
