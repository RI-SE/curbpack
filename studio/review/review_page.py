"""Review page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from app.pages import _flash, _reading, page, repo_config_panel
from checks.labels import check_caption, check_short_label
from studio.claim.researcher import check_editor_dialog, check_form_script, _check_editor_values
from review.compile import NO_CRA_FIELD, NOT_A_LEGAL_CONCLUSION, worktree_sentence
from review.present import UNCHANGED
from studio.compile.impl.report import assessment_identity


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
    run_facts = ""
    run_summary = ""
    run_preamble = ""
    signed_report = isinstance(report, dict) and isinstance(report.get("signed"), dict)
    if report is None:
        if str((door or {}).get("latest_result") or ""):
            body_report = "<p>Choose a Check run. Nothing is reviewed until you open one.</p>"
        else:
            body_report = "<p>No run result for a report.</p>"
    else:
        decision = report.get("decision") or ""
        result = report.get("run_result") if isinstance(report.get("run_result"), dict) else {}
        note = worktree_sentence(result)
        limits = "".join(
            f"<li>{html.escape(item)}</li>" for item in (NOT_A_LEGAL_CONCLUSION, NO_CRA_FIELD)
        )
        if same_run_value is True:
            same_html = '<p data-same-run="yes">same run: yes</p>'
        elif same_run_value is False:
            same_html = '<p data-same-run="no">same run: no. This saved report is an older run.</p>'
        else:
            same_html = ""
        unchecked_html = ""
        if unchecked:
            codes = ", ".join(f"<code>{html.escape(item)}</code>" for item in unchecked)
            unchecked_html = f"<p>These selected Requirements were not checked: {codes}</p>"
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
        reading_html = _reading(reading) if saved else "<p>not saved</p>"
        if door and door.get("presentation"):
            run_facts, run_summary, queue = _review_groups(
                door["presentation"],
                door,
                discover_href,
                assessments=_assessment_index(report),
                editable=not signed_report,
            )
            queue_html = queue + appendix_html
        else:
            run_facts = ""
            run_summary = ""
            queue_html = (
                f"<h2>Check results</h2><ul>{''.join(rows)}</ul>{appendix_html}"
                f"<pre>{html.escape(json.dumps(result, indent=2, ensure_ascii=False))}</pre>"
            )
        file_dialog = _review_file_dialog(door or {})
        run_preamble = f"""
{reading_html}
{same_html}
<p>{html.escape(note)}</p>
<ul>{limits}</ul>
{unchecked_html}
"""
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
    if saved and signed:
        decision_forms = f"""
<p data-decision>{html.escape(decision)}</p>
"""
    elif saved:
        decision_forms = f"""
<form method="post" action="/review" data-include-assessments>
{hidden}
<label>Decision</label>
<textarea name="decision">{html.escape(decision)}</textarea>
<button type="submit">Save decision</button>
</form>
<form method="post" action="/review/sign" data-include-assessments>
{hidden}
<label>Signer name</label>
<input type="text" name="name" placeholder="External Reviewer">
<button type="submit">review-sign</button>
</form>
"""
    else:
        decision_forms = (
            '<p class="muted">Save decision and review-sign need a report file.</p>'
        )
    if not repo_id and report is None:
        body_report = "<p>No repository is chosen.</p>"
        decision_forms = ""
    chrome = _review_report_line(door)
    if report is None:
        shown = f"<div class=\"card\">{body_report}</div>"
        detail = ""
    else:
        shown = body_report
        detail = _run_detail_dialog(
            door,
            report,
            saved,
            preamble=run_preamble,
            facts=run_facts,
            reports=_run_reports_card(door),
            banner=_selected_banner(door, report, saved),
            chrome=chrome,
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
{_review_start(door, report)}
{_current_run_card(door, report, saved, run_summary)}
{_review_empty(door)}
{_flash(message, error)}
{detail}
{shown}
{decision_forms}
{_review_actions(door, report, saved, repo_id)}
{dialogs}
</div>
"""
    return page("Review", body, banner=panel)


def _review_groups(
    presentation: dict,
    door: dict,
    discover_href: str = "",
    *,
    assessments: dict | None = None,
    editable: bool = False,
) -> tuple[str, str, str]:
    header = presentation.get("header") if isinstance(presentation.get("header"), dict) else {}
    packs = " ".join(
        f"{html.escape(str(pack.get('id') or ''))} {html.escape(str(pack.get('version') or ''))}"
        for pack in header.get("packs") or []
        if isinstance(pack, dict)
    )
    report_label = str(presentation.get("report_seal_label") or "")
    report_label_html = (
        f'<p data-report-seal="{html.escape(report_label)}">{html.escape(report_label)}</p>'
        if report_label
        else ""
    )
    header_html = (
        '<section class="card" data-run-header>'
        f"<p>{html.escape(str(header.get('tool') or ''))} {html.escape(str(header.get('tool_version') or ''))}</p>"
        f"<p>commit {html.escape(str(header.get('commit') or ''))}</p>"
        f"<p>worktree {html.escape(str(header.get('worktree') or ''))}</p>"
        f"<p>{packs}</p>"
        f"{report_label_html}"
        "</section>"
        f"{_secondary_details(presentation)}"
    )
    queue = _review_queue(
        presentation, door, discover_href, assessments or {}, editable
    )
    return header_html, "", queue


def _review_queue(
    presentation: dict,
    door: dict,
    discover_href: str,
    assessments: dict,
    editable: bool,
) -> str:
    """Attention queue. Passing Claims stay out of the table."""
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
            if deviations:
                queued.append((claim, deviations))
            else:
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
            if passes:
                claim_rows.append(("passes", passes))
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
                        f"{_file_cell(claim, open_ids, repo, document, discover_href)}</td>"
                    )
                if kind == "passes":
                    cells.append(
                        "<td>"
                        + " ".join(
                            _check_span(claim, check, dialog_id)
                            for check in payload
                            if isinstance(check, dict)
                        )
                        + "</td><td></td><td></td><td></td>"
                    )
                elif kind == "requirement":
                    cells.append(f"<td></td><td>{payload}</td><td></td><td></td>")
                else:
                    deviation = payload if isinstance(payload, dict) else {}
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
            '<th class="tips" title="Wrench: tip from the Claim. '
            'Scroll: tip from the Requirement.">Tips</th>'
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


def _file_cell(
    claim: dict, open_ids: list[str], repo: str, document: str, discover_href: str
) -> str:
    claim_id = str(claim.get("id") or "")
    links = []
    seen = set()
    edit_href = _claim_edit_href(claim, open_ids, repo, document)
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
    if str(claim.get("binding") or "") in {"stale", "missing"} and edit_href:
        extras.append(f'<a data-leave="1" href="{html.escape(edit_href)}">Rebind</a>')
    status = str(claim.get("status") or "")
    if status in {"fail", "skipped"} and claim_id:
        if discover_href:
            extras.append(
                f'<a class="discover-again" data-leave="1" href="{html.escape(discover_href)}">Re-Discover</a>'
            )
        else:
            extras.append(
                f'<button type="button" class="link discover-again" '
                f'data-dialog="{html.escape(_dialog_id(claim_id))}">Re-Discover</button>'
            )
    extra = f'<div class="file-actions">{"".join(extras)}</div>' if extras else ""
    return "".join(links) + extra


def _claim_edit_href(claim: dict, open_ids: list[str], repo: str, document: str) -> str:
    claim_id = str(claim.get("id") or "")
    if not claim_id or not repo:
        return ""
    for check in claim.get("checks") or []:
        if isinstance(check, dict) and str(check.get("edit") or "") == "ok":
            return_to = (
                f"/review?repo={repo}&{document}"
                f"&expanded={quote(','.join(open_ids), safe='')}"
            )
            return (
                f"/claims?repo_id={repo}&return_to={quote(return_to, safe='')}"
                f"#claim-{quote(claim_id, safe='')}"
            )
    return ""


def _passing_checks(claim: dict) -> list[dict]:
    return [
        check
        for check in claim.get("checks") or []
        if isinstance(check, dict) and str(check.get("status") or "") == "pass"
    ]


def _claim_row_count(claim: dict, deviations: list[dict]) -> int:
    return (
        len(deviations)
        + (1 if _passing_checks(claim) else 0)
        + (1 if _requirement_remedy(claim) else 0)
    )


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
            pills.append(
                f'<span class="check fail" data-binding="{html.escape(binding)}">'
                f"Binding {html.escape(binding)}</span>"
            )
    return " ".join(pills)


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


def _secondary_details(presentation: dict) -> str:
    """Seal readings and Check arguments stay out of the queue."""
    seals = []
    arguments = []
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
                seals.append(f'<p class="muted">{chain}</p>')
            claim_label = str(claim.get("seal_label") or "")
            claim_seal = claim.get("seal") if isinstance(claim.get("seal"), dict) else None
            if claim_label or claim_seal:
                line = _seal_line(claim_seal) if claim_seal else ""
                seals.append(
                    f'<p data-claim-seal="{html.escape(claim_label)}">'
                    f"{html.escape(str(claim.get('id') or ''))}{line}</p>"
                )
            for check in claim.get("checks") or []:
                if not isinstance(check, dict):
                    continue
                args = check.get("args") if isinstance(check.get("args"), dict) else {}
                if not args:
                    continue
                arguments.append(
                    '<details class="technical"><summary>Technical details</summary>'
                    f"<code>{html.escape(json.dumps(args, ensure_ascii=False))}</code></details>"
                )
    body = "".join(seals) + "".join(arguments)
    if not body:
        return ""
    return f'<section data-secondary>{body}</section>'


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
        remedy = f'<p data-detail>{html.escape(detail)}</p>' if detail else ""
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
    verdict, comment, dialog = _verdict_controls(
        identity, claim, assessments, editable, dialog_id
    )
    return remedy, verdict, comment, dialog


def _binding_remedy(binding: str) -> str:
    if binding == "stale":
        text = "The Requirement has changed since this Claim was bound to it."
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
    if hint_from == "unresolved":
        return (
            '<p data-requirement-remediation data-hint-from="unresolved">'
            f'{_remedy_icon("info", "Requirement remediation")} Unavailable for this run.</p>'
        )
    if not hint:
        return ""
    return (
        f'<p data-requirement-remediation data-hint-from="{html.escape(hint_from)}">'
        f'{_remedy_icon("scroll", "Requirement remediation")} {html.escape(hint)}</p>'
    )


def _icon_svg(body: str, *, label: str = "", css: str) -> str:
    named = (
        f' role="img" aria-label="{html.escape(label)}" title="{html.escape(label)}"'
        if label
        else ' aria-hidden="true"'
    )
    return (
        f'<svg class="{css}" viewBox="0 0 24 24" width="16" height="16" fill="none" '
        f'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
        f"{named}>{body}</svg>"
    )


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
        "info": (
            '<circle cx="12" cy="12" r="10"/>'
            '<path d="M12 16v-4"/>'
            '<path d="M12 8h.01"/>'
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
    identity: dict, claim: dict, assessments: dict, editable: bool, dialog_id: str
) -> tuple[str, str, str]:
    saved = assessments.get(assessment_identity(identity))
    disposition = str(saved.get("disposition") or "") if isinstance(saved, dict) else ""
    text = str(saved.get("text") or "") if isinstance(saved, dict) else ""
    hidden = _assessment_hidden(identity, claim)
    if not editable:
        if disposition == "accept":
            label = "Accept"
        elif disposition == "must_fix":
            label = "Must be fixed"
        else:
            label = "Not assessed"
        carried = hidden + (
            f'<input type="hidden" name="assess_disposition" form="review-compile" data-assessment-field '
            f'value="{html.escape(disposition)}">'
            f'<input type="hidden" name="assess_text" form="review-compile" data-assessment-field '
            f'value="{html.escape(text)}">'
        )
        verdict = (
            f'{carried}<span data-disposition="{html.escape(disposition or "not_assessed")}">'
            f"{html.escape(label)}</span>"
        )
    else:
        selected = {
            "": " selected" if disposition == "" else "",
            "accept": " selected" if disposition == "accept" else "",
            "must_fix": " selected" if disposition == "must_fix" else "",
        }
        verdict = f"""
{hidden}
<select class="verdict" name="assess_disposition" form="review-compile" data-assessment data-assessment-field>
<option value=""{selected[""]}>Not assessed</option>
<option value="accept"{selected["accept"]}>Accept</option>
<option value="must_fix"{selected["must_fix"]}>Must be fixed</option>
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
  document.querySelectorAll("[data-comment-for]").forEach(function(button) {{
    button.addEventListener("click", function() {{
      var dialog = document.getElementById(button.getAttribute("data-comment-for"));
      if (dialog && dialog.showModal) dialog.showModal();
    }});
  }});
  document.querySelectorAll("[data-close-comment]").forEach(function(button) {{
    button.addEventListener("click", function() {{
      var dialog = button.closest("dialog");
      if (!dialog) return;
      var opener = document.querySelector('[data-comment-for="' + dialog.id + '"]');
      if (opener) refresh(opener);
      dialog.close();
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
    parts = []
    for attr, key in (
        ("data-requirement-location", "requirement_location"),
        ("data-requirement-commit", "requirement_commit"),
        ("data-recorded-digest", "recorded_digest"),
        ("data-current-digest", "current_digest"),
        ("data-signature-method", "signature_method"),
        ("data-signature-status", "signature_status"),
        ("data-claim-location", "claim_location"),
        ("data-claim-commit", "claim_commit"),
        ("data-claim-recorded-digest", "claim_recorded_digest"),
        ("data-claim-recovered-digest", "claim_recovered_digest"),
        ("data-claim-current-digest", "claim_current_digest"),
        ("data-claim-signature-method", "claim_signature_method"),
        ("data-claim-signature-status", "claim_signature_status"),
        ("data-chain-binding", "chain_binding"),
    ):
        value = str(claim.get(key) or "")
        if not value:
            continue
        text = html.escape(value)
        parts.append(f'<span {attr}="{text}">{text}</span>')
    for item in claim.get("differences") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        if not name:
            continue
        historical = html.escape(str(item.get("historical") or ""))
        current = html.escape(str(item.get("current") or ""))
        parts.append(f'<span data-difference="{html.escape(name)}">{historical} {current}</span>')
    return "".join(parts)


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
    label = (
        f'{html.escape(check_short_label(entry))} · {html.escape(status)}'
    )
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
        f"{_unsaved_script()}"
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
  document.querySelectorAll("[data-leave]").forEach(function(node) {
    node.addEventListener("click", function(event) {
      if (dirty() && !window.confirm("Unsaved assessments will be lost.")) event.preventDefault();
    });
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
})();
</script>
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
{report_input}
{note}
<p class="actions"><button type="submit">Create New Report</button></p>
</form>
"""


def _review_start(door: dict, report: dict | None) -> str:
    if report is not None:
        return ""
    if str(door.get("selected_result") or "") or str(door.get("selected_report") or ""):
        return ""
    latest = str(door.get("latest_result") or "")
    repo = str(door.get("repo_id") or "")
    if not latest or not repo:
        return ""
    name = Path(latest).name
    href = f"/review?repo={quote(repo, safe='')}&result={quote(latest, safe='')}"
    return (
        '<div class="card" data-latest-run>'
        f"<p>Latest Check run <code>{html.escape(name)}</code>. "
        "Nothing is opened until you choose a Check run.</p>"
        f'<p><a class="btn primary" href="{html.escape(href)}">Review the latest run</a></p>'
        "</div>"
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
    preamble: str,
    facts: str,
    reports: str,
    banner: str,
    chrome: str,
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
    <p>This is the Check result under review. A new report copies this run and does not change it.</p>
    {banner}
    {reports}
    {chrome}
    {preamble}
    {facts}
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


def _run_reports_card(door: dict) -> str:
    if not (str(door.get("selected_result") or "") or str(door.get("selected_report") or "")):
        return ""
    repo = quote(str(door.get("repo_id") or ""), safe="")
    items = []
    for entry in door.get("run_reports") or []:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "")
        path = str(entry.get("path") or "")
        href = f"/review?repo={repo}&report={quote(path, safe='')}" if repo and path else ""
        label = html.escape(name)
        if href:
            label = f'<a href="{html.escape(href)}">{label}</a>'
        decision = str(entry.get("decision") or "").strip() or "No decision yet."
        if entry.get("signed"):
            signer = str(entry.get("signer") or "").strip()
            state = f"Signed by {signer}" if signer else "Signed"
            marker = "signed"
        else:
            state = "Unsigned"
            marker = "draft"
        items.append(
            "<li>"
            f"{label}"
            f"<p>{html.escape(decision)}</p>"
            f'<p data-report-state="{marker}">{html.escape(state)}</p>'
            "</li>"
        )
    if not items:
        body = "<p>No report for this run yet.</p>"
    else:
        body = "<ul>" + "".join(items) + "</ul>"
    return f'<div class="card" data-run-reports><h2>Reports for this run</h2>{body}</div>'


def _review_empty(door: dict) -> str:
    if str(door.get("selected_result") or "") or str(door.get("selected_report") or ""):
        return ""
    notice = str(door.get("results_notice") or "")
    if not notice:
        return ""
    return f"<p>{html.escape(notice)}</p>"


def _selected_banner(door: dict, report: dict | None, saved: bool) -> str:
    if report is None or not saved:
        return ""
    path = str(door.get("report_path") or door.get("selected_report") or "")
    if not path:
        return ""
    name = Path(path).name
    if isinstance(report.get("signed"), dict):
        return (
            f'<p data-selected="report" data-report-state="signed">Signed review report '
            f"<code>{html.escape(name)}</code>. This file is read-only. "
            "A new decision needs a new report.</p>"
        )
    return (
        f'<p data-selected="report" data-report-state="draft">Unsigned draft '
        f"<code>{html.escape(name)}</code>. The review decision can be edited. "
        "Signing locks this file.</p>"
    )


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


def _review_report_line(door: dict) -> str:
    if not str(door.get("repo_id") or "") or not door.get("report_path"):
        return ""
    return f"<p>Review report <code>{html.escape(str(door.get('report_path') or ''))}</code></p>"


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
