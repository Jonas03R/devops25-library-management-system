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

Demonstrationsrepositoryt är `https://github.com/cloudfactoreu/devops25-ci-cd-demo`. Följ [projektuppgiftens steg-för-steg-guide](docs/project-assignment.md) innan du börjar bygga vidare. Om du redan arbetar i den här klonade katalogen ska du inte klona en kopia inuti den.

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
