"""Git provenance Checks. Invoked by curbcheck-git."""

from __future__ import annotations

import math
import os
import stat
import subprocess
from pathlib import Path

from checks.schema import parse_rfc3339
from common.errors import ModelError

# These point Git at a different repository or pathspec dialect than the repo argument.
_GIT_ENV_DROP = frozenset(
    {
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_GLOB_PATHSPECS",
        "GIT_NOGLOB_PATHSPECS",
    }
)


def _git_child_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if key not in _GIT_ENV_DROP}
    env["GIT_LITERAL_PATHSPECS"] = "1"
    return env


def _git_run(repo: Path, *args: str, input_text: str | None = None) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), "-c", "i18n.logOutputEncoding=utf-8", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=_git_child_env(),
            input=input_text,
        )
    except FileNotFoundError:
        return None


def _git_run_bytes(repo: Path, *args: str) -> subprocess.CompletedProcess | None:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            env=_git_child_env(),
        )
    except FileNotFoundError:
        return None


def _entry_path(repo: Path, relative: str) -> Path:
    """Worktree path without resolving a final symlink."""
    root = repo.resolve()
    path = root / relative
    parent = path.parent.resolve()
    if parent != root and root not in parent.parents:
        raise ModelError("check", "args.path", "a path inside the repository")
    return path


def _head_mode_and_blob(repo: Path, relative: str) -> tuple[str, str] | None:
    """Mode and blob at HEAD. None if Git failed. Empty strings when the path is absent."""
    head = _git_run(repo, "ls-tree", "HEAD", "--", relative)
    if head is None or head.returncode != 0:
        return None
    parts = head.stdout.split()
    if len(parts) < 3:
        return "", ""
    return parts[0], parts[2]


def _symlink_target_text(target: str) -> str:
    """Link text Git stores. On Windows that text uses forward slashes."""
    if os.name != "nt":
        return target
    text = target.replace("\\", "/")
    if text.startswith("//?/"):
        text = text[4:]
    return text


def _worktree_blob(repo: Path, relative: str) -> str | None:
    """Blob id Git would record for the worktree entry. None if Git failed."""
    path = _entry_path(repo, relative)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return ""
    if stat.S_ISLNK(info.st_mode):
        hashed = _git_run(
            repo,
            "hash-object",
            "--stdin",
            input_text=_symlink_target_text(os.readlink(path)),
        )
    elif stat.S_ISREG(info.st_mode):
        hashed = _git_run(repo, "hash-object", "--", relative)
    else:
        return ""
    if hashed is None or hashed.returncode != 0:
        return None
    return hashed.stdout.strip()


def _worktree_differs_from_head(repo: Path, relative: str) -> bool | None:
    """True when the worktree entry is not the blob at HEAD. None if Git failed."""
    head = _head_mode_and_blob(repo, relative)
    blob = _worktree_blob(repo, relative)
    if head is None or blob is None:
        return None
    mode, head_blob = head
    if not head_blob or not blob:
        return True
    path = _entry_path(repo, relative)
    if stat.S_ISLNK(path.lstat().st_mode):
        return mode != "120000" or blob != head_blob
    if mode == "120000" or blob != head_blob:
        return True
    if not _filemode_tracked(repo):
        return False
    recorded = "100755" if path.lstat().st_mode & 0o111 else "100644"
    return recorded != mode


def _filemode_tracked(repo: Path) -> bool:
    probed = _git_run(repo, "config", "--get", "core.filemode")
    if probed is None or probed.returncode != 0:
        return True
    return probed.stdout.strip().lower() != "false"


def _last_change(repo: Path, relative: str) -> tuple[str, str] | None:
    """Commit id and committer instant for the last commit that changes the path."""
    log = _git_run(repo, "log", "-1", "--no-show-signature", "--format=%H%n%cI", "HEAD", "--", relative)
    if log is None or log.returncode != 0:
        return None
    lines = [line.strip() for line in log.stdout.splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    return lines[0], lines[1]


def _fail_with_commit(repo: Path, relative: str, cause: str) -> dict:
    found = _last_change(repo, relative)
    if found is None:
        return {"status": "fail", "detail": cause}
    return {"status": "fail", "detail": f"{cause}; commit {found[0]}"}


def _path_error_detail(relative: str, exc: Exception) -> str:
    if isinstance(exc, NotADirectoryError):
        return f"{relative} is not a directory path"
    if isinstance(exc, RuntimeError) and "Symlink loop" in str(exc):
        return f"{relative} is a symlink loop"
    return f"{relative} cannot be read"


def _not_a_directory_path(repo: Path, relative: str) -> bool:
    """True when a parent of relative exists and is not a directory.

    Windows reports that path as missing. POSIX raises NotADirectoryError.
    """
    cursor = repo
    for part in Path(relative).parts[:-1]:
        cursor = cursor / part
        try:
            info = cursor.lstat()
        except FileNotFoundError:
            return False
        except NotADirectoryError:
            return True
        if stat.S_ISLNK(info.st_mode):
            try:
                if not cursor.is_dir():
                    return True
            except OSError:
                return True
            continue
        if not stat.S_ISDIR(info.st_mode):
            return True
    return False


def _prepare_git_path(repo: Path, relative: str) -> dict | None:
    """Fail when path is not a clean tracked entry. None when history may be read."""
    probe = _git_run(repo, "rev-parse", "--is-inside-work-tree")
    if probe is None:
        return {"status": "fail", "detail": "git is unavailable"}
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return {"status": "fail", "detail": f"{relative} has no Git metadata"}
    try:
        entry = _entry_path(repo, relative)
        try:
            info = entry.lstat()
        except FileNotFoundError:
            if _not_a_directory_path(repo, relative):
                return {"status": "fail", "detail": f"{relative} is not a directory path"}
            return _fail_with_commit(repo, relative, f"{relative} is absent")
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
            return _fail_with_commit(repo, relative, f"{relative} is absent")
        listed = _git_run(repo, "ls-files", "--", relative)
        if listed is None:
            return {"status": "fail", "detail": "git is unavailable"}
        if listed.returncode != 0:
            return {"status": "fail", "detail": f"{relative} has no Git metadata"}
        if not listed.stdout.strip():
            return {"status": "fail", "detail": f"{relative} is untracked"}
        differs = _worktree_differs_from_head(repo, relative)
        if differs is None:
            return {"status": "fail", "detail": "git is unavailable"}
        if differs:
            return _fail_with_commit(repo, relative, f"{relative} differs from HEAD")
        return None
    except ModelError as exc:
        return {"status": "fail", "detail": str(exc)}
    except (OSError, RuntimeError) as exc:
        return {"status": "fail", "detail": _path_error_detail(relative, exc)}


_AUTHOR_UNREADABLE = object()


def _author_name_email(raw: bytes):
    """Name and email from a raw commit. None when the author bytes are not UTF-8."""
    header, _, _message = raw.partition(b"\n\n")
    for line in header.split(b"\n"):
        if not line.startswith(b"author "):
            continue
        body = line[len(b"author ") :]
        try:
            text = body.decode("utf-8")
        except UnicodeDecodeError:
            return None
        end = text.rfind(">")
        start = text.rfind(" <", 0, end if end >= 0 else None)
        if start < 1 or end < 0:
            return _AUTHOR_UNREADABLE
        name = text[:start]
        email = text[start + 2 : end]
        if not name or not email or not text[end + 1 :].strip():
            return _AUTHOR_UNREADABLE
        return name, email
    return _AUTHOR_UNREADABLE


def _author_of(repo: Path, relative: str):
    """Commit id, author name, and author email. Unreadable when the record is not three fields.

    The author line is read from the commit object. Git on Windows exits instead of
    printing an author that is not UTF-8, which would otherwise look like a missing commit.
    """
    listed = _git_run(repo, "rev-list", "-1", "HEAD", "--", relative)
    if listed is None or listed.returncode != 0 or not listed.stdout.strip():
        return None
    commit = listed.stdout.strip()
    raw = _git_run_bytes(repo, "cat-file", "commit", commit)
    if raw is None or raw.returncode != 0:
        return None
    parsed = _author_name_email(raw.stdout)
    if parsed is None:
        return None, None, None
    if parsed is _AUTHOR_UNREADABLE:
        return _AUTHOR_UNREADABLE
    name, email = parsed
    return commit, name, email


def run_git_fresh(repo: Path, args: dict) -> dict:
    """Age of the last commit that changed path, measured from args.as_of."""
    relative = args["path"]
    prepared = _prepare_git_path(repo, relative)
    if prepared is not None:
        return prepared
    found = _last_change(repo, relative)
    if found is None:
        return {"status": "fail", "detail": f"{relative} has no commit"}
    commit, stamp = found
    try:
        committer = parse_rfc3339(stamp)
        as_of = parse_rfc3339(args["as_of"])
    except ModelError as exc:
        return {"status": "fail", "detail": str(exc)}
    if committer > as_of:
        return {"status": "fail", "detail": f"{relative} commit {commit} is after as_of"}
    age = math.floor((as_of - committer).total_seconds() / 86400)
    if age <= args["max_age_days"]:
        return {"status": "pass"}
    return {
        "status": "fail",
        "detail": f"{relative} commit {commit} is {age} days old, max {args['max_age_days']}",
    }


def run_git_author(repo: Path, args: dict) -> dict:
    """Exact author name and email on the last commit that changed path. Not a signature."""
    relative = args["path"]
    prepared = _prepare_git_path(repo, relative)
    if prepared is not None:
        return prepared
    found = _author_of(repo, relative)
    if found == (None, None, None):
        return {"status": "fail", "detail": f"{relative} author is not UTF-8"}
    if found is _AUTHOR_UNREADABLE:
        return {"status": "fail", "detail": f"{relative} author record is unreadable"}
    if found is None:
        return {"status": "fail", "detail": f"{relative} has no commit"}
    commit, name, email = found
    mismatches = []
    if "name" in args and args["name"] != name:
        mismatches.append(f"name {name!r}")
    if "email" in args and args["email"] != email:
        mismatches.append(f"email {email!r}")
    if mismatches:
        listed = " and ".join(mismatches)
        return {"status": "fail", "detail": f"{relative} author {listed}; commit {commit}"}
    return {"status": "pass"}
