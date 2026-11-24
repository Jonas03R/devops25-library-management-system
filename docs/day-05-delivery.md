# Dag 5: Continuous Delivery och verifiering

## Mål

Följ bibliotekssystemet genom kedjan **Build → Run → Verify → Cleanup**. CI testar och bygger; den simulerade CD-workflowen startar en container på en tillfällig GitHub-runner och kontrollerar att tjänsten svarar. Det här är inte en permanent eller publik produktionsdeployment.

## 1. Kontrollera branch och Docker

Från Git Bash i projektets rot:

```bash
pwd
git status
git branch --show-current
docker info
```

Arbeta i branchen `feature/day5-delivery`. Om du redan är på den branchen fortsätter du där. Om Docker Engine inte svarar startar du Docker Desktop innan du provar de lokala kommandona.

## 2. Följ CI-kontrollerna och testrapporten

I `.github/workflows/ci.yml` kör **Test and Lint** Pytest och Ruff. Pytest skriver `reports/pytest.xml` i JUnit-format; `actions/upload-artifact` försöker spara filen även om tester misslyckas. Efter godkända tester och lint bygger **Build Docker Image** en SHA-taggad image, startar den och verifierar API:t.

Efter en pull request mot `main`, öppna GitHub → **Actions** → den aktuella CI-körningen → **Summary**. Under **Artifacts** ska du kunna ladda ner `pytest-results` och öppna `reports/pytest.xml`. Workflow-körningen är resultat/loggar; XML-filen är en sparad artifact. CI-imagen byggs på en tillfällig runner och publiceras inte till ett registry.

## 3. Simulerad deployment i GitHub Actions

I `.github/workflows/cd-simulated.yml` startas CD-workflowen av push till `feature/day5-delivery` eller `feature/day6-operations` (eller manuellt när GitHub erbjuder **Run workflow**). Den checkar ut koden, bygger `library-management:<commit-SHA>`, startar containern, verifierar hälsa och bokkatalogens API, kontrollerar applikationsversionen, visar containerloggar vid verifieringsfel och stoppar containern även om verifieringen misslyckas.

Efter push, öppna GitHub → **Actions** → **CD - Simulated Deployment** → körningen → jobbet **Build, run and verify**. Läs stegen **Build Docker image**, **Start application**, **Verify deployment**, **Verify deployed version** och **Stop application**. En grön körning betyder att just dessa kontroller passerade på runnern; den betyder inte att applikationen publicerats eller körs efter att jobbet avslutats.

CI och CD har separata triggers. I den här undervisningssimuleringen kan CD starta på branch-push oberoende av att CI-kontrollerna är gröna. Därför är CD inte en release-gate för produktion; i en riktig leveranskedja måste deployment villkoras av godkända kontroller och skyddad miljö. Vi publicerar inte imagen till GHCR/Docker Hub och använder inga deployment-hemligheter här. Eftersom CI- och CD-jobben bygger var för sig på tillfälliga runners får vi inte bevis på att exakt samma image-binära innehåll har flyttats mellan miljöer. För det behöver man publicera och sedan distribuera samma image, helst identifierad med digest.

## 4. Kör motsvarande flöde lokalt

I Git Bash, från projektets rot:

```bash
bash scripts/deploy_local.sh
bash scripts/verify.sh
```

Skriptet bygger `library-management:local` och startar containern `library-management-demo`. Verifieringen väntar på `/health` och kontrollerar sedan att `/api/books` svarar med en JSON-lista. När du är klar:

```bash
docker logs library-management-demo
docker rm -f library-management-demo
docker ps -a
docker image ls library-management
```

Containern tas bort, men den lokala imagen finns kvar. Skriptet tar bort en redan existerande container med just övningens namn innan den startar en ny; använd inte namnet för en annan tjänst.

## 5. Förstå vad kontrollerna bevisar

- `docker ps` visar om containern körs; det bevisar inte att API:t fungerar.
- `docker logs` visar serverstart och diagnostik.
- `/health` bekräftar att health-endpointen svarar och ger status `ok`.
- `/api/books` bekräftar att en LMS-route svarar och returnerar en JSON-lista. Den verifierar inte alla biblioteksregler.
- Unit- och API-testerna i CI kontrollerar utlånings-, återlämnings- och sökbeteenden. De ersätter inte kontroll av en körande container.

Om verifieringen fallerar ska deployment-jobbet bli rött. Läs felsteget och containerloggarna; ändra inte testet eller verifieringskravet bara för att få en grön bock.

## Dag 5 klart när du kan

- skilja CI, Continuous Delivery och en faktisk produktionsdeployment åt
- visa en lyckad simulerad körning och förklara vad som händer på runnern
- hitta och ladda ner `test-results` från GitHub Actions
- verifiera både health och ett bok-API
- förklara skillnaden mellan container som körs, fungerande API och artifact som sparats
- resonera om risken när CI och CD startar var för sig
