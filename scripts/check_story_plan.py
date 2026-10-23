#!/usr/bin/env python3
"""Check durable story-plan structure, not actual software security or test truth."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FIELDS = (
    "Plan status", "Approved by", "Current task", "Last completed task",
    "Last verified tests", "Last checkpoint commit", "Requirements",
    "Packs v2", "Blockers", "Exact next action",
)
VALID_STATES = {"DRAFT", "APPROVED", "BLOCKED", "DONE"}


def validate_plan(text: str, phase: str) -> list[str]:
    errors: list[str] = []
    sections = ["Summary", "Current checkpoint", "Requirements and acceptance mapping", "Tasks", "Work log"]
    positions = []
    for section in sections:
        m = re.search(rf"^## {re.escape(section)}\s*$", text, flags=re.M)
        if not m:
            errors.append(f"Missing section: ## {section}")
        else:
            positions.append(m.start())
    if len(positions) == len(sections) and positions != sorted(positions):
        errors.append("Plan sections are out of order; Summary and Current checkpoint must be at the top")
    ck = re.search(r"^## Current checkpoint\s*$(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    fields: dict[str, str] = {}
    if ck:
        for line in ck.group(1).splitlines():
            line = line.strip()
            if not (line.startswith("|") and line.endswith("|")):
                continue
            pieces = [v.strip().replace("**", "") for v in line.strip("|").split("|")]
            if len(pieces) == 2 and pieces[0] in FIELDS:
                if pieces[0] in fields:
                    errors.append(f"Duplicate checkpoint field: {pieces[0]}")
                fields[pieces[0]] = pieces[1]
        for field in FIELDS:
            if not fields.get(field):
                errors.append(f"Missing/empty checkpoint field: {field}")
    status = fields.get("Plan status", "").upper()
    if status and status not in VALID_STATES:
        errors.append("Plan status must be DRAFT, APPROVED, BLOCKED, or DONE")
    if not re.search(r"^### Task [0-9]+\b", text, flags=re.M):
        errors.append("Missing numbered steps (### Task N ...)")
    if not re.search(r"^\|\s*(?:REQ-|CHK-R|[A-Z]+-R)[^\n]+\|", text, flags=re.M):
        errors.append("Requirements/acceptance mapping lacks a real requirement row")

    if phase in {"ready", "checkpoint", "done"}:
        target_status = "DONE" if phase == "done" else "APPROVED"
        if status != target_status:
            errors.append(f"Phase {phase} requires Plan status = {target_status}")
        approved = fields.get("Approved by", "").lower()
        if not approved or any(x in approved for x in ("pending", "<", "not approved", "tbd")):
            errors.append("Record explicit maintainer approval of requirements and plan")
        for field in ("Requirements", "Packs v2", "Current task", "Exact next action"):
            v = fields.get(field, "")
            if not v or "<" in v or "tbd" in v.lower() or "to be" in v.lower():
                errors.append(f"Unresolved placeholder in checkpoint: {field}")
        blockers = fields.get("Blockers", "").strip().lower()
        if blockers not in {"none", "none.", "no blockers"}:
            errors.append("Cannot build/complete with blockers; set Blockers = None or stop")
        if not re.search(r"^\|\s*(?:REQ-|CHK-R|[A-Z]+-R)[^\n]+\|", text, flags=re.M):
            errors.append("No approved derived requirements")
    if phase in {"checkpoint", "done"}:
        last = fields.get("Last completed task", "").lower()
        tests = fields.get("Last verified tests", "").lower()
        if last in {"none", "n/a", "pending"} or "<" in last:
            errors.append("Last completed task must identify a completed step")
        if tests.startswith(("not run", "pending", "tbd")) or "<" in tests:
            errors.append("Last verified tests must report actual commands and outcome (including failures)")
        log = re.search(r"^## Work log\s*$(.*)", text, flags=re.M | re.S)
        if not log or not re.search(r"^[-*] \*\*.+Task \d+", log.group(1), flags=re.M):
            errors.append("Work log needs a dated task entry with actual evidence")
    if phase == "done":
        if re.search(r"^- \[ \]", text, flags=re.M):
            errors.append("Unchecked task items remain; plan cannot be DONE")
        next_action = fields.get("Exact next action", "").lower()
        if "done" not in next_action and "complete" not in next_action and "no further" not in next_action:
            errors.append("DONE plan must explicitly state no implementation step remains")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("story_id", help="e.g. CHK-05")
    ap.add_argument("--phase", choices=("draft", "ready", "checkpoint", "done"), default="draft")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = ap.parse_args()
    if not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]{2,3}", args.story_id):
        ap.error("story_id must be a canonical story ID such as CHK-05")
    path = args.root / "docs" / "plan" / (args.story_id + ".md")
    if not path.is_file():
        print(f"ERROR: Missing canonical plan: {path}", file=sys.stderr)
        return 1
    problems = validate_plan(path.read_text(encoding="utf-8"), args.phase)
    for p in problems:
        print(f"ERROR: {p}", file=sys.stderr)
    if problems:
        print(f"FAIL: {path} ({len(problems)} structural issue(s))", file=sys.stderr)
        return 1
    print(f"OK: {path} ({args.phase} structural contract only; actual test/security evidence is not verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
