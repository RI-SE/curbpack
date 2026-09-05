# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.3.0** · classifier **`refclass:2`**.

| Field | Value |
|-------|--------|
| `record_digest` | `2cebe5aac7c7de92360c9d6e8c9543c7e1529af4ef23c1eba244d826b8c36353` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` or `ClassifierVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
