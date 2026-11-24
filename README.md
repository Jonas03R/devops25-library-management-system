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

Repositoryt är byggt för att kunna användas stegvis:

1. **Dag 1:** förstå applikationen och varför versionshantering behövs
2. **Dag 2:** skapa första CI-pipelinen
3. **Dag 3:** [testning, kodkvalitet och quality gates](docs/day-03-testing.md)
4. **Dag 4:** [bygga och verifiera Docker-image](docs/day-04-docker.md)
5. **Dag 5:** [simulerad deployment, verifiering och artifacts](docs/day-05-delivery.md)
6. **Dag 6:** felsöka, verifiera och resonera om rollback
7. **Projekt:** bygga och motivera en egen CI/CD-kedja för bibliotekssystemet

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

Vid Dag 1-baseline passerade 5 tester. Den utökade LMS-testsviten kör nu 11 tester; kör `pytest` för aktuell status.
