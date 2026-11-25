# Library Management System – projektdokumentation

## Projektöversikt

Projektet är ett enkelt digitalt bibliotekssystem och en övning i Continuous Integration och Continuous Delivery (CI/CD). Applikationen byggs vidare på kursens demonstrationsrepository och använder Python, FastAPI, pytest, Ruff, Docker och GitHub Actions.

Arbetsflödet som projektet demonstrerar är:

```text
Ändring → Git-commit → CI → tester och lint → Docker-image
       → simulerad deployment → verifiering → rollback-övning
```

Målet är inte bara att få applikationen att fungera, utan också att kunna förklara vad varje kontroll gör, vilken risk den minskar och vad som händer om ett steg misslyckas.

## Syfte och funktioner

Biblioteket erbjuder ett REST-API för att:

- registrera böcker med titel, författare och valfritt ISBN
- visa och söka i bokkatalogen efter titel eller författare
- visa endast tillgängliga böcker
- registrera och visa användare
- låna en tillgänglig bok till en registrerad användare
- registrera återlämning och göra boken tillgänglig igen
- kontrollera hälsa och applikationsversion via `/health` och `/version`

### Regler som applikationen kontrollerar

- En bok som inte finns kan inte lånas.
- En användare som inte finns kan inte låna en bok.
- En bok som redan är utlånad kan inte lånas igen.
- En återlämnad bok blir tillgänglig på nytt.
- Samma lån kan inte återlämnas två gånger.
- Bok- och författarsökning är skiftlägesokänslig.

API:t returnerar bland annat `404 Not Found` för saknade poster och `409 Conflict` vid en ogiltig utlånings- eller återlämningskonflikt.

### API-översikt

| Metod | Endpoint | Funktion |
| --- | --- | --- |
| `GET` | `/health` | Hälsokontroll |
| `GET` | `/version` | Visar applikationsversion och miljö |
| `POST` | `/api/books` | Registrerar en bok |
| `GET` | `/api/books` | Visar katalogen; `?q=...` söker |
| `GET` | `/api/books/available` | Visar tillgängliga böcker |
| `POST` | `/api/users` | Registrerar en användare |
| `GET` | `/api/users` | Visar användare |
| `POST` | `/api/loans` | Lånar en bok med `book_id` och `user_id` |
| `POST` | `/api/loans/{loan_id}/return` | Registrerar återlämning |

Swagger-dokumentationen finns på `/docs` när applikationen körs lokalt.

## Teknisk struktur

| Sökväg | Innehåll |
| --- | --- |
| `app/main.py` | FastAPI-applikation och HTTP-endpoints |
| `app/library.py` | Biblioteksmodeller, utlåningsregler och service |
| `app/service.py` | Enkla exempel-endpoints från kursens demo |
| `tests/test_api.py` | Tester av API-endpoints |
| `tests/test_service.py` | Tester av service- och biblioteksregler |
| `.github/workflows/ci.yml` | Kontinuerlig integration: test, lint, artifact och Docker-verifiering |
| `.github/workflows/cd-simulated.yml` | Simulerad, tillfällig deployment på GitHub-runner |
| `scripts/verify.sh` | Smoke tests för hälsa och bokkatalog |
| `scripts/deploy_local.sh` | Lokal Docker-build och deployment |
| `scripts/rollback_local.sh` | Lokal återställning till en sparad image |
| `k8s/` | Valfria Kubernetes-manifest för lokal orientering |
| `docs/` | Dag 2-guide och kompletterande kursmaterial; Dag 3–6 sammanfattas i README |

## Hur projektet byggdes

Projektet utvecklades från kursens befintliga FastAPI-demo. De enkla räkne-endpointsen behölls som demoexempel, medan biblioteksfunktionerna lades till separat. Arbetet delades upp så att affärsregler, HTTP-gränssnitt, tester och leveransflöde går att förstå och kontrollera var för sig.

### 1. Bibliotekets modeller och affärsregler

I `app/library.py` representeras en bok, användare och ett lån med dataklasserna `Book`, `User` och `Loan`. En bok har bland annat ett ID, titel, författare, valfritt ISBN och tillgänglighetsstatus. Ett lån kopplar ihop ett bok-ID och användar-ID och har en status för om det återlämnats.

`LibraryService` sköter reglerna och lagrar posterna i tre dictionaries i minnet. ID-räknarna börjar på 1 och ökas när nya poster skapas. En trådlåsning (`Lock`) används runt läsningar och ändringar av dessa strukturer.

- Sökningen tar bort omgivande blanksteg och jämför titel och författare utan skillnad mellan stora och små bokstäver.
- Utlåning kontrollerar i ordning att boken finns, användaren finns och boken är tillgänglig. Först därefter skapas ett lån och boken markeras som utlånad.
- Återlämning kontrollerar att lånet finns och inte redan är återlämnat. Därefter markeras lånet som återlämnat och boken som tillgänglig.

Denna lagringslösning är medvetet enkel. Inget skrivs till en databas eller fil, så innehållet försvinner när applikationsprocessen startas om.

### 2. FastAPI-gränssnitt och validering

`app/main.py` exponerar biblioteksfunktionerna som HTTP-endpoints. Pydantic-modellerna `BookCreate`, `UserCreate` och `BorrowRequest` beskriver indata. Titel, författare, namn och e-post måste ha minst ett tecken; bok- och användar-ID:n i ett låneanrop måste vara större än noll.

Routes anropar `LibraryService` i stället för att innehålla hela affärslogiken själva. Nya böcker, användare och lån returnerar statuskod `201`. En gemensam exception handler översätter bibliotekets fel till JSON-svar:

- saknad bok, användare eller lån ger `404`
- bok som redan är utlånad eller lån som redan återlämnats ger `409`

FastAPI skapar dessutom Swagger-gränssnittet på `/docs`, där API:t kan provas manuellt.

### 3. Dataflöde genom applikationen

Ett typiskt anrop går genom följande steg:

```text
HTTP-anrop
  → FastAPI/Pydantic validerar indata
  → endpoint i app/main.py
  → LibraryService i app/library.py tillämpar biblioteksreglerna
  → resultat eller LibraryError blir ett JSON-svar med HTTP-statuskod
```

Detta gör att samma utlånings- och återlämningsregler kan testas direkt i tjänsten och genom API:t. Hälsokontrollen `/health` visar att applikationen svarar. `/version` returnerar applikationsversionen `1.1` och miljön `demo`, så en körande container kan verifieras både för tillgänglighet och version.

### 4. Tester och isolering

`tests/test_service.py` testar reglerna direkt mot `LibraryService`, till exempel sökning, saknade poster, dubbel utlåning och återlämning. `tests/test_api.py` använder FastAPI `TestClient` för att anropa API-routes i testmiljön och kontrollera statuskoder och JSON-svar.

API-testernas automatiska fixture ersätter bibliotekstjänsten med en ny instans före varje test. På så sätt påverkar inte böcker och lån från ett test resultatet i nästa. Tester täcker även health/version, katalogsökning och de bevarade räkne-endpointsen.

### 5. CI, container och simulerad leverans

CI i `.github/workflows/ci.yml` installerar Python 3.12 och projektets beroenden på en GitHub-hosted Ubuntu-runner. Pytest skriver en JUnit-rapport; rapporten laddas upp som `pytest-results`, även när tidigare steg misslyckats (om filen finns). Ruff körs därefter. Docker-jobbet har `needs: test` och startar därför inte förrän testjobbet lyckats.

Dockerfile bygger på `python:3.12-slim`, installerar beroenden och startar Uvicorn på port 8000. CI bygger en SHA-taggad image, startar den, verifierar hälsa och bokkatalog samt kontrollerar att `/version` svarar med `1.1`. Vid verifieringsfel samlas containerloggar in; containern tas bort i ett avslutande steg.

`cd-simulated.yml` demonstrerar en separat, tillfällig deployment på en GitHub-runner. Den bygger och verifierar en container men publicerar inte imagen till ett registry och lämnar inte applikationen körande efter jobbet. Eftersom CI och CD har separata triggers väntar CD inte automatiskt på en grön CI-körning.

### 6. Lokal drift och rollback

För lokal drift bygger `scripts/deploy_local.sh` imagen `library-management:local` och startar containern `library-management-demo`. Om en container med detta övningsnamn redan finns, sparar skriptet dess image under taggen `library-management:previous` innan containern ersätts.

`scripts/verify.sh` väntar på att health-endpointen ska svara och kontrollerar sedan att bokkatalogen returnerar en JSON-lista. `scripts/rollback_local.sh` kontrollerar att rollback-imagen finns, startar den och verifierar hälsa/katalog samt en valfri förväntad appversion.

Rollback fungerar bara om det finns en tidigare fungerande image att återgå till. En image-rollback återställer inte beständig data; nuvarande applikation lagrar data i minnet. Kubernetes-manifesten är en separat, valfri orienteringsövning och är inte en produktionsdeployment.

## **Projektets arbetsplan**

### 1. Planera projektet – syfte, funktioner och krav

**Genomfört:** Projektidén avgränsades till ett litet bibliotekssystem med böcker, användare, utlåning och återlämning. Kraven omfattar även sökning, tillgänglighetsstatus och automatiska kontroller av felaktiga lån.

**Tekniskt val:** Första versionen har ett litet REST-API. Inloggning, betalningar, förseningsavgifter och produktionsdatabas ingår inte i omfattningen.

**Begränsning:** Data lagras i minnet och återställs när processen startas om. Det är en medveten förenkling för CI/CD-övningen, inte en lösning för ett verkligt bibliotek.

### 2. Förbereda utvecklingsmiljön – Python, Git och projektstruktur

**Genomfört:** Projektet använder Python och en virtuell miljö (`.venv`). Beroenden är definierade i `requirements.txt`. Git används för att följa kodändringar och GitHub för att lagra repositoryt och köra Actions.

Skapa och aktivera en virtuell miljö i Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Kontrollera sedan att rätt branch och ändringar används:

```powershell
git status
git branch --show-current
git remote -v
```

**Teknik:** FastAPI och Uvicorn kör API:t, pytest kör automatiska tester och Ruff kontrollerar kodstil.

### 3. Bygga bibliotekssystemet – böcker, användare och utlåning

**Genomfört:** API:t kan skapa och lista böcker och användare, söka i katalogen, visa tillgängliga böcker, låna och återlämna böcker. Biblioteksregler och datahantering finns i `app/library.py`; HTTP-gränssnittet finns i `app/main.py`.

**Felhantering:** Applikationen returnerar tydliga HTTP-felkoder för poster som saknas och för böcker eller lån i ett ogiltigt tillstånd.

**Versionskontroll:** `GET /version` returnerar nu version `1.1` och miljö `demo`. CI och simulerad CD kontrollerar också svaret från en körande container.

### 4. Skriva automatiska tester – kontrollera att funktionerna fungerar

**Genomfört:** Pytest-tester täcker bland annat:

- hälsokontroll och versionsendpoint
- sökning efter bok
- nekad utlåning av bok som saknas eller redan är utlånad
- nekad utlåning till användare som saknas
- återlämning och uppdaterad tillgänglighet
- nekad upprepad återlämning
- grundläggande servicefunktioner, inklusive division med noll

Kör kontrollerna lokalt:

```powershell
python -m pytest -v
python -m ruff check app tests
```

Vid den senaste lokala kontrollen passerade **12 tester** och Ruff-kontrollen. Pytest visade även ett deprecation-varningsmeddelande från en beroendekedja (Starlette/AnyIO); varningen hindrade inte testen från att passera.

### 5. Versionshantera med Git och GitHub – branches, commits och Pull Requests

**Genomfört:** Projektet versionshanteras med Git. Feature branches används för arbete med en ändring i taget. Ändringar kan pushas till GitHub och föreslås för `main` genom en Pull Request (PR).

Exempel på arbetsflöde:

```powershell
git switch -c feature/min-andring
git add app tests docs
git commit -m "Beskriv ändringen kort"
git push -u origin feature/min-andring
```

Öppna därefter en PR med `main` som **base** och feature-branchen som **compare**. Granska ändringarna och resultatet från CI innan eventuell merge. En PR är ett förslag om att föra in ändringar; den mergar inte automatiskt sig själv.

**Viktigt:** Kontrollera alltid att `origin` pekar på ditt eget GitHub-repository innan du pushar.

### 6. Skapa CI-pipeline – automatisera bygg- och testkontroller

**Genomfört:** `.github/workflows/ci.yml` körs vid push till `main` och `feature/**`, samt vid pull request mot `main`. Den använder en GitHub-hosted Ubuntu-runner och utför följande:

1. checkar ut koden och installerar Python 3.12
2. installerar beroenden från `requirements.txt`
3. kör pytest och skriver en JUnit-rapport till `reports/pytest.xml`
4. laddar upp rapporten som artifact med namnet `pytest-results`
5. kör Ruff
6. efter godkänt test-/lint-jobb bygger och startar en Docker-container
7. verifierar `/health`, bokkatalogen och `/version`
8. visar containerloggar vid fel och städar containern efteråt

**Varför:** Automatiska kontroller ger snabb feedback och kan fånga fel innan ändringar integreras. Docker-jobbet väntar på att testjobbet lyckas (`needs: test`).

**Begränsning:** En grön körning bevisar bara att de automatiserade kontroller som ingår har passerat. Den är inte i sig en fullständig säkerhetsgranskning eller garanti för produktionsmiljö.

### 7. Paketering och leverans – förbereda applikationen för leverans

**Genomfört:** Projektet innehåller en `Dockerfile` och `docker-compose.yml`. Docker-image kan byggas med en commitbaserad tagg i CI eller med taggen `library-management:local` lokalt.

Exempel:

```bash
docker build -t library-management:local .
```

**Leverans i den här kurslösningen:** CI bygger en image och CD-workflowen bygger en image på sin runner. Imagen publiceras inte till ett externt container registry som GHCR eller Docker Hub.

**Tekniskt val:** En tagg med commit-SHA gör det lättare att koppla en byggd image till källkodens commit. I en produktionskedja bör samma spårbara image publiceras och återanvändas mellan miljöer.

### 8. Deployment och verifiering – starta och kontrollera applikationen

**Genomfört:** `scripts/deploy_local.sh` bygger och startar containern `library-management-demo`. `scripts/verify.sh` kontrollerar att `/health` svarar och att `/api/books` returnerar en JSON-lista.

I Git Bash från projektroten:

```bash
bash scripts/deploy_local.sh
bash scripts/verify.sh
```

GitHub-workflowen `cd-simulated.yml` kör också en separat deployment på en tillfällig GitHub-runner. Den verifierar applikationen och städar containern när jobbet avslutas.

**Avgränsning:** Det är en simulerad deployment; applikationen körs inte permanent och blir inte publicerad för externa användare. CD och CI har separata triggers, så CD är inte automatiskt en release-gate som väntar på grön CI.

Kubernetes-manifest finns i `k8s/` som en valfri lokal övning. De har inte verifierats mot ett lokalt kluster i denna utvecklingsmiljö. Kontrollera alltid aktiv `kubectl`-context och använd endast ett lokalt övningskluster.

### 9. Felhantering och rollback – visa hur problem upptäcks och hanteras

**Genomfört:** Workflowen kan visa containerloggar om verifieringen misslyckas och städar containern även vid fel. Dag 6-avsnittet i README beskriver felsökning från första röda steget: kontrollera commit och trigger, läs loggen, formulera en hypotes, återskapa felet och verifiera rättningen.

`scripts/deploy_local.sh` sparar den befintliga containerns image som `library-management:previous` innan den ersätter containern. `scripts/rollback_local.sh` kan starta den sparade imagen och verifiera hälsa, katalog samt valfri förväntad appversion:

```bash
bash scripts/rollback_local.sh library-management:previous 1.1
```

**Viktig begränsning:** Första deploymenten har ingen tidigare image att återställa. Rollback av en image återställer inte beständig data. I nuläget lagras dessutom applikationsdata endast i minnet. En rollback fungerar bara som verklig kodåterställning om den sparade imagen kommer från en tidigare fungerande version.

### 10. Dokumentation och demonstration – redovisa lösningen och dina tekniska val

Denna fil sammanfattar projektets mål, genomförda funktioner och CI/CD-kedja. Övriga guider finns i `docs/`:

- Slutprojektets steg-för-steg-guide finns under Dag 6 i [README.md](README.md)
- [Dag 2 – CI](docs/day-02-ci.md)
- Dag 3–6 sammanfattas i [README.md](README.md)

För en demonstration kan du visa:

1. hur en bok och användare registreras och hur en bok lånas och återlämnas
2. ett automatiskt test som kontrollerar en biblioteksregel
3. en GitHub Actions-körning och JUnit-artifacten
4. Docker-build och resultatet från API-verifieringen
5. en felsöknings- eller rollback-övning
6. vilka begränsningar som finns och hur systemet skulle kunna utvecklas vidare

Förklara vid varje del: **Vilket problem löser detta? Vilken risk minskar det? Vad händer om kontrollen misslyckas?**

## Starta applikationen lokalt

Aktivera den virtuella miljön och starta FastAPI:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Öppna sedan `http://127.0.0.1:8000/docs` för att prova API:t. Starta en ny terminal för tester och kör `python -m pytest -v`.

## Nästa möjliga utvecklingssteg

Projektets medvetna begränsningar ger förslag på fortsättning:

- byt minneslagringen mot SQLite så data överlever omstart
- lägg till fler validerings- och API-tester
- aktivera GitHub branch protection så merge kräver godkända kontroller
- lägg till testtäckningsrapport eller beroendesårbarhetskontroll
- omfatta faktisk artifact-/image-publicering och en skyddad testmiljö först när det ingår i uppgiften

Utöka projektet stegvis och uppdatera tester, workflow och dokumentation tillsammans med varje beteendeförändring.
