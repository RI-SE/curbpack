# Future architecture policy

**Status:** Not in force. [`policies/architecture.md`](../../policies/architecture.md) governs the pilot. This file takes effect when EP-01 is accepted, by moving it to `policies/architecture.md`. Until then it authorizes no code moves.

**Applies to:** Curbpack Studio after the pilot. CTAM and Curbpack are sources to copy from. Do not change those repositories from this policy.

EP-02 remains the only planned reshape of the existing packages. This policy does not add a third directory layout and does not rename Requirements, Claims, Discovery, Checks, Compile, Review, or the application shell.

Delivery is [`future_cicd.md`](future_cicd.md). This file does not repeat its Make targets.

## KISS

A person must be able to read the file.

Prefer a copy of a small function over a shared function that needs flags, callbacks, or a new layer. Do not add an empty package.

## One unit, one file

A functional unit is one file. It contains only the functions it needs:

- a logic function that takes plain data and returns plain data
- a read function, a write function, or both, when the unit loads or saves

The public function loads when needed, decides whether this caller may do this, calls the logic, and saves when needed. Every outer call makes that decision again. The logic function does not call the edge, authentication, or the database.

Unit tests call the logic function. Separate tests cover the public function and the edges.

## Database

When the program has a database, one package owns it: `impl/db` in Python, `internal/db` in Go. The project chooses an ORM or the language's DB-API.

- All SQL and procedures live there.
- Values are bound parameters. A unit cannot pass SQL text in.
- Dynamic table or column names come from a fixed list in that package.
- A query that returns a user's rows takes the user id.
- The transaction is opened there.

Authentication and units call that package. No database means no db package. A file read stays in the unit. Studio stores packs as files. This section does not add a database.

## Two thin edges

A web route and a CLI main are thin. Each parses its own input and calls the unit's public function when that function already takes plain data. That is the whole sharing rule.

| Situation | What to do |
| --- | --- |
| The function already takes plain data | Both edges call it. No wrapper. |
| Sharing needs flags, callbacks, or a new layer | Copy the small piece. |
| Nothing logs in | No auth files. |
| No database | No db package. |
| CLI only | A thin main. No `apis/` and no `app/authorization.py`. |

## Authentication, when something logs in

There is no `verify.py`. Four places:

| File | Does | Does not |
| --- | --- | --- |
| `apis/credentials.py` | Login routes, including the list of OIDC issuers | Validate tokens on later calls |
| `app/authorization.py` | `mandatory` or `optional` on the route. Reads the bearer and calls impl | Parse the JWT or read the database |
| `impl/authentication/<method>.py` | One method per file. Checks that credential | Decide scopes for a later call |
| `impl/authorization.py` | Chooses the method, loads the user, requires the scopes the route declared | Contain SQL |

Other code reads the username through one function, not by digging in the token. `user_management.py` is the user unit, one file, and it calls the db package.

Route scopes are the check for that HTTP call. A rule about a record, such as who owns it, stays in that unit's public function.

This split follows the OpenEO DES driver (October 2024). SQL that lived in its user management moves into the db package.

Python, for a web app that has login:

```text
app/main.py
app/authorization.py
apis/credentials.py
apis/<area>.py
impl/authentication/<method>.py
impl/authorization.py
impl/user_management.py
impl/<subsystem>/<unit>.py
impl/db/engine.py
impl/db/user.py
impl/db/sql/<procedure>.sql
```

Go uses the same roles under `cmd/` and `internal/`. A CLI edge is `cli.py` or `cmd/<app>/main.go`. Omit every file the program does not need.

## Evidence

A protected operation has one row: operation, check, test name. The row is wrong if the test is missing.

- Login: a valid credential yields a user id. An invalid one is rejected. NIS2 Article 21(2)(j). SSDF PW.8.
- A protected change: no login is rejected, an authenticated caller who is not allowed is rejected, and an allowed caller proceeds. NIS2 Article 21(2)(i). SSDF PW.1 and PW.8.
- An operation without that check is explicitly open, with a test that shows it is open.

The existence of an auth file is not evidence. SSDF and NIS2 here are a map to controls, not a conformance claim. Record the rows in `docs/ssdf/`. That table is separate from CI pass and fail lines in [`future_cicd.md`](future_cicd.md).
