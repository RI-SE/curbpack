# Official XML sources for Requirements extract

Descriptive engineer procedure. Packs v2 and `requirements/ARCHITECTURE.md` remain normative.

## What is pinned

Under `poc2/requirements/extract/data/official_xml/`:

| Directory | Act | CELEX | Edition |
| --- | --- | --- | --- |
| `cra/` | Cyber Resilience Act | `32024R2847` | Original OJ Formex EN (not consolidated) |
| `nis2/` | NIS 2 Directive (EU) | `32022L2555` | Original OJ Formex EN (not Swedish implementing law) |

Identity, retrieval URL, Accept headers, and SHA-256 for every file: `MANIFEST.json`.

## Obtain / refresh (optional)

EUR-Lex HTML/XML notice pages may be blocked by WAF. Publications Office CELLAR Formex works:

```bash
curl -fsSL -L \
  -H 'Accept: application/zip;mtype=fmx4' \
  -H 'Accept-Language: eng' \
  -o cra.fmx4.zip \
  'https://publications.europa.eu/resource/celex/32024R2847'

curl -fsSL -L \
  -H 'Accept: application/zip;mtype=fmx4' \
  -H 'Accept-Language: eng' \
  -o nis2.fmx4.zip \
  'https://publications.europa.eu/resource/celex/32022L2555'
```

Unzip into `official_xml/cra` or `official_xml/nis2`, keep the DOC entry file, update `MANIFEST.json` hashes. Do not mix original, consolidated, or corrigendum editions.

## Verify

```bash
cd poc2
.venv/bin/python -m unittest tests.test_formex_package tests.test_formex_no_number_leak -v
```

## Extract

Adapters:

- `cra` — existing Annex VII text fixture (regression)
- `cra-xml` — CRA Formex (`pack_id` `cra-xml-baseline`); ready annex `VII`
- `nis` — EU NIS2 Formex (`pack_id` `nis2-baseline`)
  - **Ready:** Articles `Art.1` … `Art.46` (each verified for non-empty provisions, stable loci, no `NO.P` leak into `law_text`, and Packs v2 assemble of a probe proposal)
  - **Not ready (diagnostic only):** Annexes `I`, `II`, `III` — contain `<TBL>`; reported in inventory diagnostics, not exposed as extractable

`NO.P` / `NO.PARAG` markers stay in locators (`3`, `21(1)`), not in `law_text`.

Python:

```bash
cd poc2
.venv/bin/python - <<'PY'
from requirements.extract.adapter import ADAPTERS, load_adapter, stage00, section_provisions

adapter = load_adapter(ADAPTERS / 'nis' / 'adapter.json')
print('ready', sum(1 for s in adapter['sections'] if s['ready']))
print([p['locus'] for p in section_provisions(ADAPTERS / 'nis', adapter, 'Art.13')['provisions']])
PY
```

UI: open Requirements, choose source (`cra` / `cra-xml` / `nis`; `medtech` remains stub), inspect structure and provisions, extract a ready section. Each run creates a new timestamped working copy. The product extract path runs stages 02/03 producers (default local model endpoint) then assemble; fixture `proposals=` remain available only in tests. Stages 00–01 and assemble alone need no LLM.

## Compare CRA text vs XML

```bash
cd poc2
.venv/bin/python -m unittest tests.test_cra_vii_compare -v
```

Artifacts: `requirements/extract/data/official_xml/compare/cra_annex_vii_text_vs_xml.json` and `.md`.

Current classification (after `NO.P` leak fix; fixture unchanged):

| Class | Count | Loci |
| --- | --- | --- |
| Shared | 13 | all Annex VII atom loci |
| Exact matches | 6 | `3`–`8` |
| Normalization-only | 6 | `1(a)`–`1(c)`, `2(a)`–`2(c)` |
| Genuine wording | 1 | `1(d)` — fixture left unchanged pending independent OJ/PDF check |

## Plan

Implementation progress: `poc2/doc/PLAN/XML_SOURCE_ADAPTERS_PLAN.md` is COMPLETE. Requirements Task 18 reconciles against that acceptance.
