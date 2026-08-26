# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.1.1**.

| Field | Value |
|-------|--------|
| `record_digest` | `1cab72f82fb8275f972cca251ca40b56c2a2d217650fa6bcf91107e93b700773` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
