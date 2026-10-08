# Student

FastAPI-Appserver zur Verwaltung von Studierendendaten.

## Stand und Technik

Eine minimale FastAPI-Anwendung unter `src/student/` ist eingerichtet.
`GET /hello/` liefert HTTP 200 mit `{"Hello": "World"}` als JSON.
Der Server läuft über HTTPS mit einem selbstsignierten Zertifikat; Host, Port und
TLS-Dateien kommen aus der Konfigurationsdatei `app.toml`.
Ein HTTP-Test prüft Statuscode, Content-Type und Antwort ohne externe Dienste.
Geplant: REST und GraphQL, Pydantic, SQLAlchemy/PostgreSQL, Keycloak und Docker.
Python und Abhängigkeiten werden mit uv verwaltet; Qualitätssicherung erfolgt
mit pytest, Ruff und ty, ergänzt um SonarQube und OWASP Dependency Check.

## Einrichtung

Voraussetzungen: Python >=3.15 und uv >=0.12.20, entsprechend dem FastAPI-Beispiel.
Die installierten Versionen vor der Einrichtung prüfen:

```powershell
python --version
uv --version
```

Python 3.15 ist derzeit nur als Release Candidate verfügbar. uv lädt Vorabversionen
nicht automatisch herunter, deshalb einmalig:

```powershell
uv python install 3.15
```

Im Projektverzeichnis die virtuelle Umgebung und alle Abhängigkeiten einrichten:

```powershell
uv sync --all-groups
```

Das Paket wird dabei aus `src/student/` installiert. FastAPI und Uvicorn werden
zur Laufzeit benötigt, pytest, httpx und python-dotenv für Tests und Hilfsskripte
sowie Ruff und ty für die Codeprüfung. `uv.lock` hält die aufgelösten Versionen fest.

Für Python 3.15 gibt es noch kein fertiges Wheel von `pydantic-core`. uv baut das
Paket deshalb beim ersten `uv sync` mit Rust aus dem Quellcode; das dauert einige
Minuten. Voraussetzung ist eine Rust-Installation (`cargo --version`).

Für OWASP Dependency Check wird eine lokale `.env` benötigt (siehe
[Sicherheits- und Codeanalyse](#sicherheits--und-codeanalyse)):

```powershell
Copy-Item .env.example .env
```

## Server starten

Der Eintrag `student = "student:main"` in `pyproject.toml` startet Uvicorn:

```powershell
uv run student
```

Endpunkte: <https://127.0.0.1:8000/hello/> und
<https://127.0.0.1:8000/rest/1> (Studierender mit der ID 1). Da das Zertifikat
selbstsigniert ist, zeigt der Browser beim ersten Aufruf eine Warnung, die man für
die Entwicklung bestätigt.

Jede Response enthält Security-Header (HSTS, `nosniff`, `X-Frame-Options`,
Content-Security-Policy). Die Content-Security-Policy erlaubt nur Inhalte vom
eigenen Server; die Swagger-Oberfläche unter `/docs` lädt ihre Skripte aber von
einem CDN und bleibt deshalb im Browser leer. Die API-Beschreibung ist weiterhin
unter <https://127.0.0.1:8000/openapi.json> abrufbar; zum manuellen Testen dient
Bruno (siehe unten).

Beenden mit `Strg+C`. Solange der Browser noch eine Verbindung offen hält, wartet
Uvicorn bei „Shutting down“; dann den Tab schließen oder ein zweites Mal `Strg+C`
drücken.

## Konfiguration

Die Konfiguration liegt in `src/student/config/resources/app.toml` und wird beim
Start mit `tomllib` eingelesen:

- `[server]`: `host-binding` (Standard `127.0.0.1`) und `port` (Standard `8000`)
- `[tls]`: Dateinamen von `key` (Standard `key.pem`) und `certificate`
  (Standard `certificate.crt`) im Verzeichnis `resources/tls/`

Auskommentierte Einträge verwenden den Standardwert. Das Paket `student.config`
stellt die Werte für die Anwendung bereit. Der private Schlüssel ist bewusst im
Repository, da er nur für die lokale Entwicklung dient.

## PostgreSQL

Der Datenbankserver läuft als Docker-Container mit TLS (Datenbank, DB-User und Schema
jeweils `student`). Die einmalige Einrichtung pro Rechner und der tägliche Start sind
in [extras/compose/postgres/ReadMe.md](extras/compose/postgres/ReadMe.md) beschrieben.
Die Anwendung greift noch nicht auf die Datenbank zu; das folgt mit SQLAlchemy.

## Manuelle Tests mit Bruno

Die Bruno-Collection liegt in `extras/bruno/student` (OpenCollection-Format wie im
FastAPI-Beispiel). In Bruno (`C:\Zimmermann\Bruno\Bruno.exe`) über
*Open Collection* den Ordner `extras\bruno\student` öffnen. Da das Zertifikat
selbstsigniert ist, unter *Preferences > General* die Option
*SSL/TLS Certificate Verification* deaktivieren.

Jeder Request enthält Assertions (Statuscode, Header, Body). Mit dem Server im
Hintergrund (`uv run student`) lassen sich alle Requests über *Run* auf der
Collection auf einmal ausführen. Die Variable `baseUrl` steht in
`opencollection.yml`.

## Tests und Codeprüfung

Die Tests verwenden FastAPIs `TestClient`; ein separat gestarteter Server,
PostgreSQL und Keycloak sind dafür nicht erforderlich.

```powershell
uv run pytest
uv run ruff check --preview src tests
uv run ruff format --preview --check src tests
uv run ty check src tests/integration
```

Ruff verwendet das Regelset aus dem FastAPI-Beispiel (`[tool.ruff.lint]` in
`pyproject.toml`), unter anderem mit Regeln für Sicherheit, Docstrings und
Import-Sortierung. Die Prüfungen vor jedem Push lokal ausführen, da die CI sonst
fehlschlägt.

`tests/unit` wird bei der Typprüfung ergänzt, sobald dort Tests vorhanden sind.
Beim Testlauf erscheint eine Deprecation-Warnung zur Nutzung von httpx im
TestClient mit dem Hinweis auf httpx2. Der Test besteht; die Umstellung bleibt ein
offener Punkt für ein späteres Dependency-Paket.

## Continuous Integration

Der Workflow [CI](.github/workflows/ci.yml) führt bei Push und Pull Request auf
GitHub den HTTP-Test, Ruff, die Formatprüfung und ty aus. Er läuft auf Ubuntu
mit uv 0.12.23 und Python `"3.15"` mit `allow-prereleases: true`. Solange es
kein finales Python 3.15 gibt, wird der neueste Release Candidate verwendet,
danach automatisch die finale Version.

`uv sync --locked --all-groups` installiert die Abhängigkeiten aus `uv.lock`
und bricht ab, falls die Lockdatei nicht zur Projektkonfiguration passt.
Auch die Prüfungen verwenden `uv run --locked`. Externe Dienste und Secrets
sind für den bestehenden Test nicht erforderlich.

Die Einrichtung orientiert sich an der
[offiziellen uv-Anleitung für GitHub Actions](https://docs.astral.sh/uv/guides/integration/github/).
Die verwendeten Actions sind auf Commit-SHAs festgelegt. Ergebnisse erscheinen
nach dem Push im GitHub-Reiter **Actions** und beim Pull Request unter den Checks.

## Sicherheits- und Codeanalyse

### Abhängigkeiten prüfen

```powershell
uv tree --outdated --all-groups --depth=1
uv audit
```

`uv tree --outdated` zeigt direkte Abhängigkeiten mit neueren Versionen,
`uv audit` gleicht alle Pakete aus `uv.lock` mit bekannten Sicherheitslücken ab.

### SonarQube

Der SonarQube-Server läuft als Docker-Container
([compose.yml](extras/compose/sonarqube/compose.yml)); die Daten liegen unter
`C:/Zimmermann/volumes/sonarqube`:

```powershell
cd extras\compose\sonarqube
docker compose up
```

Beim ersten Start unter <http://localhost:9000> mit `admin`/`admin` anmelden, das
Passwort ändern und unter *My Account > Security*
(<http://localhost:9000/account/security>) einen *Global Analysis Token* erzeugen.
Jeder nutzt seinen eigenen lokalen Server und Token. Der Token steht deshalb nicht
in `sonar-project.properties`, sondern als Windows-Umgebungsvariable:

```powershell
[Environment]::SetEnvironmentVariable("SONAR_TOKEN", "<Token>", "User")
```

Danach VS Code bzw. das Terminal neu starten. Die Analyse startet man in einem
zweiten Terminal im Projektverzeichnis; das Ergebnis erscheint unter
<http://localhost:9000> im Projekt `student`:

```powershell
uv run python sonar-scanner.py
```

Herunterfahren mit `docker compose down` im Verzeichnis `extras\compose\sonarqube`.

### OWASP Dependency Check

OWASP Dependency Check gleicht die installierten Pakete mit der NVD-Datenbank ab.
Dafür wird ein eigener API-Key benötigt
(<https://nvd.nist.gov/developers/request-an-api-key>), der in der lokalen `.env`
als `NVD_API_KEY` eingetragen wird. `.env` ist in `.gitignore`; `.env.example`
dient als Vorlage.

```powershell
uv run extras/dependency-check.py
```

Der Report wird als `dependency-check-report.html` im Projektverzeichnis abgelegt.
Die Python-Analyzer sind bei Dependency Check experimentell und werden im Skript
mit `--enableExperimental` aktiviert; ohne diese Option werden keine Python-Pakete
geprüft. Bekannte Fehlalarme stehen mit Begründung in
[extras/suppression.xml](extras/suppression.xml).

## Zusammenarbeit

Vorläufige Aufteilung für zwei Personen; die Zuordnung ist noch offen:

- Person A: Datenmodell, Repository, Services und Unit-Tests.
- Person B: REST, GraphQL, Security und Integrationstests.
- Gemeinsam: Schnittstellen, Konfiguration, CI und Dokumentation.

Gearbeitet wird nach der `VORGEHENSWEISE.md` aus dem FastAPI-Beispiel.
Abgeschlossen sind die Abschnitte „Elementare Infrastruktur und einfacher Server“
(Endpunkt, HTTPS, Konfiguration mit TOML) und „Codeanalyse, Formatierung,
Typprüfung und Sicherheit“ (Ruff, ty, CI, uv audit, SonarQube, OWASP Dependency
Check) sowie „Infrastruktur“ (Schichten Router → Service → Repository mit
Dependency Injection, gebündelte Router, gzip, Security-Header). Bruno ist bereits
eingerichtet. Als Nächstes folgt der Abschnitt „REST-Schnittstelle, DB-Zugriff,
Validierung, Bruno und Testen“.

Datenmodell: Student mit einer 1:1-Beziehung zu Adresse und einer 1:N-Beziehung zu
Prüfungsleistungen. Bis zur Anbindung von PostgreSQL liefert das Repository
Beispieldaten aus dem Speicher.
