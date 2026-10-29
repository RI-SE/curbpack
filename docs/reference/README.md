# Reference

[Packs v2](packs2.md), [Outputs](outputs.md), and [Workspace](workspace.md) define the contracts.

| Page | Owns |
| --- | --- |
| [Packs v2](packs2.md) | Persistent Pack, Requirement, Claim, signature, and Check shapes. Selection and `search_hints` on `curbpack.json` are §2.3. |
| [Outputs](outputs.md) | Run-result and review-report JSON structures, field meanings, and interpretation. |
| [Workspace](workspace.md) | Where product and Studio config live, which keys exist, and the path fields Check and Compile read. |

[Configuration](configuration.md) restates that contract.

[curbcheck](curbcheck-cli.md) is the reference for the `curbcheck` command: arguments, printed output, the result file, and exit codes.

[Outputs](outputs.md) defines the run result and the review report. Paths are Workspace §2–§3.

[Stable contracts](stable-contracts.md) is the review report object Compile writes. An unknown key is rejected. The path is Workspace §2.
