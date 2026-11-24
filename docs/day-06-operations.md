# Dag 6: Felsökning, rollback och Kubernetes

## Mål

Följ ett fel från första röda steget till en verifierad rättning. Öva också på att återgå till en tidigare image och orientera dig i Kubernetes Deployment, Pods, Service och rollout. Kubernetes-delen är en lokal, valfri demonstration – inte ett krav för att köra bibliotekssystemet.

## 1. Felsök från första felet

När en workflow blir röd:

1. Kontrollera vilken branch, commit och trigger som startade körningen.
2. Öppna det första röda jobbet och steget; senare fel kan vara följdfel.
3. Läs loggen och skriv en hypotes om felet gäller kod/test, lint, Docker-build, containerstart, port eller verifiering.
4. Återskapa felet lokalt om möjligt och ändra en sak i taget.
5. Kör tester/lint igen och bekräfta rättningen med en ny GitHub Actions-körning.

Vid Docker-problem:

```bash
docker ps -a
docker logs library-management-demo
docker ps --format "table {{.Names}}\t{{.Ports}}"
docker inspect --format '{{.Config.Image}}' library-management-demo
```

En namnkonflikt betyder att en container med samma namn redan finns. En portkonflikt betyder att en annan process/container redan använder värddatorns port. Om port 8000 används kan du prova en annan värdport, exempelvis `-p 8001:8000`, och anropa `http://127.0.0.1:8001/health`. En grön CI kan fortfarande följas av deploymentfel: CI och CD är separata workflows med separata triggers.

## 2. Versionskontroll av den körande applikationen

API:t har nu `GET /version`, som returnerar:

```json
{"version":"1.1","environment":"demo"}
```

Testet i `tests/test_api.py` kontrollerar svaret. CI- och CD-jobben bygger och startar containern, kontrollerar `/health`, `/api/books` och därefter att `/version` faktiskt är `1.1`. En health check visar att tjänsten svarar; versionskontrollen visar vilken applikationsversion som svarar.

Om applikationsversionen ändras senare ska testet och båda workflowens förväntade version uppdateras avsiktligt. Docker-taggen `library-management:<commit-SHA>` identifierar källkodens commit; den ersätter inte `/version`-kontrollen.

## 3. Lokal rollback med sparad image

Rollback är ett versionsbyte tillbaka till en känd fungerande image, inte en omstart av samma felaktiga image. `scripts/deploy_local.sh` sparar den tidigare containerns image som `library-management:previous` när den ersätter en befintlig övningscontainer. Den första deploymenten har inget tidigare image att återställa.

Kör i Git Bash från projektroten:

```bash
bash scripts/deploy_local.sh
```

När du senare gör en ny deployment genom samma skript bevaras den föregående containerns image. Återställ den sedan och kontrollera image samt applikationsversion:

```bash
bash scripts/rollback_local.sh library-management:previous 1.1
docker inspect --format '{{.Config.Image}}' library-management-demo
docker logs library-management-demo
```

Skriptet verifierar först att rollback-imagen finns, startar den, kör health-/katalogkontroller och kontrollerar om den förväntade applikationsversionen angavs. Om ingen tidigare image finns stoppar skriptet innan den nuvarande containern tas bort.

Om båda byggen kommer från samma kod är detta bara en demonstration av versionsbyte – taggar gör inte innehållet olika. En verklig rollback kräver att den tidigare, fungerande imagen sparats innan uppgraderingen. Kontrollera också att en databasändring är kompatibel; att byta image återställer inte beständig data. Ibland är en ny korrigerande version (roll forward) säkrare än rollback.

## 4. Simulerad CD i GitHub Actions

CI bygger image, startar containern, verifierar API och version och städar sedan upp. CD-workflowen gör en separat, tillfällig deployment på en GitHub-runner och kontrollerar också `/version`. Om verifieringen misslyckas sparas containerloggar i Actions och containern tas bort med ett `always()`-steg.

CI och CD startas separat av push till feature-branchen. CD väntar inte automatiskt på att CI ska vara grön och är därför inte en produktions-release-gate. En riktig lösning behöver styra ordningen, använda skyddade miljöer och distribuera samma spårbara image från ett registry. Den här kurslösningen publicerar inte image och gör ingen permanent deployment.

## 5. Kubernetes lokalt (valfri orientering)

Manifesten i `k8s/` beskriver en Deployment med en Pod och en intern Service. Readiness- och liveness-proberna anropar `/health`. Image-pull är avstängd (`Never`), så image måste finnas tillgänglig i det lokala klustret. Docker Desktop Kubernetes kan använda den lokala imagen; för Minikube behöver du vanligtvis ladda in den:

```bash
docker build -t library-management:local .
minikube image load library-management:local
```

Kontrollera noggrant att `kubectl` pekar på ett lokalt övningskluster – kör inte dessa kommandon mot ett produktionscontext:

```bash
kubectl config current-context
kubectl apply -f k8s/
kubectl get deployments,pods,services
kubectl rollout status deployment/library-management
kubectl describe pods -l app=library-management
```

Öppna en lokal tunnel:

```bash
kubectl port-forward service/library-management 8080:80
```

I en annan terminal verifierar du `http://127.0.0.1:8080/health` och `http://127.0.0.1:8080/version`. Avsluta port-forward med `Ctrl+C`.

För att se self-healing kan du radera en av Deploymentens pods och observera att Kubernetes skapar en ny:

```bash
kubectl get pods
kubectl delete pod POD-NAMN
kubectl get pods --watch
```

För en kontrollerad misslyckad rollout:

```bash
kubectl set image deployment/library-management library-management=library-management:does-not-exist
kubectl get pods
kubectl describe pods -l app=library-management
kubectl rollout history deployment/library-management
kubectl rollout undo deployment/library-management
kubectl rollout status deployment/library-management --timeout=60s
```

Den felaktiga imagen kan inte hämtas och den nya poden blir inte redo. `rollout undo` återgår till föregående Pod-template; det är inte samma sak som att ändra applikationsdata. Städa endast efter lokal övning:

```bash
kubectl delete -f k8s/
```

Kubernetes är mer komplext än vad en liten enskild applikation normalt behöver. Överväg det först när problem med flera noder, skalning, self-healing eller samordnade rollouts motiverar komplexiteten.

## Dag 6 klart när du kan

- visa felsökningskedjan logg → hypotes → ändring → grön kontroll
- skilja containerstatus, health check och applikationsversion åt
- beskriva när rollback är möjlig och varför sparade, versionsmärkta images behövs
- orientera dig i Pods, Deployment, Service och `kubectl rollout`
- beskriva begränsningarna: lokal in-memory-data, ingen registry-publicering och ingen produktionsdeployment
