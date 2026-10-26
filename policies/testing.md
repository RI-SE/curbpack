# Testing policy

Tests provide evidence that the behavior defined by a story has been implemented without breaking existing behavior or protected data.

The story is the primary source of observable acceptance behavior. New stories define this behavior using Given/When/Then, examples, or an equivalent semi-executable format. Older stories may additionally rely on derived requirements in `docs/req/`.

Do not create duplicate derived requirements when the story already defines the required behavior.

## 1. Story acceptance

A story is complete only when every applicable acceptance criterion, and every applicable legacy derived requirement, has evidence.

Translate the story's Given/When/Then criteria and examples into human-readable executable acceptance tests whenever practical.

An acceptance test must:

- identify the story it verifies, for example `PE-08`;
- include applicable existing formal requirement IDs, for example `REQ-PE-008`, when the story uses legacy derived requirements;
- make the relevant precondition, action, and expected observable result clear;
- be understandable by a human without reconstructing the implementation;
- test externally meaningful behavior rather than implementation structure;
- preserve the meaning of the story rather than reinterpret it.

Do not manufacture a separate test for every sentence or requirement ID. One acceptance scenario may provide evidence for several related criteria.

If an acceptance criterion cannot reasonably be automated, record an explicit manual acceptance step and its expected result.

If the story is too ambiguous to derive a deterministic acceptance test, stop that scope and record the ambiguity. Do not invent the missing behavior.

## 2. Test first

For an approved behavior change, write the smallest deterministic acceptance test that demonstrates the missing behavior before implementing it.

Run it and establish RED:

- the test must fail;
- it must fail for the intended missing behavior;
- infrastructure, import, setup, network, or unrelated failures do not count as RED.

If the acceptance test already passes, record the behavior as already present. Do not manufacture a failing test or unnecessary implementation change.

Then make the smallest implementation change required to establish GREEN.

A refactor that intentionally changes no observable behavior does not require an artificial RED test.

## 3. Test levels

In this policy, a **test level** is unit, functional, integration, or acceptance. Techniques such as fuzzing, mutation testing, race detection, repeated execution, hostile-input testing, and model comparison may be used at an appropriate level; they are not additional levels.

| Level | Question |
|---|---|
| **Unit** | Does one function or component meet its contract? |
| **Functional** | Does one operation or command produce the required observable behavior? |
| **Integration** | Does the behavior hold across the real subsystem boundaries it depends on? |
| **Acceptance** | Does the behavior described by the story work in a form a person can observe and verify? |

Use the lower levels needed to diagnose and protect the implementation, but do not substitute them for story acceptance evidence.

A language model may propose, generate, or explain a test. It does not determine whether the system passed it.

## 4. What to cover

Cover behavior applicable to the story, including where relevant:

- successful operation;
- invalid or missing input;
- failure;
- cancellation or interruption;
- repeated execution;
- hostile input;
- preservation of existing accepted, signed, or published data;
- regression of behavior affected by the change.

Do not add meaningless variants solely to satisfy this list.

For behavior involving persistent Pack, Requirement, Claim, signature, or result data, verify persisted data against `docs/reference/packs2.md`, including applicable references, signatures, and immutable published versions.

Published or signed data must not be silently rewritten by a test or its fixtures.

## 5. Test independence and determinism

Expected results must be specified independently of the implementation or frozen from an independently verified baseline. The implementation under test must not generate its own expected result.

Use representative fixtures for repeatable tests.

Tests expected to be deterministic must not depend on live network services, external models, mutable remote data, or uncontrolled environment state.

Tests that intentionally depend on a model, network service, manual observation, or external system must be marked explicitly and must not be reported as deterministic automated evidence.

Where exact persistent output matters, compare structured or typed values and canonical serialized data rather than relying on substring matches in prose.

Code that writes files must, where the applicable story or contract requires it, verify confinement to the declared root, repeatability, interruption behavior, and agreement with a later read-only evaluation.

## 6. Regression baseline

Before moving, rewriting, or replacing existing tests, establish the relevant baseline from the fresh PoC2 archive and current implementation.

Distinguish:

- existing baseline failures;
- newly introduced regressions;
- behavior intentionally changed by the approved story.

Never weaken an existing test merely to make a new implementation pass.

The old PoC/Pilot may establish observed regression behavior, but it does not override an approved story, architecture decision, policy, or the authoritative Packs v2 contract.

## 7. Verification evidence

For every verified story step, record:

- story ID and applicable legacy requirement IDs;
- acceptance scenario(s) exercised;
- RED result, or evidence that the behavior already existed;
- implementation change;
- exact test commands executed;
- actual pass/fail/skip counts or results;
- relevant regression results;
- tests or acceptance steps not executed;
- known gaps.

A test file's existence is not evidence that it passed. A skipped test is not a passing test. An unexecuted test is not verification. Only observed results count as evidence.
