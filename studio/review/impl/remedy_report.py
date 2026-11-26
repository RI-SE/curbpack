"""The readable account of one signed remediation. The PDF is a rendering of this."""

from __future__ import annotations

from pathlib import Path

from studio.review.impl.items import (
    binding_digest,
    check_digest,
    failing_checks,
    find_item,
    is_retired,
    remediation_comment,
)


def remedy_account(document: dict, run: dict | None) -> dict:
    """Counts, rows, and the appendix. Derived from the seal and the source Check."""
    items = [row for row in (document.get("items") or []) if isinstance(row, dict)]
    outside = [row for row in (document.get("outside") or []) if isinstance(row, dict)]
    reference = document.get("reference") if isinstance(document.get("reference"), dict) else {}
    full_checks = [name for name in (document.get("full_checks") or []) if isinstance(name, str) and name]
    signed = document.get("signed") if isinstance(document.get("signed"), dict) else {}
    rows = _original_rows(items, run if isinstance(run, dict) else {})
    remediated = [row for row in rows if row["result"] == "pass"]
    retired = [row for row in rows if row["result"] == "retired"]
    remaining = [row for row in rows if row["result"] == "open"]
    regressed = [row for row in rows if row["regressed"]]
    outside_rows = _outside_rows(outside, "ok")
    rolled_back = _outside_rows(outside, "rolled_back")
    account = {
        "original": len(rows),
        "remediated": len(remediated),
        "remaining": len(remaining),
        "retired": len(retired),
        "outside_new": len(outside_rows),
        "full_check_ran": bool(full_checks),
        "full_checks": full_checks,
        "reference": {
            "run": str(reference.get("run") or ""),
            "review": str(reference.get("review") or ""),
            "reviewer": str(reference.get("reviewer") or ""),
            "reviewed_at": str(reference.get("reviewed_at") or ""),
        },
        "notes": str(document.get("notes") or "").strip(),
        "signed_name": str(signed.get("name") or ""),
        "signed_at": str(signed.get("at") or ""),
        "rows": rows,
        "outstanding": remaining,
        "retired_rows": retired,
        "outside": outside_rows,
        "rolled_back": rolled_back,
        "regressed": regressed,
    }
    account["outcome"] = _outcome(account)
    return account


def publish_remedy_reading(document: dict, run: dict | None, json_path: Path) -> tuple[Path, Path]:
    """Write the Markdown from the seal, then the PDF from that Markdown. Neither file is replaced."""
    import os

    from studio.compile.impl.remedy_pdf import write_remedy_pdf
    from studio.review.impl.remedy_markdown import remedy_markdown

    md_path = Path(json_path).with_suffix(".md")
    pdf_path = Path(json_path).with_suffix(".pdf")
    if os.path.lexists(md_path) or os.path.lexists(pdf_path):
        raise FileExistsError(f"Remediation report already exists: {md_path.name}")
    text = remedy_markdown(remedy_account(document, run))
    md_path.write_text(text, encoding="utf-8")
    try:
        write_remedy_pdf(text, pdf_path)
    except Exception:
        md_path.unlink(missing_ok=True)
        raise
    return md_path, pdf_path


def published_remedy_file(
    directory: Path | None,
    document: object,
    requested: str = "",
    suffix: str = ".md",
) -> Path | None:
    """The Markdown or PDF beside a sealed remedy file. A requested name cannot leave the directory."""
    from studio.review.impl.items import active_remedy_report

    if suffix not in {".md", ".pdf"} or directory is None or not Path(directory).is_dir():
        return None
    folder = Path(directory).resolve()
    if requested:
        name = Path(requested).name
        if name != requested or not _reading_name(name, suffix):
            return None
        path = folder / name
        if path.is_file() and path.with_suffix(".json").is_file() and path.parent.resolve() == folder:
            return path
        return None
    active = active_remedy_report(folder, document)
    if active is None:
        return None
    path = active.with_suffix(suffix)
    if path.is_file() and path.parent.resolve() == folder:
        return path
    return None


def _reading_name(name: str, suffix: str) -> bool:
    return (
        name.startswith("remedy-report")
        and name.endswith(suffix)
        and "/" not in name
        and "\\" not in name
    )


def _original_rows(items: list[dict], run: dict) -> list[dict]:
    rows = []
    seen: set[tuple] = set()
    for failed in failing_checks(run):
        key = (failed.get("claim_id"), failed.get("digest"))
        if key in seen:
            continue
        seen.add(key)
        probe = {"key": {"claim_id": failed.get("claim_id"), "check_digest": failed.get("digest")}}
        item = find_item(probe, items)
        check = _run_check(run, failed.get("claim_id"), failed.get("digest"))
        rows.append(_row(item, str(failed.get("claim_id") or ""), _check_label(check), "fail"))
    binding = binding_digest()
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or claim.get("binding") not in {"stale", "missing"}:
            continue
        key = (claim.get("id"), binding)
        if key in seen:
            continue
        seen.add(key)
        probe = {"key": {"claim_id": claim.get("id"), "check_digest": binding}}
        item = find_item(probe, items)
        rows.append(_row(item, str(claim.get("id") or ""), "Requirement binding", str(claim.get("binding"))))
    return rows


def _row(item: dict | None, claim_id: str, check: str, original: str) -> dict:
    retired = bool(item) and is_retired(item)
    decision = str((item or {}).get("decision") or "")
    if retired:
        result = "retired"
        recommendation = "Retired. This is not a completed fix."
    elif decision == "pass":
        result = "pass"
        recommendation = "Remediated. The Check is green. The signed Review is unchanged."
    else:
        result = "open"
        recommendation = "Still open."
    return {
        "claim_id": claim_id,
        "check": check,
        "original": original,
        "action": _action_text(item),
        "result": result,
        "recommendation": recommendation,
        "comment": remediation_comment(item) if item else "",
        "history": _history_lines(item),
        "regressed": _regressed(item, retired, decision),
    }


def _run_check(run: dict, claim_id: object, digest: object) -> dict:
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or claim.get("id") != claim_id:
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            if check_digest(str(check.get("check") or ""), args) == digest:
                return check
    return {}


def _check_label(check: dict) -> str:
    name = str(check.get("check") or "Check")
    args = check.get("args") if isinstance(check.get("args"), dict) else {}
    paths: list[str] = []
    single = args.get("path")
    if isinstance(single, str) and single:
        paths.append(single)
    for item in args.get("paths") or []:
        if isinstance(item, str) and item and item not in paths:
            paths.append(item)
    if not paths:
        return name
    return f"{name} ({', '.join(paths[:3])})"


def _action_text(item: dict | None) -> str:
    if not item:
        return "No remediation recorded."
    found = ""
    for entry in item.get("remediation_history") or []:
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("remediation") or "").strip()
        if text and text not in {"Check", "Re-check"}:
            found = text
    if found:
        return found
    comment = remediation_comment(item)
    return comment or "No remediation recorded."


def _history_lines(item: dict | None) -> list[str]:
    lines = []
    for entry in (item or {}).get("remediation_history") or []:
        if not isinstance(entry, dict):
            continue
        text = str(entry.get("remediation") or "").strip()
        transition = str(entry.get("transition") or "").strip()
        when = str(entry.get("date") or "").strip()
        line = " ".join(part for part in (when, text, transition) if part)
        if line:
            lines.append(line)
    return lines


def _regressed(item: dict | None, retired: bool, decision: str) -> bool:
    """A Check that became green and was red again afterwards."""
    if not item or retired:
        return False
    saw_green = False
    for entry in item.get("remediation_history") or []:
        if not isinstance(entry, dict):
            continue
        destination = _destination(str(entry.get("transition") or ""))
        if destination == "pass":
            saw_green = True
            continue
        if saw_green and destination and destination != "pass":
            return True
    return saw_green and decision != "pass"


def _destination(transition: str) -> str:
    if "->" not in transition:
        return ""
    return transition.split("->")[-1].strip()


def _outside_rows(events: list[dict], choice: str) -> list[dict]:
    rows = []
    for event in events:
        if event.get("choice") != choice:
            continue
        run = str(event.get("run") or "")
        for check in event.get("checks") or []:
            if not isinstance(check, dict):
                continue
            rows.append(
                {
                    "run": run,
                    "claim_id": str(check.get("claim_id") or ""),
                    "check": str(check.get("check") or ""),
                }
            )
    return rows


def _outcome(account: dict) -> str:
    parts = []
    remediated = account["remediated"]
    remaining = account["remaining"]
    retired = account["retired"]
    outside_new = account["outside_new"]
    if account["original"] == 0:
        parts.append("This remediation recorded no original deviations.")
    if remediated:
        verb = "was" if remediated == 1 else "were"
        noun = "deviation" if remediated == 1 else "deviations"
        if account["full_check_ran"]:
            parts.append(
                f"{remediated} original {noun} {verb} remediated and verified by a full Check."
            )
        else:
            parts.append(f"{remediated} original {noun} {verb} remediated and became green.")
    if remaining:
        verb = "remains" if remaining == 1 else "remain"
        noun = "deviation" if remaining == 1 else "deviations"
        parts.append(f"{remaining} original {noun} {verb} unresolved.")
    if retired:
        verb = "was" if retired == 1 else "were"
        noun = "Check" if retired == 1 else "Checks"
        parts.append(f"{retired} {noun} {verb} retired.")
    if account["full_check_ran"] and outside_new == 0:
        parts.append("The full Check found no new deviations outside the original scope.")
    elif outside_new:
        verb = "was" if outside_new == 1 else "were"
        noun = "deviation" if outside_new == 1 else "deviations"
        parts.append(f"{outside_new} new {noun} {verb} detected outside the original scope.")
    if not account["full_check_ran"]:
        parts.append("A full Check was not run, so new deviations outside the original scope are not known.")
    return " ".join(parts)
