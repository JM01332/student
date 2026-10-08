# Student

FastAPI-Appserver zur Verwaltung von Studierendendaten.

## Stand und Technik

Eine minimale FastAPI-Anwendung unter `src/student/` ist eingerichtet.
`GET /hello/` liefert HTTP 200 mit `{"Hello": "World"}` als JSON.
Ein HTTP-Test prüft Statuscode, Content-Type und Antwort ohne externe Dienste.
Geplant: REST und GraphQL, Pydantic, SQLAlchemy/PostgreSQL, Keycloak und Docker.
Python und Abhängigkeiten werden mit uv verwaltet; Qualitätssicherung erfolgt
mit pytest, Ruff und ty oder Pyrefly.

## Einrichtung

Voraussetzungen: Python >=3.15 und uv >=0.12.20, entsprechend dem FastAPI-Beispiel.
Die installierten Versionen vor der Einrichtung prüfen:

```powershell
python --version
uv --version
```

Im Projektverzeichnis die virtuelle Umgebung und alle Abhängigkeiten einrichten:

```powershell
uv sync --all-groups
```

Das Paket wird dabei aus `src/student/` installiert. FastAPI und Uvicorn werden
zur Laufzeit benötigt, pytest und httpx für Tests sowie Ruff und ty für die
Codeprüfung. `uv.lock` hält die aufgelösten Versionen fest.

## Server starten

Der Eintrag `student = "student:main"` in `pyproject.toml` startet Uvicorn:

```powershell
uv run student
```

Endpunkt: <http://127.0.0.1:8000/hello/>, API-Dokumentation:
<http://127.0.0.1:8000/docs>. Beenden mit `Strg+C`.
Der Entwicklungsserver bindet lokal an `127.0.0.1:8000` und verwendet HTTP.

## Tests und Codeprüfung

Die Tests verwenden FastAPIs `TestClient`; ein separat gestarteter Server,
PostgreSQL und Keycloak sind dafür nicht erforderlich.

```powershell
uv run pytest
uv run ruff check --preview src tests
uv run ruff format --preview --check src tests
uv run ty check src tests/integration
```

`tests/unit` wird bei der Typprüfung ergänzt, sobald dort Tests vorhanden sind.
Beim Testlauf mit Starlette 1.7.0 erscheint eine Deprecation-Warnung zur Nutzung
von httpx im TestClient mit dem Hinweis auf httpx2. Der Test besteht; die
Umstellung bleibt ein offener Punkt für ein späteres Dependency-Paket.

## Zusammenarbeit

Vorläufige Aufteilung für zwei Personen; die Zuordnung ist noch offen:

- Person A: Datenmodell, Repository, Services und Unit-Tests.
- Person B: REST, GraphQL, Security und Integrationstests.
- Gemeinsam: Schnittstellen, Konfiguration, CI und Dokumentation.

Abgeschlossen: einfacher FastAPI-Endpunkt mit passendem Test.
Das nächste kleine Aufgabenpaket wird gemeinsam festgelegt.
