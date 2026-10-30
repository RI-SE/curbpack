"""HTML for a curbcheck run-result / review-report board.

Takes a presentation dict (from review.present) plus link context. No Studio door
chrome, no claim editing, no Discovery. Callers pass repo id and selected
result/report paths so expand/file/edit links stay on the Review routes.
"""

from __future__ import annotations

import html
import json
from urllib.parse import quote


def render_review_board(presentation: dict, *, repo_id: str, selected_result: str = "", selected_report: str = "") -> str:
    """Render the Requirement/Claim board for one run result or compiled report."""
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
    )
    groups = [group for group in presentation.get("groups") or [] if isinstance(group, dict)]
    open_ids = [str(group.get("id") or "") for group in groups if group.get("open")]
    open_count = len(open_ids)
    total = len(groups)
    fail_open = sum(
        1 for group in groups if group.get("open") and "fail" in str(group.get("result_summary") or "")
    )
    topline = (
        f'<div class="card topline">'
        f'<p style="margin:0">{open_count} of {total} requirements need attention. '
        f"{'Failed Checks remain visible for review. ' if fail_open else ''}"
        f"Passed Requirements stay collapsed. "
        f"Expand a row to inspect paths and Checks, then Edit or Re-Discover as needed.</p>"
        f'<p class="muted" style="margin:.65rem 0 0">'
        f"{open_count} open · {total - open_count} collapsed · "
        f"Compile writes the review report; decision and seal stay separate.</p>"
        f"</div>"
    )
    repo = quote(str(repo_id or ""), safe="")
    result = quote(str(selected_result or ""), safe="")
    report = quote(str(selected_report or ""), safe="")
    document = f"report={report}" if selected_report else f"result={result}"
    attention_parts = []
    collapsed_parts = []
    for group in groups:
        block = _requirement_card(group, open_ids, repo, document)
        if group.get("open"):
            attention_parts.append(block)
        else:
            collapsed_parts.append(block)
    attention = ""
    if attention_parts:
        attention = "<h2>Requirements needing attention</h2>" + "".join(attention_parts)
    collapsed = ""
    if collapsed_parts:
        collapsed = "<h2>Passed / unchanged</h2>" + "".join(collapsed_parts)
    return header_html + topline + attention + collapsed


def _requirement_card(group: dict, open_ids: list[str], repo: str, document: str) -> str:
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
        bad = ' class="pill pill-bad"' if label == "Invalid seal" else ' class="pill"'
        label_html = (
            f'<span{bad} data-seal-label="{html.escape(label)}">{html.escape(label)}</span>'
        )
    seal = _seal_line(group.get("seal")) if isinstance(group.get("seal"), dict) else ""
    counts = _check_counts(group)
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
        claim_header.append(f" claim {html.escape(claim_id)}{claim_label_html}{claim_facts}")
        req_for_claim = group_id if group_id != "Unresolved Claims" else str(claim.get("requirement_id") or "")
        claims_html.append(_claim_card(claim, open_ids, repo, document, req_for_claim))
    note = _attention_note(group)
    note_html = f'<p class="note">{html.escape(note)}</p>' if note else ""
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
        f"{note_html}{''.join(claims_html)}</details>"
    )


def _claim_card(
    claim: dict, open_ids: list[str], repo: str, document: str, requirement_id: str
) -> str:
    claim_id = str(claim.get("id") or "")
    status = str(claim.get("status") or "")
    klass = ' class="pill-bad"' if status == "fail" else ""
    unresolved = str(claim.get("requirement_id") or "")
    requirement_html = (
        f'<p class="muted">Unresolved requirement <code>{html.escape(unresolved)}</code></p>'
        if unresolved
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
    if unchanged and status not in {"fail", "skipped"} and not attention_sentences:
        unchanged_html = "<p>The Claim is unchanged since the Check run.</p>"
    elif unchanged:
        unchanged_html = '<p class="muted" hidden>The Claim is unchanged since the Check run.</p>'
    else:
        unchanged_html = ""
    path_rows, check_items, actions, tech_parts = _claim_checks(
        claim, open_ids, repo, document, requirement_id
    )
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
    return (
        f'<div class="card claim-card" data-claim="{html.escape(claim_id)}">'
        f'<div class="header" style="margin-bottom:.35rem">'
        f"<div><h3>Claim <code>{html.escape(claim_id)}</code></h3></div>"
        f'<div><span data-status="{html.escape(status)}"{klass}>{html.escape(status)}</span></div>'
        f"</div>"
        f"{requirement_html}{sentences}{unchanged_html}"
        f"{table}"
        f"{tech_block}"
        f'<ul class="review-check-list" aria-hidden="true">{"".join(check_items)}</ul>'
        f'<div class="actions">{"".join(actions)}</div>'
        f"</div>"
    )


def _claim_checks(
    claim: dict, open_ids: list[str], repo: str, document: str, requirement_id: str
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
        pill = _check_pill(check_name, check_status)
        path_cell, path_bits = _path_cell(check, open_ids, repo, document)
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
                f"/claims?repo_id={repo}&claim={quote(claim_id, safe='')}"
                f"&return_to={quote(return_to, safe='')}"
                f"#claim-{quote(claim_id, safe='')}"
            )
            if requirement_id and requirement_id != "Unresolved Claims":
                edit_href = (
                    f"/claims?repo_id={repo}&claim={quote(claim_id, safe='')}"
                    f"&requirement_id={quote(requirement_id, safe='')}"
                    f"&return_to={quote(return_to, safe='')}"
                    f"#claim-{quote(claim_id, safe='')}"
                )
            edit_html = (
                f'<a class="edit-review" data-edit-check="{html.escape(str(check.get("index")))}" '
                f'href="{html.escape(edit_href)}">Edit</a>'
            )
            if not action_edit_added:
                actions.append(
                    f'<a class="btn primary edit-review" data-edit-check="{html.escape(str(check.get("index")))}" '
                    f'href="{html.escape(edit_href)}">Edit</a>'
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
    if status in {"fail", "skipped"} and claim_id:
        actions.append(
            f'<button type="button" class="btn discover-again" '
            f'data-dialog="{html.escape(_dialog_id(claim_id))}">'
            f"Re-Discover</button>"
        )
    return path_rows, check_items, actions, tech_parts


def _path_cell(check: dict, open_ids: list[str], repo: str, document: str) -> tuple[str, list[str]]:
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
        visible.append('<span class="muted">—</span>')
    return " ".join(visible), path_bits


def _check_pill(name: str, status: str) -> str:
    kind = status if status in {"pass", "fail", "skipped"} else "fail"
    return (
        f'<span class="check {html.escape(kind)}">'
        f"{html.escape(name)} · {html.escape(status)}</span>"
    )


def _check_counts(group: dict) -> dict[str, int]:
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


def _attention_note(group: dict) -> str:
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
                        f"Path {path.get('path')} is missing; restore it or re-point the Check."
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


def _dialog_id(claim_id: str) -> str:
    safe = "".join(ch if ch.isalnum() else "-" for ch in claim_id)
    return f"review-discover-{safe}"
