# NIS2 Formex adapter

`requirements/extract/adapters/nis/adapter.json`

Formex adapter. `status` is `partial`. `pack_id` is `nis2-baseline`. `source_format` is `formex`. The package is `../../data/official_xml/nis2`. The source is the EU NIS 2 Directive, `CELEX:32022L2555`, English. It is the directive, not a national implementing law.

Article ids are `Art.` plus the article number. `Art.1` through `Art.46` are in scope and ready. A ready section has no fixture.

Annexes:

| Section | Title on the adapter | In scope | Ready |
| --- | --- | --- | --- |
| `I` | Highly critical sectors | yes | no |
| `II` | Other critical sectors | yes | no |
| `III` | Correlation table | no | no |

The titles record that the tables are not extracted. The Formex cutter reports a table and does not emit its cells as provisions.

Guidance for stages 02 and 03 is `prompts/interpret.txt` and `prompts/discovery_hints.txt`.

Fetching the package is [Official XML sources](../xml-sources.md). How an adapter is added is [Adding a regulation adapter](../regulation-adapter.md).
