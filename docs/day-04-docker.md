# Dag 4: Docker och image-build för bibliotekssystemet

## Mål

Följ bibliotekssystemets kod genom byggkedjan: Dockerfile → image → container → verifierat svar. CI bygger samma projekt som en SHA-taggad image efter att lint och tester har passerat.

## 1. Förstå delarna

- **Dockerfile:** byggreceptet. `FROM` väljer Python-basimage, `WORKDIR` väljer arbetskatalog, `COPY` lägger in beroendefilen och applikationen, `RUN` installerar paket, `EXPOSE` dokumenterar containerns port och `CMD` startar Uvicorn.
- **Image:** det paketerade resultatet av Docker-bygget. Den kan få namn och tagg.
- **Container:** en körande instans av en image. `-p 8000:8000` kopplar värddatorns port 8000 till containerns port 8000. `--rm` tar bort containern när den stängs, inte imagen.

Projektets [Dockerfile](../Dockerfile) använder `python:3.12-slim`, installerar `requirements.txt` och startar API:t på port 8000. Du behöver inte aktivera `.venv` för att köra containern; den har sin egen Pythonmiljö. Stäng en separat lokal Uvicorn-server om den redan använder port 8000.

## 2. Bygg imagen lokalt

Starta Docker Desktop och kör från projektets rotmapp i PowerShell:

```powershell
docker version
docker build -t library-management:local .
docker image ls library-management
```

Punkten betyder att den aktuella mappen används som build context. Docker kan återanvända oförändrade lager (`CACHED`), vilket ofta gör efterföljande byggen snabbare.

## 3. Starta och verifiera en container

```powershell
docker run --rm --name library-management-demo -p 8000:8000 library-management:local
```

Låt containern köra och öppna `http://127.0.0.1:8000/health` och `http://127.0.0.1:8000/docs`. Health-anropet ska returnera `{"status":"ok"}`. Prova även `http://127.0.0.1:8000/api/add?a=2&b=3`, som ska ge resultatet `5`. `/api/add` finns kvar från demoapplikationen och fungerar som ett enkelt smoke test.

Stoppa containern med `Ctrl+C`. Kontrollera därefter:

```powershell
docker ps -a
docker image ls library-management
```

Containern ska ha tagits bort genom `--rm`, medan imagen finns kvar. Om Docker Engine inte startar, kontrollera Docker Desktop och `docker version`. Om värdport 8000 är upptagen kan du i stället starta med `-p 8001:8000` och öppna URL:erna på port 8001.

## 4. Följ bygget i GitHub Actions

I [CI-workflowen](../.github/workflows/ci.yml) kör jobbet **Test and Lint** Ruff och Pytest. Jobbet **Build Docker Image** har `needs: test` och startar därför först när lint och tester är godkända. Det bygger imagen med taggen `library-management:${{ github.sha }}`. SHA-taggen kopplar det byggda resultatet till en bestämd commit, till skillnad från en flytande `latest`-tagg.

Arbetsflödet körs vid push till `main` och vid en pull request mot `main`. Skapa en arbetsbranch, pusha den till din egen GitHub-fork och öppna en PR mot `main`. Öppna PR:ens **Checks** eller GitHub Actions och verifiera att båda jobben passerar. Om testjobbet blir rött ska Docker-jobbet inte köras.

**Viktigt:** `docker build` bygger imagen på den lokala maskinen eller den tillfälliga GitHub-runnern. Dag 4 publicerar inte imagen till Docker Hub eller GHCR; att publicera kräver ett separat `docker push`-steg, registry och behörigheter. En lyckad build visar att imagen byggdes, inte att den publicerades eller att deployment verifierades.

## Dag 4 klart när du kan

- förklara skillnaden mellan Dockerfile, image och container
- visa en lokal image och starta dess container
- verifiera health-endpointen och förklara portmappningen
- hitta den SHA-taggade Docker-builden i GitHub Actions
- förklara varför CI-bygget väntar på tester och varför build inte är samma sak som publicering eller deployment
