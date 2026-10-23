# Security policy

Apply security controls to actual risks, and record their implementation and evidence under `docs/ssdf/`.

- Never commit private keys, credentials, `.env` secrets, or generated customer workspaces. The old PoC2 export contained key material in `data/workspace/`; treat such files as sensitive.
- Validate untrusted inputs, file paths, uploaded archives, and external document data at relevant boundaries.
- Do not report SSDF compliance because a policy exists. A claim needs a real control and test or other verifiable evidence.
- Changes affecting cryptographic signing or validation must use the normative Packs v2 semantics, with negative tests for changed content or invalid signatures.
- Use approved security review and vulnerability scanning when available. Verify findings and record their disposition. Confirmed High/Critical vulnerabilities must be fixed or explicitly risk-accepted by the maintainer before release.
