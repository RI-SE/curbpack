# Studio: säkerhetstester från verkliga tillitsgränser

**Underlag:** `curbpack-review.zip`, `ctam-review.zip`, `curbpack-studio-review(2).zip` (äldre Studio-arkiv, **inte dagens HEAD**). Skripten är nyskrivna mot Studios verkliga Python-API:er; inga gamla Curbpack-bashskript har kopierats. Ingen produktkod ändras.

## Installera och köra

Skripten ligger i `tests/cs/` tills testerna följer system och delsystem. De ingår inte i `make test` eller `make ci-tests`. Kör individuellt:

```sh
python3 tests/cs/path_boundary.py
python3 tests/cs/review_signature.py
python3 tests/cs/check_result_integrity.py
python3 tests/cs/git_provenance.py
python3 tests/cs/workspace_selector.py
```

Eller alla (exitkod 1 om något test fallerar):

```sh
./tests/cs/run_all.sh
```

Ingen ny Make-target, testram, externa testtjänster eller referensrepo behövs. Python 3, Git och redan använda paketet `cryptography` krävs. Tester bygger endast temporära filer/Git-repon och ändrar inte arbetskopian. Varje skript kan anropas separat från Make/CI senare. **Koppla inte in en kontroll som obligatorisk CI-grind förrän dess utfall är granskat och kända brister åtgärdats. Rapportera den inte som PASS dessförinnan.**

## Varför just dessa tester?

| Skript | Faktisk fråga | Arkivutfall | Status |
|---|---|---|---|
| `path_boundary.py` | Kan traversal/symlänkar läsa evidens utanför repo, via Checks eller Discovery? | 3 PASS | Befintligt skydd; regression |
| `review_signature.py` | Verifierar en verklig signerad Review-rapport även efter ändring av Check, beslut, signatur eller signeridentitet? | 4 PASS | Befintligt skydd; regression |
| `check_result_integrity.py` | Kan saknad evidens/SKIP ge grönt? Kan ändrade Claim-digests eller Check-args smugglas in i Compile? | 4 PASS | Befintligt skydd; regression |
| `git_provenance.py` | Kan osignerad Git-author utges för att vara signerad, eller dirty worktree presenteras som verifierad commit? | 2 PASS | Befintligt skydd; regression |
| `workspace_selector.py` | Kan `../` i `pack_id` välja en arbetskopia eller publicerad pack utanför workspace? | 1 PASS, 2 FAIL i arkivet | Samma katalognamnsregel som tidstämpel och version. Testet kräver `ModelError` |

### `pack_id` är ett katalognamn

Arkivet lät `../outside` välja en katalog utanför workspace. `_pack_id_name` avvisar ett id som inte är ett enda katalognamn, på samma sätt som tidstämpel och version. Regeln sitter där id:t fogas in i sökvägen: arbetskopia, publicerad pack, listning och publicering. `workspace_selector.py` visar att `house` fortfarande går att välja, och att `../outside` och `../external` ger `ModelError`.

Testet visar inte HTTP-formuläret, en symlänk med ett lagligt id, eller att den upplösta sökvägen ligger kvar under workspace.

## Vad som inte ingår

- Curbpacks formatteringskontroller, grep på dokument, allowlist över gamla Pack-ID:n och andra så kallade redteam-fall som inte prövar en attack.
- En ny R-state-testmodell, penetrationstestplattform eller generell fuzzmotor.
- SAST, secrets-scanning, dependency-scanning, attack mot internet, supply-chain-granskning eller fullständig SSDF-efterlevnad. Dessa kräver egna kontroller och riskbedömning.
- Ett test som påstår att Compiler själv kan autentisera en osignerad `run-result.json`. **Det kan man inte sluta sig till från dessa källor**; hantering av opålitliga körresultat kräver ett separat kontraktsbeslut.

**Referens:** NIST SP 800-218, SSDF 1.1, PW.8.1–PW.8.2: val av relevant säkerhetstestning och faktiskt utförd/verifierad testning. Detta paket är en konkret delmängd, ingen certifiering: https://csrc.nist.gov/pubs/sp/800/218/final
