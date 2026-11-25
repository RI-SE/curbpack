"""review_item for one Check: provenance, reuse, workspace, and history.

The object is defined in docs/reference/studio-internal.md. A review and a
remediation round each keep their own file. Signing writes a third copy next
to the Review Report.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

from checks.run import _git_run
from common.canonical import canonical_json, version_digest
from common.errors import ModelError
from common.jsonio import read_json, write_json
from common.signing import sign_object
from discovery.studio import load_user_studio

BINDING_CHECK = {"check": "requirement_binding", "args": {}}
_DECISIONS = {"pass", "accepted", "not_assessed", "must_fix"}


def check_digest(check: str, args: dict) -> str:
    payload = canonical_json({"args": args, "check": check}).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def binding_digest() -> str:
    return check_digest(BINDING_CHECK["check"], BINDING_CHECK["args"])


def studio_temp_dir(repo: Path) -> Path:
    """paths.temp_dir from the user studio file, else .curbpack/tmp under the product repo."""
    relative = ".curbpack/tmp"
    loaded = load_user_studio()
    if loaded is not None:
        relative = str(loaded["paths"]["temp_dir"])
    path = Path(relative)
    if path.is_absolute():
        return path
    return Path(repo) / path


def workspace_dir(temp_dir: Path, source_name: str) -> Path:
    stem = Path(source_name).name
    if stem.endswith(".json"):
        stem = stem[: -len(".json")]
    return Path(temp_dir) / stem


def workspace_items_path(temp_dir: Path, source_name: str) -> Path:
    return workspace_dir(temp_dir, source_name) / "review_items.json"


def check_directory(path: Path) -> Path | None:
    """The Check directory when this file is the run, its Review, its items, or its Remedy."""
    path = Path(path)
    if path.name == "run-result.json" and path.parent.name.startswith("run-result_"):
        return path.parent
    if path.parent.name.startswith("run-result_") and (
        path.name in {"review-report.json", "remedy-report.json", "review_items.json"}
        or _snapshot_name(path.name)
    ):
        return path.parent
    return None


def _snapshot_name(name: str) -> bool:
    """A dated report inside a Check directory. The work file is review_items.json."""
    return (
        name.endswith(".json")
        and not name.endswith(".items.json")
        and (name.startswith("review-report_") or name.startswith("remedy-report_"))
    )


def items_home(repo: Path, source: Path) -> Path:
    """Working review items live in the Check directory. Older files still use the temp directory."""
    directory = check_directory(source)
    if directory is not None:
        return directory / "review_items.json"
    return workspace_items_path(studio_temp_dir(repo), Path(source).name)


def run_stem(run_path: Path) -> str:
    directory = check_directory(run_path)
    if directory is not None:
        return directory.name
    return Path(run_path).name


def files_sidecar_path(temp_dir: Path, run_name: str) -> Path:
    stem = Path(run_name).name
    if stem.endswith(".json"):
        stem = stem[: -len(".json")]
    return Path(temp_dir) / f"{stem}.files.json"


def relevant_paths(args: dict) -> list[str]:
    found: list[str] = []
    single = args.get("path")
    if isinstance(single, str) and single and single not in found:
        found.append(single)
    listed = args.get("paths")
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, str) and item and item not in found:
                found.append(item)
    return found


def _file_record(repo: Path, relative: str) -> dict | None:
    path = Path(repo) / relative
    if not path.is_file():
        return None
    stat = path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"path": relative, "size": stat.st_size, "mtime": mtime}


def capture_run_files(repo: Path, run: dict) -> list[dict]:
    """Path, size, and mtime for each Check, taken from the worktree now."""
    rows: list[dict] = []
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            files = [record for path in relevant_paths(args) if (record := _file_record(repo, path))]
            rows.append(
                {
                    "claim_id": claim_id,
                    "check_digest": check_digest(str(check.get("check") or ""), args),
                    "files": files,
                }
            )
    return rows


def record_dirty_files(repo: Path, run_path: Path, run: dict) -> Path | None:
    """Write the sidecar once, while the worktree is still the one that ran.

    A later edit of the worktree does not rewrite an existing sidecar.
    curbcheck without Studio does not call this.
    """
    if run.get("worktree") != "dirty":
        return None
    target = files_sidecar_path(studio_temp_dir(repo), run_stem(run_path))
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, {"checks": capture_run_files(repo, run)})
    return target


def load_files_sidecar(temp_dir: Path, run_name: str) -> dict[tuple, list[dict]]:
    path = files_sidecar_path(temp_dir, run_name)
    if not path.is_file():
        return {}
    document = read_json(path)
    found: dict[tuple, list[dict]] = {}
    for row in document.get("checks") or []:
        if not isinstance(row, dict):
            continue
        files = [item for item in row.get("files") or [] if isinstance(item, dict)]
        found[(row.get("claim_id"), row.get("check_digest"))] = files
    return found


def _provenance(run: dict, claim: dict, files: list[dict] | None) -> dict:
    provenance: dict = {}
    digest = claim.get("requirement_digest")
    if isinstance(digest, str) and digest:
        provenance["requirement_digest"] = digest
    commit = run.get("commit")
    if isinstance(commit, str) and commit:
        provenance["git_commit"] = commit
    worktree = run.get("worktree")
    if worktree == "dirty":
        provenance["dirty_git"] = True
    elif worktree == "clean":
        provenance["dirty_git"] = False
    if files:
        provenance["files"] = files
    return provenance


def _item(claim_id: str, digest: str, decision: str, provenance: dict) -> dict:
    item = {
        "key": {"claim_id": claim_id, "check_digest": digest},
        "decision": decision,
    }
    if provenance:
        item["provenance"] = provenance
    return item


def items_from_run(run: dict, files_by_check: dict[tuple, list[dict]] | None = None) -> list[dict]:
    """Decisions from the run. History is empty. pass where the Check passed, otherwise not_assessed."""
    files_by_check = files_by_check or {}
    items: list[dict] = []
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str):
            continue
        claim_id = claim["id"]
        binding = claim.get("binding")
        if binding in {"match", "stale", "missing"}:
            digest = binding_digest()
            decision = "pass" if binding == "match" else "not_assessed"
            items.append(
                _item(claim_id, digest, decision, _provenance(run, claim, files_by_check.get((claim_id, digest))))
            )
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            digest = check_digest(str(check.get("check") or ""), args)
            decision = "pass" if check.get("status") == "pass" else "not_assessed"
            items.append(
                _item(claim_id, digest, decision, _provenance(run, claim, files_by_check.get((claim_id, digest))))
            )
    return items


def item_key(item: dict) -> tuple:
    key = item.get("key") if isinstance(item.get("key"), dict) else {}
    return (key.get("claim_id"), key.get("check_digest"))


def _replaced_digests(items: list[dict]) -> set[tuple]:
    """Check keys a later configuration already replaced."""
    replaced = set()
    for item in items:
        claim_id = item_key(item)[0]
        for entry in item.get("remediation_history") or []:
            if isinstance(entry, dict) and entry.get("old_check_digest"):
                replaced.add((claim_id, entry["old_check_digest"]))
    return replaced


def merge_items(existing: list[dict], new_items: list[dict]) -> list[dict]:
    """Keep the existing item when the key matches. Add a Check that exists only on the run."""
    kept = {item_key(item): item for item in existing}
    replaced = _replaced_digests(existing)
    merged: list[dict] = []
    seen: set[tuple] = set()
    for item in new_items:
        key = item_key(item)
        if key in replaced and key not in kept:
            continue
        merged.append(kept[key] if key in kept else item)
        seen.add(key)
    for item in existing:
        key = item_key(item)
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged


def load_items(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    document = read_json(path)
    rows = document.get("items") if isinstance(document, dict) else None
    if not isinstance(rows, list):
        raise ModelError("review_items", "items", "a list")
    return [row for row in rows if isinstance(row, dict)]


def write_items(path: Path, items: list[dict], *, signed: dict | None = None, marker: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kept: dict = {}
    if path.is_file():
        current = read_json(path)
        if isinstance(current, dict):
            for key in (
                "history_from",
                "remedy",
                "projected_runs",
                "notes",
                "remedy_notes",
                "work_saved",
                "review_locked",
                "remedy_locked",
                "remedy_revoked",
                "outside",
                "pending_outside",
                "studio_snapshot",
            ):
                if key in current:
                    kept[key] = current[key]
    if marker:
        for key, value in marker.items():
            if value is None:
                kept.pop(key, None)
            else:
                kept[key] = value
    document: dict = {"items": items, **kept}
    if signed is not None:
        document["signed"] = signed
    write_json(path, document)


def open_review_items(
    path: Path,
    run: dict,
    *,
    files_by_check: dict[tuple, list[dict]] | None = None,
    choice: str = "",
    repo: Path | None = None,
    run_name: str = "",
) -> tuple[list[dict], str]:
    """Return items and the question state: ready, ask, continued, or restarted.

    A missing file is written from the run. An existing file always asks
    continue or start over until the caller passes that choice.
    A dirty run's sidecar is copied onto provenance.files when the items are created.
    """
    if files_by_check is None and repo is not None and run_name:
        files_by_check = load_files_sidecar(studio_temp_dir(repo), run_name)
    new_items = items_from_run(run, files_by_check)
    if not path.is_file():
        write_items(path, new_items)
        return new_items, "ready"
    if choice == "continue":
        merged = merge_items(load_items(path), new_items)
        write_items(path, merged)
        return merged, "continued"
    if choice == "start":
        write_items(path, new_items)
        return new_items, "restarted"
    return load_items(path), "ask"


def same_file_metadata(left: list[dict] | None, right: list[dict] | None) -> bool:
    if not left or not right:
        return False
    def rows(items: list[dict]) -> dict[str, tuple]:
        return {
            str(item.get("path")): (item.get("size"), item.get("mtime"))
            for item in items
            if isinstance(item, dict) and item.get("path")
        }
    return rows(left) == rows(right)


def _blob(repo: Path, commit: str, relative: str) -> str | None:
    proc = _git_run(repo, "rev-parse", f"{commit}:{relative}")
    if proc is None or proc.returncode != 0:
        return None
    return proc.stdout.strip()


def _clean_same(repo: Path, previous: dict, current: dict, paths: list[str]) -> bool:
    left = str((previous.get("provenance") or {}).get("git_commit") or "")
    right = str((current.get("provenance") or {}).get("git_commit") or "")
    if not left or not right:
        return False
    if left == right:
        return True
    if not paths:
        return False
    for relative in paths:
        before = _blob(repo, left, relative)
        after = _blob(repo, right, relative)
        if before is None or after is None or before != after:
            return False
    return True


def decision_reusable(previous: dict, current: dict, *, repo: Path, paths: list[str]) -> bool:
    """True when the earlier decision may fill the new item. History is not part of this."""
    if item_key(previous) != item_key(current):
        return False
    left = previous.get("provenance") if isinstance(previous.get("provenance"), dict) else {}
    right = current.get("provenance") if isinstance(current.get("provenance"), dict) else {}
    if not left.get("requirement_digest") or left.get("requirement_digest") != right.get("requirement_digest"):
        return False
    if "dirty_git" not in left or "dirty_git" not in right:
        return False
    if left.get("dirty_git") or right.get("dirty_git"):
        return same_file_metadata(left.get("files"), right.get("files"))
    return _clean_same(repo, previous, current, paths)


def apply_reused_decision(current: dict, previous: dict) -> dict:
    """Copy the decision onto the new item. Leave remediation_history untouched."""
    updated = dict(current)
    updated["decision"] = previous.get("decision")
    for field in ("priority", "comment", "assessed_at"):
        if field in previous and previous.get("decision") in {"accepted", "must_fix"}:
            updated[field] = previous[field]
        else:
            updated.pop(field, None)
    if "remediation_history" in current:
        updated["remediation_history"] = current["remediation_history"]
    else:
        updated.pop("remediation_history", None)
    return updated


def history_to_show(source_items: list[dict], item: dict) -> list[dict]:
    """History written by remediation, matched by key. It does not set decision."""
    wanted = item_key(item)
    for source in source_items:
        if item_key(source) == wanted:
            history = source.get("remediation_history")
            if isinstance(history, list):
                return [entry for entry in history if isinstance(entry, dict)]
    return []


def append_history(
    item: dict,
    *,
    remediation: str,
    action: str | None = None,
    transition: str | None = None,
    old_check_digest: str | None = None,
    name: str | None = None,
    date: str | None = None,
) -> dict:
    """Append one history row. `name` is the person who signed that change, when there is one."""
    if not isinstance(remediation, str) or not remediation.strip():
        raise ModelError("review_item", "remediation", "non-empty text")
    entry: dict = {
        "date": date or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "remediation": remediation.strip(),
    }
    if action:
        entry["action"] = action
    if transition:
        entry["transition"] = transition
    if old_check_digest:
        entry["old_check_digest"] = old_check_digest
    signer = name.strip() if isinstance(name, str) else ""
    if signer:
        entry["name"] = signer
    updated = dict(item)
    history = [row for row in (item.get("remediation_history") or []) if isinstance(row, dict)]
    history.append(entry)
    updated["remediation_history"] = history
    return updated


def _plain_comment(entry: dict) -> bool:
    """A typed note. A re-check, retire, or rebind is a record, not that note."""
    if entry.get("action") or entry.get("transition"):
        return False
    text = str(entry.get("remediation") or "").strip()
    return bool(text) and text not in {"Check", "Re-check"}


def remediation_comment(item: dict) -> str:
    """The current note. It is the comment, not a history entry."""
    text = item.get("comment")
    if isinstance(text, str) and text.strip():
        return text.strip()
    found = ""
    for entry in item.get("remediation_history") or []:
        if isinstance(entry, dict) and _plain_comment(entry):
            found = str(entry.get("remediation") or "").strip()
    return found


def set_remediation_comment(item: dict, text: str, *, date: str | None = None) -> dict:
    """Store the note on `comment`. A note is not a remediation action."""
    del date
    history = [row for row in (item.get("remediation_history") or []) if isinstance(row, dict)]
    kept = [row for row in history if not _plain_comment(row)]
    updated = dict(item)
    note = text.strip() if isinstance(text, str) else ""
    if note:
        updated["comment"] = note
    else:
        updated.pop("comment", None)
    if kept:
        updated["remediation_history"] = kept
    else:
        updated.pop("remediation_history", None)
    return updated


def record_retire(item: dict, *, remediation: str, name: str | None = None, date: str | None = None) -> dict:
    """A Retire post names the action. A free-text comment does not."""
    return append_history(item, remediation=remediation, action="retire", name=name, date=date)


def retarget_check(
    item: dict,
    check: str,
    args: dict,
    *,
    remediation: str,
    transition: str | None = None,
    action: str | None = None,
    name: str | None = None,
    date: str | None = None,
) -> dict:
    """Keep the item. Store the old digest and point the key at the new configuration."""
    old = str((item.get("key") or {}).get("check_digest") or "")
    updated = append_history(
        item,
        remediation=remediation,
        transition=transition,
        action=action,
        old_check_digest=old,
        name=name,
        date=date,
    )
    key = dict(updated.get("key") or {})
    key["check_digest"] = check_digest(check, args)
    updated["key"] = key
    return updated


_BACKGROUND_RUN = {"Check", "Re-check"}


def _noted_change(remediation: str, change: str) -> str:
    """A background run is not the note. The change is."""
    note = remediation.strip()
    if note in _BACKGROUND_RUN:
        return change
    return note


def apply_recheck(item: dict, status: str, *, remediation: str, name: str | None = None, date: str | None = None) -> dict:
    """Record a re-check only when it changes the outcome.

    A pass sets the recommendation to pass and the history names that change.
    A result that leaves the decision is the check running again, not history.
    A retired Check keeps its decision.
    """
    if is_retired(item):
        return item
    previous = str(item.get("decision") or "")
    if status == "pass":
        if previous == "pass":
            return item
        transition = f"{previous} -> pass" if previous else "pass"
        updated = append_history(
            item,
            remediation=_noted_change(remediation, transition),
            transition=transition if previous else None,
            name=name,
            date=date,
        )
        updated["decision"] = "pass"
        return updated
    if status == "fail" and previous == "pass":
        transition = "pass -> fail"
        updated = append_history(
            item,
            remediation=_noted_change(remediation, transition),
            transition=transition,
            name=name,
            date=date,
        )
        updated["decision"] = "must_fix"
        return updated
    return item


def _checks_in_run(run: dict) -> list[dict]:
    found = []
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            name = str(check.get("check") or "")
            found.append(
                {
                    "claim_id": claim_id,
                    "check": name,
                    "args": args,
                    "status": str(check.get("status") or ""),
                    "digest": check_digest(name, args),
                }
            )
    return found


def find_item(item: dict, sources: list[dict]) -> dict | None:
    """The source for this Check, by its current key or a recorded old_check_digest."""
    key = item_key(item)
    for source in sources:
        if item_key(source) == key:
            return source
    claim_id, digest = key
    for source in sources:
        if item_key(source)[0] != claim_id:
            continue
        for entry in source.get("remediation_history") or []:
            if isinstance(entry, dict) and entry.get("old_check_digest") == digest:
                return source
    return None


def _binding_recheck_status(run: dict, claim_id: str) -> str | None:
    """pass when the Claim's binding is match. fail when it is still stale or missing."""
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or claim.get("id") != claim_id:
            continue
        binding = claim.get("binding")
        if binding == "match":
            return "pass"
        if binding in {"stale", "missing"}:
            return "fail"
        return None
    return None


def _recorded_files(
    files_by_check: dict[tuple, list[dict]] | None,
    repo: Path | None,
    run_name: str,
) -> dict[tuple, list[dict]] | None:
    if files_by_check is not None:
        return files_by_check
    if repo is not None and run_name:
        return load_files_sidecar(studio_temp_dir(repo), run_name)
    return None


def failing_checks(run: dict) -> list[dict]:
    """The failing Checks in one run. Identity is the claim and the check digest."""
    found = []
    for row in _checks_in_run(run):
        if row["status"] != "fail":
            continue
        found.append(
            {"claim_id": row["claim_id"], "check": row["check"], "digest": row["digest"]}
        )
    return found


def canonical_digest(claim_id: str, digest: str, items: list[dict]) -> str:
    """The original digest of a Check. A retarget counts as the Check it replaced."""
    for item in items:
        if item_key(item) != (claim_id, digest):
            continue
        for entry in item.get("remediation_history") or []:
            if isinstance(entry, dict) and entry.get("old_check_digest"):
                return str(entry["old_check_digest"])
    return digest


def outside(found: list[dict], reference: list[dict], items: list[dict] | None = None) -> list[dict]:
    """Failing Checks in found whose identity is not a failing Check in reference.

    The comparison is the set of identities, not the number of failures.
    """
    owned = {(row.get("claim_id"), row.get("digest")) for row in reference}
    kept = items or []
    extra = []
    for row in found:
        claim_id = row.get("claim_id")
        digest = str(row.get("digest") or "")
        canonical = canonical_digest(str(claim_id), digest, kept)
        if (claim_id, canonical) in owned or (claim_id, digest) in owned:
            continue
        extra.append(row)
    return extra


def affected(remediated: list[dict], found: list[dict]) -> list[dict]:
    """Remediated rows whose Check fails again in found."""
    failing = {(row.get("claim_id"), row.get("digest")) for row in found}
    return [item for item in remediated if item_key(item) in failing]


def turned_green(deviations: list[dict], run: dict) -> list[dict]:
    """Deviation rows whose Check passes in this run."""
    passing = {
        (row["claim_id"], row["digest"])
        for row in _checks_in_run(run)
        if row["status"] == "pass"
    }
    return [item for item in deviations if item_key(item) in passing]


def project_run(
    items: list[dict],
    run: dict,
    *,
    remediation: str,
    files_by_check: dict[tuple, list[dict]] | None = None,
    repo: Path | None = None,
    run_name: str = "",
    source: dict | None = None,
) -> list[dict]:
    """Apply one full run to the open remediation copy.

    A pass that changes the recommendation records that change and sets it to
    pass. An unchanged result leaves the item. A changed Check configuration is
    linked through old_check_digest. The binding Check is updated from the
    Claim's binding and is not retargeted onto another Check.

    When source is the original report, a Check that did not fail there is left
    unchanged and is not added.
    """
    files = _recorded_files(files_by_check, repo, run_name)
    checks = _checks_in_run(run)
    by_key = {(row["claim_id"], row["digest"]): row for row in checks}
    known = {item_key(item) for item in items}
    owned = None
    if source is not None:
        owned = {(row["claim_id"], row["digest"]) for row in failing_checks(source)}
    updated = []
    for item in items:
        claim_id, digest = item_key(item)
        if owned is not None and digest != binding_digest():
            canonical = canonical_digest(claim_id, str(digest or ""), items)
            if (claim_id, digest) not in owned and (claim_id, canonical) not in owned:
                updated.append(item)
                continue
        if is_retired(item):
            updated.append(item)
            continue
        current = item
        row = by_key.get((claim_id, digest))
        if row is None and digest == binding_digest():
            status = _binding_recheck_status(run, claim_id)
            if status is not None and not (status == "pass" and str(current.get("decision") or "") == "pass"):
                current = apply_recheck(current, status, remediation=remediation)
        elif row is None:
            candidates = [
                check
                for check in checks
                if check["claim_id"] == claim_id and (claim_id, check["digest"]) not in known
            ]
            if len(candidates) == 1:
                row = candidates[0]
                current = retarget_check(
                    current,
                    row["check"],
                    row["args"],
                    remediation=_noted_change(remediation, "Check configuration updated."),
                )
        if row is not None:
            current = apply_recheck(current, row["status"], remediation=remediation)
        updated.append(current)
    if source is not None:
        return updated
    present = {item_key(item) for item in updated}
    for fresh in items_from_run(run, files):
        if item_key(fresh) not in present and find_item(fresh, updated) is None:
            updated.append(fresh)
            present.add(item_key(fresh))
    return updated


def _outside_event(pending: dict, choice: str) -> dict:
    event = {
        "run": str(pending.get("run") or ""),
        "checks": [row for row in pending.get("checks") or [] if isinstance(row, dict)],
        "choice": choice,
    }
    studio = pending.get("studio")
    if isinstance(studio, dict) and (studio.get("claim_id") or studio.get("check")):
        event["studio"] = {"claim_id": studio.get("claim_id"), "check": studio.get("check")}
    return event


def remember_studio_edit(items_path: Path, claim: dict, claim_file: str, action: dict) -> None:
    """Keep the claim and the rows from before the latest Studio change."""
    import copy

    items = load_items(items_path)
    write_items(
        items_path,
        items,
        marker={
            "studio_snapshot": {
                "claim_file": claim_file,
                "claim": copy.deepcopy(claim),
                "items": copy.deepcopy(items),
                "action": {
                    "claim_id": action.get("claim_id"),
                    "check": action.get("check"),
                },
            }
        },
    )


def settle_regression(
    items_path: Path,
    source_run: dict,
    new_run: dict,
    *,
    run_name: str,
    run_path: str,
) -> str:
    """Project a full run, or stop when it fails a Check the original report passed.

    Returns "outside" or "applied". An outside result leaves the queue unchanged.
    """
    document = read_json(items_path) if items_path.is_file() else {}
    if not isinstance(document, dict):
        document = {}
    items = load_items(items_path)
    extra = outside(failing_checks(new_run), failing_checks(source_run), items)
    if extra:
        snapshot = document.get("studio_snapshot")
        studio = snapshot.get("action") if isinstance(snapshot, dict) else None
        write_items(
            items_path,
            items,
            marker={
                "pending_outside": {
                    "run": run_name,
                    "run_path": run_path,
                    "checks": extra,
                    "studio": studio,
                }
            },
        )
        return "outside"
    projected = project_run(items, new_run, remediation="Check", source=source_run)
    write_items(
        items_path,
        projected,
        marker={"pending_outside": None, "studio_snapshot": None},
    )
    return "applied"


def accept_pending(items_path: Path, source_run: dict, new_run: dict) -> None:
    """Record the outside Checks and update only the original deviations."""
    document = read_json(items_path)
    pending = document.get("pending_outside") if isinstance(document, dict) else None
    if not isinstance(pending, dict) or not pending.get("checks"):
        raise ModelError("remediation", "outside", "a warning to acknowledge")
    events = [row for row in (document.get("outside") or []) if isinstance(row, dict)]
    events.append(_outside_event(pending, "ok"))
    projected = project_run(load_items(items_path), new_run, remediation="Check", source=source_run)
    write_items(
        items_path,
        projected,
        marker={"outside": events, "pending_outside": None, "studio_snapshot": None},
    )


def rollback_pending(items_path: Path, repo: Path) -> None:
    """Restore the latest Studio change. Files edited outside Studio stay as they are."""
    document = read_json(items_path)
    if not isinstance(document, dict):
        document = {}
    snapshot = document.get("studio_snapshot")
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("claim"), dict):
        raise ModelError("remediation", "rollback", "a Studio change to restore")
    relative = Path(str(snapshot.get("claim_file") or ""))
    if relative.is_absolute() or ".." in relative.parts:
        raise ModelError("remediation", "rollback", "a claim inside this repository")
    target = (repo / relative).resolve()
    if repo.resolve() not in target.parents:
        raise ModelError("remediation", "rollback", "a claim inside this repository")
    write_json(target, snapshot["claim"])
    pending = document.get("pending_outside") if isinstance(document.get("pending_outside"), dict) else {}
    events = [row for row in (document.get("outside") or []) if isinstance(row, dict)]
    if pending.get("checks"):
        events.append(_outside_event(pending, "rolled_back"))
    restored = [row for row in (snapshot.get("items") or []) if isinstance(row, dict)]
    write_items(
        items_path,
        restored,
        marker={"outside": events, "pending_outside": None, "studio_snapshot": None},
    )


def _history_rows(source: dict | None) -> list[dict]:
    if not source:
        return []
    return [dict(entry) for entry in source.get("remediation_history") or [] if isinstance(entry, dict)]


def carry_history(items: list[dict], source_items: list[dict]) -> list[dict]:
    """Copy remediation history onto items that have none. The history does not set decision."""
    carried = []
    for item in items:
        own = item.get("remediation_history")
        if isinstance(own, list) and own:
            carried.append(item)
            continue
        history = _history_rows(find_item(item, source_items))
        if not history:
            carried.append(item)
            continue
        updated = dict(item)
        updated["remediation_history"] = history
        carried.append(updated)
    return carried


def _signed_for(item: dict, remedy: dict | None, signed_items: list[dict]) -> dict | None:
    found = find_item(item, signed_items)
    if found is not None:
        return found
    if remedy is None:
        return None
    claim_id = item_key(item)[0]
    olds = {
        entry.get("old_check_digest")
        for entry in remedy.get("remediation_history") or []
        if isinstance(entry, dict) and entry.get("old_check_digest")
    }
    for signed in signed_items:
        if item_key(signed)[0] == claim_id and item_key(signed)[1] in olds:
            return signed
    return None


def take_in_remedy(
    repo: Path,
    run: dict,
    fresh: list[dict],
    remedy_items: list[dict],
    signed_items: list[dict],
) -> list[dict]:
    """Bring a Remedy Report into a new Review.

    Unchanged underlag fills the signed decision. Changed underlag keeps the
    Check's own decision. A pass then records previous -> pass in the history,
    and that transition does not choose the decision.
    """
    taken = []
    for item in fresh:
        remedy = find_item(item, remedy_items)
        signed = _signed_for(item, remedy, signed_items)
        history = _history_rows(remedy) or _history_rows(signed)
        updated = dict(item)
        if history:
            updated["remediation_history"] = history
        source = signed or remedy
        if source and decision_reusable(source, updated, repo=repo, paths=paths_for_item(run, updated)):
            updated = apply_reused_decision(updated, source)
        else:
            previous = str((source or {}).get("decision") or "")
            if updated.get("decision") == "pass" and previous and previous != "pass":
                transition = f"{previous} -> pass"
                if not any(entry.get("transition") == transition for entry in history):
                    updated = append_history(updated, remediation=transition, transition=transition)
        taken.append(updated)
    return taken


def sign_remedy_document(
    items: list[dict],
    *,
    name: str,
    private_key: bytes,
    at: str,
    outside: list | None = None,
    notes: str | None = None,
    reference: dict | None = None,
    full_checks: list | None = None,
) -> dict:
    """The same seal as a review report. Reading it uses what 'remedy report'.

    outside is the acknowledged regressions. It is part of the signed remedy,
    not of the locked review. notes are the round's own words, also inside the seal.
    reference names the Check and the signed Review. full_checks names the full
    runs recorded for this round. An empty list means no full Check was run.
    """
    document: dict = {"items": items, "remedy": True}
    if outside:
        document["outside"] = outside
    text = notes.strip() if isinstance(notes, str) else ""
    if text:
        document["notes"] = text
    if isinstance(reference, dict):
        stored = {
            "run": str(reference.get("run") or ""),
            "review": str(reference.get("review") or ""),
        }
        reviewer = str(reference.get("reviewer") or "").strip()
        reviewed_at = str(reference.get("reviewed_at") or "").strip()
        if reviewer:
            stored["reviewer"] = reviewer
        if reviewed_at:
            stored["reviewed_at"] = reviewed_at
        document["reference"] = stored
    if full_checks is not None:
        document["full_checks"] = [name for name in full_checks if isinstance(name, str) and name]
    return sign_object(document, name=name, private_key=private_key, at=at)


def summarize_review(items: list[dict]) -> str:
    decisions = [item.get("decision") for item in items if isinstance(item, dict)]
    if not decisions:
        return "—"
    if all(decision == "pass" for decision in decisions):
        return "All Passed · Signed"
    parts = []
    for decision, label in (("pass", "Passed"), ("accepted", "Accepted"), ("must_fix", "Must fix")):
        count = decisions.count(decision)
        if count:
            parts.append(f"{count} {label}")
    if not parts:
        return "Signed"
    return " · ".join(parts) + " · Signed"


def summarize_remedy(items: list[dict]) -> str:
    count = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        count += len([entry for entry in item.get("remediation_history") or [] if isinstance(entry, dict)])
    if count == 0:
        return "Signed"
    noun = "action" if count == 1 else "actions"
    return f"{count} {noun} · Signed"


def is_retired(item: dict) -> bool:
    return any(
        isinstance(entry, dict) and entry.get("action") == "retire"
        for entry in item.get("remediation_history") or []
    )


def mark_retired(items: list[dict], claim_id: str, digest: str, note: str, *, claim_gone: bool) -> list[dict]:
    """Retire one Check. Retire every row of the Claim when the Claim itself is gone."""
    updated = []
    for item in items:
        key_claim, key_digest = item_key(item)
        if key_claim == claim_id and (claim_gone or key_digest == digest) and not is_retired(item):
            item = record_retire(item, remediation=note)
        updated.append(item)
    return updated


def retired_absences(remedy_items: list[dict], run: dict) -> list[dict]:
    """A Check or Claim missing from the new run is retired only with action retire."""
    present_claims = {
        claim.get("id")
        for claim in run.get("claims") or []
        if isinstance(claim, dict)
    }
    present_checks: set[tuple] = set()
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        claim_id = claim.get("id")
        binding = claim.get("binding")
        if binding in {"match", "stale", "missing"}:
            present_checks.add((claim_id, binding_digest()))
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            present_checks.add((claim_id, check_digest(str(check.get("check") or ""), args)))
    missing: list[dict] = []
    claims_with_retire = {item_key(item)[0] for item in remedy_items if is_retired(item)}
    for item in remedy_items:
        claim_id, digest = item_key(item)
        claim_gone = claim_id not in present_claims
        check_gone = (claim_id, digest) not in present_checks
        if claim_gone and claim_id in claims_with_retire:
            missing.append(item)
        elif check_gone and is_retired(item):
            missing.append(item)
    return missing


def _binding_assessment(item: dict, run: dict) -> dict | None:
    """A must_fix or accepted binding becomes a binding assessment. A match has no assessment slot."""
    claim_id, digest = item_key(item)
    if digest != binding_digest():
        return None
    claim = next(
        (
            row
            for row in run.get("claims") or []
            if isinstance(row, dict) and row.get("id") == claim_id
        ),
        None,
    )
    if claim is None or claim.get("binding") not in {"stale", "missing"}:
        return None
    text = item.get("comment")
    text = text.strip() if isinstance(text, str) else ""
    assessment = {
        "kind": "binding",
        "claim_id": claim.get("id"),
        "claim_digest": claim.get("digest"),
        "namespace": claim.get("namespace"),
        "pack_id": claim.get("pack_id"),
        "requirement_id": claim.get("requirement_id"),
        "requirement_digest": claim.get("requirement_digest"),
        "binding": claim.get("binding"),
        "disposition": "must_fix" if item.get("decision") == "must_fix" else "accept",
        "text": text,
    }
    for field, value in assessment.items():
        if field == "text":
            continue
        if not isinstance(value, str) or not value.strip():
            return None
    return assessment


def assessments_from_decisions(items: list[dict], run: dict) -> list[dict]:
    """Signed decisions are what the report records. pass and not_assessed add no assessment."""
    index_by_key: dict[tuple, dict] = {}
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict) or not isinstance(check.get("index"), int):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            index_by_key[(claim.get("id"), check_digest(str(check.get("check") or ""), args))] = {
                "claim_id": claim.get("id"),
                "claim_digest": claim.get("digest"),
                "index": check.get("index"),
                "status": check.get("status"),
            }
    assessments: list[dict] = []
    for item in items:
        decision = item.get("decision")
        if decision not in {"must_fix", "accepted"}:
            continue
        if item_key(item)[1] == binding_digest():
            assessment = _binding_assessment(item, run)
            if assessment is not None:
                assessments.append(assessment)
            continue
        located = index_by_key.get(item_key(item))
        if located is None:
            continue
        text = item.get("comment")
        text = text.strip() if isinstance(text, str) else ""
        if decision == "accepted" and located.get("status") == "fail" and not text:
            raise ModelError("review_item", "comment", "non-empty text")
        assessments.append(
            {
                "kind": "check",
                "claim_id": located["claim_id"],
                "claim_digest": located["claim_digest"],
                "index": located["index"],
                "disposition": "must_fix" if decision == "must_fix" else "accept",
                "text": text,
            }
        )
    return assessments


def signed_decision(items_document: dict, claim_id: str, digest: str) -> str | None:
    """The signed file's decision is what reporting uses."""
    if not isinstance(items_document.get("signed"), dict):
        return None
    for item in items_document.get("items") or []:
        if isinstance(item, dict) and item_key(item) == (claim_id, digest):
            decision = item.get("decision")
            if decision in _DECISIONS:
                return str(decision)
    return None


def sign_items_document(
    items: list[dict],
    *,
    name: str,
    private_key: bytes,
    at: str,
) -> tuple[dict, str]:
    """Sign the items object. Return the sealed document and the version digest the report stores."""
    document = {"items": items}
    digest = version_digest(document)
    sealed = sign_object(document, name=name, private_key=private_key, at=at)
    return sealed, digest


def paths_for_item(run: dict, item: dict) -> list[str]:
    """Relevant paths: provenance.files when present, otherwise the Check arguments."""
    provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
    files = provenance.get("files")
    if isinstance(files, list) and files:
        return [str(row.get("path")) for row in files if isinstance(row, dict) and row.get("path")]
    claim_id, digest = item_key(item)
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict) or claim.get("id") != claim_id:
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            if check_digest(str(check.get("check") or ""), args) == digest:
                return relevant_paths(args)
    return []


def with_history(items: list[dict], source_items: list[dict]) -> list[dict]:
    """Attach remediation history for display. The attached history does not set decision."""
    shown = []
    for item in items:
        own = item.get("remediation_history")
        if isinstance(own, list) and own:
            shown.append(item)
            continue
        history = history_to_show(source_items, item)
        if not history:
            shown.append(item)
            continue
        copy = dict(item)
        copy["remediation_history"] = history
        shown.append(copy)
    return shown


def reuse_decisions(repo: Path, run: dict, items: list[dict], source_items: list[dict]) -> list[dict]:
    """Fill decision from a matching source item. History stays on the source."""
    by_key = {item_key(item): item for item in source_items}
    reused = []
    for item in items:
        previous = by_key.get(item_key(item))
        if previous and decision_reusable(previous, item, repo=repo, paths=paths_for_item(run, item)):
            reused.append(apply_reused_decision(item, previous))
        else:
            reused.append(item)
    return reused


def apply_assessment_decisions(items: list[dict], assessments: list[dict], run: dict) -> list[dict]:
    """Copy a saved review verdict onto the matching item. Retire is not a verdict."""
    located: dict[tuple, tuple] = {}
    for claim in run.get("claims") or []:
        if not isinstance(claim, dict):
            continue
        for check in claim.get("checks") or []:
            if not isinstance(check, dict) or not isinstance(check.get("index"), int):
                continue
            args = check.get("args") if isinstance(check.get("args"), dict) else {}
            located[(claim.get("id"), check.get("index"))] = (
                claim.get("id"),
                check_digest(str(check.get("check") or ""), args),
                check.get("status"),
            )
    updated = [dict(item) for item in items]
    by_key = {item_key(item): item for item in updated}
    for assessment in assessments:
        if not isinstance(assessment, dict) or assessment.get("kind") != "check":
            continue
        found = located.get((assessment.get("claim_id"), assessment.get("index")))
        if found is None:
            continue
        item = by_key.get((found[0], found[1]))
        if item is None:
            continue
        disposition = assessment.get("disposition")
        if disposition == "must_fix":
            item["decision"] = "must_fix"
        elif disposition == "accept":
            item["decision"] = "accepted"
        elif disposition in {"", "pass"}:
            item["decision"] = "pass" if found[2] == "pass" else "not_assessed"
        else:
            continue
        text = assessment.get("text")
        if item["decision"] in {"must_fix", "accepted"} and isinstance(text, str) and text.strip():
            item["comment"] = text.strip()
    return updated


def status_for_item(claim_result: dict, item: dict) -> str | None:
    """The re-check status for this item. None when the claim result has no such Check."""
    _claim_id, digest = item_key(item)
    for check in claim_result.get("checks") or []:
        if not isinstance(check, dict):
            continue
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        if check_digest(str(check.get("check") or ""), args) == digest:
            status = check.get("status")
            return str(status) if isinstance(status, str) else None
    return None


def recheck_item(
    repo: Path,
    claims_dir: Path,
    items: list[dict],
    claim_id: str,
    digest: str,
    text: str,
    *,
    name: str | None = None,
) -> list[dict]:
    """Run the Claim and merge that Check's status onto the same item."""
    from checks.run import run_claim
    from common.store import load_claim

    claim = load_claim(Path(claims_dir) / f"{claim_id}.json")
    result = run_claim(repo, claim)
    updated = []
    found = False
    for item in items:
        key = item.get("key") if isinstance(item.get("key"), dict) else {}
        if key.get("claim_id") == claim_id and key.get("check_digest") == digest:
            found = True
            status = status_for_item(result, item)
            if status is not None:
                item = apply_recheck(item, status, remediation=text, name=name)
        updated.append(item)
    if not found:
        raise ModelError("review_item", "check_digest", "an item in this workspace")
    return updated


def latest_ready_remedy(temp_dir: Path, reports_dir: Path, run: dict) -> tuple[str, list[dict]] | None:
    """The newest Remedy Report whose Review Report is not this Run Result."""
    from review.compile import load_report, same_run

    if not Path(temp_dir).is_dir():
        return None
    found: list[tuple[str, list[dict]]] = []
    for path in sorted(Path(temp_dir).glob("review-report_*/review_items.json")):
        try:
            document = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict) or document.get("remedy") is not True:
            continue
        stem = path.parent.name
        report_path = Path(reports_dir) / f"{stem}.json"
        if report_path.is_file():
            try:
                report = load_report(report_path)
            except (ModelError, ValueError):
                continue
            if same_run(report, run):
                continue
        found.append((stem, load_items(path)))
    if not found:
        return None
    return found[-1]


def _workspace_from_return(repo: Path, return_to: str) -> Path | None:
    from urllib.parse import parse_qs, urlparse

    if "mode=remediation" not in str(return_to or ""):
        return None
    query = parse_qs(urlparse(return_to).query)
    source = (query.get("report") or query.get("result") or [""])[0]
    if not source:
        return None
    path = items_home(repo, Path(source))
    if not path.is_file():
        return None
    return path


def record_check_change(
    repo: Path,
    return_to: str,
    claim_id: str,
    old_check: str,
    old_args: dict,
    new_check: str,
    new_args: dict,
    *,
    name: str | None = None,
) -> None:
    """A changed Check configuration keeps the item and records old_check_digest."""
    path = _workspace_from_return(repo, return_to)
    if path is None:
        return
    old_digest = check_digest(old_check, old_args if isinstance(old_args, dict) else {})
    new_digest = check_digest(new_check, new_args if isinstance(new_args, dict) else {})
    if old_digest == new_digest:
        return
    updated = []
    for item in load_items(path):
        if item_key(item) == (claim_id, old_digest):
            item = retarget_check(
                item,
                new_check,
                new_args if isinstance(new_args, dict) else {},
                remediation="Check configuration updated.",
                name=name,
            )
        updated.append(item)
    write_items(path, updated)


def record_rebind(
    repo: Path,
    return_to: str,
    claim_id: str,
    *,
    signed: bool = False,
    matched: bool = False,
    name: str | None = None,
) -> None:
    """Rebind checks the binding and records that on the binding item."""
    path = _workspace_from_return(repo, return_to)
    if path is None:
        return
    items = load_items(path)
    digest = binding_digest()
    if not any(item_key(item) == (claim_id, digest) for item in items):
        items.append(_item(claim_id, digest, "pass" if matched else "not_assessed", {}))
    updated = []
    for item in items:
        if item_key(item) == (claim_id, digest):
            item = append_history(
                item,
                remediation="Rebound the Claim.",
                action="rebind" if signed else None,
                name=name if signed else None,
            )
            if matched:
                item["decision"] = "pass"
        updated.append(item)
    write_items(path, updated)


def retire_live_check(claims_dir: Path, claim_id: str, digest: str) -> None:
    """Remove the Check, or the Claim when none remain. Uses the existing Claim writers."""
    from common.store import load_claim, save_claim
    from studio.claim.impl.bind import rebind, retire_claim

    if digest == binding_digest():
        retire_claim(claims_dir, claim_id)
        return
    path = Path(claims_dir) / f"{claim_id}.json"
    if not path.is_file():
        raise ModelError(f"claim {claim_id}", "id", "an existing claim file")
    claim = load_claim(path)
    kept = []
    removed = False
    for check in claim.get("checks") or []:
        if not isinstance(check, dict):
            continue
        args = check.get("args") if isinstance(check.get("args"), dict) else {}
        if not removed and check_digest(str(check.get("check") or ""), args) == digest:
            removed = True
            continue
        kept.append(check)
    if not removed:
        raise ModelError("review_item", "check_digest", "a Check on this Claim")
    if not kept:
        retire_claim(claims_dir, claim_id)
        return
    save_claim(claims_dir, rebind(claim, checks=kept))


def remedy_report_path(report_path: Path) -> Path:
    if check_directory(report_path) is not None and report_path.name == "review-report.json":
        return report_path.with_name("remedy-report.json")
    name = report_path.name
    if name.endswith(".json"):
        name = name[: -len(".json")] + ".remedy.json"
    else:
        name = name + ".remedy.json"
    return report_path.with_name(name)


def revoked_remedy_names(document: object) -> set[str]:
    """Filenames of remedy seals that no longer lock the round."""
    if not isinstance(document, dict):
        return set()
    names: set[str] = set()
    for row in document.get("remedy_revoked") or []:
        if isinstance(row, dict) and isinstance(row.get("report"), str) and row["report"]:
            names.add(row["report"])
    return names


def active_remedy_report(directory: Path | None, document: object) -> Path | None:
    """The newest remedy seal, unless that seal has been revoked."""
    if directory is None:
        return None
    newest = _newest_signed(Path(directory), "remedy-report.json", "remedy-report_*.json")
    if newest is None or newest.name in revoked_remedy_names(document):
        return None
    return newest


def remediation_is_sealed(items_path: Path) -> bool:
    """A round is sealed by its newest unrevoked remedy file, or by the lock when no file exists."""
    document: dict = {}
    if items_path.is_file():
        try:
            loaded = read_json(items_path)
        except (OSError, ValueError):
            loaded = {}
        if isinstance(loaded, dict):
            document = loaded
    directory = check_directory(items_path)
    if directory is not None:
        newest = _newest_signed(directory, "remedy-report.json", "remedy-report_*.json")
        if newest is not None:
            return newest.name not in revoked_remedy_names(document)
    return document.get("remedy_locked") is True


def _newest_signed(directory: Path, *patterns: str) -> Path | None:
    """The newest signed file in a Check directory. Missing directories yield nothing."""
    if not directory.is_dir():
        return None
    found: list[Path] = []
    for pattern in patterns:
        for path in directory.glob(pattern):
            if not path.is_file():
                continue
            try:
                document = read_json(path)
            except (OSError, ValueError):
                continue
            if not _snapshot_name(path.name) and path.name not in {"review-report.json", "remedy-report.json"}:
                continue
            if isinstance(document, dict) and isinstance(document.get("signed"), dict):
                found.append(path)
    if not found:
        return None
    return sorted(found, key=lambda path: _round_stamp(path.stem))[-1]


def _newest_sealed_review(directory: Path) -> tuple[Path, Path] | None:
    """A signed review snapshot and the sealed items beside it. The work file is not a snapshot."""
    if not directory.is_dir():
        return None
    pairs: list[tuple[Path, Path]] = []
    legacy = directory / "review-report.json"
    if legacy.is_file() and (directory / "review_items.json").is_file():
        pairs.append((legacy, directory / "review_items.json"))
    for report_path in directory.glob("review-report_*.json"):
        if not _snapshot_name(report_path.name):
            continue
        sealed = report_path.with_name(report_path.stem + ".items.json")
        if report_path.is_file() and sealed.is_file():
            pairs.append((report_path, sealed))
    signed = []
    for report_path, items_path in pairs:
        try:
            report = read_json(report_path)
            items = read_json(items_path)
        except (OSError, ValueError):
            continue
        if (
            isinstance(report, dict)
            and isinstance(report.get("signed"), dict)
            and isinstance(items, dict)
            and isinstance(items.get("signed"), dict)
        ):
            signed.append((report_path, items_path))
    if not signed:
        return None
    return sorted(signed, key=lambda pair: _round_stamp(pair[0].stem))[-1]


def remedy_bundle(
    reports_dir: Path, stem: str, *, results_dir: Path | None = None
) -> tuple[list[dict], list[dict]]:
    """Remedy items, then the signed review items they started from."""
    folder = Path(reports_dir)
    remedy_items: list[dict] = []
    remedy_path = folder / f"{stem}.remedy.json"
    signed_path = folder / f"{stem}.items.json"
    if results_dir is not None:
        directory = Path(results_dir) / stem
        newest = _newest_signed(directory, "remedy-report.json", "remedy-report_*.json")
        if newest is not None:
            remedy_path = newest
            pair = _newest_sealed_review(directory)
            if pair is not None:
                signed_path = pair[1]
    if remedy_path.is_file():
        try:
            document = read_json(remedy_path)
        except (OSError, ValueError):
            document = None
        if isinstance(document, dict):
            remedy_items = [row for row in document.get("items") or [] if isinstance(row, dict)]
    signed_items = list(remedy_items)
    report_path = signed_path.with_name(
        "review-report.json" if signed_path.name == "review_items.json" else signed_path.name.replace(".items.json", ".json")
    )
    signed_items = _verified_decision_rows(report_path, signed_path, signed_items)
    return remedy_items, signed_items


def latest_signed_remedy(
    reports_dir: Path,
    run: dict,
    *,
    results_dir: Path | None = None,
    skip_directory: Path | None = None,
) -> tuple[str, list[dict], list[dict]] | None:
    """The newest signed Remedy Report that does not belong to this Check.

    The remedy items carry the history. The third value is the newest signed
    review items from another Check, or this Remedy's own signed items.
    Identity is the Check directory. A matching result does not hide an earlier Remedy.
    """
    folder = Path(reports_dir)
    found: list[tuple[str, list[dict], list[dict]]] = []
    if folder.is_dir():
        found.extend(_legacy_remedies(folder, skip_directory))
    if results_dir is not None and Path(results_dir).is_dir():
        found.extend(_directory_remedies(Path(results_dir), skip_directory))
    if not found:
        return None
    found.sort(key=lambda row: _round_stamp(row[0]))
    stem, remedy_items, signed_items = found[-1]
    newer = latest_signed_review_items(
        folder, run, results_dir=results_dir, skip_directory=skip_directory
    )
    if newer:
        signed_items = newer
    return stem, remedy_items, signed_items


def _round_stamp(stem: str) -> str:
    return stem.split("_", 1)[1] if "_" in stem else stem


def _legacy_remedies(
    folder: Path, skip_directory: Path | None
) -> list[tuple[str, list[dict], list[dict]]]:
    from review.compile import load_report

    found: list[tuple[str, list[dict], list[dict]]] = []
    for path in sorted(folder.glob("review-report_*.remedy.json")):
        try:
            document = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict) or not isinstance(document.get("signed"), dict):
            continue
        stem = path.name[: -len(".remedy.json")]
        report_path = path.with_name(stem + ".json")
        if skip_directory is not None and path.parent.resolve() == Path(skip_directory).resolve():
            continue
        if report_path.is_file():
            try:
                load_report(report_path)
            except (ModelError, ValueError):
                continue
        remedy_items = [row for row in document.get("items") or [] if isinstance(row, dict)]
        signed_path = path.with_name(stem + ".items.json")
        signed_items = _verified_decision_rows(report_path, signed_path, remedy_items)
        found.append((stem, remedy_items, signed_items))
    return found


def _directory_remedies(
    results_dir: Path, skip_directory: Path | None
) -> list[tuple[str, list[dict], list[dict]]]:
    from review.compile import load_report

    found: list[tuple[str, list[dict], list[dict]]] = []
    paths = list(results_dir.glob("run-result_*/remedy-report.json"))
    paths.extend(results_dir.glob("run-result_*/remedy-report_*.json"))
    for path in sorted(paths):
        if skip_directory is not None and path.parent.resolve() == Path(skip_directory).resolve():
            continue
        try:
            document = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict) or not isinstance(document.get("signed"), dict):
            continue
        pair = _newest_sealed_review(path.parent)
        report_path = pair[0] if pair is not None else path.with_name("review-report.json")
        if report_path.is_file():
            try:
                load_report(report_path)
            except (ModelError, ValueError):
                continue
        remedy_items = [row for row in document.get("items") or [] if isinstance(row, dict)]
        items_path = pair[1] if pair is not None else path.with_name("review_items.json")
        signed_items = _verified_decision_rows(report_path, items_path, remedy_items)
        found.append((path.parent.name, remedy_items, signed_items))
    return found


def latest_signed_review_items(
    reports_dir: Path,
    run: dict,
    *,
    results_dir: Path | None = None,
    skip_directory: Path | None = None,
) -> list[dict]:
    """The newest signed review items that do not belong to this Check.

    History stays on the Remedy Report. This list is the decision baseline.
    A flat report is skipped when its embedded result equals this run, because
    that file cannot be tied to one Check. A Check directory is skipped only
    when it is this Check. Items count only when their digest matches the report.
    """
    found: list[tuple[str, list[dict]]] = []
    folder = Path(reports_dir)
    if folder.is_dir():
        for path in sorted(folder.glob("review-report_*.items.json")):
            stem = path.name[: -len(".items.json")]
            report_path = path.with_name(stem + ".json")
            rows = _signed_item_rows(report_path, path, run, skip_same_content=True)
            if rows:
                found.append((stem, rows))
    if results_dir is not None and Path(results_dir).is_dir():
        for directory in sorted(Path(results_dir).glob("run-result_*")):
            if not directory.is_dir():
                continue
            if skip_directory is not None and directory.resolve() == Path(skip_directory).resolve():
                continue
            legacy = directory / "review-report.json"
            rows = _signed_item_rows(
                legacy,
                directory / "review_items.json",
                run,
                skip_same_content=False,
            )
            if rows:
                found.append((directory.name, rows))
            for report_path in sorted(directory.glob("review-report_*.json")):
                if not _snapshot_name(report_path.name):
                    continue
                sealed = report_path.with_name(report_path.stem + ".items.json")
                rows = _signed_item_rows(report_path, sealed, run, skip_same_content=False)
                if rows:
                    found.append((report_path.stem, rows))
    if not found:
        return []
    found.sort(key=lambda row: _round_stamp(row[0]))
    return found[-1][1]


def _signed_item_rows(
    report_path: Path,
    items_path: Path,
    run: dict,
    *,
    skip_same_content: bool,
) -> list[dict]:
    from review.compile import load_report, same_run

    if not report_path.is_file() or not items_path.is_file():
        return []
    try:
        report = load_report(report_path)
    except (ModelError, OSError, ValueError):
        return []
    if not isinstance(report.get("signed"), dict):
        return []
    if skip_same_content and same_run(report, run):
        return []
    try:
        document = read_json(items_path)
    except (OSError, ValueError):
        return []
    if not isinstance(document, dict):
        return []
    return _bound_item_rows(report, document)


def _bound_item_rows(report: dict, document: dict) -> list[dict]:
    """The items file counts only when it is signed and still matches items_digest."""
    if not isinstance(document.get("signed"), dict):
        return []
    expected = report.get("items_digest")
    rows = [row for row in document.get("items") or [] if isinstance(row, dict)]
    if not rows or not isinstance(expected, str):
        return []
    if version_digest({"items": rows}) != expected:
        return []
    return rows


def _verified_decision_rows(report_path: Path, items_path: Path, fallback: list[dict]) -> list[dict]:
    """Use the sealed review items when they still match. Otherwise keep the fallback."""
    from review.compile import load_report

    if not report_path.is_file() or not items_path.is_file():
        return fallback
    try:
        report = load_report(report_path)
        document = read_json(items_path)
    except (ModelError, OSError, ValueError):
        return fallback
    if not isinstance(report, dict) or not isinstance(document, dict):
        return fallback
    return _bound_item_rows(report, document) or fallback


def projected_run_names(repo: Path) -> set[str]:
    """Run results written while a Remedy was still open. They are not their own rows."""
    temp = studio_temp_dir(repo)
    names: set[str] = set()
    if not temp.is_dir():
        return names
    for path in temp.glob("*/review_items.json"):
        try:
            document = read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict):
            continue
        for name in document.get("projected_runs") or []:
            if isinstance(name, str) and name:
                names.add(name)
    return names


def report_items_path(report_path: Path) -> Path:
    """Sealed items for a snapshot sit beside that file. The work file stays unsigned."""
    if report_path.name in {"review-report.json", "remedy-report.json"}:
        directory = check_directory(report_path)
        if directory is not None:
            return directory / "review_items.json"
    name = report_path.name
    if name.endswith(".json"):
        name = name[: -len(".json")] + ".items.json"
    else:
        name = name + ".items.json"
    return report_path.with_name(name)
