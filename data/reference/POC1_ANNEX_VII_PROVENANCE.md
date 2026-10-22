# PoC1 Annex VII reference — provenance

Integrity record for the unsigned comparison set. SHA-256 is of the file bytes. This file is not inside the pack directory, because `load_pack_directory` treats every other `*.json` file there as a Requirement.

**Label.** A Cursor agent produced the PoC1 maps and this Packs v2 conversion. The user has inspected the result. It is not an independently legally certified gold standard, and it is not fully human-reviewed. The YAML `description` lines that say "Human-reviewed" are not treated as certification.

The Requirement JSON and `pack.json` were written by commit `d8c743ac2360bd232b326635ff2e66defcc62f8f` and were not rewritten when this record was added.

## Reproduction

From the repository root, with `poc2/.venv` and Ruby available:

```bash
poc2/.venv/bin/python poc2/data/reference/build_poc1_annex_vii_reference.py
```

The script refuses to run when `poc2/data/reference/poc1-annex-vii-unsigned/` already exists. To check integrity, hash the files below and compare. The script does not call a model.

## Source inputs

| Path | SHA-256 |
| --- | --- |
| `poc/components/transform/adapters/cra/maps/claims.yml` | `532d646c662e24da3e26aa5734d7ef891bab00c10b2701b5e4ffca392173d945` |
| `poc/components/transform/adapters/cra/maps/search.yml` | `0940cfbff1cab3557b624a520d26977acc773587645499d3e09d4df436178aef` |
| `poc/data/in/ctam_cra_requirements_search.yml` | `5858178da10c9987fa9c75da6236d1ae7c5f82178eb838a26e6a14f616441e66` |
| `poc2/requirements/extract/adapters/cra-xml/adapter.json` | `9bd995f8845f0de5ab8be16d66a727dda06f3252d2cb5cf364822bfeccbf1532` |
| `poc2/requirements/extract/data/official_xml/cra/L_202402847EN.007501.fmx.xml` | `34796e49040eed5f83c0a762a3ce205a1bcf768fcedea65802944791ace06d4f` |

Passages and locators come from `section_provisions` on adapter `cra-xml`, section `VII`. The Formex path above is the `file` that call returned.

## Converter and report

| Path | SHA-256 |
| --- | --- |
| `poc2/data/reference/build_poc1_annex_vii_reference.py` | `2d6b97944c9c760d88914e44937cfd36dad99639528e8b860b34f1f871b190c3` |
| `poc2/data/reference/POC1_ANNEX_VII_MAPPING.md` | `f3cd9b79a2b793376634ce72fa6fc4e309432d162b187a1e83de3b080b5e4d20` |

## Frozen reference files

| Path | SHA-256 |
| --- | --- |
| `poc2/data/reference/poc1-annex-vii-unsigned/pack.json` | `44639b232f05ab398d72751bf924d7030261f6363d5447cbe43602d584255513` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-1A.json` | `c39dad5c4e442f236986bd93b7ceced38ee4631d9e63002dbbb0f1345bc03681` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-1B.json` | `ba64500d71c3a613bcefe9624c1a1d2b03839c38bfefc7aaff671208614b1c4b` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-1C.json` | `18e5c6e3206e8ca3095143ed2012a3ce1cccc708ae3bd035d115e5e749cf5d27` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-1D.json` | `70dde7a68b354648546749b7b01ec658f425cb0115b0b63ede979d93c2bfe6d0` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-2A.json` | `16d651dee80d77f2a79aa6ba6809898adf8130765fd5c5b15774b70eb7e632f3` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-2B.json` | `a1a3fd8f77eb8925bd5356ab16bf95922994b2c6995c022cfc69fed489c2e46a` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-2C.json` | `cef7dba0acef36f39eb23d7899bc830ff46754e0eeb82de7e445ff0554564405` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-3.json` | `f092069bcdb8f32dd6c864a5a56029a8a42e337d1fb337f39219e01885466c1d` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-4.json` | `6fca93e7f2ea3999a8e586959c4cb32c71bd4e3dfeb8f84c0d9476cff35dc1d8` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-5.json` | `a1c8bb153512c86cffc601c94788d782e827a3a718a4b3c076809c4dd4d9f661` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-6.json` | `edf71a6ef52ccea97cdda0aebd9ba4f12fd52707adf0c56a9243b2b658c28d4a` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-7.json` | `b2804700712da9ac718ea642ab6ceaf2ed395f9affd908870a7afb7952efba55` |
| `poc2/data/reference/poc1-annex-vii-unsigned/POC1-REF-VII-8.json` | `247098385d62f963c935d4c0591c3ac5cca707e4978996a5d436416dbc5d8dbd` |
