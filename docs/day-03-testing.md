# Dag 3: Testning, kvalitet och Quality Gates för bibliotekssystemet

## Mål

En lyckad build visar att koden går att bygga, inte att bibliotekets regler fungerar. Dag 3 använder testresultat som riskkontroller och visar hur en misslyckad kontroll ska stoppa leveranskedjan.

## 1. Kör kontrollerna lokalt

Från projektets rot:

```powershell
python -m pytest -v
ruff check app tests
```

Pytest kör kodens testfall. Ruff analyserar kodkvalitet utan att köra applikationen. De fångar olika saker; ett godkänt resultat från den ena ersätter inte den andra.

## 2. Knyt testerna till biblioteksrisker

| Testnivå | Vad den kontrollerar i projektet | Risk den minskar |
|---|---|---|
| Unit (`tests/test_service.py`) | Söklogik, utlåningsregler och återlämning direkt i `LibraryService` | Fel i affärsregler och tillstånd |
| API/integration (`tests/test_api.py`) | HTTP-anrop, JSON, statuskoder och samspelet mellan FastAPI och tjänsten | Fel i routes, validering eller felöversättning |
| Manuell systemkontroll | Starta appen och prova `/docs`; CD-simuleringen kontrollerar `/health` | Fel i start och container-/deployflöde |

Pyramiden är ett sätt att resonera om hastighet och risk, inte ett krav på ett visst antal tester. Unit-tester är snabba och många; API/integrationstester ger kontroll av delar tillsammans; fulla end-to-end-tester är dyrare och kan läggas till när fler riktiga användarflöden finns.

De centrala acceptansfallen för Library Management System är:

- en utlånad bok kan inte lånas en gång till (`409`)
- en bok eller användare som saknas kan inte lånas (`404`)
- återlämning gör boken tillgänglig igen
- sökning matchar titel och författare utan hänsyn till versaler/gemener

Ett grönt testresultat betyder bara att de beteenden testerna beskriver passerar. Det bevisar inte att alla fel, säkerhetsrisker eller produktionssituationer är täckta.

## 3. Gör ett kontrollerat rött test lokalt

Det här demonstrerar att testet faktiskt kan upptäcka en felaktig förväntan. I `tests/test_api.py`, hitta `test_cannot_borrow_a_missing_or_already_borrowed_book` och ändra tillfälligt den sista förväntningen från `409` till `200`:

```python
assert second_loan.status_code == 200  # Tillfälligt felaktig förväntan
```

Kör just testet:

```powershell
python -m pytest tests/test_api.py::test_cannot_borrow_a_missing_or_already_borrowed_book -q
```

Testet ska bli rött: API:t ger `409`, eftersom boken redan är utlånad. Det är förväntningen `200` som är fel. Ändra tillbaka till `409` för att återställa testet och kör sedan hela sviten igen:

```powershell
python -m pytest -q
ruff check app tests
```

**Viktigt i den här arbetskopian:** projektändringarna kan vara osparade i Git. Återställ inte hela testfilen med `git restore tests/test_api.py` och byt inte branch på chans; det kan kasta bort projektarbete. Återställ bara den enda ändrade förväntningen. Skapa inte en commit med det avsiktligt felaktiga testet i din vanliga arbetsbranch.

## 4. Följ kontrollen genom den faktiska CI:n

Läs `.github/workflows/ci.yml`:

1. Workflowen startar vid push till `main` eller pull request mot `main`.
2. Jobbet `test` kör Ruff och därefter Pytest på en GitHub-hosted Ubuntu-runner.
3. Jobbet `build-image` har `needs: test`, så Docker-imagen byggs först om testjobbet lyckas.

En push till en vanlig feature-branch startar alltså inte den här workflowen. För att se kontroller på din ändring ska pull requesten riktas mot `main` i din egen fork. Om ingen körning startar, kontrollera först aktuell katalog, `git branch --show-current`, `git remote -v`, Actions-status och PR:ens målbranch.

Vid rött resultat: öppna det första misslyckade steget och läs felet, rätta orsaken, kör kontrollerna lokalt och pusha rättningen till samma PR-branch. En varning är inte samma sak som ett misslyckat test; läs exit status och resultatet innan du drar slutsatser.

## 5. Quality Gate och skyddad merge

I den nuvarande pipelinen fungerar `test`-jobbet som gate för `build-image`: om lint eller tester misslyckas ska imagen inte byggas. Men en grön workflow blockerar inte automatiskt merge. Repositoryts ägare behöver konfigurera en ruleset/branch protection som kräver pull request och godkänd status check om det ska vara obligatoriskt.

Dag 3-guiden ber dig studera **Settings → Rules → Rulesets** och flikarna **Commits** och **Checks**. Ändra inte repository-inställningar i övningen. En code review är dessutom en mänsklig kontroll; den ersätter inte testerna.

## 6. Säkerhet som del av flödet

Säkerhetskontroller kompletterar testerna; de svarar på andra frågor:

- **Dependabot** bevakar kända sårbarheter i beroenden och kan föreslå uppdateringar.
- **CodeQL/code scanning** söker efter säkerhetsrisker i kodmönster utan att köra vanliga användarflöden.
- **Secret scanning** kan upptäcka vissa nycklar eller tokens som råkat checkas in. Lägg aldrig riktiga hemligheter i källkod; använd GitHub Actions secrets när ett workflow verkligen behöver dem.

De här kontrollerna är inte samma sak som befintlig Ruff/Pytest-körning och de aktiveras inte av den nuvarande `ci.yml`. Dag 3:s security-princip är att granska beroenden, kod och hemligheter kontinuerligt, inte först vid release. För övningen: studera GitHub Security-inställningarna och ändra dem inte utan behörighet eller kursinstruktion.

## Dag 3 klart när du kan

- förklara skillnaden mellan Pytest, Ruff och en säkerhetsanalys
- visa vilket biblioteksbeteende varje viktigt test skyddar
- få ett avsiktligt fel att ge rött test och sedan återställa ett grönt resultat
- förklara varför CI måste stoppa image-build när testjobbet misslyckas
- skilja en workflow-status från en ruleset som faktiskt kräver godkännande före merge
- beskriva varför gröna tester inte ensamma bevisar full kvalitet eller säkerhet
