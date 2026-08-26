# Comparison bundle 2026-1 — expected digests

Frozen input: [`testdata/comparison-bundle-2026-1/`](../../testdata/comparison-bundle-2026-1/).

Method: `curbpack-review-method` **1.0.0**.

| Field | Value |
|-------|--------|
| `record_digest` | `8b1f880e45351d22a0d81efe7541e03f370c538488221a934aa5844131fe8546` |

Divergence means a different tool version, a modified tool, or altered input — never operator variation.

Recompute:

```bash
curbpack review ./testdata/comparison-bundle-2026-1 --json 2>/dev/null | jq -r .record_digest
```

When `MethodVersion` changes, update this file and `TestComparisonBundleDigestPinned` together.
