"""The readable remediation report. The signed JSON is rendered to Markdown, and the PDF is rendered from that Markdown."""

from __future__ import annotations

import html


def remedy_markdown(account: dict) -> str:
    """One Markdown document. A later PDF reads this text and does not rebuild it."""
    reference = account["reference"]
    signed = account["signed_name"] or "Not recorded"
    when = account["signed_at"]
    signed_by = f"{signed} · {when}" if when else signed
    lines = [
        "# Remediation report",
        "",
        "CURBPACK STUDIO / REMEDIATION REPORT",
        "",
        "## Remediation summary",
        "",
        account["outcome"],
        "",
        _table(
            ["Original", "Remediated", "Remaining", "Retired", "New deviations"],
            [[
                account["original"],
                account["remediated"],
                account["remaining"],
                account["retired"],
                account["outside_new"] if account["full_check_ran"] else "—",
            ]],
        ),
        "",
        "Remediated means a Check became green. It does not change the signed Review.",
        "",
        "## Scope and reference",
        "",
        f"Check run: {reference['run'] or 'Not recorded in the signed remediation.'}",
        "",
        _review_line(reference),
        "",
        f"Remediation signed by: {signed_by}",
        "",
        "## Remediation results",
        "",
        "One row for each deviation in the original Check. The recommendation is the performer's record.",
        "",
    ]
    if account["rows"]:
        lines.append(_table(
            ["Claim", "Check", "What was done", "Now", "Recommendation"],
            [[row["claim_id"], row["check"], row["action"], row["result"], row["recommendation"]] for row in account["rows"]],
        ))
    else:
        lines.append("No original deviations were recorded.")
    lines.extend(["", "## Outstanding deviations", ""])
    if account["outstanding"]:
        lines.append(_table(
            ["Claim", "Check", "Comment", "What remains"],
            [[row["claim_id"], row["check"], row["comment"] or "No comment.", row["action"]] for row in account["outstanding"]],
        ))
    else:
        lines.append("No original deviation is still open.")
    lines.extend([
        "",
        "## New deviations outside the original scope",
        "",
        "OK means the deviation was recorded. It does not approve it.",
        "",
    ])
    if not account["full_check_ran"]:
        lines.append("A full Check was not run.")
    elif account["outside"]:
        lines.append(_table(
            ["Full Check", "Claim", "Check"],
            [[row["run"], row["claim_id"], row["check"]] for row in account["outside"]],
        ))
    else:
        lines.append("The full Check found no new deviations outside the original scope.")
    lines.extend([
        "",
        "## Retired Checks",
        "",
        "Retired means the Check was taken out of the remediation. It was not fixed.",
        "",
    ])
    if account["retired_rows"]:
        lines.append(_table(
            ["Claim", "Check", "Why"],
            [[row["claim_id"], row["check"], row["action"]] for row in account["retired_rows"]],
        ))
    else:
        lines.append("No Check was retired.")
    lines.extend(["", "## Verification and history", ""])
    if account["full_check_ran"]:
        lines.append("A full Check was run.")
    else:
        lines.append("No full Check is recorded on this signed remediation.")
    lines.append("")
    history = [
        [row["claim_id"], row["check"], line]
        for row in account["rows"]
        for line in row["history"]
    ]
    if history:
        lines.append(_table(["Claim", "Check", "History"], history))
    else:
        lines.append("No remediation history was recorded on the original deviations.")
    lines.extend([
        "",
        "## Notes and sign-off",
        "",
        account["notes"] or "No closing note was recorded.",
        "",
        f"Signed by: {signed}",
        "",
        f"Signed at: {when or 'time not recorded'}",
        "",
        "This PDF is a reading of the signed JSON. The signature covers the JSON, not these PDF bytes.",
        "",
        "## Appendix. Deviations at sign-off",
        "",
        "These are the deviations present when the remediation was signed.",
        "",
    ])
    present = [
        [row["claim_id"], row["check"], row["comment"] or "No comment."]
        for row in account["outstanding"]
    ]
    if account["full_check_ran"]:
        present.extend(
            [row["claim_id"], row["check"], "Recorded outside the original work."]
            for row in account["outside"]
        )
    if present:
        lines.append(_table(["Claim", "Check", "Comment"], present))
    else:
        lines.append("No deviations were present.")
    if not account["full_check_ran"]:
        lines.extend(["", "A full Check was not run, so deviations outside the original work are not listed."])
    lines.append("")
    return "\n".join(lines)


def _review_line(reference: dict) -> str:
    review = reference.get("review") or "Not recorded in the signed remediation."
    reviewer = reference.get("reviewer") or ""
    reviewed_at = reference.get("reviewed_at") or ""
    if reviewer and reviewed_at:
        return f"Signed Review: {review}. Signed by {reviewer} at {reviewed_at}."
    if reviewer:
        return f"Signed Review: {review}. Signed by {reviewer}."
    return f"Signed Review: {review}"


def parse_remedy_markdown(text: str) -> list[tuple]:
    """Headings, paragraphs, and tables. This is the only reading of the Markdown file."""
    blocks: list[tuple] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
            index += 1
        elif line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
            index += 1
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].startswith("|"):
                cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                if not _rule_row(cells):
                    rows.append(cells)
                index += 1
            if rows:
                blocks.append(("table", rows[0], rows[1:]))
        elif line.strip():
            blocks.append(("p", line.strip()))
            index += 1
        else:
            index += 1
    return blocks


def remedy_markdown_html(text: str) -> str:
    """The Markdown report as a page, escaped. It is not a second authoring of the report."""
    parts = ['<article class="remedy-reading">']
    for kind, *rest in parse_remedy_markdown(text):
        if kind == "h1":
            parts.append(f"<h1>{html.escape(rest[0])}</h1>")
        elif kind == "h2":
            parts.append(f"<h2>{html.escape(rest[0])}</h2>")
        elif kind == "p":
            parts.append(f"<p>{html.escape(rest[0])}</p>")
        else:
            headers, rows = rest
            head = "".join(f"<th>{html.escape(cell)}</th>" for cell in headers)
            body = "".join(
                "<tr>" + "".join(f"<td>{html.escape(cell)}</td>" for cell in row) + "</tr>"
                for row in rows
            )
            parts.append(f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>")
    parts.append("</article>")
    return "".join(parts)


def _table(headers: list[str], rows: list[list[object]]) -> str:
    width = len(headers)
    lines = [
        "| " + " | ".join(_cell(cell) for cell in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = list(row) + [""] * (width - len(row))
        lines.append("| " + " | ".join(_cell(cell) for cell in cells[:width]) + " |")
    return "\n".join(lines)


def _cell(value: object) -> str:
    return " ".join(str(value).replace("|", "/").split())


def _rule_row(cells: list[str]) -> bool:
    return bool(cells) and all(cell and set(cell) <= set("-: ") for cell in cells)
