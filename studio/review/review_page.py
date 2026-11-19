"""Review page HTML. Renders the values it is given and does not decide them."""

from __future__ import annotations

import html
import json
import re
from urllib.parse import quote

from app.pages import _flash, _reading, page, repo_config_panel
from checks.labels import check_caption
from review.compile import NO_CRA_FIELD, NOT_A_LEGAL_CONCLUSION, worktree_sentence


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
    if report is None:
        body_report = "<p>No run result to compile.</p>"
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
        rows = []
        dialog_parts = []
        review_return = _review_return_url(door or {})
        for row in result.get("claims") or []:
            if not isinstance(row, dict):
                continue
            claim = claims_by_id.get(row.get("id")) or {}
            rows.append(_review_claim_row(row, claim, claims_href))
            dialog = _review_discover_dialog(row, claim, discovery or {}, return_to=review_return)
            if dialog:
                dialog_parts.append(dialog)
        if door and isinstance(door.get("presentation"), dict) and not dialog_parts:
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
            listed = _review_groups(door["presentation"], door) + appendix_html
        else:
            listed = f"<h2>Check results</h2><ul>{''.join(rows)}</ul>{appendix_html}<pre>{html.escape(json.dumps(result, indent=2, ensure_ascii=False))}</pre>"
        file_dialog = _review_file_dialog(door or {})
        body_report = f"""
{reading_html}
{same_html}
<p>{html.escape(note)}</p>
<ul>{limits}</ul>
{unchecked_html}
{file_dialog}
{listed}
"""
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
    if saved:
        decision_forms = f"""
<form method="post" action="/review">
{hidden}
<label>Decision</label>
<textarea name="decision">{html.escape(decision)}</textarea>
<button type="submit">Save decision</button>
</form>
<form method="post" action="/review/sign">
{hidden}
<label>Signer name</label>
<input type="text" name="name" placeholder="External Reviewer">
<button type="submit">review-sign</button>
</form>
"""
    else:
        decision_forms = (
            '<p class="muted">Compile writes the report. Save decision and review-sign need that file.</p>'
        )
    compile_form = ""
    if repo_id:
        selected_result = str(door.get("selected_result") or "")
        result_input = ""
        if selected_result:
            result_input = (
                f'<input type="hidden" name="result" value="{html.escape(selected_result)}">'
            )
        compile_form = f"""
<form method="post" action="/review/compile">
<input type="hidden" name="repo_id" value="{html.escape(repo_id)}">
{result_input}
<p class="actions"><button type="submit">Compile</button></p>
</form>
"""
    if not repo_id and report is None:
        body_report = "<p>No repository is chosen.</p>"
        decision_forms = ""
        compile_form = ""
    chrome = _review_report_line(door)
    body = f"""
<div class="review-board">
<div class="brand">curbpack-review</div>
<div class="header">
<div>
<h1>Review</h1>
<p class="muted">The decision is the reviewer's words. There is no field for meeting CRA.</p>
</div>
</div>
{chrome}
{_review_lists(door)}
{_flash(message, error)}
<div class="card">{body_report}</div>
{compile_form}
<p><a href="/check">Run checks</a></p>
{decision_forms}
{dialogs}
</div>
"""
    return page("Review", body, banner=panel)


def _review_groups(presentation: dict, door: dict) -> str:
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
    fail_open = sum(1 for group in groups if group.get("open") and "fail" in str(group.get("result_summary") or ""))
    topline = (
        f'<div class="card topline">'
        f"<p style=\"margin:0\">{open_count} of {total} requirements need attention. "
        f"{'Failed Checks remain visible for review. ' if fail_open else ''}"
        f"Passed Requirements stay collapsed. "
        f"Expand a row to inspect paths and Checks, then Edit or Re-Discover as needed.</p>"
        f'<p class="muted" style="margin:.65rem 0 0">'
        f"{open_count} open · {total - open_count} collapsed · "
        f"Compile writes the review report; decision and seal stay separate.</p>"
        f"</div>"
    )
    repo = quote(str(door.get("repo_id") or ""), safe="")
    selected_result = quote(str(door.get("selected_result") or ""), safe="")
    selected_report = quote(str(door.get("selected_report") or ""), safe="")
    document = (
        f"report={selected_report}" if selected_report else f"result={selected_result}"
    )
    attention_parts = []
    collapsed_parts = []
    for group in groups:
        block = _review_requirement_card(group, open_ids, repo, document)
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


def _review_requirement_card(
    group: dict,
    open_ids: list[str],
    repo: str,
    document: str,
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
        status = str(claim.get("status") or "")
        klass = ' class="pill-bad"' if status == "fail" else ""
        claim_label = str(claim.get("seal_label") or "")
        claim_label_html = (
            f' <span class="pill" data-claim-seal="{html.escape(claim_label)}">'
            f"{html.escape(claim_label)}</span>"
            if claim_label
            else ""
        )
        claim_facts = _seal_line(claim.get("seal")) if isinstance(claim.get("seal"), dict) else ""
        binding = str(claim.get("binding") or "")
        binding_html = (
            f' <span data-binding="{html.escape(binding)}">{html.escape(binding)}</span>'
            if binding
            else ""
        )
        claim_header.append(
            f" claim {html.escape(claim_id)}{claim_label_html}{binding_html}{claim_facts}"
        )
        claims_html.append(
            _review_claim_card(claim, open_ids, repo, document)
        )
    note = _review_attention_note(group)
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


def _review_claim_card(claim: dict, open_ids: list[str], repo: str, document: str) -> str:
    claim_id = str(claim.get("id") or "")
    status = str(claim.get("status") or "")
    klass = ' class="pill-bad"' if status == "fail" else ""
    binding = str(claim.get("binding") or "")
    binding_html = (
        f'<span data-binding="{html.escape(binding)}">{html.escape(binding)}</span>'
        if binding
        else ""
    )
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
        claim, open_ids, repo, document
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
        f'<div><span data-status="{html.escape(status)}"{klass}>{html.escape(status)}</span>{binding_html}{_chain_html(claim)}</div>'
        f"</div>"
        f"{requirement_html}{sentences}{unchanged_html}"
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
    claim: dict, open_ids: list[str], repo: str, document: str
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
                f'<a class="edit-review" data-edit-check="{html.escape(str(check.get("index")))}" '
                f'href="{html.escape(edit_href)}">Edit</a>'
            )
            if not action_edit_added:
                actions.append(
                    f'<a class="btn primary edit-review" data-edit-check="{html.escape(str(check.get("index")))}" '
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
    if status in {"fail", "skipped"} and claim_id:
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


def _check_pill(name: str, status: str) -> str:
    kind = status if status in {"pass", "fail", "skipped"} else "fail"
    return (
        f'<span class="check {html.escape(kind)}">'
        f"{html.escape(name)} · {html.escape(status)}</span>"
    )


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
        f"<pre>{html.escape(str(view.get('text') or ''))}</pre>"
        f'<p><a href="{html.escape(close_href)}">Close file</a></p></div>'
    )


def _review_lists(door: dict) -> str:
    if not str(door.get("repo_id") or ""):
        return ""
    repo = quote(str(door.get("repo_id") or ""), safe="")

    def rows(entries: list, kind: str, label: str, key: str) -> str:
        parts = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            href = f"/review?repo={repo}&{key}={quote(str(entry.get('path') or ''), safe='')}"
            parts.append(
                f'<li data-kind="{kind}"><a href="{html.escape(href)}">'
                f"{html.escape(label)} {html.escape(str(entry.get('name') or ''))}</a></li>"
            )
        return "".join(parts)

    notice = str(door.get("results_notice") or "")
    notice_html = f"<p>{html.escape(notice)}</p>" if notice else ""
    return (
        "<h2>Run results</h2>"
        f'<ul data-list="run-results">{rows(door.get("run_results") or [], "run-result", "Run result", "result")}</ul>'
        f"{notice_html}"
        "<h2>Review reports</h2>"
        f'<ul data-list="review-reports">{rows(door.get("review_reports") or [], "review-report", "Review report", "report")}</ul>'
    )


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


def _review_claim_row(row: dict, claim: dict, claims_href: str) -> str:
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
    if requirement_id:
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
