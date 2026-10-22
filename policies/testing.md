# Testing policy

A story is complete only when its acceptance criteria **and the applicable derived requirements** have been verified by tests or recorded manual acceptance steps.

- Link tests to story IDs (`PE-08`) and formal requirement IDs (`REQ-PE-008`, `REQ-PE-009`), without manufacturing a test-per-line bureaucracy.
- Cover success, failure, cancellation, and preservation of existing accepted/published data.
- Establish the baseline from the fresh PoC2 archive before moving or rewriting any existing tests.
- Check persistent Pack/Requirement data against the authoritative Packs v2 specification, including references, signatures and immutable published versions.
- Use representative fixtures for repeatable tests that should not depend on network/model availability. Mark manual or model-dependent tests explicitly.
- Report exact executed commands, outcomes and known gaps. A test file's existence is not evidence it passed.
