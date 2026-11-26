# Use case: Från första Check till avslutad granskning

**Status:** Så här gör Studio. `docs/reference/studio-internal.md` styr `review_item`. Sidans steg står i [Reviewing](../user-guides/reviewers.md).

### Dag 1 – Olle checkar in

Olle har gjort ändringar i produkten och checkar in koden.

En fullständig **Check** körs och blir en rad under **Checks performed**. Niklas öppnar den. Sidan leder med avvikelserna. Han sätter fyra Checks till `must_fix`.

**Sign** låser de besluten, skriver review-rapporten i Checkens katalog och går tillbaka till Check. Raden säger **View**. Granskningen är skrivskyddad. Remediation har inte börjat förrän någon väljer **Start**.

### Dag 2 – Urban arbetar med Remediation

Urban väljer **Start** på den signerade raden.

1. **Finding #1:** En Claim är bunden till fel Requirement. Urban gör Rebind och kör Re-check. Den raden blir grön och flyttas till **Remediated**. Det signerade `must_fix` står kvar.
2. **Finding #2:** Samma åtgärd har löst nästa problem. Re-check gör även den grön, utan ytterligare ändring.
3. **Finding #3:** En Check har felaktigt datum. Urban rättar datumet och kör Re-check. Raden blir grön.
4. **Finding #4:** Ett obligatoriskt dokument saknas. Urban kan inte färdigställa det. **Add comment** sätter anteckningen på Checken: *"Dokumentet kräver Lisas medverkan. Lisa är tillbaka nästa månad."* Anteckningen är `comment`. Den är inte en historikpost.

Historiken visar åtgärderna: rebind, och en re-check som ändrade utfallet. En Check som redan var grön och som fallerar i en hel körning visas som **Checks outside the original report**. Den läggs inte i kön. **OK** sparar händelsen på remedieringen. **Rollback** lägger bara tillbaka senaste ändringen som Studio själv gjorde.

### Dag 3 – Remedy Report och en ny Check

Urban väljer **Sign Off**. Sigillet är en remedy report: namn, tid och signatur över arbetet, historiken, rundans anteckningar och en kvitterad avvikelse utanför den ursprungliga kön. Det är inte ett granskningsbeslut, och det ändrar inte Niklas signerade beslut. Studio skriver en läsbar rapport och går tillbaka till Check. Remedy-kolumnen säger **Completed**.

Niklas läser rapporten. Vill han gå vidare kör han en ny Check. Den är en ny rad.

Den nya granskningen kan fråga om den ska ta in remedieringsrapporten.

- De tre rättade punkterna har ändrat underlag. Deras `must_fix` återanvänds inte. Checken visar pass, och Niklas godkänner dem.
- Den fjärde har samma underlag. Niklas läser kommentaren och sätter **Accept**.

Finns redan en påbörjad granskning av just den körningen frågar sidan först om den ska fortsätta eller börja om.

Niklas signerar. Resultatet är 3 Passed, 1 Accepted, 0 Must fix. Ett problem är accepterat utan att vara tekniskt åtgärdat.

### Senare Checkar – beslutet ligger kvar

Nästa Check kan åter ta in den senaste signerade remedieringen. Oförändrat underlag fyller det signerade beslutet, även det förberedda `accepted`. Historiken visas oavsett valet. **Keep the new decisions** lämnar de beslut den nya körningen fyllde i.

När Lisa färdigställer dokumentet och Olle checkar in ändringen ger den fjärde Checken pass. Underlaget är nytt, så det tidigare `accepted` återanvänds inte. De tre andra kan fortfarande återanvändas om deras underlag står stilla.

Niklas granskar den fjärde punkten och godkänner. En ny review-rapport signeras.

Historiken visar fortfarande att dokumentet först saknades, att avvikelsen accepterades, och att den senare blev pass.
