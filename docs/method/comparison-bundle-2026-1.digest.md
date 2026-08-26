# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.1.0**.

| Field | Value |
|-------|--------|
| `record_digest` | `098590e91597ec823df3e02c631ea1caf22dd9ad329f61871c4290cb952f4fe8` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
