# HISTORICAL / TARGET — `curbpack verify` sketches

> **NOT SHIPPED.** `curbpack verify` is **not** a CLI verb. Do not run it; do not teach it as available.
>
> Recipient-side document triage is intended as future **`curbpack review`**. Do not resurrect `verify` as the ship name.
>
> Structural evidence for human review — not conformity assessment, not certification, not CE / notified-body opinion.

These snippets were design-intent examples formerly presented without enough shipping fences in the SDD. Kept here so implementers can see the old shape without mistaking it for product surface.

## Asker loop (historical wording)

```
asker publishes signed pack → supplier runs it locally →
supplier returns signed evidence → asker runs `curbpack verify`
```

**Today:** stop after signed evidence; humans review artifacts. **Target ship name:** `curbpack review`.

## Operations sketch (historical)

```
curbpack packs sign <pack>
curbpack packs trust import <allowed_signers>   # human-only; not built yet
curbpack verify <bundle|pack|onepager>          # NOT SHIPPED — historical name only
```

## Artifact footer (historical)

```
Generated locally by curbpack. Nothing was uploaded. Verify it yourself: `curbpack verify <file>`.
```

**Today:** do not print a `curbpack verify` invitation. Prefer claim-safe review language until `curbpack review` ships.

See also: [software-design-document.md](../software-design-document.md) banner + §9.1; [sdd-gap-analysis.md](sdd-gap-analysis.md).
