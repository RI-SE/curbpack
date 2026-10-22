# Architecture policy

Keep the design as simple as the approved user stories allow.

- **Packs v2** in the separate Curbpack repository is authoritative for Pack, Requirement, Claim, signing, and result formats. Do not create alternative persistent versions of these objects.
- Keep one system architecture and one architecture contract per actual subsystem when these have been reconciled with the imported pilot. Do not create extra layers or entities without a concrete requirement and an explicit architecture decision.
- Preserve the existing separation: Requirements/Pack Editor, Claims (including Discovery), Checks, Compile, Review, and the application shell. Treat these as existing responsibilities, not a mandate to move code today.
- Each proposed architecture change must state the observable problem, the simplest alternative, the affected contract, and how the change will be tested.
- Do not rewrite an architecture contract during an ordinary implementation task unless the maintainer has explicitly authorized the architecture change.
- If imported code and a target document conflict, report the mismatch. Do not silently change behavior or the contract.
