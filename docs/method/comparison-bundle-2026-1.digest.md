# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.3.0** · classifier **`refclass:2`**.

| Field | Value |
|-------|--------|
| `record_digest` | `173ca211b359ad3402bcae2dc04bee15a13a4e103d7079b29882cbb5388589ab` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` or `ClassifierVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.


Note: tip reports include `conformity_claim: none` (hashed into `record_digest`).

Current reports also include the optional `curbpack-pack-audit:1` extension and
use failed-gate counts in human-facing parse findings. Both affect current
record bytes. The historical record digest
`7e7a8de08bef231703953f1457468682d8967ae44448815b3e34e05cb706a2b4` remains verifiable
using its original report, frozen in
[`report_before_pack_audit.json`](../../internal/review/testdata/report_before_pack_audit.json).
The reference triage method remains 1.3.0; the separately versioned audit contract
is described in [schema compatibility](../../schema/COMPATIBILITY.md).
