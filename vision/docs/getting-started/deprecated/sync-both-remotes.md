# Sync both remotes (deprecated)

**Removed.** Single source of truth: [RI-SE/curbpack](https://github.com/RI-SE/curbpack).

Use branch + PR + merge on RI-SE/curbpack. Public site: **https://ri-se.github.io/curbpack/**.

See [repo ops hardening](repo-ops-hardening.md).

If asked to “make remotes identical” or run a full-tree parity/mirror sync, **stop** — that flow is forbidden. Product changes land on RI-SE first; afelin catch-up is optional one-way merge from `corp-origin/main`. See [fork policy](../internal/fork-policy.md).
