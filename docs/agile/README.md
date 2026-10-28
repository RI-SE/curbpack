# Epics and user stories

This is the **user-facing backlog**: what people need to accomplish and how they recognize success. It is not the implementation specification.

- `epics/01-pack-editor/` contains **EP-01 — Complete Functional Pilot**. The directory name is retained to avoid an unrelated rename. [SYS-03](epics/01-pack-editor/stories/SYS-03-one-repo-door.md) is the pilot door: one repository, its `curbpack.json`, and a packs root. PE-01–PE-11 cover Pack Editor; CHK-01–CHK-04, REV-01–REV-02 and SYS-01 extend the epic through working Checks and a signed Review. [DOC-04](epics/01-pack-editor/stories/DOC-04-single-persistent-model.md) follows Review. It is draft and is not authorization to implement.
- `epics/02-modularize-studio/` contains **EP-02 — Modularize Studio**, planned only after EP-01 is accepted.
- `epics/09-standalone-tools/` contains **EP-09 — Start each Packs v2 tool on its own**. Draft. The current `app/` is the pilot shell (`pilot_app`). EP-02 does not by itself make the tools separately startable.
- `epics/12-development-environment/` contains **EP-12 — Development environment**. Draft. One container, built and started with Make. CI calls that same build. Not authorization to implement.
- `epics/04-studio-doc-truth/` contains **EP-04 — Studio documentation truth**. DOC-01–DOC-03 are done: the SDD account under `daniel/ny_sdd/`. [DOC-06](epics/04-studio-doc-truth/stories/DOC-06-published-reader-docs.md) updates the published documents a reader opens from the repository README. It is draft, it does not edit `daniel/ny_sdd/` or `docs/reference/packs2.md`, and it is not authorization to edit a document until that document is the current row.
- `epics/13-developer-guides/` contains **EP-13 — Developer guides**. Draft. How-tos for an extension the code already supports. [DOC-05](epics/13-developer-guides/stories/DOC-05-document-regulation-adapter.md) is the regulation-adapter guide. It does not block EP-01 and is not authorization to implement.
- `epics/14-regulation-adapters/` contains **EP-14 — Regulation adapters**. Draft. CRA text annexes II, V, and VIII from the CTAM poc. NIS2 is not in that poc. It does not block EP-01 and is not authorization to implement.
- `DECISIONS.md` records product decisions and open questions. Only accepted stories and derived requirements authorize implementation.
- CHK, REV and SYS still need formal requirements and acceptance tests derived and checked against the actual pilot. Do not assume the UI proves their behavior.

Flow: **Epic → Story → formal requirement (`docs/req/`) → test evidence (`docs/test/`, `tests/`) → implementation**. One story may produce several requirements; keep IDs stable and link them.
