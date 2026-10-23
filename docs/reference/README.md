# Packs v2 reference

`packs2.md` was imported from Curbpack's `docs/reference/packs2.md` at commit `b07b8deb9fed331b493241251087ce7ce648f5e4` (2026-10-23, `docs: replace fresh and owned with four Git checks`).

Source SHA-256: `67bc92680cf43dec37e414d2b5fde50403188fec6e7193562736e3271deb2f18`.

Apart from removal of dead links to the old companion documents `packs.md` and `dataflow.md`, and trailing whitespace on the status line and one semantics line, the contract text is unchanged. That includes §4 and §4.1 (`git_fresh`, `git_signed`, `git_author`, `git_signer`). This is now Studio's local reference for the persistent data contract; the old repository is not needed to read it. The upstream file is labelled **design sketch**. Importing it does not resolve open design questions or claim that every feature is implemented. Validate supported shapes against `common/validate.py` and the tests; resolve actual differences explicitly before changing a persisted format.

Future contract changes are made and reviewed in Studio, not silently synchronized from a retired repository. Older Curbpack `packs.md` describes the v1 rule-pack model; it must not replace Packs v2 here.
