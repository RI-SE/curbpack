# End-to-end scenario

The historical scenario below is the text written on 12 October 2026. It is kept unchanged, including its design findings. It is not normative.

`docs/reference/packs2.md` in the curbpack repository is the model. Where the historical text disagrees with that document, the document wins. Two examples: `discovery_hints` belongs on the Requirement, and a missing file is `fail`.

## Historical scenario (12 October 2026)

Annex VII punkt 3 följer med från RISE till en extern granskare. Bara sådant som står i den frysta skissen används som verktyg eller fält.

En jurist på RISE och en utvecklare sitter med textvyn för CELEX 32024R2847. Juristen pekar på bilaga VII punkt 3, stycket om att den tekniska dokumentationen ska innehålla bedömningen av de cybersäkerhetsrisker som produkten är konstruerad, utvecklad, producerad, levererad och underhållen mot. Utvecklaren kör **curbpack-extract**. Verktyget lägger stycket som `law_text` på ett krav, `CRA-ANNEX-VII-RISK`, med `locator` `VII.3` och `nr` 1. Källan skrivs en gång: samma url, språket `en`, beteckningen `CELEX:32024R2847`. `pack_id` är `cra-baseline`.

Juristen läser stycket och låter bli att fylla i `strength`. Ordet ”shall” står inte i det här stycket. `applicability`, `exceptions` och `scope` lämnas också borta, av samma skäl. Att bedömningen ska hållas aktuell är ett annat krav. Det tas inte in här, och det får ingen claim.

Utvecklaren skriver ett sökförslag som pekar på kravet: begreppen risk assessment och cybersecurity risk, och sökvägsmönster i stil med `*risk*assessment*` och `*THREAT*`. Förslaget har inget sigill och inget versionsnummer. Juristen signerar inte det. Hon signerar kravet. Innan hon gör det slår hon upp dagen texten gäller och skriver `edition` `2024-11-20`. Hon lägger också in ett `remediation_hint` om att filen ska vara produktens egen bedömning och inte en platshållare. `signed` får hennes namn, tiden och signaturen. Kravets version är den payloaden. Sökförslaget ingår inte.

Kravet läggs i en fil under packkatalogen, tillsammans med `pack.json`. Där står utgivarens etikett `version` `0.1.0`, och `description` säger en gång att CRA gäller produkter med digitala element. Utvecklaren förseglar katalogen. Det sigillet är ett annat än juristens: det säger att filerna i katalogen hör ihop, inte att stycket är rätt läst. De publicerar trädet som tagg plus digest. Den pinnen är det en köpare senare väljer. Den ligger inte i någon fil i skissen.

**Designfynd.** Skissen säger inte var sökförslaget lagras. Ligger filen i packkatalogen ingår den i katalogsigillet, och en ändrad sökväg tvingar fram ett nytt packsigill fast kravets sigill ska stå stilla. Ligger den utanför saknar skissen en plats.

Ett produktteam pinnar `cra-baseline` och skriver `curbpack.json` i sitt repo. Där står packet, och en gemensam hunt som hoppar över `node_modules` och sådant som heter `FUTURE_`. Filen är teamets. RISE äger den inte.

QA öppnar **curbpack-claims** i discover. Verktyget tar hunt-filtret och lägger sökförslaget ovanpå. Träffarna är dåliga på det sätt träffar brukar vara. En marknadsfil nämner cybersecurity risk och kommer högt. En `threat-model-draft.md` träffar mönstret `*THREAT*`. Ingen av dem är bilaga VII. QA binder dem inte. Förslagen är inte bevis, och skissen har ingen plats där ett avslaget förslag blir kvar. Beslutet syns bara som frånvaron av en claim.

**Designfynd.** `sources` kan vara `documents` eller `git`. Skissen säger inte vad ett git-träff är för något.

Rätt fil finns inte. QA låter **curbpack-scaffold** lägga en stubbe på `docs/annex-vii/risk_assessment.md`. Sen binder hon två claims i repot. Den ena är `exist` med den sökvägen. Den andra är `contents` med minst 200 byte, rubrikerna `# Risk Assessment`, `## Product Overview` och `## Identified Risks`, och `token`. `severity` sätter hon till `high` på båda. Det är hennes etikett, inte lagens. Preferenserna i `curbpack.json` drar också fram `README.md`, och en kollega binder en tredje claim, `exist` på den. QA tar bort den. Stycket nämner inte en README, och en claim som inte hör till kravet ska inte ligga kvar och bli grön.

**curbcheck** körs i CI mot repots commit. Exitkoden är röd. `exist` är grön, filen finns. `contents` faller: stubben är för kort och saknar rubrikerna. En utvecklare skriver produktens namn i filen, lägger dit rubrikerna och fyller på tills storleken räcker. Nästa körning är grön. QA signerar de två claims. Företaget har bestämt att det är hennes nyckel. Hade signaturen saknats, och committen varit signerad, hade committen gällt i stället. En osignerad commit hade lämnat claimen osignerad. Det är ett annat rött än en röd check.

Första cykeln är därmed slut. Kravet från RISE är orört. Sökförslaget är orört. Det som ändrats är filen och claimsen, och de ligger i produktrepot.

Andra cykeln börjar med att någon flyttar filen till `docs/security/risk_assessment.md` för att samla säkerhetsdokumenten. CI blir röd samma natt. Båda claims pekar på den gamla sökvägen, så `exist` faller, och `contents` ska inte falla för att filen saknas. Utvecklaren öppnar inte discover igen. I **curbpack-claims** uppdaterar hon `paths` och `path` på de två claims och committar. Nästa **curbcheck** är grön. Kravets sigill har inte rört sig. Inte heller sökförslaget, vars mönster fortfarande letar efter `*risk*assessment*` och skulle ha hittat filen om någon jagat på nytt.

Tredje cykeln är en rubrik. Teamet tycker att `## Identified Risks` låter som en mall och skriver `## Risks we accept`. **curbcheck** blir röd på `contents`, eftersom rubriken i `args` är en ordagrann sträng, inte en tolkning av stycket. De ändrar claimens `args` så att den följer rubriken de faktiskt använder, och committar. Grönt igen. Lagtexten krävde aldrig den engelska rubriken. Den krävde en bedömning. Rubriken är teamets val, och en grön check säger att bytena matchar det valet.

Mellan cyklerna lägger RISE ut `0.2.0`. Juristen har förtydligat `remediation_hint`. Det är en ny payload, så hon signerar kravet på nytt. Sökförslaget är detsamma, och claimsen i produktrepot pekar fortfarande på samma `requirement_id`. Teamet har ingen ruta i `curbpack.json` för taggen de pinnat. Någon jämför digesten för hand och tar in den nya filen. De gamla claims får ligga kvar. Ingen ny bindning behövs, för `check` och `args` handlar inte om rådet.

**Designfynd.** Pinnen tagg plus digest ligger ”utanför” `curbpack.json`. Skissen säger inte var produktrepot skriver vilken pinne som gäller.

Intern revision görs av någon som inte skrivit filen. Hon kör **curbcheck** och får grönt. Sedan läser hon `law_text` och filen. Filen har rätt rubriker, produktens namn och tillräckligt många byte. Innehållet är fortfarande en omskriven mall: inga risker som hör till den här produkten, inget om hur den är tänkt att användas. Den gröna checken räcker inte för stycket. Det finns ingen check som läser om bedömningen faktiskt är en bedömning. Hon signerar inte review-rapporten.

Utvecklarna skriver om filen på allvar. De rör inte `args`. Nästa check är grön av samma skäl som förra gången. Revisorn läser igen, och den här gången stämmer filen med stycket så långt hon kan se utan att påstå att produkten därmed uppfyller förordningen. **curbpack-compile** bygger rapporten. Den listar vilka krav som kollats och vilka claims som är bundna. Hon signerar den, `review-sign`. Det sigillet är inte juristens sigill på kravet, och det är inte QA:s sigill på claimen.

**Designfynd.** Rapporten, så som skissen beskriver den, tar inte med exitkoden och inte vilken commit som kördes. Committen är git. Den är inget fält på kravet. En läsare som bara har rapporten ser vad som var bundet, inte att checken var grön just den dagen, om inte någon kör **curbcheck** igen.

Inför den externa granskningen skickar teamet det compile byggt. Granskaren öppnar det i **curbpack-review**. Hon ser RISE-sigillet på kravet, QA-sigillen på de två claims, sökvägen filen har nu, och stycket. Hon kör **curbcheck** mot den commit teamet pekar ut i följebrevet. Grönt. Hon läser filen och tycker att omarbetningen håller som dokumentation av bedömningen. Hon ser också att inget i underlaget säger att bedömningen hålls aktuell. Det kravet ligger inte i den här bindningen, och check kör inte obundna krav. Hon skriver det i sitt eget utlåtande. Skissen har ingen post för det utlåtandet. Det hon kan signera inne i verktyget är en review-rapport av samma slag: vilka krav som kollats, vilka claims som är bundna. Att checken var grön är inte att stycket är uppfyllt som juridisk slutsats, och ingen i kedjan påstår det.

**Designfynd.** En extern slutsats har ingen struktur. `review-sign` signerar listan över krav och claims, inte ett omdöme om att produkten uppfyller CRA.

| Struktur | Producent | Konsument | Lagras | Ägare |
| --- | --- | --- | --- | --- |
| Pack (`pack.json`, `version`, katalogsigill) | RISE-utvecklaren, efter juristens krav | Produktteamet, som pinnar tagg plus digest | Packkatalogen | RISE |
| Requirement, med `signed` | Juristen i **curbpack-extract** | QA, utvecklare, revisorer | Fil under packkatalogen | RISE. Ny text är ny version, inte en tyst redigering |
| Search proposal | RISE-utvecklaren | Discover i **curbpack-claims** | Inte angivet i skissen | Inte avgjort när teamet byter ut förslaget |
| `curbpack.json` | Produktteamet | Discover och **curbcheck** | Repots rot | Produktteamet |
| Claim (`check`, `args`, `severity`, valfritt `signed`) | QA i **curbpack-claims** | **curbcheck**, revisorer | Claim-filer i produktrepot | Produktteamet. Nyckeln väljer företaget |
| Check-definition | **curbcheck** | **curbcheck** | Verktygets release, inte repot | Den som ger ut curbcheck |
| Filen `args` pekar på | Utvecklarna, stubbe via **curbpack-scaffold** | **curbcheck** och den som läser | Produktrepot | Produktteamet. Den är inte en post i skissen |
| Review-rapport | **curbpack-compile**, signerad med `review-sign` | **curbpack-review** | Inte angivet utöver att compile bygger den | Den människa som bedömde att claims räckte att granska |

## Acceptance criteria

These criteria are the end-to-end acceptance test for the Annex VII point 3 path. They follow the events above and use only the model in `docs/reference/packs2.md`. They do not restore a separate search proposal, a pin outside `pack.json`, or a rule that a missing file fails only `exist`. Scenarios that cross several provisions, a model change, and the cover page are in `ARCHITECTURE.md`.

1. **Publish.** The published Requirement carries `references[]`, one legal `source`, and `discovery_hints` on the Requirement itself. A published Requirement has `signed`. `discovery_hints` is inside that sealed payload. `pack.json` `version` is the publisher's hand-set label. The pack directory digest is the digest already defined for the pack seal.

2. **Select.** `curbpack.json` lists the pack id. The version in use is `version` on the local `pack.json`. A local working copy sets `origin` when it is created and stays an unsigned draft until someone approves it. The fetched Requirement is left unchanged.

3. **Discover.** Discovery reads `discovery_hints` and the repo `hunt`. Candidates are not Claims. A rejected candidate is not stored. The PoC implements the working-tree file walk only.

4. **Bind.** Claims live in the product repo. `exist` and `contents` are separate claims, each with its own `check` and `args`. A claim that does not belong to the Requirement is not kept.

5. **Check.** `curbcheck` writes one run result. Each claim that ran is one row: claim id, version digest, `check`, `args`, `status`, and `detail` when the status is not `pass`. A short stub or a missing header is `fail` on `contents`. The process exits 0 only when at least one claim ran and every row is `pass`. A run with no claim rows is not a successful verification.

6. **Move the file.** A missing file is `fail` on every claim that ran against it, including `contents`. Updating a claim's `args` does not change the published Requirement.

7. **Rename a header.** `contents` stays `fail` while `args` still name the old header. A later `pass` means the bytes matched `args`. It does not mean the legal requirement is fulfilled.

8. **New published pack.** A changed `remediation_hint` is a new Requirement payload and a new publisher seal. The run result records pack id, `pack.version`, and the directory digest, so two trees that share a hand-set version stay distinguishable. `origin.version` changes only when that published version is taken in and the new payload is approved.

9. **Internal review.** The reviewer reads that same run result. The compiled report includes it. `review-sign` signs the report. That signature is not the Requirement seal and not the Claim seal. Signing shows what was signed, who, the stated time, the content version, and whether the signature verifies.

10. **External review.** `curbpack-review` shows the same report and the same run result, including the Git commit and whether the worktree was clean when Git was used. A dirty run is not presented as verification of that commit's content. The reviewer's decision is their own words in the signed report. There is no field for a conclusion that the product meets CRA.
