# DEVOPS25 CI/CD – Library Management System

Det här repositoryt används stegvis i kursen **Continuous Integration och Continuous Delivery**. Den ursprungliga demoapplikationen finns kvar, och en första version av projektidén **Library Management System** går att köra och testa.

Nyckelordet är **VARFÖR**. Verktygen används för att göra principerna synliga, inte för att kursen ska bli en verktygskurs.

## Kursens röda tråd

```text
Commit → Build → Test → Artifact/Image → Deploy → Verify → Rollback
```

## Vad repositoryt innehåller

- Ett FastAPI-API för bokkatalog, användare och lån
- De ursprungliga demo-endpointsen `/api/add` och `/api/divide`
- Unit tests och integrationstester
- Dockerfile och docker-compose
- GitHub Actions för CI och en simulerad CD-kedja
- Sparad JUnit-testrapport från CI
- Scripts för lokal körning, verifiering, deployment och rollback
- Studentuppgifter för vecka 1–4
- Projektuppgift och bedömningsstöd
- [Samlad projektdokumentation för Library Management System](Library.md)

## Snabbstart lokalt

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
pytest
python -m uvicorn app.main:app --reload
```

- Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- API-dokumentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Börja projektarbetet

Demonstrationsrepositoryt är `https://github.com/cloudfactoreu/devops25-ci-cd-demo`. Följ [slutprojektets steg-för-steg-guide under Dag 6](#slutprojekt-library-management-system) innan du börjar bygga vidare. Om du redan arbetar i den här klonade katalogen ska du inte klona en kopia inuti den.

Den första implementationen lagrar data i minnet. Böcker och lån återställs därför när applikationen startas om; det gör att vi kan fokusera på Git, tester och CI innan vi senare väljer beständig lagring.

### Första API-funktioner

| Metod | Endpoint | Syfte |
| --- | --- | --- |
| `POST` | `/api/books` | Registrera bok |
| `GET` | `/api/books` | Visa eller söka böcker med `?q=...` |
| `GET` | `/api/books/available` | Visa tillgängliga böcker |
| `POST` | `/api/users` | Registrera användare |
| `GET` | `/api/users` | Visa användare |
| `POST` | `/api/loans` | Låna bok (`book_id`, `user_id`) |
| `POST` | `/api/loans/{loan_id}/return` | Registrera återlämning |

## Docker

```bash
docker build -t library-management:local .
docker run --rm -p 8000:8000 library-management:local
```

## Pedagogisk användning

Repositoryt följer kursens steg från första commit till verifierad leverans:

- **Dag 1:** förstå applikationen och varför versionshantering behövs
- **Dag 2:** skapa första CI-pipelinen – se [Dag 2-guiden](docs/day-02-ci.md)
- **Dag 3–6:** testning, Docker, simulerad leverans och drift – sammanfattas i avsnitten nedan
- **Projekt:** bygga och motivera en egen CI/CD-kedja för bibliotekssystemet

## Viktig fråga i varje steg

> Vilket problem löser detta steg, och vad riskerar vi om steget saknas?

## CI/CD Dag 1

## Genomförda moment

Jag har genomfört följande moment:

- Klonat demonstrationsrepositoryt.
- Skapat en virtuell Python-miljö.
- Installerat projektets beroenden.
- Kört automatiserade tester med pytest.
- Undersökt API:et med Swagger.
- Skapat en egen Git-branch.

## Testresultat

Vid Dag 1-baseline passerade 5 tester. LMS-testsviten har utökats vidare; kör `python -m pytest -v` för aktuellt testresultat.

## Dag 3: Testning, kvalitet och quality gates

En build visar att projektet kan byggas, men inte att biblioteksreglerna fungerar. Därför används flera kontroller:

- **Unit tests** i `tests/test_service.py` kontrollerar sökning, utlåning och återlämning direkt i tjänsten.
- **API-tester** i `tests/test_api.py` kontrollerar HTTP-svar, statuskoder och samspelet mellan API och tjänst.
- **Ruff** kontrollerar kodkvalitet och fångar andra problem än testerna.
- Manuell verifiering och smoke tests kontrollerar att applikationen kan starta och svara.

Viktiga testfall är att en redan utlånad eller saknad bok inte kan lånas, att en återlämnad bok blir tillgänglig och att sökning ger rätt resultat. Kör kontrollerna lokalt:

```powershell
python -m pytest -v
python -m ruff check app tests
```

I CI körs **Test and Lint** före **Build Docker Image**. `needs: test` gör att Docker-jobbet väntar tills testjobbet lyckats. Detta stoppar image-build vid misslyckade kontroller, men kräver inte automatiskt godkända kontroller före merge. Det behöver ställas in separat med branch protection eller ruleset. Dependabot, CodeQL och secret scanning är kompletterande säkerhetsfunktioner och aktiveras inte av den nuvarande CI-workflowen.

## Dag 4: Docker och image-build

En **Dockerfile** beskriver byggreceptet, en **image** är det paketerade resultatet och en **container** är en körande instans av imagen. Projektets Dockerfile installerar Python-beroenden och startar API:t på port 8000.

Bygg och starta lokalt:

```powershell
docker build -t library-management:local .
docker run --rm --name library-management-demo -p 8000:8000 library-management:local
```

Öppna `http://127.0.0.1:8000/health` eller `/docs` medan containern kör. Stoppa den med `Ctrl+C`. Om port 8000 används kan värdporten ändras, till exempel `-p 8001:8000`.

CI bygger imagen med en tagg som innehåller commitens SHA och startar den för att kontrollera hälsa, bokkatalog och applikationsversion. Builden sker på en tillfällig runner och imagen publiceras inte till Docker Hub eller GHCR. En lyckad build är alltså inte samma sak som publicering eller deployment.

## Dag 5: Simulerad Continuous Delivery och verifiering

CI sparar Pytests JUnit-rapport `reports/pytest.xml` som artifacten `pytest-results`. Rapporten kan laddas ner från GitHub Actions-körningens **Summary**. Den visar testresultat; den är inte en körande applikation.

CD-workflowen bygger och startar en container på en tillfällig GitHub-runner. Den verifierar `/health`, bokkatalogen och `/version`, visar loggar vid verifieringsfel och städar sedan containern. Flödet kan också köras lokalt med Docker:

```bash
bash scripts/deploy_local.sh
bash scripts/verify.sh
```

CI och CD har separata triggers; CD väntar inte automatiskt på att CI ska vara grön. CD-flödet är därför en undervisningssimulering, inte en produktions-release-gate. Ingen image publiceras och deploymenten är inte permanent.

## Dag 6: Felsökning, versionskontroll och rollback

Vid ett rött workflow kontrolleras först branch, commit och trigger. Läs det första misslyckade steget, formulera en hypotes, återskapa felet om möjligt, ändra en sak i taget och verifiera rättningen.

API:ets `GET /version` returnerar `1.1` och miljön `demo`. CI och CD kontrollerar denna endpoint i den startade containern. `/health` visar att tjänsten svarar, medan `/version` hjälper till att kontrollera vilken appversion som körs.

`scripts/deploy_local.sh` sparar den tidigare containerns image som `library-management:previous` när en befintlig lokal container ersätts. En rollback kan göras med:

```bash
bash scripts/rollback_local.sh library-management:previous 1.1
```

Det kräver att en tidigare image finns. Den första deploymenten har inget att återställa, och rollback av en image återställer inte applikationsdata. I nuvarande projekt lagras data i minnet och försvinner vid omstart.

Manifesten i `k8s/` visar en valfri lokal Kubernetes Deployment och Service med readiness- och liveness-prober. Image måste finnas i det lokala klustret; kontrollera alltid `kubectl`-context och använd inte produktionsmiljö för övningen. Kubernetes-delen är orientering, inte ett krav för bibliotekssystemet.

### Slutprojekt: Library Management System

#### Mål

Bygg vidare på kursens demonstrationsrepository till ett enkelt digitalt bibliotek. Visa samtidigt hur GitHub Actions automatiskt kontrollerar ändringar före en testdeployment. Börja med minsta fungerande version. Lägg inte till databas, inloggning eller molndrift innan grundflödet och testerna fungerar.

#### Steg 0: Hämta och kontrollera rätt repository

Kursmaterialet använder två olika repositoryn:

- `cloudfactoreu/devops25-ci-cd-course` är kursmallen och innehåller generell vägledning.
- `cloudfactoreu/devops25-ci-cd-demo` är demonstrationsrepositoryt för Dag 2 och kodbasen som bibliotekssystemet bygger vidare på.

Om du börjar från kursens demo ska du arbeta i din egen fork. Om du redan arbetar i ditt eget Library Management System-repository ska du inte klona en ny kopia eller byta remote utan anledning.

Kontrollera arbetsmapp, branch och remote i PowerShell:

```powershell
git status
git branch --show-current
git remote -v
```

Om du behöver klona en egen fork av demonstrationsrepositoryt, byt ut `DIN-ANVÄNDARE` mot ditt GitHub-kontonamn:

```powershell
Set-Location C:\GitHub
git clone https://github.com/DIN-ANVÄNDARE/devops25-ci-cd-demo.git
Set-Location C:\GitHub\devops25-ci-cd-demo
git remote -v
```

Kontrollera att `origin` pekar på din egen fork innan du pushar. Om du redan har en projektmapp ska du inte klona en kopia inuti den. Flytta eller radera inte en befintlig projektmapp på chans; spara ändringar och kontrollera Git-status först. Kursguiden rekommenderar att undvika synkroniserade mappar om möjligt.

Om `origin` pekar på kursens original och du redan har skapat en egen fork kan du ändra adressen så här:

```powershell
git remote set-url origin https://github.com/DIN-ANVÄNDARE/devops25-ci-cd-demo.git
git remote -v
```

#### Steg 1: Kör och förstå nuläget

Skapa en virtuell Python-miljö, installera beroenden och starta appen:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
python -m uvicorn app.main:app --reload
```

Öppna `http://127.0.0.1:8000/docs` och prova `/health`, `/api/add` och `/api/divide`. Läs `.github/workflows/ci.yml` och följ kedjan **commit → trigger → build → resultat → feedback**. Den nuvarande CI:n körs vid push till `main` och `feature/**`, samt vid pull request mot `main`. Den installerar beroenden, kör Pytest och Ruff och bygger/verifierar Docker-imagen efter godkända kontroller.

Om du saknar arbetsbranch skapar du en:

```powershell
git switch -c feature/library-management
```

Notera vad den befintliga pipelinen faktiskt kontrollerar. I Dag 2-övningen ska du läsa `ci.yml` och förstå den innan du ändrar den.

#### Steg 2: Avgränsa första versionen

Implementera och testa dessa flöden först:

1. Registrera en bok med titel, författare och valfritt ISBN.
2. Visa katalogen och sök efter titel eller författare, utan skillnad mellan stora och små bokstäver.
3. Registrera och visa användare.
4. Låna en tillgänglig bok till en registrerad användare.
5. Registrera återlämning och kontrollera att boken blir tillgänglig igen.

API:t ska ge `404` för en bok, användare eller ett lån som saknas och `409` när en redan utlånad bok lånas eller ett lån återlämnas en andra gång. Första versionen använder minnet som lagring. Om processen startas om försvinner data; detta är en avsiktlig förenkling, inte beständig biblioteksdrift.

#### Steg 3: Testa reglerna innan nästa steg i kedjan

Kör tester och lint lokalt:

```powershell
python -m pytest
python -m ruff check app tests
```

Kontrollera minst att:

- en tillgänglig bok går att låna av en registrerad användare
- en bok som redan är utlånad inte kan lånas igen
- en bok som inte finns inte kan lånas
- en bok blir tillgänglig efter återlämning
- sökning matchar titel/författare och inte returnerar orelaterade böcker
- felaktiga ID:n ger tydliga HTTP-felkoder

Som övning kan du i en tillfällig branch ändra en testförväntning så att testet blir rött. Läs felmeddelandet, återställ just den ändringen och kör hela testsamlingen igen. Återställ inte hela testfilen eller byt branch på chans; det kan kasta bort arbete. Skapa inte en commit med det avsiktligt felaktiga testet.

För en konkret övning, ändra tillfälligt förväntningen för den andra utlåningen i `test_cannot_borrow_a_missing_or_already_borrowed_book` från `409` till `200` och kör testet:

```powershell
python -m pytest tests/test_api.py::test_cannot_borrow_a_missing_or_already_borrowed_book -q
```

Testet ska bli rött eftersom API:t korrekt svarar `409`. Återställ den ändrade förväntningen till `409` och kör sedan hela testsamlingen och Ruff igen.

I CI kör **Test and Lint** Pytest och Ruff. **Build Docker Image** väntar på att det jobbet lyckas, vilket stoppar image-build om testjobbet fallerar. Denna gate kräver inte automatiskt godkända kontroller före merge; det kräver branch protection eller en ruleset. En code review är en mänsklig kontroll och ersätter inte testerna. Gröna tester bevisar endast att de testade beteendena passerar, inte att alla fel eller säkerhetsrisker är täckta.

#### Steg 4: Använd GitHub som arbetsflöde

Gör små commits med ett tydligt syfte. Exempel:

```powershell
git add app tests docs README.md Dockerfile .github/workflows scripts
git commit -m "Describe the change"
git status
git push -u origin feature/library-management
```

Öppna en pull request (PR) från arbetsbranchen till din egen forks `main`. Kontrollera att CI körs, läs loggar vid fel och pusha rättningar till samma branch. Slå inte ihop en ändring med misslyckade obligatoriska kontroller.

I GitHub Actions är ett **workflow** YAML-beskrivningen, ett **job** en grupp steg och en **runner** maskinen som kör jobbet. `uses` kör en färdig Action, `run` kör ett kommando och `needs` gör att ett jobb väntar på ett annat. I projektets CI kör Ruff lint, Pytest tester och Docker-jobbet väntar på testjobbet. Runnern är GitHub-hosted Ubuntu; bygg inte en self-hosted runner för denna övning.

Säkerhetskontroller kompletterar testning. Dependabot kan bevaka beroenden, CodeQL kan analysera kodmönster och secret scanning kan upptäcka vissa incheckade hemligheter. De är inte aktiverade i nuvarande workflow. Lägg aldrig riktiga tokens eller lösenord i källkod.

#### Steg 5: Bygg och verifiera leveransen

Bygg och starta containern lokalt:

```powershell
docker build -t library-management:local .
docker run --rm -p 8000:8000 library-management:local
```

Verifiera `/health` och prova API:t i `/docs`. Dag 3–6-avsnitten ovan förklarar testnivåerna, Docker, artifacts, simulerad deployment, versionskontroll och rollback. CI sparar en JUnit-rapport men publicerar inte imagen till ett registry. CD-workflowen startar en tillfällig container och verifierar hälsa, katalog och applikationsversion; det är inte produktionsdrift.

#### Steg 6: Redovisa och resonera

Visa:

1. API:t och en lyckad utlåning/återlämning
2. ett automatiserat test som fångar en regelöverträdelse
3. en GitHub Actions-körning från commit eller pull request
4. image-build, testrapport-artifact och verifiering av simulerad deployment
5. ett fel i pipelinen, loggen och hur felet åtgärdades
6. rollback-strategin och begränsningarna för beständig data
7. möjliga förbättringar, exempelvis databas, autentisering, övervakning och säker deployment

För varje steg ska du kunna förklara: **Vilket problem löser det? Vilken risk minskar det? Vad händer om steget saknas eller misslyckas?**

Kubernetes-manifesten är en orienteringsövning, inte ett krav för ett så litet projekt. Använd endast ett lokalt testkluster och kontrollera aktiv `kubectl`-context innan du kör kommandon.

#### Kort ordlista

- **Repository:** Git-projekt med kod och historik.
- **Fork:** en egen kopia av någon annans GitHub-repository.
- **Clone:** hämtar repositoryt och dess Git-historik till datorn.
- **Branch:** en separat utvecklingslinje för en ändring.
- **Commit:** ett namngivet, spårbart tillstånd i Git-historiken.
- **Push:** skickar lokala commits till ett fjärrrepository.
- **Pull request (PR):** ett förslag att föra branchens ändringar till exempelvis `main`; GitHub kan köra CI-kontroller på förslaget.
- **CI:** automatisk feedback på ändringar genom exempelvis lint, test och build.
- **Runner:** maskinen som utför ett GitHub Actions-jobb; den är inte samma sak som en Docker-image.

#### Bedömning

Projektet bedöms inte bara på att det fungerar tekniskt. Du ska kunna förklara varför CI/CD-kedjan är byggd som den är.

Minimikraven är:

- repository och versionshanterade ändringar
- build
- automatiserade tester
- artifact eller container image
- deployment till testmiljö eller simulerad miljö
- verifiering
- felhantering eller rollback-resonemang

Vid muntlig presentation visar du kedjans arkitektur, en fungerande körning, ett fel eller en risk, hur kedjan reagerar och vad du skulle förbättra i en produktionsmiljö.
