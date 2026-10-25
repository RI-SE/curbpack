# Epics and user stories

This is the **user-facing backlog**: what people need to accomplish and how they recognize success. It is not the implementation specification.

- `epics/01-pack-editor/` contains **EP-01 — Complete Functional Pilot**. The directory name is retained to avoid an unrelated rename. PE-01–PE-11 cover Pack Editor; CHK-01–CHK-04, REV-01–REV-02 and SYS-01 extend the epic through working Checks and a signed Review.
- `epics/02-modularize-studio/` contains **EP-02 — Modularize Studio**, planned only after EP-01 is accepted.
- `epics/09-standalone-tools/` contains **EP-09 — Start each Packs v2 tool on its own**. Draft. The current `app/` is the pilot shell (`pilot_app`). EP-02 does not by itself make the tools separately startable.
- `DECISIONS.md` records product decisions and open questions. Only accepted stories and derived requirements authorize implementation.
- CHK, REV and SYS still need formal requirements and acceptance tests derived and checked against the actual pilot. Do not assume the UI proves their behavior.

Flow: **Epic → Story → formal requirement (`docs/req/`) → test evidence (`docs/test/`, `tests/`) → implementation**. One story may produce several requirements; keep IDs stable and link them.
