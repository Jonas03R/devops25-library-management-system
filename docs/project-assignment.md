# Slutprojekt: Library Management System och egen CI/CD-kedja

## Mål

Bygg vidare på demonstrationsrepositoryt till ett enkelt digitalt bibliotek. Visa samtidigt hur GitHub Actions automatiskt kontrollerar ändringar innan de går vidare mot en testdeployment. Börja med den minsta fungerande versionen; lägg inte till databas, inloggning eller molndrift innan grundflödet och testerna fungerar.

## Steg 0: Hämta och kontrollera rätt repository

Guiderna nämner två olika repositoryn:

- `cloudfactoreu/devops25-ci-cd-course` är kursmallen. Den allmänna Git-guiden visar hur du forkar den till din egen GitHub-användare.
- `cloudfactoreu/devops25-ci-cd-demo` är demonstrationsrepositoryt för Dag 2. Det är där studentguiden säger att CI-övningarna ska göras, och det är den kodbas som den här Library Management System-versionen bygger vidare på.

Arbeta alltså i din egen fork av demonstrationsrepositoryt:

```text
https://github.com/cloudfactoreu/devops25-ci-cd-demo
```

Om du inte har klonat det ännu:

1. Skapa en fork av `devops25-ci-cd-demo` på GitHub.
2. Följ Git-guidens rekommenderade plats `C:\GitHub` (undvik om möjligt OneDrive/synkroniserade mappar).
3. Klona din fork i PowerShell; byt ut `DIN-ANVÄNDARE` mot ditt GitHub-kontonamn:

```powershell
Set-Location C:\GitHub
git clone https://github.com/DIN-ANVÄNDARE/devops25-ci-cd-demo.git
Set-Location C:\GitHub\devops25-ci-cd-demo
git remote -v
git status
```

Om du redan står i den här klonade projektmappen ska du inte klona en kopia inuti den. Kontrollera först:

```powershell
git branch --show-current
git status --short
git remote -v
```

Kontrollera att `origin` pekar på din egen fork innan du pushar. Om den pekar på kursens original, skapa först en fork och ändra därefter remote:

```powershell
git remote set-url origin https://github.com/DIN-ANVÄNDARE/devops25-ci-cd-demo.git
git remote -v
```

Flytta inte eller radera en befintlig projektmapp på chans. Guiden rekommenderar att hela mappen (inklusive den dolda `.git`) flyttas och att `git status` kontrolleras efteråt. Spara först lokala ändringar och säkerställ att de finns i din fork.

## Steg 1: Kör och förstå nuläget

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest
python -m uvicorn app.main:app --reload
```

Öppna `http://127.0.0.1:8000/docs`. Prova `/health`, `/api/add` och `/api/divide`. Läs sedan `.github/workflows/ci.yml`: vid push eller pull request mot `main` installeras beroenden, Ruff körs, tester körs och Docker-imagen byggs efter godkända tester.

Om du redan har en arbetsbranch, fortsätt där. Annars skapa en:

```powershell
git switch -c feature/library-management
```

Skriv ned testresultatet och vad den befintliga pipelinen faktiskt kontrollerar. Föreläsningens Dag 2-kedja är **commit → trigger → build → resultat → feedback**. En vanlig push till en ny branch startar inte den befintliga CI:n; öppna en pull request mot `main`. I Dag 2-övningen ska du läsa `ci.yml`, inte ändra den.

## Steg 2: Avgränsa första versionen

Implementera och testa dessa flöden först:

1. Registrera en bok med titel, författare och valfritt ISBN.
2. Visa hela katalogen och sök efter titel eller författare (skiftlägesokänsligt).
3. Registrera en användare.
4. Låna en bok som finns och är tillgänglig till en registrerad användare.
5. Registrera återlämning och kontrollera att boken blir tillgänglig igen.

API:t ska ge `404` för bok, användare eller lån som inte finns och `409` när en redan utlånad bok lånas eller ett lån återlämnas en andra gång. Första versionen använder minne som lagring. Om processen startas om försvinner data; det är en avsiktlig ramarbetingelse, inte beständig biblioteksdrift.

## Steg 3: Testa reglerna innan nästa steg i kedjan

Kör tester lokalt:

```powershell
pytest
ruff check app tests
```

Kontrollera minst:

- en tillgänglig bok går att låna av en registrerad användare
- en bok som redan är utlånad inte kan lånas igen
- en bok som inte finns inte kan lånas
- en bok blir tillgänglig efter återlämning
- sökning ger träffar på titel/författare och returnerar inte orelaterade böcker
- felaktiga ID:n ger tydliga HTTP-felkoder

Skapa gärna ett avsiktligt fel i en egen, tillfällig branch och se att ett test blir rött. Återställ felet genom att ändra koden, inte genom att radera eller skriva över arbete som du vill behålla. Förklara vad loggen visar och varför pipelinen ska stoppa vid fel.

Se sammanfattningarna för Dag 3–6 i [README.md](../README.md) för testning, quality gates, Docker, simulerad deployment, verifiering och rollback. I det här repositoryt kör **Test and Lint** Ruff och Pytest; **Build Docker Image** väntar på att det jobbet lyckas. Den gate:en stoppar image-build, men ruleset/branch protection behövs separat för att kräva gröna kontroller före merge.

## Steg 4: Använd GitHub som arbetsflöde

Gör små commits med ett tydligt syfte:

```powershell
git add app tests docs README.md Dockerfile .github/workflows scripts
git commit -m "Add library CI/CD workflow"
git status
```

Pusha din branch till din egen fork och öppna en pull request mot dess `main`. Kontrollera att CI-jobbet kör Ruff, tester och image-build. Läs loggarna även när jobbet misslyckas; åtgärda felet och pusha en ny commit. Slå inte ihop en ändring som har röda obligatoriska kontroller.

I GitHub Actions är ett **workflow** YAML-beskrivningen, ett **job** en grupp steg, och en **runner** maskinen som kör jobbet. `uses` kör en färdig Action, `run` kör ett kommando och `needs` gör att ett jobb väntar på ett annat. I den här CI:n kör Ruff lint, Pytest tester och Docker-builden väntar på att kontrollerna lyckas. Runnern är GitHub-hosted Ubuntu; bygg inte en self-hosted runner för den här övningen.

Säkerhet är en kompletterande del av kvalitet: Dependabot kan bevaka beroenden, CodeQL kan analysera riskmönster i kod och secret scanning kan upptäcka vissa incheckade hemligheter. De här funktionerna är inte aktiverade av nuvarande workflow. Följ Dag 3-guiden och kursens instruktioner för att studera dem; lägg aldrig riktiga tokens eller lösenord i koden.

## Steg 5: Bygg och verifiera leveransen

Bygg lokalt och starta containern:

```powershell
docker build -t library-management:local .
docker run --rm -p 8000:8000 library-management:local
```

Se Dag 3–6 i [README.md](../README.md) för Docker, simulerad deployment, test-artifact, felsökning, versionskontroll, rollback och lokal Kubernetes-orientering. CI sparar en JUnit-rapport men publicerar inte imagen till ett registry. CD-workflowen startar en tillfällig container och verifierar hälsa, katalog och applikationsversion; den är inte produktionsdrift.

## Steg 6: Redovisa och resonera

Visa:

1. applikationens API och en lyckad utlåning/återlämning
2. ett automatiserat test som fångar en regelöverträdelse
3. en GitHub Actions-körning från commit eller pull request
4. image-build, testrapport-artifact och verifiering av simulerad deployment
5. ett fel i pipelinen, loggen och hur det åtgärdades
6. rollback-strategin och begränsningarna för beständig data
7. hur du skulle förbättra systemet med databas, autentisering, övervakning och säker deployment i en riktig miljö

För varje steg ska du kunna förklara: **Vilket problem löser det? Vilken risk minskar det? Vad händer om steget saknas eller misslyckas?**

Kubernetes-manifesten är en orienteringsövning, inte ett krav på att använda Kubernetes för ett så litet projekt. Använd bara ett lokalt testkluster och kontrollera aktiv `kubectl`-context innan du kör kommandon.

## Kort ordlista

- **Repository:** Git-projekt med kod och historik. GitHub är en tjänst där repositoryn kan lagras och delas.
- **Fork:** din egen kopia av någon annans GitHub-repository.
- **Clone:** hämtar repositoryt och dess Git-historik till datorn.
- **Branch:** en separat utvecklingslinje för en ändring.
- **Commit:** ett namngivet, spårbart tillstånd i Git-historiken.
- **Push:** skickar lokala commits till ett fjärrrepository.
- **Pull request (PR):** ett förslag på att föra branchens ändringar till exempelvis `main`; GitHub kan köra CI-kontroller på förslaget.
- **CI:** automatisk feedback på ändringar genom exempelvis lint, test och build.
- **Runner:** maskinen som utför ett GitHub Actions-jobb. Den är inte samma sak som en Docker-image.

## Bedömning

Projektet bedöms inte bara på att det fungerar tekniskt. Du ska kunna förklara **varför** kedjan är byggd som den är.

### Minimikrav

- Repository och versionshanterade ändringar
- Build
- Automatiserade tester
- Artifact eller container image
- Deployment till testmiljö eller simulerad miljö
- Verifiering
- Felhantering eller rollback-resonemang

### Muntlig presentation

Visa:

1. Kedjans arkitektur
2. En fungerande körning
3. Ett fel eller en risk
4. Hur kedjan reagerar
5. Vad du skulle förbättra i en produktionsmiljö
