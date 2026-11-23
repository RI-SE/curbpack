# Use case: Från första Check till avslutad granskning

**Status:** Målbild för Check, Review och Remediation. Texten beskriver det avsedda förloppet. Den beskriver inte vad Studio gör i dag, och den är inte ett normativt kontrakt. `docs/reference/studio-internal.md` styr `review_item`.

### Dag 1 – Olle checkar in

Olle har gjort ändringar i produkten och checkar in koden.

En fullständig **Check** körs och identifierar ett antal problem. Niklas öppnar resultatet i **Review**, granskar underlaget och beslutar att fyra Checks är `must_fix`.

Niklas signerar Review Report. Därmed finns fyra dokumenterade avvikelser som måste hanteras.

### Dag 2 – Urban arbetar med Remediation

Urban öppnar **Remediation** från den signerade rapporten.

1. **Finding #1:** En Claim är bunden till fel Requirement. Urban gör Rebind och kör Re-check. Resultatet blir PASS.
2. **Finding #2:** Samma åtgärd visar sig även ha löst nästa problem. Vid Re-check blir även denna PASS, utan ytterligare ändring.
3. **Finding #3:** En Check har felaktigt datum i sin konfiguration. Urban rättar datumet och kör Re-check. PASS.
4. **Finding #4:** Ett obligatoriskt dokument saknas. Urban kan inte färdigställa det och skriver i Remediation: *"Dokumentet kräver Lisas medverkan. Lisa är tillbaka nästa månad."*

`remediation_history` visar vad Urban har gjort, vilka Checks som ändrat resultat och varför den sista punkten är olöst.

### Dag 3 – Remedy Report och en ny Check

Urban signerar en **Remedy Report** med samma sigill som en Review Report. Han skriver under att arbetet är gjort så bra det gick, och tar ansvar för den redogörelsen. Rapporten berättar vad han gjort: tre Re-checkar blev PASS, och den fjärde är olöst med kommentaren om Lisa. Den har kvar sina `review_items`. Det är inte ett granskningsbeslut.

Niklas kan signera den Review han redan har och skicka den vidare. Om han är smart läser han Remedy Report och begär en ny Check.

Den nya körningen erbjuder två saker: återuppta en påbörjad Review, eller ta in synpunkterna från senaste Remedy Report.

- De tre rättade punkterna har ändrat underlag. Deras `must_fix` återanvänds inte. Checken visar PASS, och Niklas godkänner dem.
- Den fjärde har samma underlag. Niklas läser kommentaren och beslutar att acceptera avvikelsen tills Lisa kan färdigställa dokumentet.

Niklas signerar Review Report.

**Resultat:**

- 3 Passed
- 1 Accepted
- 0 Must fix

Granskningen är avslutad, men rapporten visar tydligt att ett problem accepterades utan att vara tekniskt åtgärdat.

### Senare Checkar – beslutet ligger kvar

Efter signeringen körs många nya Checkar. För den accepterade avvikelsen är beslutet redan förberett: kommentaren säger varför, och underlaget är oförändrat tills Lisa färdigställer dokumentet. Samma sak gäller de tre Passed, så länge deras krav och underlag står stilla.

En ny Review erbjuder **Reuse decisions** från den senaste signerade rapporten. Niklas väljer återanvändning. De fyra besluten fylls i igen. Den accepterade punkten behöver inte granskas om.

När Lisa färdigställer dokumentet och Olle checkar in ändringen ger den fjärde Checken PASS. Underlaget är nytt, så det tidigare `accepted` återanvänds inte. Checken föreslår `pass`. De tre andra kan fortfarande återanvändas.

Niklas granskar den fjärde punkten, konstaterar att dokumentet finns och godkänner.

En ny Review Report signeras.

**Resultat:**

- 4 Passed
- 0 Accepted
- 0 Must fix

Historiken visar fortfarande att dokumentet först saknades, att avvikelsen accepterades tills Lisa kunde färdigställa det, och att det senare blev `pass`.
