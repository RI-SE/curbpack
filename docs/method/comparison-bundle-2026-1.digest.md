# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.3.0** · classifier **`refclass:2`**.

| Field | Value |
|-------|--------|
| `record_digest` | `fd822e2ebdab2f9dcd6cbffaf1f2085acd08926e60af149db1de0e1473f8c41e` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` or `ClassifierVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
