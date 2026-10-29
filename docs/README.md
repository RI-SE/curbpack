# Curbpack documentation

Start with the shortest path for what you need to do.

## The workflow

The cover at `http://127.0.0.1:8770` links the activities. They do not have to be visited in one fixed order. A Check can run when the product repository, the selected Pack and the Claims already exist, without opening Extract first.

```text
Pack Sources: choose a repository
    → start empty writes curbpack.json in a working folder, pointing at that folder
    → otherwise read the Packs named in that repository's curbpack.json
    → the URL cell shows the document URL and the pack directory from that file
    → add a Pack into that folder
    → Extract, review, sign
    → Discovery shows candidates
    → a person writes a Claim and its checks[]
    → Run curbcheck writes one run result
    → Review compiles that result, records a decision, and signs the report
```

Importing a Pack is the same write as accepting an extraction. It is not a second path.

A passing Check is what those questions observed. A person still decides what that means.

## Start here

| You are | Start here |
| --- | --- |
| **New user** | [Install](user-guides/install.md) · [Getting Started](user-guides/getting-started.md) |
| **Buyer / reviewer** | [Reviewer guide](user-guides/reviewers.md) |
| **Authority / auditor** | [Reviewer guide](user-guides/reviewers.md) |
| **Pack author** | [Pack author guide](user-guides/pack-developers.md) |
| **Builder / product team** | [Developer guide](user-guides/developers.md) · [CI/CD](user-guides/ci-cd.md) |
| **Curbpack contributor** | [Development](development/README.md) · [Architecture](arch/ARCHITECTURE.md) · [Stories](agile/README.md) · [Requirements](req/README.md) |

| Goal | Read |
| --- | --- |
| Install and start Studio | [Install](user-guides/install.md) |
| Walk Pack Editor, Discovery & Claims, Check, and Review | [Getting started](user-guides/getting-started.md) |
| Use Studio on a product repository | [Developer guide](user-guides/developers.md) |
| Run the same Check outside the browser | [CI/CD](user-guides/ci-cd.md) |
| Test this repository (Studio and curbcheck) | [Development](development/README.md) · [Testing curbcheck](testing/README.md) |
| Read a compiled report and sign a decision | [Reviewer guide](user-guides/reviewers.md) |
| Author a Requirements Pack and the Claims that monitor it | [Pack author guide](user-guides/pack-developers.md) |

## Common tasks

| Task | Read |
| --- | --- |
| Select Packs for a product | [Packs](concepts/packs.md) and Packs v2 §2.3 |
| Understand repository evidence and results | [Evidence](concepts/evidence.md) |
| Understand Extract, Discovery, Check and Review | [Concepts](concepts/README.md) |
| Prepare material for another person | [Developer guide](user-guides/developers.md) |
| Review received material | [Reviewer guide](user-guides/reviewers.md) |

## Already in this repository

| Subject | Document |
| --- | --- |
| Persistent data | [Packs v2](reference/packs2.md) |
| Product configuration | [Configuration](reference/configuration.md) |
| System boundaries and the cover | [Architecture](arch/ARCHITECTURE.md) |
| Inherited requirement ids | [System requirements](arch/SYSTEM_REQUIREMENTS.md) |
| Annex VII point 3, historical narrative and current acceptance | [End-to-end scenario](concepts/end-to-end-scenario.md) |
| Stories | [Agile](agile/README.md) |
| Derived requirements | [Requirements](req/README.md) |
| Pack Editor behavior still being specified | [Pack Editor requirements](req/pack-editor.md) |
