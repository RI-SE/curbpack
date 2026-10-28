# curbcheck

`curbcheck` evaluates the Claims in a product repository and writes one run result. The process exit code is the result a person or a CI job uses. The JSON file is the result a later review reads.

There is one repository command. It does not scan, init, heal, export, attest, or prepare a release. Pack choice lives in the product's `curbpack.json`. The question a Check asks lives in that Claim's `checks[]`. The data contract is [Packs v2](packs2.md) §2.3–§2.5, §3.1, and §4. This page is how you start the program and how you read what it prints.

A source checkout and a packaged binary take the same arguments. The Check page in Curbpack Studio calls the same runner. Skip is the `--skip` flag; that page has no skip control.

## Start

From a source checkout of this repository, including Linux:

```bash
python3 -m checks --repo /path/to/product \
  --packs /path/to/packs-root \
  --out /path/to/product/.curbpack/run-result.json
```

On Windows, from the same kind of checkout, the module start is `python -m checks` with the same flags.

`make package` on the matching host also writes a single file:

| Host | File |
| --- | --- |
| macOS ARM64 | `dist/curbcheck-macos-arm64` |
| Windows x64 | `dist/curbcheck-windows-x64.exe` |

Run that file with the same `--repo`, `--packs`, `--out`, and `--skip`. Git is the `git` already on the machine. The Studio application file is a different program and does not contain the check tools.

`-h` prints the four flags. The usage line names whatever file started the process (`__main__.py` from `python3 -m checks`, or the packaged file name). There is no `--version` flag. The build string is `tool_version` inside the result. In this tree that string is `0.0.1a`, from `common/version.py`.

## Arguments

| Flag | Required | Meaning |
| --- | --- | --- |
| `--repo` | yes | Product repository. The process reads `<repo>/curbpack.json` and `<repo>/claims/*.json`. |
| `--packs` | yes | Directory whose children are pack directories. Each selected id is `<packs>/<pack-id>/pack.json`. This is a path, not a comma-separated list of ids. |
| `--out` | yes | File that receives the run result. Parent directories are created. The file is replaced in one step after the result has been validated. |
| `--skip` | no | `claim-id=reason`. Repeat the flag to skip more than one Claim. See [Skip](#skip). |

`--repo`, `--packs`, and `--out` are paths. A missing flag, or `--skip` without an `=` , exits 2 and writes nothing:

```text
skip needs claim-id=reason, got 'nope'
```

There is no global `--as-of`, `--packs id,id`, `--json`, `--heal`, or `--diff`. `git_fresh` carries its own `as_of` inside the Claim. The run result file is the JSON; stdout is a short summary.

## What the run reads

`curbpack.json` sits at the repository root. The runner validates `packs`, `requirements`, `exclude_requirements`, and `hunt` when they are present. It uses `packs` together with either `requirements` or `exclude_requirements` to decide which Requirements are in scope. A valid `hunt` block stays in the file; the run does not walk its globs or discovery sources.

`packs` is a list of pack ids. Use either `requirements` (only these ids) or `exclude_requirements` (every Requirement in the selected packs, minus these ids). A file that sets both stops before a result is written. An id in `requirements` that is not in the loaded packs stops the same way.

```json
{
  "packs": ["house-policy", "cra-baseline"]
}
```

For each id, the runner loads `<packs>/<id>/pack.json` and the Requirement JSON files beside it (every `*.json` in that directory except `pack.json`). The result records that pack's `id`, the `version` string from `pack.json`, and a digest of the pack directory. It does not fetch a newer pack, and it does not read `CURBPACK_PACKS_DIR` or `.curbpack.json`.

Claims are the `*.json` files directly inside `<repo>/claims/`, in filename order. Files in subdirectories are not loaded. Each file is one Claim, in the shape in Packs v2 §2.4. A Claim whose `checks` array is empty is omitted: it is a saved proposal, and it adds no row. A Claim whose `requirement_id` is outside the selection stops the run before a result is written. A Requirement that has no executed Claim adds no row either. The runner does not invent one.

The runner does not read `discovery_hints`, `note`, `remediation_hint`, or the Claim `description` to decide pass or fail. A missing or invalid Claim signature is not turned into a failed Check. Signing and the review report are later steps.

## What the run prints

After a result has been written, stdout is one summary. Claim status is padded to seven characters. Each configured Check follows, indented, with its zero-based index. A `detail` is appended after an em dash when that Check has one.

A passing Claim:

```text
wrote /path/to/run.json
claims 1 exit 0
pass    HOUSE-SECURITY-MD
  pass    [0] exist
  pass    [1] contents
```

A Claim whose file exists and whose content probes do not:

```text
wrote /path/to/run.json
claims 1 exit 1
fail    HOUSE-SECURITY-MD
  pass    [0] exist
  fail    [1] contents — SECURITY.md is 17 bytes, not >= 80; SECURITY.md has 3 words, not >= 20
```

`claims` is the number of rows in the result: Claims that had at least one Check. It is not a count of every file under `claims/`.

When the repository is a Git checkout with a commit and `git status --porcelain` is non-empty, one extra line is printed:

```text
worktree dirty: this result is not verification of that commit's exact content
```

The snapshot is taken before `--out` is written. A dirty tree can still exit 0 when every executed Check passed. A later run records `dirty` again if Git sees the result file, or any other change, inside the repository.

## The result file

One JSON object, Packs v2 §3.1. `tool` is `curbcheck`. The exit code is not a field.

```json
{
  "commit": "<HEAD, present only together with worktree>",
  "worktree": "clean",
  "packs": [
    { "id": "house-policy", "version": "0.1.0", "digest": "<pack directory digest>" }
  ],
  "tool": "curbcheck",
  "tool_version": "0.0.1a",
  "claims": [
    {
      "id": "HOUSE-SECURITY-MD",
      "digest": "<sha256 of the canonical Claim, without signed>",
      "status": "pass",
      "checks": [
        { "index": 0, "check": "exist", "args": { "paths": ["SECURITY.md"] }, "status": "pass" }
      ]
    }
  ]
}
```

`commit` and `worktree` appear together when `git rev-parse HEAD` and `git status --porcelain` both succeed. `worktree` is `clean` or `dirty`. Both keys are omitted when the directory is not such a checkout, or when `git` cannot be run. A directory that is not a Git checkout is still evaluated.

`digest` on a Claim row is the version digest of that whole Claim, with `signed` removed before hashing. Reordering `checks[]` changes the digest. A later reader must not attach this result to a newer Claim that reused the id.

Claim status is `fail` if any Check failed, otherwise `skipped` if any Check was skipped, otherwise `pass`. Each Check result has `index`, `check`, the `args` that were configured, and `status`. `detail` is omitted on `pass` and required on `fail` and `skipped`. These are mechanical outcomes. They are not a legal conclusion about the product.

A finished run replaces `--out`, including a run that exits 1 because a Check failed or was skipped, and including a run whose `claims` array is empty. An empty array is a real result and is not a successful verification.

## Exit codes

| Code | When |
| --- | --- |
| 0 | At least one Check ran, and every Claim row and every Check is `pass`. A dirty worktree does not change this. |
| 1 | A Check failed or was skipped, or no Check ran. Also the process status when the run stops with an exception before writing. The summary line then shows `exit 1`, or the exception text is the whole error. |
| 2 | The arguments could not be parsed, or a `--skip` value has no `=`. Nothing is written. |

Exit 0 is the repository gate. A Check tool's own process often exits 0 even when its JSON says `fail`; that code belongs to the tool, and CI should use the repository command.

## Skip

```bash
python3 -m checks --repo /path/to/product \
  --packs /path/to/packs-root \
  --out /path/to/run.json \
  --skip HOUSE-SECURITY-MD='not this build'
```

The Claim is not executed. Every configured Check on that Claim is `skipped`, and each `detail` is the reason with surrounding whitespace removed. The Claim status is `skipped`. The process exits 1:

```text
wrote /path/to/run.json
claims 1 exit 1
skipped HOUSE-SECURITY-MD
  skipped [0] exist — not this build
  skipped [1] contents — not this build
```

Repeat `--skip` for another Claim. The same id twice keeps the last reason. The reason may contain `=`; the split is on the first one. An id that is not an executed Claim in this run is ignored, and the other Claims still run. A reason that is empty or only whitespace stops the run, writes nothing, and exits 1:

```text
claim HOUSE-SECURITY-MD: field detail: expected a reason for skipped
```

Skip is per Claim, not per Check index. It does not delete the Claim file and it does not hide a missing path inside a Check that still runs.

## Which Checks run

`checks/available_checks.json` is the registry: Check id, command name, and args schema. The runner validates each `checks[]` entry against that schema, then starts the command. One Claim may list several Checks, including the same id with different arguments. A failure on one Check does not stop the later Checks in that Claim, or the later Claims.

Paths in args are relative to `--repo`. An absolute path, or a path that contains a `..` segment, fails that Check before a tool starts. A symlink that resolves outside the repository fails that Check; the outside bytes are not read and do not appear in `detail`.

| Check id | Command | In this build |
| --- | --- | --- |
| `exist` | `curbcheck-exist` | Runs |
| `contents` | `curbcheck-contents` | Runs |
| `git_fresh` | `curbcheck-git` | Runs |
| `git_author` | `curbcheck-git` | Runs |
| `git_signed` | `curbcheck-git` | Registered. The tool answers that this id is not implemented. |
| `git_signer` | `curbcheck-git` | Registered. The tool answers that this id is not implemented. |
| `dep_ban` | `curbcheck-node` | Node: inspects root `package.json` dependency maps for an exact banned version string. |
| `npm_dep_ban` | `curbcheck-node` | Registry alias id of `dep_ban`. |
| `manifest_dep_ban` | `curbcheck-node` | Registry alias id of `dep_ban`. |
| `fresh` | `curbcheck-fresh` | Registered so a discovery form can save it. Not a Packs v2 §4 id. The command is not installed, so the Check fails. |
| `owned` | `curbcheck-owned` | Registered so a discovery form can save it. Not a Packs v2 §4 id. The command is not installed, so the Check fails. |

An id that is not in the registry fails that Check with a detail that names the unknown type. The result file is still written. A missing command is recorded as `fail` with a detail such as `check tool 'curbcheck-node' is unavailable`. The next Check still runs. None of these are `skipped`, and none of them are `pass`.

`file_present` is not a Check id.

### `exist`

Every entry in `paths` must be a file. The bytes are not read. Anything that is not a file fails the Check, and `detail` says that path is absent (`SECURITY.md is absent`). Several paths are joined with `; `.

```json
{ "check": "exist", "args": { "paths": ["SECURITY.md"] } }
```

`paths` is required and must contain at least one non-empty string. A single `path` field is the wrong shape for `exist`.

### `contents`

The same files, then the probes. `path` is one file. `paths` is the same probes on each file. Exactly one of those two shapes, plus `probes` with at least one probe.

A missing file fails the Check and the detail says the file is absent. Probes are not reported for a file that is absent. When every file is present, each probe runs, and the failures are joined with `; `.

| Probe `kind` | Other fields | Passes when |
| --- | --- | --- |
| `size` | `bytes` (integer), `op` | The file's length compared with `bytes`. `op` is `>`, `>=`, `<`, or `<=`. |
| `words` | `n` (integer), `op` | The whitespace-separated word count, same operators. |
| `headers` | `headers` (one or more strings) | Each string occurs as a literal substring. The first missing header is named. This is not a regular expression. |
| `token` | — | The text contains the repository directory name, a `name` from `package.json`, or a `module` line from `go.mod`. |
| `pattern` | `pattern` | The regular expression matches nothing in the file. A match fails the Check: the pattern is forbidden text. An invalid expression fails the Check and names the expression error. |
| `placeholder` | — | None of this build's placeholder patterns match. |

The placeholder patterns in this build, from `checks/filecheck.py`, are case-insensitive: the words `lorem ipsum`, `TODO`, `TBD`, `FIXME`, and `placeholder`, and the text `<placeholder>`.

```json
{
  "check": "contents",
  "args": {
    "path": "SECURITY.md",
    "probes": [
      { "kind": "size", "bytes": 80, "op": ">=" },
      { "kind": "words", "n": 20, "op": ">=" },
      { "kind": "headers", "headers": ["# Security"] }
    ]
  }
}
```

A size miss reads `SECURITY.md is 17 bytes, not >= 80`. A word miss reads `SECURITY.md has 3 words, not >= 20`. A header miss reads `SECURITY.md is missing header '## Identified Risks'`. A forbidden match reads `SECURITY.md matches forbidden pattern 'SECRET'`. A placeholder reads `SECURITY.md contains placeholder text 'TODO'`.

### `git_fresh` and `git_author`

Both ids are subcommands of `curbcheck-git`. Each has its own args and its own result. The relevant commit is the last commit reachable from HEAD that changes `path`. History is not followed across a rename. The run-level `commit` stays HEAD. These Checks do not add a field of their own; on failure, `detail` names the cause and, when a commit was found, that commit id.

The path must be a regular file or a symlink, tracked, and the same blob as HEAD. A missing path, an untracked path, or a worktree entry that differs from HEAD fails that Check even when other files are clean. The run-level dirty warning is separate: another dirty file can leave `worktree` as `dirty` while this path still passes.

`git` is taken from `PATH`. If the binary cannot be started, the detail is `git is unavailable`. The child process drops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_COMMON_DIR`, `GIT_NAMESPACE`, `GIT_GLOB_PATHSPECS`, and `GIT_NOGLOB_PATHSPECS`, and sets `GIT_LITERAL_PATHSPECS=1`, so those variables cannot point the Check at a different repository.

`git_fresh` asks how old that commit is, measured from `as_of`, not from the wall clock.

```json
{
  "check": "git_fresh",
  "args": {
    "path": "SECURITY.md",
    "max_age_days": 90,
    "as_of": "2026-10-23T06:00:00Z"
  }
}
```

`max_age_days` is an integer greater than or equal to 0. `as_of` is an RFC 3339 instant with a time and a `Z` or numeric offset (`2026-10-23T06:00:00Z`). A date alone is rejected. Age in whole days is `floor((as_of - committer_time) / 86400)`. The Check passes when that age is less than or equal to `max_age_days`. A committer time after `as_of` fails. A miss reads `SECURITY.md commit <id> is 12 days old, max 2`, or `SECURITY.md commit <id> is after as_of`.

`git_author` compares the author name and email on that commit. It does not verify a signature. Supply `name`, `email`, or both. Comparison is exact and case-sensitive.

```json
{
  "check": "git_author",
  "args": {
    "path": "SECURITY.md",
    "name": "Anna",
    "email": "anna@example.com"
  }
}
```

A mismatch reads `SECURITY.md author name 'Other' and email 'other@example.com'; commit <id>`, listing only the fields that were supplied and differed. An author record that is not UTF-8, or that Git did not return as three fields, fails with its own detail.

### `git_signed` and `git_signer`

Both are registered on `curbcheck-git`. This build's handler answers `not implemented`, the Check is `fail`, and later Checks still run. The argument shapes the registry already accepts are in Packs v2 §4.1:

| Check id | Args |
| --- | --- |
| `git_signed` | `path`, plus exactly one of `allowed_signers` (a relative path) or `openpgp` with the value `repo` |
| `git_signer` | `path`, `signer`, plus that same one trust input |

### `dep_ban`, `fresh`, and `owned`

`dep_ban`, `npm_dep_ban`, and `manifest_dep_ban` take `package` and `banned_versions` (one or more strings) and run as subcommands of `curbcheck-node` against root `package.json` — same shape as Git Checks on `curbcheck-git`. `fresh` takes `path` plus either `max_age_days` or `since_ref`. `owned` takes `path`, `bind_repo_token` set to `true`, and an optional `name` or `email`. `fresh` and `owned` are not installed, so a run records `fail` and the detail says the check tool is unavailable.

## The three programs the runner starts

A repository run does not ask you to pick a tool. For each Check, the runner starts the command named in the registry:

```text
<command> <check-id> --repo <repo> --args <json object>
```

`<command>` is `curbcheck-exist`, `curbcheck-contents`, or `curbcheck-git`. Stdout is one JSON object, `{"status":"pass"}` or `{"status":"fail","detail":"..."}`. The repository command copies that into the run result. A pass is kept only when the tool exits 0 and the object says `pass`. Anything else becomes `fail`.

From a source checkout the runner puts `checks/bin` on the child's `PATH` and the repository root on `PYTHONPATH`, then starts the script. A packaged build is that same entry in one file. When the file is started with argv0 set to `curbcheck-exist`, `curbcheck-contents`, or `curbcheck-git`, it runs that tool. The Studio application file stays a separate program.

Starting a tool by hand is a debugging interface. Its `-h` lists `check`, `--repo`, and `--args`. A usage error from the tool exits 2. A tool that parsed its arguments and printed a result exits 0, including when `status` is `fail`. Judge the repository command, or the JSON `status`, for the Check outcome.

## Runs that write nothing

These stop with an exception on stderr and exit 1. `--out` is left as it was, including left absent.

| Situation | What you see |
| --- | --- |
| `<repo>/curbpack.json` is missing | `FileNotFoundError` naming that path |
| That file, a pack file, or a Claim file is not JSON | `ValueError` naming the path |
| `requirements` and `exclude_requirements` are both set | `ModelError` on `curbpack.json` |
| A `requirements` id is not in the loaded packs | `ModelError` naming that id |
| A selected pack directory has no `pack.json` | `ModelError` naming the directory it expected |
| A Claim's `requirement_id` is not selected | `ModelError` on that Claim |
| `--skip` has an `=` and the reason is empty | `ModelError` asking for a reason |

A Check that fails validation, or whose tool is missing, does not belong in this list. That Check is a `fail` row, and the result file is written.

## Related pages

| Page | What it settles |
| --- | --- |
| [Configuration](configuration.md) | `curbpack.json`, pack selection, and repository paths |
| [Packs v2](packs2.md) §3.1 and §4 | The result document and the Check argument contract |
| `checks/ARCHITECTURE.md` | What the runner loads, and which sentences the current code follows |
| `docs/user-guides/ci-cd.md` | Using this exit status as a job result |
| `docs/testing/README.md` | `make test-curbcheck` on a prepared clone. That target is the suite, not an extra curbcheck command |
