# User guides

| Guide | What it shows |
| --- | --- |
| [Install](install.md) | Start the local application from a source checkout. |
| [Getting started](getting-started.md) | A disposable workspace, Glucose Log, two Claims, then two edits that each move a known row. |
| [Developer guide](developers.md) | A product repository: select a Pack, bind Claims, run Check, compile, sign. |
| [CI/CD](ci-cd.md) | The same Check in a pipeline. Studio's own GitHub workflows are a separate pipeline. |
| [Reviewers](reviewers.md) | The report at `docs/reports/review-report.json`, and how to read a row. |
| [Troubleshooting](troubleshooting.md) | Startup, Git, packaging, and a green run that watched the wrong file. |
| [Pack authors](pack-developers.md) | A Pack, its Requirements, and the Claims that monitor them. |

## Typical workflow

1. **Start Studio.** [Install](install.md).
2. **Try the reference product.** Set up the walkthrough Pack and Claims, remove one evidence file, run Check, restore it. [Getting started](getting-started.md).
3. **Select a Pack for your repository.** Write `curbpack.json`. Author Requirements in Pack Editor. [Developer guide](developers.md).
4. **Discover and bind.** Candidates are not Claims. A person saves the Claim and its `checks[]`.
5. **Run curbcheck.** The browser button or `python3 -m checks`.
6. **Fix the product or the Claim.** Read `law_text` and the row detail.
7. **Run curbcheck again.**
8. **Compile the report.** [Developer guide](developers.md).
9. **A person writes the decision and signs the report.**
10. **A reviewer reads that report.** [Reviewers](reviewers.md).
11. **After later edits, run Check again.** The previous signed report stays the record of the earlier run.

CI runs step 5. It does not sign and it does not scaffold.

Pack authors start at [Pack authors](pack-developers.md). Reviewers start at step 10.
