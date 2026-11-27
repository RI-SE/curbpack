# Adding a regulation adapter

An adapter is the files for one regulation. It names the source and the sections, and the existing cutter turns a ready section into provisions. A provision is `locus` and `law_text`. It is not a Requirement.

The loader is `load_adapter` in `requirements/extract/adapter.py`. This guide follows that function. `requirements/ARCHITECTURE.md` §4.1 still describes NIS2 as an empty `adapter.yml` stub. The NIS2 adapter in this tree is the Formex adapter below.

There is no registry. `list_adapters()` lists every `requirements/extract/adapters/*/adapter.json`.

## What already exists

Each adapter has its own page:

- [cra](adapters/cra-adapter.md), text
- [cra-xml](adapters/cra-xml-adapter.md), Formex
- [nis](adapters/nis-adapter.md), Formex
- [medtech](adapters/medtech-adapter.md), stub
- [manual](adapters/manual-adapter.md), stub

`docs/ssdf/` maps NIST SP 800-218 to evidence in this repository. That map is not an adapter. Do not add `adapters/nist/`.

## Status

`status` is `partial` or `stub`. Any other value is refused.

A stub has `id`, `status`, and `sections`. It has no `pack_id` and no `source`. Asking for provisions from a stub is refused.

A `partial` adapter requires `pack_id` and `source`. `source` has five non-empty strings: `framework`, `instrument`, `identifier`, `language`, `url`. `source.edition` is refused. The edition is set later, on the Requirement, by a person.

`pack_id` is copied onto assembled Requirements. The cutter does not choose Requirement ids.

## Two shapes

A document that fits neither shape needs its own cutting code. That is not a new field in `adapter.json`.

### Text, as in `cra`

A ready section has `fixture`, a path relative to the adapter directory, and that file must exist. A section with `ready: false` has no fixture. The text cutter is the CRA atomizer: parts, numbered points, and lettered clauses, with EUR-Lex footnote tails removed.

### Formex, as in `nis` and `cra-xml`

```json
{
  "id": "nis",
  "status": "partial",
  "pack_id": "nis2-baseline",
  "source_format": "formex",
  "formex_package": "../../data/official_xml/nis2",
  "source": {
    "framework": "EU",
    "instrument": "NIS2",
    "identifier": "CELEX:32022L2555",
    "language": "en",
    "url": "https://publications.europa.eu/resource/celex/32022L2555"
  },
  "sections": [
    {
      "id": "Art.21",
      "title": "Article 21: Cybersecurity risk-management measures",
      "in_scope": true,
      "ready": true
    }
  ]
}
```

`source_format` is `formex`. `formex_package` is a path relative to the adapter directory and must be an existing directory. The loader opens it. The package needs exactly one DOC entry file (`*.doc.fmx.xml` or `*.doc.xml`).

A ready Formex section has no `fixture`. The section id has to be one the package cutter already understands:

- an article is `Art.` plus the article number in the body, such as `Art.21`
- an annex id is the roman numeral of that annex in DOC order: the first annex is `I`, the second is `II`

`load_adapter` does not check that a ready section id exists in the package. `section_provisions` does, when that section is requested.

Pinned packages and their hashes live under `requirements/extract/data/official_xml/`. Fetching and checking those bytes is [Official XML sources](xml-sources.md). Run the commands in this checkout. That page still tells you to `cd poc2`; this repository has no `poc2` directory.

## Sections

Every adapter has a `sections` array. Each section has:

| Field | Rule |
| --- | --- |
| `id` | Non-empty string, unique in the adapter |
| `in_scope` | Boolean |
| `ready` | Boolean |
| `title` | Optional. The loader does not read it |
| `fixture` | Required only when `ready` is true and the adapter is not Formex. The file must exist |

Both `ready` and `in_scope` have to be true before a section can be cut. `ready` means the fixture or the Formex unit is there and the cutter has been checked against the official text. Mark a section ready only after that check. A wrong cut is fixed in the adapter code or the fixture, then checked again.

## Check it

From the repository root:

```bash
python3 - <<'PY'
from requirements.extract.adapter import ADAPTERS, list_adapters, load_adapter, section_provisions

print(sorted(item["id"] for item in list_adapters()))
adapter = load_adapter(ADAPTERS / "nis" / "adapter.json")
cut = section_provisions(ADAPTERS / "nis", adapter, "Art.21")
print(cut["section_id"], [item["locus"] for item in cut["provisions"]])
PY
```

`tests/test_xml_adapters.py` is the existing check for the CRA Formex and NIS2 adapters. Read the provisions against the official text before treating a new section as ready.
