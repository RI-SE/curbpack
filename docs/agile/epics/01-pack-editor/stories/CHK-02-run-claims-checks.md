# CHK-02 — Run Checks for Claims

**Epic:** [EP-01 Complete Functional Pilot](../EPIC.md)

**As a product engineer**, I want to run the configured Checks for each Claim against my product evidence, so that I can see whether the stated, mechanically verifiable conditions hold now.

**Accept when:**

- The run evaluates the Checks and arguments actually configured on each Claim, against the selected product repository.
- The result is reproducible for the same Pack, Claim definitions, evidence and product revision, with relevant environment/tool inputs recorded where they affect the result.
- A missing evidence file fails every applicable Claim/Check that requires that file. Errors are not turned into success.
- The user can run Checks again after changing evidence or a Claim, and receives a result for the new run.
- Only the Check evaluation determines PASS/FAIL/SKIP for configured mechanical assertions. Discovery and Review do not independently re-judge that outcome.

**Boundary:** Whether to invoke the existing Curbpack CLI or reuse the current PoC2 Check implementation must be verified before integration. Do not build a second competing engine as a side effect.
