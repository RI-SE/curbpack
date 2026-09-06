# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.3.0** · classifier **`refclass:2`**.

| Field | Value |
|-------|--------|
| `record_digest` | `7e7a8de08bef231703953f1457468682d8967ae44448815b3e34e05cb706a2b4` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` or `ClassifierVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.


Note: tip reports include `conformity_claim: none` (hashed into `record_digest`).
