# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.0.0**.

| Field | Value |
|-------|--------|
| `record_digest` | `98ec096dd575ee3c732c9dd84d589a28614551a77c797a6abc7073dc6cd7c368` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
