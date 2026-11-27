# CRA Formex adapter

`requirements/extract/adapters/cra-xml/adapter.json`

Formex adapter. `status` is `partial`. `pack_id` is `cra-xml-baseline`. `source_format` is `formex`. The package is `../../data/official_xml/cra`. The source is the EU Cyber Resilience Act, `CELEX:32024R2847`, English.

A ready section has no fixture. The cutter reads the DOC package. Annex ids are roman numerals in DOC order. Annex `VII` is ready.

| Section | In scope | Ready |
| --- | --- | --- |
| `II`, `V`, `VIII` | yes | no |
| `VII` | yes | yes |
| `I`, `III`, `IV`, `VI` | no | no |

Guidance for stages 02 and 03 is `prompts/interpret.txt` and `prompts/discovery_hints.txt`.

The text adapter for the same act is [cra](cra-adapter.md). Fetching the package is [Official XML sources](../xml-sources.md).
