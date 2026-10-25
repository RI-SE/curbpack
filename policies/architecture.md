# Architecture policy

Keep the design as simple as the approved user stories allow.

- **Packs v2** in `docs/reference/packs2.md` is authoritative for Pack, Requirement, Claim, signing, and result formats. Do not create alternative persistent versions of these objects.
- Keep one system architecture and one architecture contract per actual subsystem when these have been reconciled with the imported pilot. Do not create extra layers or entities without a concrete requirement and an explicit architecture decision.
- Preserve the existing separation: Requirements/Pack Editor, Claims (including Discovery), Checks, Compile, Review, and the application shell. Treat these as existing responsibilities, not a mandate to move code today.
- Each proposed architecture change must state the observable problem, the simplest alternative, the affected contract, and how the change will be tested.
- Do not rewrite an architecture contract during an ordinary implementation task unless the maintainer has explicitly authorized the architecture change.
- If imported code and a target document conflict, report the mismatch. Do not silently change behavior or the contract.
- Curbpack Studio and curbcheck stay in this repository. `checks/` may import `common/`. It does not import `app`, `pilot_app`, `requirements.ui`, `claims.ui`, review, or scaffold. A later repository for curbcheck is a move of `checks/` plus the part of `common/` it uses. Do not copy `common/` to make that move early.
- `make test` is the Studio suite. curbcheck's verification is `make test-curbcheck` and lives under `tests/check/`. The app suite does not absorb that tree, and that tree does not drive the app.
