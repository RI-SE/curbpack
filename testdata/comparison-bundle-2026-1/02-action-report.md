# COMPLIANCE ALERT: GATE FAILURE [OCC-ID: :v3.33-OCC]
**Statechart Path:** Root / ActiveVerification / PackEval
**Failed Region:** HOUSE-DEP-AXIOS-PIN, HOUSE-ANTI-PLACEHOLDER

## VIOLATION 1: SYS_TRACE_VIOLATION [HOUSE-DEP-AXIOS-PIN] (critical)
* **Location:** `package.json`
* **AST Path:** ``
* **Symbol Target:** ``
* **Context:**
<untrusted_metadata>
House policy bans vulnerable axios@1.6.0 pins in package.json. (target absent)
</untrusted_metadata>

### REQUIRED REMEDIATION
* **Goal State:** No banned axios versions in dependencies or devDependencies.
* **Resolution Path:** Upgrade axios to a patched release and refresh the lockfile.

## VIOLATION 2: POLICY_VIOLATION [HOUSE-ANTI-PLACEHOLDER] (high)
* **Location:** `SECURITY.md`
* **AST Path:** ``
* **Symbol Target:** ``
* **Context:**
<untrusted_metadata>
House policy docs contain placeholder / boilerplate text. (scaffold body overlap)
</untrusted_metadata>

### REQUIRED REMEDIATION
* **Goal State:** No placeholder patterns in required security docs.
* **Resolution Path:** Replace TODO / lorem ipsum / [insert ...] with real contact and process details.

## VIOLATION 3: POLICY_VIOLATION [HOUSE-ANTI-PLACEHOLDER] (high)
* **Location:** `.well-known/security.txt`
* **AST Path:** ``
* **Symbol Target:** ``
* **Context:**
<untrusted_metadata>
House policy docs contain placeholder / boilerplate text. (scaffold body overlap)
</untrusted_metadata>

### REQUIRED REMEDIATION
* **Goal State:** No placeholder patterns in required security docs.
* **Resolution Path:** Replace TODO / lorem ipsum / [insert ...] with real contact and process details.
