# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.2.0**.

| Field | Value |
|-------|--------|
| `record_digest` | `83542b87d0381c71bc10252e0f64ee541a612f5281eb616a7afa295d3ed08fe4` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
