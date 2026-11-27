# CRA text adapter

`requirements/extract/adapters/cra/adapter.json`

Text adapter. `status` is `partial`. `pack_id` is `cra-baseline`. The source is the EU Cyber Resilience Act, `CELEX:32024R2847`, English, cut from the EUR-Lex text URL in the file.

The cutter is the text atomizer. It is this regulation's code. A ready section has a fixture. Annex `I` is `../../data/annex_i.txt`. Annex `VII` is `../../data/annex_vii.txt`.

| Section | In scope | Ready |
| --- | --- | --- |
| `II`, `V`, `VIII` | yes | no |
| `I`, `VII` | yes | yes |
| `III`, `IV`, `VI` | no | no |

Guidance for stages 02 and 03 is `prompts/interpret.txt` and `prompts/discovery_hints.txt`.

How an adapter is added is [Adding a regulation adapter](../regulation-adapter.md). The same act as Formex is [cra-xml](cra-xml-adapter.md).
