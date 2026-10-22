# CHK-01 — Select a product and its Packs

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a product engineer**, I want to select the product repository and the published Packs to check, so that I know what product and requirements a run applies to.

**Accept when:**

- The selected product repository and Pack identities/versions can be inspected before the run.
- Missing or unresolvable Pack versions are reported clearly; they are not silently replaced with another version.
- The application does not imply that selecting a Pack proves the product complies with it.
- It is clear which revision of the product was evaluated. If the working tree is dirty, it must not be reported as a verified clean commit.

**Implementation note:** Preserve the normative product configuration (`curbpack.json`) and Packs v2 semantics. No new Pack inheritance or `requires` schema is authorized by this story.
