# Student

FastAPI-Appserver zur Verwaltung von Studierendendaten.

## Stand und Technik

Python-Projektkonfiguration und Source-Layout unter `src/student/` sind vorhanden.
Die Anwendung ist noch nicht startbar.
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

Das Paket wird dabei aus `src/student/` installiert. Aktuell werden nur die
Build-Konfiguration sowie Ruff und ty benötigt; Laufzeitabhängigkeiten folgen
mit dem ersten FastAPI-Endpunkt. `uv.lock` hält die aufgelösten Versionen fest.

Import und vorhandenen Quellcode prüfen:

```powershell
uv run python -c "import student; print(student.__file__)"
uv run ruff check --preview src
uv run ruff format --preview --check src
uv run ty check src
```

Tests und ein Server-Startbefehl folgen mit dem ersten Endpunkt.

## Zusammenarbeit

Vorläufige Aufteilung für zwei Personen; die Zuordnung ist noch offen:

- Person A: Datenmodell, Repository, Services und Unit-Tests.
- Person B: REST, GraphQL, Security und Integrationstests.
- Gemeinsam: Schnittstellen, Konfiguration, CI und Dokumentation.

Nächster Schritt: einfacher FastAPI-Endpunkt mit passendem Test.
